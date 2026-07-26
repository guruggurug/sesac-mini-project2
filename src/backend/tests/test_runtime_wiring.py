from pathlib import Path
import sys

from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import (
    CORS_ALLOWED_ORIGINS,
    DART_API_KEY,
    SESSION_COOKIE_HTTPS_ONLY,
    SESSION_SECRET_KEY,
)
from app.core.runtime import (
    issue_sync_coordinator,
    market_dashboard_service,
    market_quote_service,
)
from app.main import app
from app.services.sync_coordinator import UnavailableIssueSyncWorkflow
from app.services.issue_sync_workflow import InternalIssueSyncWorkflow
import app.routes.market as market_route
import app.routes.portfolio as portfolio_route


def middleware_options(middleware_type):
    middleware = next(
        item for item in app.user_middleware if item.cls is middleware_type
    )
    return middleware.kwargs


def test_session_middleware_uses_environment_backed_secure_options():
    options = middleware_options(SessionMiddleware)

    assert options["secret_key"] == SESSION_SECRET_KEY
    assert options["same_site"] == "lax"
    assert options["https_only"] is SESSION_COOKIE_HTTPS_ONLY


def test_cors_middleware_uses_explicit_allowlist_when_configured():
    if not CORS_ALLOWED_ORIGINS:
        assert all(item.cls is not CORSMiddleware for item in app.user_middleware)
        return

    options = middleware_options(CORSMiddleware)
    assert options["allow_origins"] == CORS_ALLOWED_ORIGINS
    assert "*" not in options["allow_origins"]

    client = TestClient(app)
    allowed = client.options(
        "/health",
        headers={
            "Origin": CORS_ALLOWED_ORIGINS[0],
            "Access-Control-Request-Method": "GET",
        },
    )
    rejected = client.options(
        "/health",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert allowed.headers["access-control-allow-origin"] == CORS_ALLOWED_ORIGINS[0]
    assert "access-control-allow-origin" not in rejected.headers


def test_public_routes_use_the_production_market_runtime_objects():
    assert market_route.market_dashboard_service is market_dashboard_service
    assert portfolio_route.market_dashboard_service is market_dashboard_service
    assert portfolio_route.market_quote_service is market_quote_service


def test_issue_sync_runtime_requires_dart_configuration():
    expected_type = (
        InternalIssueSyncWorkflow if DART_API_KEY else UnavailableIssueSyncWorkflow
    )
    assert isinstance(issue_sync_coordinator._workflow, expected_type)
