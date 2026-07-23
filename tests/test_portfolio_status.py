"""
Unit tests for portfolio status scoring and summaries (portfolio_status.py).
"""

import pytest
from src.modeling.portfolio_status import calculate_portfolio_status


def test_calculate_portfolio_status_green():
    """Verify that low risk (total risk 0.25) yields green status."""
    opt_result = {
        "current_total_risk": 0.25,
        "current_weights": {"005930": 0.50, "000660": 0.50},
        "recommended_weights": {"005930": 0.50, "000660": 0.50},
        "risk_reduction_rate": 0.0,
        "company_risks": {
            "005930": {"risk_level": "low"},
            "000660": {"risk_level": "low"}
        }
    }

    status = calculate_portfolio_status(opt_result)
    assert status["portfolio_status_score"] == 75  # 100 * (1 - 0.25) = 75
    assert status["signal"] == "green"
    assert "안정적인 포트폴리오 상태" in status["label"]
    assert len(status["summary"]) >= 2
    assert any("분산되어 있습니다" in s for s in status["summary"])


def test_calculate_portfolio_status_yellow_with_warnings():
    """Verify that medium risk (total risk 0.55) yields yellow status and risk reduction warning."""
    opt_result = {
        "current_total_risk": 0.55,
        "current_weights": {"005930": 0.30, "000660": 0.70},
        "recommended_weights": {"005930": 0.50, "000660": 0.50},
        "risk_reduction_rate": 0.15,
        "company_risks": {
            "005930": {"risk_level": "low"},
            "000660": {"risk_level": "high"}
        }
    }

    status = calculate_portfolio_status(opt_result)
    assert status["portfolio_status_score"] == 45  # 100 * (1 - 0.55) = 45
    assert status["signal"] == "yellow"
    assert "비중 조정 검토 필요" in status["label"]
    assert any("SK하이닉스 비중이 상대적으로 높습니다" in s for s in status["summary"])
    assert any("15.0% 감소합니다" in s for s in status["summary"])
    assert any("SK하이닉스의 하방위험 혹은 ESG 지표 수준이 취약" in s for s in status["summary"])
