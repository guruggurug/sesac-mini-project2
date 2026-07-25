import asyncio
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.repositories.runtime_state_repository import RuntimeStateRepository
from app.services.sync_coordinator import (
    IssueSyncCoordinator,
    UnavailableIssueSyncWorkflow,
)
from app.services.issue_sync_workflow import IssueSyncWorkflowResult


NOW = datetime(2026, 7, 22, 3, 0, tzinfo=timezone.utc)


class SuccessfulWorkflow:
    def __init__(self, status="success"):
        self.status = status
        self.calls = 0

    async def run(self, report_stage):
        self.calls += 1
        report_stage("normalizing")
        report_stage("validating")
        report_stage("publishing")
        return IssueSyncWorkflowResult(
            status=self.status,
            collected_items=2,
            snapshot_updated=False,
            published_snapshot_version=None,
            published_at=None,
            candidate_items=2,
            validated_items=0,
            rejected_items=0,
            published_items=0,
            recalculation_triggered=False,
            recalculation_status="not_required",
            recalculated_at=None,
        )


def make_coordinator(repository, workflow, sync_id="sync-new", owner="owner-new"):
    return IssueSyncCoordinator(
        repository,
        workflow,
        now=lambda: NOW,
        sync_id_factory=lambda: sync_id,
        owner_token_factory=lambda: owner,
    )


def test_manual_and_scheduled_execution_share_the_same_success_path(tmp_path):
    repository = RuntimeStateRepository(tmp_path / "runtime.db")
    manual_workflow = SuccessfulWorkflow()
    manual = asyncio.run(
        make_coordinator(repository, manual_workflow, "sync-manual").execute("manual")
    )
    scheduled_workflow = SuccessfulWorkflow("partial_success")
    scheduled = asyncio.run(
        make_coordinator(
            repository, scheduled_workflow, "sync-scheduled"
        ).execute("scheduled")
    )

    assert manual.status == "success"
    assert scheduled.status == "partial_success"
    assert manual.workflow_result.candidate_items == 2
    assert repository.get_sync_run("sync-manual")["stage"] == "completed"
    assert repository.get_sync_run("sync-scheduled")["status"] == "partial_success"


def test_existing_active_run_is_reused_without_running_workflow(tmp_path):
    repository = RuntimeStateRepository(tmp_path / "runtime.db")
    repository.acquire_sync_lock(
        sync_id="sync-existing",
        sync_type="manual",
        owner_token="owner-existing",
        now=NOW,
    )
    workflow = SuccessfulWorkflow()

    result = asyncio.run(make_coordinator(repository, workflow).execute("scheduled"))

    assert result.acquired is False
    assert result.sync_id == "sync-existing"
    assert result.status == "queued"
    assert workflow.calls == 0


def test_unavailable_workflow_is_recorded_as_failed_not_success(tmp_path):
    repository = RuntimeStateRepository(tmp_path / "runtime.db")

    result = asyncio.run(
        make_coordinator(repository, UnavailableIssueSyncWorkflow()).execute("manual")
    )

    assert result.status == "failed"
    assert result.error_code == "ISSUE_SYNC_WORKFLOW_NOT_CONFIGURED"
    stored = repository.get_sync_run("sync-new")
    assert stored["status"] == "failed"
    assert stored["error_code"] == "ISSUE_SYNC_WORKFLOW_NOT_CONFIGURED"


def test_invalid_workflow_terminal_status_is_failed(tmp_path):
    repository = RuntimeStateRepository(tmp_path / "runtime.db")
    workflow = SuccessfulWorkflow("running")

    result = asyncio.run(make_coordinator(repository, workflow).execute("manual"))

    assert result.status == "failed"
    assert result.error_code == "ISSUE_SYNC_WORKFLOW_FAILED"


def test_workflow_failure_code_is_recorded_deterministically(tmp_path):
    repository = RuntimeStateRepository(tmp_path / "runtime.db")

    class CollectionFailure:
        async def run(self, report_stage):
            error = RuntimeError("injected")
            error.code = "ISSUE_SYNC_COLLECTION_FAILED"
            raise error

    first = asyncio.run(
        make_coordinator(repository, CollectionFailure()).execute("manual")
    )

    assert first.status == "failed"
    assert first.error_code == "ISSUE_SYNC_COLLECTION_FAILED"
    assert repository.get_sync_run("sync-new")["error_code"] == first.error_code


def test_stage_heartbeats_follow_collecting_to_publishing_order(tmp_path):
    class TracingRepository(RuntimeStateRepository):
        def __init__(self, path):
            super().__init__(path)
            self.stages = []

        def mark_sync_running(self, **kwargs):
            super().mark_sync_running(**kwargs)
            self.stages.append("collecting")

        def heartbeat_sync(self, **kwargs):
            super().heartbeat_sync(**kwargs)
            self.stages.append(kwargs["stage"])

    repository = TracingRepository(tmp_path / "runtime.db")

    result = asyncio.run(
        make_coordinator(repository, SuccessfulWorkflow()).execute("manual")
    )

    assert result.status == "success"
    assert repository.stages == [
        "collecting",
        "normalizing",
        "validating",
        "publishing",
    ]
