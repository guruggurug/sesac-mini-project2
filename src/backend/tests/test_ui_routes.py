import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app


client = TestClient(app)
TEMPLATE_ROOT = Path(__file__).parents[2] / "frontend" / "templates"


@pytest.mark.parametrize(
    ("path", "screen"),
    [
        ("/", "splash"),
        ("/splash", "splash"),
        ("/login", "login"),
        ("/home", "home"),
        ("/settings", "setting"),
        ("/portfolio/input", "portfolio-input"),
        ("/portfolio/edit", "portfolio-edit"),
        ("/portfolio/summary", "portfolio-summary"),
        ("/diagnosis/result", "diagnosis-result"),
        ("/issue/analysis", "issue-analysis"),
    ],
)
def test_intended_frontend_routes_render_only_approved_designs(path: str, screen: str):
    response = client.get(path)

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert f'data-ui-screen="{screen}"' in response.text


@pytest.mark.parametrize(
    "legacy_path",
    [
        "/templates/home.html",
        "/templates/diagnosis_result.html",
        "/templates/portfolio_input.html",
        "/templates/portfolio_edit.html",
        "/templates/portfolio_summary.html",
        "/templates/issue_analysis.html",
    ],
)
def test_raw_template_urls_are_not_public_routes(legacy_path: str):
    assert client.get(legacy_path).status_code == 404


def test_unintended_ui_templates_are_absent_from_production():
    unintended = {
        "diagnosis.html",
        "index.html",
        "issues.html",
        "rebalancing_profile.html",
        "settings_result.html",
        "components/bottom_nav.html",
        "components/issue_cards.html",
        "components/risk_result.html",
    }

    assert all(not (TEMPLATE_ROOT / relative_path).exists() for relative_path in unintended)


@pytest.mark.parametrize(
    "path",
    [
        "/login",
        "/settings",
        "/portfolio/input",
        "/portfolio/edit",
        "/portfolio/summary",
        "/diagnosis/result",
        "/issue/analysis",
    ],
)
def test_ui_uses_generated_local_tailwind_stylesheet(path: str):
    response = client.get(path)

    assert "/static/css/index.css" in response.text
    assert "cdn.tailwindcss.com" not in response.text
    assert "tailwind.config" not in response.text
