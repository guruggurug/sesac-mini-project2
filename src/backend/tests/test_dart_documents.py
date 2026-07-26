from __future__ import annotations

import hashlib
import io
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import BASE_DIR
from app.services.dart_disclosures import (
    DART_COMPANIES,
    DartCandidateStore,
    DartCollectionService,
    DartDisclosureProvider,
    DartDocumentArchive,
    DartDocumentProvider,
    DartDocumentResult,
    DartDocumentService,
    DartDocumentStore,
    DartDocumentTextExtractor,
    DartProviderError,
    DartRawStore,
    RuntimeArtifact,
)
from app.services.issue_bundle_normalizer import (
    DataAIssueBundleNormalizer,
    adapt_dart_batch,
)
from app.services.issue_sync_workflow import (
    IssueCollectionResult,
    scoring_relevant_bundle_changed,
)
from app.utils.csv_validator import validate_data_a_bundle


ROOT = Path(BASE_DIR)
NOW = datetime(2026, 7, 26, 1, 0, tzinfo=timezone.utc)
SECRET = "x" * 40
RECEIPT = "20260722000001"


class BinaryResponse:
    def __init__(self, content: bytes, status_code: int = 200):
        self.content = content
        self.status_code = status_code


class Client:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def document_zip(text: str, *, name: str = "document.xml") -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            name,
            f'<?xml version="1.0" encoding="utf-8"?><DOCUMENT><P>{text}</P></DOCUMENT>',
        )
    return buffer.getvalue()


def disclosure_payload(company, *, title="사업보고서"):
    return {
        "status": "000",
        "message": "정상",
        "page_no": 1,
        "page_count": 100,
        "total_count": 1,
        "total_page": 1,
        "list": [
            {
                "corp_cls": "Y",
                "corp_name": company.company_name,
                "corp_code": company.corp_code,
                "stock_code": company.company_id,
                "report_nm": title,
                "rcept_no": RECEIPT,
                "flr_nm": company.company_name,
                "rcept_dt": "20260722",
                "rm": "",
            }
        ],
    }


def list_provider(company, *, title="사업보고서"):
    class Response:
        status_code = 200

        def json(self):
            return disclosure_payload(company, title=title)

    return DartDisclosureProvider(
        api_key=SECRET,
        client=Client(Response()),
        max_attempts=1,
        now=lambda: NOW,
    )


def test_document_provider_downloads_official_zip_without_leaking_key():
    content = document_zip("중대재해 발생 사실")
    client = Client(BinaryResponse(content))
    provider = DartDocumentProvider(
        api_key=SECRET,
        client=client,
        max_attempts=1,
        now=lambda: NOW,
    )

    result = provider.fetch(RECEIPT)

    assert result.content == content
    assert result.receipt_no == RECEIPT
    url, request = client.calls[0]
    assert url == "https://opendart.fss.or.kr/api/document.xml"
    assert request["params"]["rcept_no"] == RECEIPT
    assert "crtfc_key" in request["params"]


def test_document_provider_maps_error_xml_to_sanitized_code():
    error_xml = b"<result><status>014</status><message>secret body</message></result>"
    provider = DartDocumentProvider(
        api_key=SECRET,
        client=Client(BinaryResponse(error_xml)),
        max_attempts=1,
    )

    with pytest.raises(DartProviderError) as captured:
        provider.fetch(RECEIPT)

    assert captured.value.code == "DART_DOCUMENT_014"
    assert "secret body" not in str(captured.value)
    assert SECRET not in str(captured.value)


def test_document_extractor_reads_xml_text_and_blocks_zip_slip():
    extractor = DartDocumentTextExtractor()

    text = extractor.extract(document_zip("반도체 사업장 중대재해 발생"))

    assert "중대재해 발생" in text

    unsafe = document_zip("unsafe", name="../outside.xml")
    with pytest.raises(ValueError, match="unsafe path"):
        extractor.extract(unsafe)


def test_document_extractor_rejects_excessive_uncompressed_size(monkeypatch):
    import app.services.dart_disclosures as dart_module

    monkeypatch.setattr(dart_module, "MAX_DOCUMENT_UNCOMPRESSED_BYTES", 10)

    with pytest.raises(ValueError, match="expands beyond"):
        DartDocumentTextExtractor().extract(document_zip("x" * 100))


def test_document_raw_archive_remains_when_extraction_fails(tmp_path):
    archive = DartDocumentArchive(RECEIPT, NOW, document_zip("본문"))

    class Provider:
        def fetch(self, receipt_no):
            return archive

    class Extractor:
        def extract(self, content):
            raise ValueError("parser failed")

    service = DartDocumentService(
        Provider(),
        DartDocumentStore(tmp_path),
        Extractor(),
    )

    with pytest.raises(ValueError, match="parser failed"):
        service.fetch_and_extract(RECEIPT)

    assert len(list((tmp_path / "raw/dart/documents").rglob("*.zip"))) == 1


def test_systemic_document_provider_failure_aborts_company_batch(tmp_path):
    class Documents:
        def fetch_and_extract(self, receipt_no):
            raise DartProviderError(
                "DART_DOCUMENT_NETWORK_ERROR",
                retryable=True,
            )

    service = DartCollectionService(
        list_provider(DART_COMPANIES[0]),
        DartRawStore(tmp_path),
        DartCandidateStore(tmp_path),
        document_service=Documents(),
    )

    with pytest.raises(DartProviderError) as captured:
        service.collect_company(
            DART_COMPANIES[0],
            "20260722",
            "20260722",
        )

    assert captured.value.code == "DART_DOCUMENT_NETWORK_ERROR"
    assert len(list((tmp_path / "raw/dart").glob("*/*.json"))) == 1
    assert not (tmp_path / "candidate/dart").exists()


def collection_service(
    tmp_path: Path,
    document_text: str,
    *,
    title: str = "사업보고서",
):
    company = DART_COMPANIES[0]
    archive_path = tmp_path / "document.zip"
    archive_path.write_bytes(document_zip(document_text))
    artifact = RuntimeArtifact(
        archive_path,
        hashlib.sha256(archive_path.read_bytes()).hexdigest(),
    )

    class Documents:
        def fetch_and_extract(self, receipt_no):
            return DartDocumentResult(artifact, document_text)

    return DartCollectionService(
        list_provider(company, title=title),
        DartRawStore(tmp_path / "runtime"),
        DartCandidateStore(tmp_path / "runtime"),
        document_service=Documents(),
    )


def test_collection_enriches_candidate_with_body_evidence(tmp_path):
    service = collection_service(
        tmp_path,
        "정기보고서 본문에서 반도체 사업장 중대재해 발생 사실을 공시하였다.",
    )

    batch = service.collect_company(
        DART_COMPANIES[0],
        "20260722",
        "20260722",
    )

    candidate = batch.candidates[0]
    assert candidate["validation_status"] == "pending"
    assert candidate["description"].startswith(
        "DART_BODY_MATCH[OCCUPATIONAL_SAFETY]"
    )
    assert RECEIPT in batch.document_artifacts


def test_collection_rejects_document_without_approved_body_evidence(tmp_path):
    service = collection_service(
        tmp_path,
        "임원 및 주요주주의 주식 소유 현황을 정기적으로 보고한다.",
    )

    batch = service.collect_company(
        DART_COMPANIES[0],
        "20260722",
        "20260722",
    )

    candidate = batch.candidates[0]
    assert candidate["validation_status"] == "rejected"
    assert (
        candidate["rejection_reason"]
        == "dart_document_no_approved_esg_event_match"
    )


def test_body_metric_name_alone_does_not_create_event_candidate(tmp_path):
    service = collection_service(
        tmp_path,
        "지속가능경영 지표로 산업재해율 0.10을 공시한다.",
    )

    batch = service.collect_company(
        DART_COMPANIES[0],
        "20260722",
        "20260722",
    )

    assert batch.candidates[0]["validation_status"] == "rejected"
    assert (
        batch.candidates[0]["rejection_reason"]
        == "dart_document_no_approved_esg_event_match"
    )


def test_body_only_match_publishes_reported_warning_without_recalculation(tmp_path):
    service = collection_service(
        tmp_path,
        "사업보고서 본문에 반도체 사업장 중대재해 발생 사실이 포함되어 있다.",
    )
    collected = service.collect_company(
        DART_COMPANIES[0],
        "20260722",
        "20260722",
    )
    normalizer = DataAIssueBundleNormalizer(
        current_bundle_root=lambda: ROOT,
        runtime_root=tmp_path / "normalizer",
    )

    prepared = normalizer.normalize(
        IssueCollectionResult((adapt_dart_batch(collected),), 1)
    )
    try:
        bundle = validate_data_a_bundle(str(prepared.bundle_root))
        candidate = next(
            row
            for row in bundle["candidates"]
            if row["external_id"] == RECEIPT
        )
        event = next(
            row
            for row in bundle["events"]
            if row["event_id"] == candidate["matched_event_id"]
        )
        source = next(
            row
            for row in bundle["sources"]
            if row["external_id"] == RECEIPT
        )

        assert candidate["validation_status"] == "validated"
        assert event["status"] == "reported"
        assert event["authority_confirmed"] is False
        assert source["file_name"].endswith(".zip")
        assert scoring_relevant_bundle_changed(ROOT, prepared.bundle_root) is False
    finally:
        prepared.cleanup()


def test_title_and_body_match_publish_confirmed_scoring_event(tmp_path):
    service = collection_service(
        tmp_path,
        "반도체 사업장 중대재해 발생 사실과 후속조치를 공시한다.",
        title="중대재해 발생",
    )
    collected = service.collect_company(
        DART_COMPANIES[0],
        "20260722",
        "20260722",
    )
    normalizer = DataAIssueBundleNormalizer(
        current_bundle_root=lambda: ROOT,
        runtime_root=tmp_path / "normalizer",
    )

    prepared = normalizer.normalize(
        IssueCollectionResult((adapt_dart_batch(collected),), 1)
    )
    try:
        bundle = validate_data_a_bundle(str(prepared.bundle_root))
        candidate = next(
            row
            for row in bundle["candidates"]
            if row["external_id"] == RECEIPT
        )
        event = next(
            row
            for row in bundle["events"]
            if row["event_id"] == candidate["matched_event_id"]
        )

        assert collected.candidates[0]["description"].startswith(
            "DART_TITLE_MATCH[OCCUPATIONAL_SAFETY]"
        )
        assert event["status"] == "confirmed"
        assert event["authority_confirmed"] is True
        assert scoring_relevant_bundle_changed(ROOT, prepared.bundle_root) is True
    finally:
        prepared.cleanup()
