from datetime import datetime, timezone
import json
from pathlib import Path

from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, FormatChecker

from app.main import app
from app.services.market_quotes import InternalQuote


client = TestClient(app)
SCHEMA_PATH = (
    Path(__file__).parents[3]
    / "schemas"
    / "api"
    / "portfolio-summary-response.schema.json"
)


class StubQuoteService:
    def __init__(self, quotes):
        self.quotes = quotes

    def get_quote(self, ticker):
        return self.quotes[ticker]


def test_portfolio_summary_api_calculates_contract_fields(monkeypatch):
    as_of = datetime(2026, 7, 25, 1, 0, tzinfo=timezone.utc)
    quote_service = StubQuoteService(
        {
            "005930": InternalQuote("005930", 80000, "kis", as_of),
            "000660": InternalQuote("000660", 200000, "kis", as_of),
        }
    )
    monkeypatch.setattr(
        "app.routes.portfolio.market_quote_service",
        quote_service,
    )
    monkeypatch.setattr(
        "app.routes.portfolio.PriceRepository.load_data_as_df",
        lambda _: (None, "validated", None),
    )

    response = client.post(
        "/portfolio/summary",
        json={
            "holdings": [
                {"ticker": "005930", "quantity": 10, "average_price": 70000},
                {"ticker": "000660", "quantity": 5, "average_price": 180000},
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_purchase_value"] == 1600000
    assert payload["total_market_value"] == 1800000
    assert payload["total_unrealized_profit_loss"] == 200000
    assert payload["total_return_rate"] == 0.125
    assert payload["price_status"] == "live"
    assert payload["data_status"] == "validated"
    assert payload["prices_as_of"].endswith("+09:00")
    assert payload["generated_at"].endswith("+09:00")
    assert sum(position["current_weight"] for position in payload["positions"]) == 1
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    ).validate(payload)


def test_portfolio_summary_api_marks_local_close_as_fallback(monkeypatch):
    as_of = datetime(2026, 7, 24, 6, 30, tzinfo=timezone.utc)
    monkeypatch.setattr(
        "app.routes.portfolio.market_quote_service",
        StubQuoteService(
            {
                "005930": InternalQuote(
                    "005930",
                    79000,
                    "local_repository",
                    as_of,
                )
            }
        ),
    )
    monkeypatch.setattr(
        "app.routes.portfolio.PriceRepository.load_data_as_df",
        lambda _: (None, "validated", None),
    )

    response = client.post(
        "/portfolio/summary",
        json={
            "holdings": [
                {"ticker": "005930", "quantity": 2, "average_price": 80000}
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["price_status"] == "fallback"
    assert payload["data_status"] == "fallback"
    assert payload["warnings"]
    assert payload["positions"][0]["current_weight"] == 1


def test_portfolio_summary_api_rejects_duplicate_tickers():
    response = client.post(
        "/portfolio/summary",
        json={
            "holdings": [
                {"ticker": "005930", "quantity": 1, "average_price": 70000},
                {"ticker": "005930", "quantity": 2, "average_price": 71000},
            ]
        },
    )

    assert response.status_code == 422
