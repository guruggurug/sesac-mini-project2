from datetime import datetime
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

import pandas as pd
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.market_dashboard import MarketDashboardService
from app.services.market_quotes import InternalQuote, MarketQuoteError
import app.routes.market as market_route


KST = ZoneInfo("Asia/Seoul")


class StubQuoteService:
    def __init__(self, quotes):
        self.quotes = quotes

    def get_quote(self, instrument_id):
        value = self.quotes[instrument_id]
        if isinstance(value, Exception):
            raise value
        return value


class StubPriceRepository:
    def load_data_as_df(self):
        return (
            pd.DataFrame(
                [
                    {"date": "2026-07-23", "ticker": "005930", "close": 79000},
                    {"date": "2026-07-24", "ticker": "005930", "close": 80000},
                    {"date": "2026-07-23", "ticker": "000660", "close": 198000},
                    {"date": "2026-07-24", "ticker": "000660", "close": 200000},
                ]
            ),
            "validated",
            None,
        )


def make_quotes(now, source="kis"):
    values = {
        "KOSPI": (3210.45, 3198.12),
        "KOSDAQ": (812.34, 808.2),
        "005930": (81000, None),
        "000660": (202000, None),
    }
    return {
        instrument_id: InternalQuote(
            instrument_id,
            current,
            source,
            now,
            previous_close=previous,
            source_url="https://apiportal.koreainvestment.com/",
        )
        for instrument_id, (current, previous) in values.items()
    }


def test_open_market_response_enables_polling_and_matches_contract_shape():
    now = datetime(2026, 7, 24, 10, 15, tzinfo=KST)
    service = MarketDashboardService(
        StubQuoteService(make_quotes(now)),
        price_repository=StubPriceRepository(),
        now=lambda: now,
    )

    response = service.get_quotes()

    assert [quote.instrument_id for quote in response.quotes] == [
        "KOSPI",
        "KOSDAQ",
        "005930",
        "000660",
    ]
    assert response.polling_enabled is True
    assert response.refresh_interval_seconds == 15
    assert response.data_status == "validated"
    assert all(quote.market_status == "open" for quote in response.quotes)
    assert response.quotes[2].previous_close == 79000
    assert response.quotes[2].change_rate == pytest.approx(2000 / 79000)


def test_closed_market_disables_polling_and_marks_all_quotes_closed():
    now = datetime(2026, 7, 25, 10, 15, tzinfo=KST)
    service = MarketDashboardService(
        StubQuoteService(make_quotes(now)),
        price_repository=StubPriceRepository(),
        now=lambda: now,
    )

    response = service.get_quotes()

    assert response.polling_enabled is False
    assert response.refresh_interval_seconds is None
    assert all(quote.market_status == "closed" for quote in response.quotes)
    assert all(quote.price_status == "cached" for quote in response.quotes)


def test_fallback_quote_is_explicitly_stale():
    now = datetime(2026, 7, 24, 10, 15, tzinfo=KST)
    quotes = make_quotes(now)
    quotes["005930"] = InternalQuote(
        "005930",
        80000,
        "local_repository",
        now,
    )
    service = MarketDashboardService(
        StubQuoteService(quotes),
        price_repository=StubPriceRepository(),
        now=lambda: now,
    )

    response = service.get_quotes()
    samsung = next(item for item in response.quotes if item.instrument_id == "005930")

    assert response.data_status == "fallback"
    assert samsung.price_status == "fallback"
    assert samsung.market_status == "delayed"
    assert samsung.is_stale is True
    assert response.warnings


def test_missing_index_previous_close_is_rejected():
    now = datetime(2026, 7, 24, 10, 15, tzinfo=KST)
    quotes = make_quotes(now)
    quotes["KOSPI"] = InternalQuote("KOSPI", 3210, "last_known_good:kis", now)
    service = MarketDashboardService(
        StubQuoteService(quotes),
        price_repository=StubPriceRepository(),
        now=lambda: now,
    )

    with pytest.raises(MarketQuoteError, match="previous close"):
        service.get_quotes()


def test_public_market_quotes_endpoint_returns_contract_response(monkeypatch):
    now = datetime(2026, 7, 24, 10, 15, tzinfo=KST)
    dashboard = MarketDashboardService(
        StubQuoteService(make_quotes(now)),
        price_repository=StubPriceRepository(),
        now=lambda: now,
    )
    monkeypatch.setattr(market_route, "market_dashboard_service", dashboard)
    app = FastAPI()
    app.include_router(market_route.router)

    response = TestClient(app).get("/market/quotes")

    assert response.status_code == 200
    assert len(response.json()["quotes"]) == 4
    assert response.json()["polling_enabled"] is True


def test_public_market_quotes_endpoint_returns_503_without_indices(monkeypatch):
    class UnavailableDashboard:
        def get_quotes(self):
            raise MarketQuoteError("No trustworthy index quote")

    monkeypatch.setattr(
        market_route,
        "market_dashboard_service",
        UnavailableDashboard(),
    )
    app = FastAPI()
    app.include_router(market_route.router)

    response = TestClient(app).get("/market/quotes")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "MARKET_QUOTES_UNAVAILABLE"
