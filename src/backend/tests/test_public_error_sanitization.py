from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app
from app.services.market_quotes import MarketQuoteError
import app.routes.issues as issues_route
import app.routes.market as market_route
import app.routes.portfolio as portfolio_route
import app.routes.risk as risk_route


SENSITIVE_MARKER = "SECRET_INTERNAL_PATH_CREDENTIAL"
client = TestClient(app)


def assert_marker_is_hidden(response):
    assert response.status_code >= 500
    assert SENSITIVE_MARKER not in response.text


def test_market_provider_error_is_sanitized(monkeypatch):
    class FailingDashboard:
        def request_refresh(self):
            return False

        def get_quotes(self):
            raise MarketQuoteError(SENSITIVE_MARKER)

    monkeypatch.setattr(
        market_route,
        "market_dashboard_service",
        FailingDashboard(),
    )

    response = client.get("/market/quotes")

    assert response.status_code == 503
    assert_marker_is_hidden(response)
    assert response.json()["detail"]["code"] == "MARKET_QUOTES_UNAVAILABLE"


def test_current_issue_repository_error_is_sanitized(monkeypatch):
    monkeypatch.setattr(
        issues_route.EventRepository,
        "load_data",
        lambda _: (_ for _ in ()).throw(RuntimeError(SENSITIVE_MARKER)),
    )

    assert_marker_is_hidden(client.get("/issues/current"))


def test_esg_repository_error_is_sanitized(monkeypatch):
    monkeypatch.setattr(
        risk_route.ESGRepository,
        "load_data",
        lambda _: (_ for _ in ()).throw(RuntimeError(SENSITIVE_MARKER)),
    )

    assert_marker_is_hidden(client.post("/risk/esg"))


def test_portfolio_repository_error_is_sanitized(monkeypatch):
    monkeypatch.setattr(
        portfolio_route,
        "get_realtime_price",
        lambda _: 100_000.0,
    )
    monkeypatch.setattr(
        portfolio_route.ESGRepository,
        "load_data",
        lambda _: (_ for _ in ()).throw(RuntimeError(SENSITIVE_MARKER)),
    )

    response = client.post(
        "/portfolio/optimize",
        data={"samsung_qty": 1, "sk_qty": 1},
    )

    assert_marker_is_hidden(response)
