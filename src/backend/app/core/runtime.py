from app.core.config import (
    ISSUE_SYNC_HOUR_KST,
    ISSUE_SYNC_MINUTE_KST,
    RUNTIME_STATE_DB_PATH,
)
from app.repositories.runtime_state_repository import RuntimeStateRepository
from app.services.issue_scheduler import DailyIssueScheduler
from app.services.sync_coordinator import (
    IssueSyncCoordinator,
    UnavailableIssueSyncWorkflow,
)


runtime_state_repository = RuntimeStateRepository(RUNTIME_STATE_DB_PATH)
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
