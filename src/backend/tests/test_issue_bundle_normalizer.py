from __future__ import annotations

import asyncio
import csv
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import BASE_DIR
from app.services.issue_bundle_normalizer import (
    CollectedCandidateBatch,
    DailyDartIssueCollector,
    DataAIssueBundleNormalizer,
)
from app.services.issue_snapshot_publisher import (
    IssueSnapshotPublisher,
    read_active_snapshot,
)
from app.services.issue_sync_workflow import (
    InternalIssueSyncWorkflow,
    IssueCollectionResult,
    RecalculationResult,
)
from app.utils.csv_validator import validate_data_a_bundle
from app.utils.issue_rules import candidate_content_hash, canonicalize_url


ROOT = Path(BASE_DIR)
NOW = datetime(2026, 7, 26, 1, 0, tzinfo=timezone.utc)


def candidate(
    *,
    receipt: str,
    title: str,
    description: str,
    company_id: str = "005930",
    company_name: str = "삼성전자",
) -> dict:
    url = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt}"
    row = {
        "candidate_id": "CND-9999",
        "company_id": company_id,
        "company_name": company_name,
        "detection_source_type": "dart_disclosure",
        "source_name": "dart.fss.or.kr",
        "external_id": receipt,
        "query": f"{company_name} Open DART disclosure",
        "title": title,
        "normalized_title": "".join(title.split()).lower(),
        "published_at": "2026-07-26",
        "collected_at": NOW.isoformat(),
        "url": url,
        "canonical_url": canonicalize_url(url),
        "description": description,
        "content_hash": "",
        "validation_status": "pending",
        "matched_event_id": None,
        "rejection_reason": None,
    }
    row["content_hash"] = candidate_content_hash(row)
    return row


def batch(tmp_path: Path, row: dict) -> CollectedCandidateBatch:
    evidence = tmp_path / f"{row['external_id']}.json"
    evidence.write_text('{"provider":"open_dart","status":"000"}', encoding="utf-8")
    payload = evidence.read_bytes()
    return CollectedCandidateBatch(
        candidates=(row,),
        evidence_path=evidence,
        evidence_hash=hashlib.sha256(payload).hexdigest(),
        provider="open_dart",
    )


def rows(root: Path, relative_path: str) -> list[dict]:
    with (root / relative_path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize(tmp_path: Path, row: dict):
    normalizer = DataAIssueBundleNormalizer(
        current_bundle_root=lambda: ROOT,
        runtime_root=tmp_path / "runtime",
    )
    return normalizer.normalize(IssueCollectionResult((batch(tmp_path, row),), 1))


def test_high_confidence_dart_event_builds_complete_validated_bundle(tmp_path):
    prepared = normalize(
        tmp_path,
        candidate(
            receipt="20260726809999",
            title="중대재해 발생",
            description="반도체 사업장 중대재해 발생 공시",
        ),
    )
    try:
        bundle = validate_data_a_bundle(str(prepared.bundle_root))
        created_candidate = next(
            row
            for row in bundle["candidates"]
            if row["external_id"] == "20260726809999"
        )
        created_event = next(
            row
            for row in bundle["events"]
            if row["event_id"] == created_candidate["matched_event_id"]
        )
        created_source = next(
            row
            for row in bundle["sources"]
            if row["external_id"] == "20260726809999"
        )

        assert created_candidate["validation_status"] == "validated"
        assert created_event["status"] == "confirmed"
        assert created_event["event_category"] == "occupational_safety"
        assert created_event["linked_indicator_id"] == "S01"
        assert created_event["authority_confirmed"] is True
        assert created_source["validation_method"] == "dart_receipt"
        assert (
            prepared.bundle_root
            / "data/raw/reports"
            / created_source["file_name"]
        ).is_file()
    finally:
        prepared.cleanup()

    assert not prepared.bundle_root.exists()


def test_unclassified_dart_filing_is_retained_as_rejected_warning(tmp_path):
    before_events = rows(ROOT, "data/processed/events.csv")
    prepared = normalize(
        tmp_path,
        candidate(
            receipt="20260726808888",
            title="임원ㆍ주요주주 특정증권등 소유상황보고서",
            description="정기 소유상황 공시",
        ),
    )
    try:
        bundle = validate_data_a_bundle(str(prepared.bundle_root))
        created_candidate = next(
            row
            for row in bundle["candidates"]
            if row["external_id"] == "20260726808888"
        )
        assert created_candidate["validation_status"] == "rejected"
        assert created_candidate["matched_event_id"] is None
        assert created_candidate["rejection_reason"] == "no_approved_esg_event_rule_match"
        assert len(bundle["events"]) == len(before_events)
    finally:
        prepared.cleanup()


def test_existing_candidate_is_deduplicated_without_new_event_or_source(tmp_path):
    existing = next(
        row
        for row in rows(ROOT, "data/candidate/news_candidates.csv")
        if row["external_id"] == "20260626801398"
    )
    prepared = normalize(tmp_path, existing)
    try:
        bundle = validate_data_a_bundle(str(prepared.bundle_root))
        matches = [
            row
            for row in bundle["candidates"]
            if row["external_id"] == "20260626801398"
        ]
        assert len(matches) == 1
        assert len(bundle["events"]) == len(rows(ROOT, "data/processed/events.csv"))
        assert len(bundle["sources"]) == len(rows(ROOT, "data/processed/sources.csv"))
    finally:
        prepared.cleanup()


def test_daily_collector_reports_partial_success_when_one_company_fails(tmp_path):
    row = candidate(
        receipt="20260726807777",
        title="중대재해 발생",
        description="중대재해 발생 공시",
    )
    evidence_batch = batch(tmp_path, row)

    class Service:
        def collect_company(
            self, company, begin_date, end_date, *, page_no=1, page_count=100
        ):
            if company.company_id == "000660":
                raise RuntimeError("provider unavailable")
            return SimpleNamespace(
                candidates=list(evidence_batch.candidates),
                raw_artifact=SimpleNamespace(
                    path=evidence_batch.evidence_path,
                    content_hash=evidence_batch.evidence_hash,
                ),
            )

    result = DailyDartIssueCollector(Service(), now=lambda: NOW).collect()

    assert result.status == "partial_success"
    assert result.collected_items == 1
    assert len(result.payload) == 1


def test_production_normalizer_runs_through_atomic_publication_and_recalculation(
    tmp_path,
):
    collected_batch = batch(
        tmp_path,
        candidate(
            receipt="20260726806666",
            title="중대재해 발생",
            description="반도체 사업장 중대재해 발생 공시",
        ),
    )

    class Collector:
        def collect(self):
            return IssueCollectionResult((collected_batch,), 1)

    class Recalculator:
        def __init__(self):
            self.versions = []

        async def recalculate(self, *, snapshot_version, published_at):
            self.versions.append(snapshot_version)
            return RecalculationResult(NOW.isoformat(), snapshot_version)

    runtime_root = tmp_path / "runtime"
    recalculator = Recalculator()
    workflow = InternalIssueSyncWorkflow(
        Collector(),
        DataAIssueBundleNormalizer(
            current_bundle_root=lambda: ROOT,
            runtime_root=runtime_root,
        ),
        IssueSnapshotPublisher(runtime_root, now=lambda: NOW),
        recalculation=recalculator,
        current_bundle_root=lambda: ROOT,
    )
    stages = []

    result = asyncio.run(workflow.run(stages.append))

    assert stages == ["normalizing", "validating", "publishing", "recalculating"]
    assert result.snapshot_updated is True
    assert result.recalculation_triggered is True
    assert recalculator.versions == [result.published_snapshot_version]
    assert read_active_snapshot(runtime_root) is not None
    assert list((runtime_root / "prepared").iterdir()) == []
