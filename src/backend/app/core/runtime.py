from app.core.config import (
    ISSUE_RUNTIME_DATA_DIR,
    ISSUE_SYNC_HOUR_KST,
    ISSUE_SYNC_MINUTE_KST,
    RUNTIME_STATE_DB_PATH,
)
from app.repositories.runtime_state_repository import RuntimeStateRepository
from app.services.data_b_recalculation import DataBRecalculationAdapter
from app.services.issue_snapshot_publisher import IssueSnapshotPublisher
from app.services.issue_scheduler import DailyIssueScheduler
from app.services.issue_sync_workflow import InternalIssueSyncWorkflow
from app.services.sync_coordinator import (
    IssueSyncCoordinator,
    UnavailableIssueSyncWorkflow,
)


runtime_state_repository = RuntimeStateRepository(RUNTIME_STATE_DB_PATH)
issue_snapshot_publisher = IssueSnapshotPublisher(ISSUE_RUNTIME_DATA_DIR)
data_b_recalculation_adapter = DataBRecalculationAdapter(
    runtime_state_repository,
    runtime_root=ISSUE_RUNTIME_DATA_DIR,
)
issue_sync_coordinator = IssueSyncCoordinator(
    runtime_state_repository,
    UnavailableIssueSyncWorkflow(),
)
daily_issue_scheduler = DailyIssueScheduler(
    runtime_state_repository,
    issue_sync_coordinator,
    hour=ISSUE_SYNC_HOUR_KST,
    minute=ISSUE_SYNC_MINUTE_KST,
)


def recover_runtime_state_after_restart() -> None:
    runtime_state_repository.recover_interrupted_syncs()


def build_internal_issue_sync_workflow(collector, normalizer):
    """Assemble the shared workflow once a complete-bundle normalizer is supplied."""
    return InternalIssueSyncWorkflow(
        collector,
        normalizer,
        issue_snapshot_publisher,
        recalculation=data_b_recalculation_adapter,
    )
