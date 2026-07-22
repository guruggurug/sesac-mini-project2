import asyncio
from datetime import datetime
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.repositories.runtime_state_repository import RuntimeStateRepository
from app.services.issue_scheduler import DailyIssueScheduler
from app.services.sync_coordinator import IssueSyncCoordinator


SEOUL = ZoneInfo("Asia/Seoul")


class CountingWorkflow:
    def __init__(self):
        self.calls = 0

    async def run(self, report_stage):
        self.calls += 1
        report_stage("validating")
        return "success"


def coordinator(repository, workflow, sync_id):
    return IssueSyncCoordinator(
        repository,
        workflow,
        now=lambda: datetime(2026, 7, 22, 4, 0, tzinfo=SEOUL),
        sync_id_factory=lambda: sync_id,
        owner_token_factory=lambda: f"owner-{sync_id}",
    )


def test_scheduler_does_not_run_before_configured_seoul_time(tmp_path):
    repository = RuntimeStateRepository(tmp_path / "runtime.db")
    workflow = CountingWorkflow()
    scheduler = DailyIssueScheduler(
        repository,
        coordinator(repository, workflow, "sync-1"),
        hour=4,
        now=lambda: datetime(2026, 7, 22, 3, 59, tzinfo=SEOUL),
    )

    assert asyncio.run(scheduler.run_due_once()) is None
    assert workflow.calls == 0


def test_scheduler_claim_allows_only_one_process_per_seoul_date(tmp_path):
    database = tmp_path / "runtime.db"
    first_repository = RuntimeStateRepository(database)
    second_repository = RuntimeStateRepository(database)
    first_workflow = CountingWorkflow()
    second_workflow = CountingWorkflow()
    now = lambda: datetime(2026, 7, 22, 4, 1, tzinfo=SEOUL)
    first = DailyIssueScheduler(
        first_repository,
        coordinator(first_repository, first_workflow, "sync-1"),
        now=now,
    )
    second = DailyIssueScheduler(
        second_repository,
        coordinator(second_repository, second_workflow, "sync-2"),
        now=now,
    )

    first_result = asyncio.run(first.run_due_once())
    second_result = asyncio.run(second.run_due_once())

    assert first_result.status == "success"
    assert second_result is None
    assert first_workflow.calls == 1
    assert second_workflow.calls == 0
