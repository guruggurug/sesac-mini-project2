from datetime import datetime
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.schemas import MarketQuoteItem, MarketQuotesResponse
from app.main import app
from app.repositories.runtime_state_repository import RuntimeStateRepository
from app.services.issue_sync_workflow import IssueSyncWorkflowResult
from app.services.market_quotes import InternalQuote
from app.services.sync_coordinator import IssueSyncCoordinator
from app.services.sync_status import SyncStatusService
import app.routes.market as market_route
import app.routes.portfolio as portfolio_route
import app.routes.sync as sync_route


SEOUL = ZoneInfo("Asia/Seoul")
NOW = datetime(2026, 7, 24, 10, 15, tzinfo=SEOUL)


class SuccessfulMarketDashboard:
    def get_quotes(self):
        instruments = [
            ("KOSPI", "index", "코스피", 3210.45, 3198.12, "points"),
            ("KOSDAQ", "index", "코스닥", 812.34, 808.2, "points"),
            ("005930", "equity", "삼성전자", 81000, 80000, "KRW"),
            ("000660", "equity", "SK하이닉스", 202000, 200000, "KRW"),
        ]
        return MarketQuotesResponse(
            quotes=[
                MarketQuoteItem(
                    instrument_id=instrument_id,
                    instrument_type=instrument_type,
                    name=name,
                    current_value=current,
                    previous_close=previous,
                    change=current - previous,
                    change_rate=(current - previous) / previous,
                    unit=unit,
                    market_status="open",
                    price_status="live",
                    as_of=NOW,
                    source="e2e-provider",
                    source_url="https://example.com/market",
                    is_stale=False,
                )
                for (
                    instrument_id,
                    instrument_type,
                    name,
                    current,
                    previous,
                    unit,
                ) in instruments
            ],
            polling_enabled=True,
            refresh_interval_seconds=15,
            data_status="validated",
            generated_at=NOW,
            warnings=[],
        )


class SuccessfulQuoteService:
    def get_quote(self, instrument_id):
        prices = {"005930": 81000, "000660": 202000}
        return InternalQuote(
            instrument_id,
            prices[instrument_id],
            "e2e-provider",
            NOW,
        )


class SuccessfulSyncWorkflow:
    async def run(self, report_stage):
        for stage in ("normalizing", "validating", "publishing"):
            report_stage(stage)
        return IssueSyncWorkflowResult(
            status="success",
            collected_items=3,
            snapshot_updated=False,
            published_snapshot_version=None,
            published_at=None,
            candidate_items=3,
            validated_items=3,
            rejected_items=0,
            published_items=0,
            recalculation_triggered=False,
            recalculation_status="not_required",
            recalculated_at=None,
        )


def test_realtime_dashboard_success_flow_across_public_apis(tmp_path, monkeypatch):
    repository = RuntimeStateRepository(tmp_path / "runtime.db")
    coordinator = IssueSyncCoordinator(
        repository,
        SuccessfulSyncWorkflow(),
        now=lambda: NOW,
        sync_id_factory=lambda: "SYNC-20260724-e2e",
        owner_token_factory=lambda: "e2e-owner",
    )
    status_service = SyncStatusService(
        repository,
        schedule_hour=4,
        schedule_minute=0,
        now=lambda: NOW,
    )
    monkeypatch.setattr(
        market_route,
        "market_dashboard_service",
        SuccessfulMarketDashboard(),
    )
    monkeypatch.setattr(
        portfolio_route,
        "market_quote_service",
        SuccessfulQuoteService(),
    )
    monkeypatch.setattr(sync_route, "runtime_state_repository", repository)
    monkeypatch.setattr(sync_route, "issue_sync_coordinator", coordinator)
    monkeypatch.setattr(sync_route, "sync_status_service", status_service)

    with TestClient(app) as client:
        home = client.get("/home")
        market = client.get("/market/quotes")
        portfolio = client.post(
            "/portfolio/summary",
            json={
                "holdings": [
                    {"ticker": "005930", "quantity": 10, "average_price": 78000},
                    {"ticker": "000660", "quantity": 5, "average_price": 190000},
                ]
            },
        )
        issue_page = client.get("/issue/analysis")
        current_issues = client.get("/issues/current")
        historical_issues = client.get("/issues/historical")
        queued_sync = client.post(
            "/sync/issues",
            json={
                "requested_by": "user",
                "reason": "manual_refresh",
                "client_request_id": "e2e-request",
            },
        )
        completed_sync = client.get(
            "/sync/status",
            params={"sync_id": queued_sync.json()["sync_id"]},
        )

    assert home.status_code == 200
    assert 'data-ui-screen="home"' in home.text
    assert market.status_code == 200
    assert len(market.json()["quotes"]) == 4
    assert market.json()["polling_enabled"] is True

    assert portfolio.status_code == 200
    assert portfolio.json()["total_market_value"] == 1_820_000
    assert portfolio.json()["data_status"] == "validated"
    assert sum(item["current_weight"] for item in portfolio.json()["positions"]) == 1

    assert issue_page.status_code == 200
    assert 'data-ui-screen="issue-analysis"' in issue_page.text
    assert current_issues.status_code == historical_issues.status_code == 200
    assert current_issues.json()["events"]
    assert historical_issues.json()["events"]

    assert queued_sync.status_code == 202
    assert queued_sync.json()["status"] == "queued"
    assert completed_sync.status_code == 200
    assert completed_sync.json()["status"] == "success"
    assert completed_sync.json()["validated_items"] == 3
