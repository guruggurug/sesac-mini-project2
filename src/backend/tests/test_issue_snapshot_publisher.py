from __future__ import annotations

import csv
import hashlib
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import BASE_DIR
from app.repositories.esg_repository import ESGRepository
from app.repositories.event_repository import EventRepository
from app.services.dart_disclosures import (
    DART_COMPANIES,
    DartCandidateNormalizer,
    DartRawPage,
)
from app.services.issue_snapshot_publisher import (
    IssueSnapshotPublisher,
    SnapshotPublicationError,
    read_active_snapshot,
)


ROOT = Path(BASE_DIR)
NOW = datetime(2026, 7, 23, 1, 0, tzinfo=timezone.utc)


def _copy_bundle(tmp_path: Path, name: str) -> Path:
    root = tmp_path / name
    shutil.copytree(ROOT / "data", root / "data")
    _materialize_raw_evidence(root)
    return root


def _rewrite_csv(path: Path, update) -> None:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        rows = list(reader)
    for row in rows:
        extra_note_parts = row.pop(None, [])
        if extra_note_parts:
            row["note"] = ",".join([row.get("note", ""), *extra_note_parts])
    update(rows)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _materialize_raw_evidence(root: Path) -> None:
    sources_path = root / "data/processed/sources.csv"
    raw_root = root / "data/raw/reports"
    raw_root.mkdir(parents=True, exist_ok=True)

    def update(rows):
        hashes = {}
        short_names = {}
        for row in rows:
            original_name = row["file_name"]
            if original_name not in short_names:
                suffix = Path(original_name).suffix or ".bin"
                short_names[original_name] = (
                    f"fixture-{len(short_names) + 1:03d}{suffix}"
                )
            file_name = short_names[original_name]
            if file_name not in hashes:
                payload = f"test evidence:{original_name}\n".encode("utf-8")
                (raw_root / file_name).write_bytes(payload)
                hashes[file_name] = hashlib.sha256(payload).hexdigest()
            row["file_name"] = file_name
            row["content_hash"] = hashes[file_name]

    _rewrite_csv(sources_path, update)


def _expected_candidate_counts(root: Path) -> tuple[int, int, int]:
    with (root / "data/candidate/news_candidates.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    return (
        len(rows),
        sum(row["validation_status"] == "validated" for row in rows),
        sum(row["validation_status"] == "rejected" for row in rows),
    )


def _change_esg_note(root: Path, note: str) -> None:
    def update(rows):
        rows[0]["note"] = note

    _rewrite_csv(root / "data/processed/esg_indicators.csv", update)


def _add_pending_dart_candidate(root: Path) -> None:
    company = DART_COMPANIES[0]
    page = DartRawPage(
        company=company,
        begin_date="20260723",
        end_date="20260723",
        page_no=1,
        page_count=100,
        collected_at=NOW,
        payload={
            "status": "000",
            "list": [
                {
                    "corp_name": company.company_name,
                    "corp_code": company.corp_code,
                    "stock_code": company.company_id,
                    "report_nm": "신규 미분류 공시",
                    "rcept_no": "20260723000099",
                    "flr_nm": company.company_name,
                    "rcept_dt": "20260723",
                    "rm": "",
                }
            ],
        },
    )
    pending = DartCandidateNormalizer().normalize(page).candidates[0]

    def update(rows):
        rows.append({key: "" if value is None else value for key, value in pending.items()})

    _rewrite_csv(root / "data/candidate/news_candidates.csv", update)


def test_valid_bundle_is_staged_and_activated_as_one_snapshot(tmp_path):
    source = _copy_bundle(tmp_path, "source")
    candidate_items, validated_items, rejected_items = _expected_candidate_counts(
        source
    )
    runtime = tmp_path / "runtime"
    publisher = IssueSnapshotPublisher(runtime, now=lambda: NOW)

    result = publisher.publish(source)

    active = read_active_snapshot(runtime)
    assert result.snapshot_updated is True
    assert result.published_snapshot_version == active.version
    assert result.published_at == NOW.isoformat()
    assert result.candidate_items == candidate_items
    assert result.validated_items == validated_items
    assert result.rejected_items == rejected_items
    assert result.published_items == validated_items
    assert active.root.is_dir()
    assert (active.root / "data/processed/events.csv").is_file()
    assert (active.root / "data/processed/esg_indicators.csv").is_file()
    assert not any((runtime / "staging").glob("*"))


def test_same_input_has_deterministic_version_and_repeat_is_noop(tmp_path):
    source = _copy_bundle(tmp_path, "source")
    first = IssueSnapshotPublisher(tmp_path / "runtime-a", now=lambda: NOW).publish(source)
    second = IssueSnapshotPublisher(tmp_path / "runtime-b", now=lambda: NOW).publish(source)

    assert first == second

    no_change = IssueSnapshotPublisher(
        tmp_path / "runtime-a", now=lambda: NOW
    ).publish(source)
    assert no_change.snapshot_updated is False
    assert no_change.published_snapshot_version is None
    assert no_change.published_at is None
    assert no_change.published_items == 0
    assert no_change.candidate_items == first.candidate_items


def test_validation_failure_keeps_previous_snapshot_and_cleans_staging(tmp_path):
    valid = _copy_bundle(tmp_path, "valid")
    invalid = _copy_bundle(tmp_path, "invalid")
    runtime = tmp_path / "runtime"
    publisher = IssueSnapshotPublisher(runtime, now=lambda: NOW)
    publisher.publish(valid)
    pointer_before = (runtime / "current.json").read_bytes()
    active_before = read_active_snapshot(runtime)

    def corrupt(rows):
        rows[0]["content_hash"] = "0" * 64

    _rewrite_csv(invalid / "data/processed/sources.csv", corrupt)

    with pytest.raises(SnapshotPublicationError) as captured:
        publisher.publish(invalid)

    assert captured.value.code == "ISSUE_SNAPSHOT_VALIDATION_FAILED"
    assert (runtime / "current.json").read_bytes() == pointer_before
    assert read_active_snapshot(runtime) == active_before
    assert not any((runtime / "staging").glob("*"))


def test_injected_pointer_io_failure_keeps_repository_on_last_good_snapshot(tmp_path):
    first_source = _copy_bundle(tmp_path, "first")
    second_source = _copy_bundle(tmp_path, "second")
    _change_esg_note(second_source, "new snapshot must not become visible")
    runtime = tmp_path / "runtime"
    IssueSnapshotPublisher(runtime, now=lambda: NOW).publish(first_source)
    pointer_before = (runtime / "current.json").read_bytes()

    def fail_pointer_replace(source, destination):
        if Path(destination).name == "current.json":
            raise OSError("injected pointer replacement failure")
        os.replace(source, destination)

    failing = IssueSnapshotPublisher(
        runtime,
        now=lambda: NOW,
        replace=fail_pointer_replace,
    )
    with pytest.raises(SnapshotPublicationError) as captured:
        failing.publish(second_source)

    assert captured.value.code == "ISSUE_SNAPSHOT_PUBLISHING_FAILED"
    assert (runtime / "current.json").read_bytes() == pointer_before
    esg_rows, status, warning = ESGRepository(
        base_dir=second_source,
        runtime_root=runtime,
    ).load_data()
    assert status == "validated"
    assert warning is None
    assert esg_rows[0]["note"] != "new snapshot must not become visible"


def test_pending_and_rejected_candidates_never_enter_scoring_repository(tmp_path):
    source = _copy_bundle(tmp_path, "source")
    _add_pending_dart_candidate(source)
    candidate_items, validated_items, rejected_items = _expected_candidate_counts(
        source
    )
    runtime = tmp_path / "runtime"

    result = IssueSnapshotPublisher(runtime, now=lambda: NOW).publish(source)
    events, status, warning = EventRepository(
        base_dir=source,
        runtime_root=runtime,
    ).load_data()

    assert result.candidate_items == candidate_items
    assert result.validated_items == validated_items
    assert result.rejected_items == rejected_items
    assert status == "validated"
    assert warning is None
    assert len(events) == validated_items
    assert all(event["event_id"].startswith("EVT-") for event in events)


def test_repository_uses_checked_in_bundle_when_no_runtime_pointer_exists(tmp_path):
    source = _copy_bundle(tmp_path, "source")
    with (source / "data/processed/events.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        expected_event_ids = {
            row["event_id"] for row in csv.DictReader(handle)
        }

    events, status, warning = EventRepository(
        base_dir=source,
        runtime_root=tmp_path / "missing-runtime",
    ).load_data()

    assert status == "validated"
    assert warning is None
    assert {event["event_id"] for event in events} == expected_event_ids
