from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.exceptions import CSVValidationError
from app.services.dart_disclosures import (
    DART_COMPANIES,
    DartCandidateNormalizer,
    DartCandidateStore,
    DartCollectionService,
    DartConfigurationError,
    DartDisclosureProvider,
    DartProviderError,
    DartRawPage,
    DartRawStore,
)
from app.utils.csv_validator import validate_candidate_rows
from app.utils.issue_rules import candidate_dedup_key


NOW = datetime(2026, 7, 22, 8, 0, tzinfo=timezone.utc)
SECRET = "x" * 40


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeClient:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def disclosure_payload(company, *, receipt="20260722000001", title="주요사항보고서"):
    return {
        "status": "000",
        "message": "정상",
        "page_no": 1,
        "page_count": 10,
        "total_count": 1,
        "total_page": 1,
        "list": [
            {
                "corp_cls": "Y",
                "corp_name": company.company_name,
                "corp_code": company.corp_code,
                "stock_code": company.company_id,
                "report_nm": title,
                "rcept_no": receipt,
                "flr_nm": company.company_name,
                "rcept_dt": "20260722",
                "rm": "유",
            }
        ],
    }


def make_provider(client, **kwargs):
    return DartDisclosureProvider(
        api_key=SECRET,
        client=client,
        timeout_seconds=2.5,
        retry_backoff_seconds=0.1,
        now=lambda: NOW,
        **kwargs,
    )


@pytest.mark.parametrize("company", DART_COMPANIES)
def test_provider_queries_each_company_with_official_mapping(company):
    client = FakeClient([FakeResponse(disclosure_payload(company))])
    provider = make_provider(client)

    page = provider.fetch_company(company, "20260701", "20260722", page_count=10)

    assert page.payload["list"][0]["rcept_no"] == "20260722000001"
    url, request = client.calls[0]
    assert url == "https://opendart.fss.or.kr/api/list.json"
    assert request["timeout"] == 2.5
    assert request["params"]["corp_code"] == company.corp_code
    assert request["params"]["bgn_de"] == "20260701"
    assert request["params"]["end_de"] == "20260722"
    assert request["params"]["page_count"] == 10


def test_provider_retries_timeout_and_retryable_dart_status():
    company = DART_COMPANIES[0]
    client = FakeClient(
        [
            httpx.ReadTimeout("timeout"),
            FakeResponse({"status": "800", "message": "점검 중"}),
            FakeResponse(disclosure_payload(company)),
        ]
    )
    sleeps = []
    provider = make_provider(client, max_attempts=3, sleep=sleeps.append)

    page = provider.fetch_company(company, "20260701", "20260722")

    assert len(page.payload["list"]) == 1
    assert len(client.calls) == 3
    assert sleeps == [0.1, 0.2]


def test_provider_classifies_permanent_error_without_leaking_secret_or_response():
    response_message = f"invalid key {SECRET}"
    client = FakeClient(
        [FakeResponse({"status": "010", "message": response_message})]
    )
    provider = make_provider(client, max_attempts=3)

    with pytest.raises(DartProviderError) as captured:
        provider.fetch_company(DART_COMPANIES[0], "20260701", "20260722")

    assert captured.value.code == "DART_API_010"
    assert captured.value.retryable is False
    assert SECRET not in str(captured.value)
    assert response_message not in str(captured.value)
    assert len(client.calls) == 1


def test_provider_treats_no_data_as_successful_empty_page():
    client = FakeClient([FakeResponse({"status": "013", "message": "조회 없음"})])
    provider = make_provider(client)

    page = provider.fetch_company(DART_COMPANIES[0], "20260701", "20260722")

    assert page.payload.get("list", []) == []


def test_provider_requires_key_and_valid_query_bounds():
    with pytest.raises(DartConfigurationError):
        DartDisclosureProvider(api_key="")

    provider = make_provider(FakeClient([]))
    with pytest.raises(ValueError, match="begin_date"):
        provider.fetch_company(DART_COMPANIES[0], "20260723", "20260722")
    with pytest.raises(ValueError, match="page_count"):
        provider.fetch_company(
            DART_COMPANIES[0], "20260701", "20260722", page_count=101
        )


def test_collection_persists_raw_before_schema_shaped_pending_candidate(tmp_path):
    company = DART_COMPANIES[0]
    provider = make_provider(FakeClient([FakeResponse(disclosure_payload(company))]))
    service = DartCollectionService(
        provider,
        DartRawStore(tmp_path),
        DartCandidateStore(tmp_path),
    )

    batch = service.collect_company(company, "20260701", "20260722")

    assert batch.raw_artifact.path.is_file()
    assert batch.candidate_artifact.path.is_file()
    raw_envelope = json.loads(batch.raw_artifact.path.read_text(encoding="utf-8"))
    assert "crtfc_key" not in json.dumps(raw_envelope)
    assert SECRET not in json.dumps(raw_envelope)
    assert raw_envelope["response"]["list"][0]["rcept_no"] == "20260722000001"

    candidate = batch.candidates[0]
    assert candidate["company_id"] == "005930"
    assert candidate["validation_status"] == "pending"
    assert candidate["matched_event_id"] is None
    assert candidate["url"].endswith("rcpNo=20260722000001")
    assert batch.dedup_keys[0] == candidate_dedup_key(candidate)
    assert validate_candidate_rows(batch.candidates) == batch.candidates

    with batch.candidate_artifact.path.open(encoding="utf-8", newline="") as handle:
        stored = list(csv.DictReader(handle))
    assert stored[0]["validation_status"] == "pending"
    assert stored[0]["matched_event_id"] == ""


def test_malformed_disclosure_is_preserved_as_rejected_candidate():
    company = DART_COMPANIES[1]
    payload = disclosure_payload(company, receipt="bad-receipt")
    page = DartRawPage(
        company=company,
        begin_date="20260701",
        end_date="20260722",
        page_no=1,
        page_count=10,
        collected_at=NOW,
        payload=payload,
    )

    batch = DartCandidateNormalizer().normalize(page)

    candidate = batch.candidates[0]
    assert candidate["validation_status"] == "rejected"
    assert candidate["external_id"] is None
    assert candidate["matched_event_id"] is None
    assert candidate["rejection_reason"] == "invalid_dart_receipt_number"
    assert validate_candidate_rows(batch.candidates) == batch.candidates


def test_raw_artifact_remains_when_candidate_normalization_fails(tmp_path):
    company = DART_COMPANIES[0]
    provider = make_provider(FakeClient([FakeResponse(disclosure_payload(company))]))

    class FailingNormalizer:
        def normalize(self, page):
            raise RuntimeError("normalization failed")

    service = DartCollectionService(
        provider,
        DartRawStore(tmp_path),
        DartCandidateStore(tmp_path),
        normalizer=FailingNormalizer(),
    )

    with pytest.raises(RuntimeError, match="normalization failed"):
        service.collect_company(company, "20260701", "20260722")

    assert len(list((tmp_path / "raw" / "dart").rglob("*.json"))) == 1
    assert not (tmp_path / "candidate").exists()


def test_duplicate_dart_disclosure_is_retained_but_not_active():
    company = DART_COMPANIES[0]
    payload = disclosure_payload(company)
    payload["list"].append(dict(payload["list"][0]))
    page = DartRawPage(
        company=company,
        begin_date="20260701",
        end_date="20260722",
        page_no=1,
        page_count=10,
        collected_at=NOW,
        payload=payload,
    )

    batch = DartCandidateNormalizer().normalize(page)

    assert [row["validation_status"] for row in batch.candidates] == [
        "pending",
        "rejected",
    ]
    assert batch.candidates[1]["rejection_reason"] == "duplicate_dart_candidate"


def test_data_a_gate_rejects_receipt_that_does_not_match_viewer_url():
    company = DART_COMPANIES[0]
    page = DartRawPage(
        company=company,
        begin_date="20260701",
        end_date="20260722",
        page_no=1,
        page_count=10,
        collected_at=NOW,
        payload=disclosure_payload(company),
    )
    candidate = DartCandidateNormalizer().normalize(page).candidates[0]
    candidate["url"] = candidate["url"].replace("20260722000001", "20260722000002")
    candidate["canonical_url"] = candidate["url"]

    with pytest.raises(CSVValidationError) as captured:
        validate_candidate_rows([candidate])

    assert captured.value.code == "INVALID_CANDIDATE_DART_SOURCE"
