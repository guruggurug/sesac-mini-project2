from __future__ import annotations

import asyncio
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
from app.services.issue_snapshot_publisher import (
    IssueSnapshotPublisher,
    SnapshotPublicationError,
    read_active_snapshot,
)
from app.services.issue_sync_workflow import (
    InternalIssueSyncWorkflow,
    IssueCollectionResult,
    IssueSyncWorkflowError,
    PreparedIssueBundle,
    RecalculationResult,
    scoring_relevant_bundle_changed,
)


ROOT = Path(BASE_DIR)
NOW = datetime(2026, 7, 23, 2, 0, tzinfo=timezone.utc)


def copy_bundle(tmp_path: Path, name: str) -> Path:
    root = tmp_path / name
    shutil.copytree(ROOT / "data", root / "data")
    materialize_raw_evidence(root)
    return root


def rewrite_csv(path: Path, update) -> None:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        rows = list(reader)
    for row in rows:
        extra_note_parts = row.pop(None, [])
        if extra_note_parts:
            row["note"] = ",".join([row.get("note", ""), *extra_note_parts])
    update(rows)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def materialize_raw_evidence(root: Path) -> None:
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

    rewrite_csv(sources_path, update)


def expected_candidate_counts(root: Path) -> tuple[int, int, int]:
    with (root / "data/candidate/news_candidates.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    return (
        len(rows),
        sum(row["validation_status"] == "validated" for row in rows),
        sum(row["validation_status"] == "rejected" for row in rows),
    )


class Collector:
    def __init__(self, *, error=None, status="success"):
        self.error = error
        self.status = status
        self.calls = 0

    def collect(self):
        self.calls += 1
        if self.error:
            raise self.error
        return IssueCollectionResult("collected", 7, self.status)


class Normalizer:
    def __init__(self, root: Path, *, error=None):
        self.root = root
        self.error = error
        self.calls = 0

    def normalize(self, collection):
        self.calls += 1
        if self.error:
            raise self.error
        return PreparedIssueBundle(self.root)


class PublisherSpy:
    def __init__(self, publisher, *, error=None):
        self.publisher = publisher
        self.error = error
        self.calls = 0

    def publish(self, root):
        self.calls += 1
        if self.error:
            raise self.error
        return self.publisher.publish(root)


class Recalculator:
    def __init__(self, *, error=None):
        self.error = error
        self.calls = []

    async def recalculate(self, *, snapshot_version, published_at):
        self.calls.append((snapshot_version, published_at))
        if self.error:
            raise self.error
        return RecalculationResult(NOW.isoformat(), snapshot_version)


def run_workflow(previous, next_root, publisher, recalculation=None, collector=None):
    stages = []
    workflow = InternalIssueSyncWorkflow(
        collector or Collector(),
        Normalizer(next_root),
        publisher,
        recalculation=recalculation,
        current_bundle_root=lambda: previous,
    )
    result = asyncio.run(workflow.run(stages.append))
    return result, stages


def test_scoring_change_recalculates_only_after_complete_bundle_publication(tmp_path):
    previous = copy_bundle(tmp_path, "previous")
    changed = copy_bundle(tmp_path, "changed")
    rewrite_csv(
        changed / "data/processed/esg_indicators.csv",
        lambda rows: rows[0].update(raw_value="999"),
    )
    candidate_items, validated_items, rejected_items = expected_candidate_counts(
        changed
    )
    runtime = tmp_path / "runtime"
    publisher = PublisherSpy(IssueSnapshotPublisher(runtime, now=lambda: NOW))
    recalculation = Recalculator()

    result, stages = run_workflow(
        previous, changed, publisher, recalculation
    )

    assert stages == ["normalizing", "validating", "publishing", "recalculating"]
    assert publisher.calls == 1
    assert len(recalculation.calls) == 1
    assert read_active_snapshot(runtime).version == result.published_snapshot_version
    assert result.snapshot_updated is True
    assert result.recalculation_triggered is True
    assert result.recalculation_status == "completed"
    assert result.candidate_items == candidate_items
    assert result.validated_items == validated_items
    assert result.rejected_items == rejected_items
    assert result.published_items == validated_items


def test_snapshot_noop_does_not_request_recalculation(tmp_path):
    source = copy_bundle(tmp_path, "source")
    runtime = tmp_path / "runtime"
    publisher = IssueSnapshotPublisher(runtime, now=lambda: NOW)
    publisher.publish(source)
    recalculation = Recalculator()

    result, stages = run_workflow(source, source, publisher, recalculation)

    assert result.snapshot_updated is False
    assert result.recalculation_status == "not_required"
    assert recalculation.calls == []
    assert stages == ["normalizing", "validating", "publishing"]


def test_pending_or_rejected_candidate_only_change_does_not_recalculate(tmp_path):
    previous = copy_bundle(tmp_path, "previous")
    changed = copy_bundle(tmp_path, "changed")
    rewrite_csv(
        changed / "data/candidate/news_candidates.csv",
        lambda rows: rows[0].update(description="candidate metadata changed"),
    )
    recalculation = Recalculator()

    result, _ = run_workflow(
        previous,
        changed,
        IssueSnapshotPublisher(tmp_path / "runtime", now=lambda: NOW),
        recalculation,
    )

    assert result.snapshot_updated is True
    assert result.recalculation_triggered is False
    assert recalculation.calls == []


def test_reported_only_event_changes_are_not_scoring_relevant(tmp_path):
    previous = copy_bundle(tmp_path, "previous")
    changed = copy_bundle(tmp_path, "changed")
    for root, note in ((previous, "old"), (changed, "new")):
        rewrite_csv(
            root / "data/processed/events.csv",
            lambda rows, note=note: rows[0].update(status="reported", note=note),
        )

    assert scoring_relevant_bundle_changed(previous, changed) is False


def test_changed_official_confirmed_event_is_scoring_relevant(tmp_path):
    previous = copy_bundle(tmp_path, "previous")
    changed = copy_bundle(tmp_path, "changed")
    rewrite_csv(
        changed / "data/processed/events.csv",
        lambda rows: rows[0].update(market_event_date="2024-05-30"),
    )

    assert scoring_relevant_bundle_changed(previous, changed) is True


def test_validation_failure_prevents_publisher_and_recalculation(tmp_path):
    previous = copy_bundle(tmp_path, "previous")
    invalid = copy_bundle(tmp_path, "invalid")
    rewrite_csv(
        invalid / "data/processed/sources.csv",
        lambda rows: rows[0].update(content_hash="0" * 64),
    )
    publisher = PublisherSpy(IssueSnapshotPublisher(tmp_path / "runtime"))
    recalculation = Recalculator()
    workflow = InternalIssueSyncWorkflow(
        Collector(),
        Normalizer(invalid),
        publisher,
        recalculation=recalculation,
        current_bundle_root=lambda: previous,
    )

    with pytest.raises(IssueSyncWorkflowError) as captured:
        asyncio.run(workflow.run(lambda stage: None))

    assert captured.value.code == "INVALID_SOURCE_CONTENT_HASH"
    assert publisher.calls == 0
    assert recalculation.calls == []


def test_collection_and_publisher_failures_stop_followup_stages(tmp_path):
    source = copy_bundle(tmp_path, "source")
    recalculation = Recalculator()
    collection_workflow = InternalIssueSyncWorkflow(
        Collector(error=RuntimeError("collection")),
        Normalizer(source),
        PublisherSpy(IssueSnapshotPublisher(tmp_path / "unused")),
        recalculation=recalculation,
        current_bundle_root=lambda: source,
    )
    with pytest.raises(IssueSyncWorkflowError) as collection_error:
        asyncio.run(collection_workflow.run(lambda stage: None))
    assert collection_error.value.code == "ISSUE_SYNC_COLLECTION_FAILED"

    publication_error = SnapshotPublicationError("publishing", "injected")
    publisher = PublisherSpy(
        IssueSnapshotPublisher(tmp_path / "unused-2"), error=publication_error
    )
    publish_workflow = InternalIssueSyncWorkflow(
        Collector(),
        Normalizer(source),
        publisher,
        recalculation=recalculation,
        current_bundle_root=lambda: source,
    )
    with pytest.raises(IssueSyncWorkflowError) as publish_error:
        asyncio.run(publish_workflow.run(lambda stage: None))
    assert publish_error.value.code == "ISSUE_SNAPSHOT_PUBLISHING_FAILED"
    assert recalculation.calls == []


def test_pointer_failure_keeps_repository_lkg_and_skips_recalculation(tmp_path):
    first = copy_bundle(tmp_path, "first")
    changed = copy_bundle(tmp_path, "changed")
    rewrite_csv(
        changed / "data/processed/esg_indicators.csv",
        lambda rows: rows[0].update(raw_value="999"),
    )
    runtime = tmp_path / "runtime"
    IssueSnapshotPublisher(runtime, now=lambda: NOW).publish(first)
    active_before = read_active_snapshot(runtime)

    def fail_pointer(source, destination):
        if Path(destination).name == "current.json":
            raise OSError("injected")
        os.replace(source, destination)

    recalculation = Recalculator()
    workflow = InternalIssueSyncWorkflow(
        Collector(),
        Normalizer(changed),
        IssueSnapshotPublisher(runtime, now=lambda: NOW, replace=fail_pointer),
        recalculation=recalculation,
        current_bundle_root=lambda: active_before.root,
    )
    with pytest.raises(IssueSyncWorkflowError) as captured:
        asyncio.run(workflow.run(lambda stage: None))

    assert captured.value.code == "ISSUE_SNAPSHOT_PUBLISHING_FAILED"
    assert read_active_snapshot(runtime) == active_before
    rows, status, _ = ESGRepository(base_dir=changed, runtime_root=runtime).load_data()
    assert status == "validated"
    assert rows[0]["raw_value"] != 999
    assert recalculation.calls == []


def test_recalculation_failure_does_not_rollback_published_snapshot(tmp_path):
    previous = copy_bundle(tmp_path, "previous")
    changed = copy_bundle(tmp_path, "changed")
    rewrite_csv(
        changed / "data/processed/esg_indicators.csv",
        lambda rows: rows[0].update(raw_value="999"),
    )
    runtime = tmp_path / "runtime"
    recalculation = Recalculator(error=RuntimeError("injected"))
    workflow = InternalIssueSyncWorkflow(
        Collector(),
        Normalizer(changed),
        IssueSnapshotPublisher(runtime, now=lambda: NOW),
        recalculation=recalculation,
        current_bundle_root=lambda: previous,
    )

    with pytest.raises(IssueSyncWorkflowError) as captured:
        asyncio.run(workflow.run(lambda stage: None))

    assert captured.value.code == "ISSUE_RECALCULATION_FAILED"
    assert read_active_snapshot(runtime) is not None
    assert len(recalculation.calls) == 1


def test_missing_recalculation_adapter_is_explicit_failure_after_publication(tmp_path):
    previous = copy_bundle(tmp_path, "previous")
    changed = copy_bundle(tmp_path, "changed")
    rewrite_csv(
        changed / "data/processed/esg_indicators.csv",
        lambda rows: rows[0].update(raw_value="999"),
    )
    runtime = tmp_path / "runtime"
    workflow = InternalIssueSyncWorkflow(
        Collector(),
        Normalizer(changed),
        IssueSnapshotPublisher(runtime, now=lambda: NOW),
        current_bundle_root=lambda: previous,
    )

    with pytest.raises(IssueSyncWorkflowError) as captured:
        asyncio.run(workflow.run(lambda stage: None))

    assert captured.value.code == "ISSUE_RECALCULATION_UNAVAILABLE"
    assert read_active_snapshot(runtime) is not None


def test_recalculation_result_must_match_published_snapshot_version(tmp_path):
    previous = copy_bundle(tmp_path, "previous")
    changed = copy_bundle(tmp_path, "changed")
    rewrite_csv(
        changed / "data/processed/esg_indicators.csv",
        lambda rows: rows[0].update(raw_value="999"),
    )

    class WrongVersionRecalculator:
        async def recalculate(self, *, snapshot_version, published_at):
            return RecalculationResult(
                NOW.isoformat(),
                "issues-" + "0" * 64,
            )

    workflow = InternalIssueSyncWorkflow(
        Collector(),
        Normalizer(changed),
        IssueSnapshotPublisher(tmp_path / "runtime", now=lambda: NOW),
        recalculation=WrongVersionRecalculator(),
        current_bundle_root=lambda: previous,
    )

    with pytest.raises(IssueSyncWorkflowError) as captured:
        asyncio.run(workflow.run(lambda stage: None))

    assert captured.value.code == "ISSUE_RECALCULATION_VERSION_MISMATCH"


def test_same_inputs_produce_deterministic_result(tmp_path):
    source = copy_bundle(tmp_path, "source")
    first, _ = run_workflow(
        source,
        source,
        IssueSnapshotPublisher(tmp_path / "runtime-a", now=lambda: NOW),
    )
    second, _ = run_workflow(
        source,
        source,
        IssueSnapshotPublisher(tmp_path / "runtime-b", now=lambda: NOW),
    )

    assert first == second
