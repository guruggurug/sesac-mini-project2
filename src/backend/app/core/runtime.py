from app.core.config import (
    KIS_APP_KEY,
    KIS_APP_SECRET,
    KIS_BASE_URL,
    KIS_MIN_REQUEST_INTERVAL_SECONDS,
    MARKET_QUOTE_CACHE_TTL_SECONDS,
    MARKET_QUOTE_TIMEOUT_SECONDS,
    MARKET_REFRESH_INTERVAL_SECONDS,
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
from app.services.kis_market_data import KISMarketDataProvider
from app.services.market_quotes import (
    MarketQuoteService,
    RepositoryPriceAdapter,
    SQLiteLastKnownGoodAdapter,
    UnavailableMarketDataProvider,
)
from app.services.market_dashboard import MarketDashboardService
from app.services.sync_coordinator import (
    IssueSyncCoordinator,
    UnavailableIssueSyncWorkflow,
)


runtime_state_repository = RuntimeStateRepository(RUNTIME_STATE_DB_PATH)
market_data_provider = (
    KISMarketDataProvider(
        app_key=KIS_APP_KEY,
        app_secret=KIS_APP_SECRET,
        base_url=KIS_BASE_URL,
        min_request_interval_seconds=KIS_MIN_REQUEST_INTERVAL_SECONDS,
    )
    if KIS_APP_KEY and KIS_APP_SECRET
    else UnavailableMarketDataProvider()
)
from app.services.sync_status import SyncStatusService
market_quote_service = MarketQuoteService(
    provider=market_data_provider,
    local_adapter=RepositoryPriceAdapter(),
    last_known_good_adapter=SQLiteLastKnownGoodAdapter(runtime_state_repository),
    cache_ttl_seconds=MARKET_QUOTE_CACHE_TTL_SECONDS,
    provider_timeout_seconds=MARKET_QUOTE_TIMEOUT_SECONDS,
)
market_dashboard_service = MarketDashboardService(
    market_quote_service,
    refresh_interval_seconds=MARKET_REFRESH_INTERVAL_SECONDS,
)
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
sync_status_service = SyncStatusService(
    runtime_state_repository,
    schedule_hour=ISSUE_SYNC_HOUR_KST,
    schedule_minute=ISSUE_SYNC_MINUTE_KST,
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
