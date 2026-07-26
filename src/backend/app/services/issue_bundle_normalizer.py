"""Production Data A normalization from collected candidates to a complete bundle."""

from __future__ import annotations

import csv
import hashlib
import os
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

from app.core.config import ISSUE_RUNTIME_DATA_DIR
from app.services.dart_disclosures import (
    DART_COMPANIES,
    DartCollectionBatch,
    DartCollectionService,
)
from app.services.issue_snapshot_publisher import (
    BUNDLE_FILES,
    resolve_data_a_bundle_root,
)
from app.services.issue_sync_workflow import (
    IssueCollectionResult,
    PreparedIssueBundle,
)
from app.services.news_collection import NewsCollectionBatch
from app.utils.csv_validator import validate_data_a_bundle
from app.utils.issue_rules import (
    calculate_event_severity,
    candidate_classification_rule,
    candidate_dedup_key,
    events_are_duplicates,
    load_issue_rules,
    source_dedup_key,
)


SEOUL = ZoneInfo("Asia/Seoul")


@dataclass(frozen=True)
class CollectedCandidateBatch:
    candidates: tuple[dict, ...]
    evidence_path: Path
    evidence_hash: str
    provider: str
    item_evidence: dict[str, tuple[Path, str]] = field(default_factory=dict)


@dataclass(frozen=True)
class CandidateClassification:
    event_category: str
    event_subcategory: str
    linked_indicator_id: str


class DailyDartIssueCollector:
    """Collect both companies over a bounded Seoul-date lookback window."""

    def __init__(
        self,
        service: DartCollectionService,
        *,
        lookback_days: int = 1,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        if lookback_days < 0:
            raise ValueError("lookback_days cannot be negative")
        self._service = service
        self._lookback_days = lookback_days
        self._now = now

    def collect(self) -> IssueCollectionResult:
        current = self._now()
        if current.tzinfo is None or current.utcoffset() is None:
            raise ValueError("collector clock must return a timezone-aware datetime")
        end_date = current.astimezone(SEOUL).date()
        begin_date = end_date - timedelta(days=self._lookback_days)
        # Local import avoids a module cycle while keeping daily and historical
        # collection on exactly the same pagination/document path.
        from app.services.dart_backfill import PagedDartIssueCollector

        return PagedDartIssueCollector(
            self._service,
            begin_date=begin_date,
            end_date=end_date,
        ).collect()


class DataAIssueBundleNormalizer:
    """Build an isolated, validated bundle without mutating the active snapshot."""

    def __init__(
        self,
        *,
        current_bundle_root: Callable[[], Path] = resolve_data_a_bundle_root,
        runtime_root: str | Path = ISSUE_RUNTIME_DATA_DIR,
    ) -> None:
        self._current_bundle_root = current_bundle_root
        self._runtime_root = Path(runtime_root)

    def normalize(self, collection: IssueCollectionResult) -> PreparedIssueBundle:
        batches = _candidate_batches(collection.payload)
        prepared_parent = self._runtime_root / "prepared"
        prepared_parent.mkdir(parents=True, exist_ok=True)
        prepared_root = Path(tempfile.mkdtemp(prefix="bundle-", dir=prepared_parent))

        def cleanup() -> None:
            shutil.rmtree(prepared_root, ignore_errors=True)

        try:
            _copy_bundle(self._current_bundle_root(), prepared_root)
            tables = {
                "candidates": _read_csv(
                    prepared_root / "data/candidate/news_candidates.csv"
                ),
                "sources": _read_csv(prepared_root / "data/processed/sources.csv"),
                "event_sources": _read_csv(
                    prepared_root / "data/processed/event_sources.csv"
                ),
                "events": _read_csv(prepared_root / "data/processed/events.csv"),
            }
            for batch in batches:
                self._merge_batch(prepared_root, batch, tables)
            _write_csv(
                prepared_root / "data/candidate/news_candidates.csv",
                tables["candidates"],
            )
            _write_csv(
                prepared_root / "data/processed/sources.csv", tables["sources"]
            )
            _write_csv(
                prepared_root / "data/processed/event_sources.csv",
                tables["event_sources"],
            )
            _write_csv(
                prepared_root / "data/processed/events.csv", tables["events"]
            )
            validate_data_a_bundle(str(prepared_root))
        except Exception:
            cleanup()
            raise
        return PreparedIssueBundle(prepared_root, cleanup=cleanup)

    def _merge_batch(
        self,
        prepared_root: Path,
        batch: CollectedCandidateBatch,
        tables: dict[str, list[dict]],
    ) -> None:
        candidates = tables["candidates"]
        existing_by_key = {candidate_dedup_key(row): row for row in candidates}
        existing_ids = {row["candidate_id"] for row in candidates}

        for incoming in batch.candidates:
            candidate = dict(incoming)
            key = candidate_dedup_key(candidate)
            duplicate = (
                existing_by_key.get(key)
                if candidate["validation_status"] != "rejected"
                else None
            )
            if duplicate is not None:
                duplicate["collected_at"] = max(
                    str(duplicate["collected_at"]), str(candidate["collected_at"])
                )
                continue

            candidate["candidate_id"] = _stable_unique_id(
                "CND", existing_ids, "|".join(key)
            )
            existing_ids.add(candidate["candidate_id"])
            classification = _classify_candidate(candidate)
            if candidate["validation_status"] == "rejected":
                pass
            elif classification is None:
                classification_rules = load_issue_rules()["candidate_classification"]
                candidate.update(
                    validation_status="rejected",
                    matched_event_id=None,
                    rejection_reason=classification_rules["unmatched_reason"],
                )
            elif (
                candidate["detection_source_type"] != "dart_disclosure"
                or not candidate.get("external_id")
            ):
                candidate.update(
                    validation_status="rejected",
                    matched_event_id=None,
                    rejection_reason="official_confirmation_required",
                )
            else:
                self._publishable_candidate(
                    prepared_root, batch, candidate, classification, tables
                )

            candidates.append(candidate)
            if candidate["validation_status"] != "rejected":
                existing_by_key[key] = candidate

    def _publishable_candidate(
        self,
        prepared_root: Path,
        batch: CollectedCandidateBatch,
        candidate: dict,
        classification: CandidateClassification,
        tables: dict[str, list[dict]],
    ) -> None:
        sources = tables["sources"]
        events = tables["events"]
        event_sources = tables["event_sources"]
        source_keys = {source_dedup_key(row): row for row in sources}
        source_ids = {row["source_id"] for row in sources}
        event_ids = {row["event_id"] for row in events}

        item_evidence = batch.item_evidence.get(str(candidate["external_id"]))
        if item_evidence is None:
            evidence_path = batch.evidence_path
            evidence_hash = batch.evidence_hash
            evidence_provider = batch.provider
        else:
            evidence_path, evidence_hash = item_evidence
            evidence_provider = f"{batch.provider}_document"
        evidence_name = (
            f"runtime_{evidence_provider}_{candidate['external_id']}_"
            f"{evidence_hash[:12]}{evidence_path.suffix or '.bin'}"
        )
        evidence_target = prepared_root / "data/raw/reports" / evidence_name
        evidence_target.parent.mkdir(parents=True, exist_ok=True)
        if not evidence_target.exists():
            shutil.copyfile(evidence_path, evidence_target)
        actual_evidence_hash = hashlib.sha256(evidence_target.read_bytes()).hexdigest()
        if actual_evidence_hash != evidence_hash:
            raise ValueError("collected evidence hash mismatch")

        source = {
            "source_id": "",
            "company_id": candidate["company_id"],
            "organization_name": "전자공시시스템(DART)",
            "source_type": "company_disclosure",
            "document_title": candidate["title"],
            "publication_year": str(candidate["published_at"])[:4],
            "external_id": candidate["external_id"],
            "file_name": evidence_name,
            "url": candidate["canonical_url"],
            "validation_method": "dart_receipt",
            "content_hash": evidence_hash,
            "validated": "true",
            "note": "Open DART 공식 API 원본에서 자동 수집·검증",
        }
        source_key = source_dedup_key(source)
        existing_source = source_keys.get(source_key)
        if existing_source is None:
            source["source_id"] = _stable_unique_id(
                "SRC", source_ids, "|".join(source_key)
            )
            source_ids.add(source["source_id"])
            sources.append(source)
        else:
            source = existing_source

        event = _event_from_candidate(candidate, classification, source["url"])
        duplicate_event = next(
            (existing for existing in events if events_are_duplicates(existing, event)),
            None,
        )
        if duplicate_event is None:
            event["event_id"] = _next_event_id(event_ids)
            event_ids.add(event["event_id"])
            events.append(event)
            event_sources.append(
                {
                    "event_id": event["event_id"],
                    "source_id": source["source_id"],
                    "source_role": "official_confirmation",
                    "is_primary": "true",
                    "note": "Open DART 법정공시 자동 확인",
                }
            )
        else:
            event = duplicate_event
            link_key = (event["event_id"], source["source_id"])
            existing_links = {
                (row["event_id"], row["source_id"]) for row in event_sources
            }
            if link_key not in existing_links:
                event_sources.append(
                    {
                        "event_id": event["event_id"],
                        "source_id": source["source_id"],
                        "source_role": "detection",
                        "is_primary": "false",
                        "note": "기존 사건과 결정적 중복 판정된 추가 DART 공시",
                    }
                )

        candidate.update(
            validation_status="validated",
            matched_event_id=event["event_id"],
            rejection_reason=None,
        )


def adapt_dart_batch(batch: DartCollectionBatch) -> CollectedCandidateBatch:
    """Adapt DART list and per-receipt document evidence to the bundle contract."""
    document_artifacts = getattr(batch, "document_artifacts", None) or {}
    return CollectedCandidateBatch(
        candidates=tuple(dict(row) for row in batch.candidates),
        evidence_path=batch.raw_artifact.path,
        evidence_hash=batch.raw_artifact.content_hash,
        provider="open_dart",
        item_evidence={
            receipt: (artifact.path, artifact.content_hash)
            for receipt, artifact in document_artifacts.items()
        },
    )


def adapt_news_batch(batch: NewsCollectionBatch) -> CollectedCandidateBatch:
    """Adapt provider-neutral news output to the shared bundle input contract."""
    return CollectedCandidateBatch(
        candidates=tuple(dict(row) for row in batch.candidates),
        evidence_path=batch.raw_artifact.path,
        evidence_hash=batch.raw_artifact.content_hash,
        provider="news",
    )


def _candidate_batches(payload: object) -> tuple[CollectedCandidateBatch, ...]:
    if not isinstance(payload, (tuple, list)):
        raise TypeError("issue collection payload must contain candidate batches")
    batches = tuple(payload)
    if not all(isinstance(batch, CollectedCandidateBatch) for batch in batches):
        raise TypeError("unsupported candidate batch in issue collection payload")
    return batches


def _classify_candidate(candidate: dict) -> CandidateClassification | None:
    text = f"{candidate.get('title', '')} {candidate.get('description', '')}"
    rule = candidate_classification_rule(text)
    if rule is None:
        return None
    return CandidateClassification(
        rule["event_category"],
        rule["event_subcategory"],
        rule["linked_indicator_id"],
    )


def _event_from_candidate(
    candidate: dict,
    classification: CandidateClassification,
    official_source_url: str,
) -> dict:
    rules = load_issue_rules()
    body_only_match = str(candidate.get("description") or "").startswith(
        "DART_BODY_MATCH["
    )
    event = {
        "event_id": "",
        "company_id": candidate["company_id"],
        "company_name": candidate["company_name"],
        "event_category": classification.event_category,
        "event_subcategory": classification.event_subcategory,
        "event_date": candidate["published_at"],
        "event_date_type": "official_disclosure_date",
        "business_unit": "DS" if candidate["company_id"] == "005930" else "semiconductor",
        "detection_source_type": "dart_disclosure",
        "status": (
            "reported"
            if body_only_match
            else rules["candidate_classification"]["official_dart_status"]
        ),
        "enforcement_action": _enforcement_action(candidate),
        "severity": "1",
        "severity_rule_version": rules["version"],
        "authority_confirmed": "false" if body_only_match else "true",
        "official_source_url": official_source_url,
        "news_url": "",
        "summary": candidate["title"],
        "note": "Open DART 법정공시 제목과 원본 응답을 승인된 규칙으로 자동 분류",
        "linked_indicator_id": classification.linked_indicator_id,
        "severity_evidence": candidate["description"],
        "responsibility_evidence": "공시 제목 외 귀책 근거는 확인되지 않음",
        "persistence_evidence": "후속 상태 변경 공시 수집 시 재평가",
        "evidence_confidence": "medium",
        "resolved_date": "",
        "market_event_date": candidate["published_at"],
        "market_event_date_type": "official_disclosure_date",
    }
    severity, _ = calculate_event_severity(event, rules)
    event["severity"] = str(severity)
    return event


def _enforcement_action(candidate: dict) -> str:
    text = f"{candidate.get('title', '')} {candidate.get('description', '')}"
    if "과징금" in text or "과태료" in text or "벌금" in text:
        return "fine"
    if "시정명령" in text or "작업중지" in text:
        return "corrective_order"
    if "조사" in text or "수사" in text:
        return "investigation"
    return "no_action"


def _stable_unique_id(prefix: str, existing: set[str], seed: str) -> str:
    counter = 0
    while True:
        payload = seed if counter == 0 else f"{seed}|{counter}"
        numeric = int(hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16], 16)
        candidate = f"{prefix}-{numeric:020d}"
        if candidate not in existing:
            return candidate
        counter += 1


def _next_event_id(existing: set[str]) -> str:
    numbers = [
        int(value.removeprefix("EVT-"))
        for value in existing
        if re.fullmatch(r"EVT-[0-9]{4}", value)
    ]
    next_number = max(numbers, default=0) + 1
    if next_number > 9999:
        raise ValueError("four-digit event ID space exhausted")
    return f"EVT-{next_number:04d}"


def _copy_bundle(source_root: Path, target_root: Path) -> None:
    source_root = Path(source_root)
    for relative_path in BUNDLE_FILES:
        source = source_root / relative_path
        target = target_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

    for source in _read_csv(source_root / "data/processed/sources.csv"):
        file_name = str(source["file_name"])
        source_file = source_root / "data/raw/reports" / file_name
        target_file = target_root / "data/raw/reports" / file_name
        target_file.parent.mkdir(parents=True, exist_ok=True)
        if not target_file.exists():
            shutil.copyfile(source_file, target_file)


def _read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty required table: {path.name}")
    fields = list(rows[0])
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
