"""
Unit tests for portfolio weight grid-search optimization engine (DATA-B-03).
"""

from pathlib import Path
import pytest
import pandas as pd

from src.modeling.optimizer import optimize_portfolio, load_esg_scores


SAMPLE_CSV_PATH = Path("data/sample/stock_prices.sample.csv")


def test_load_esg_scores():
    """Verify sample-only default ESG scores loading."""
    esg = load_esg_scores(allow_sample_defaults=True)
    assert "005930" in esg
    assert "000660" in esg
    assert 0.0 <= esg["005930"] <= 1.0
    assert 0.0 <= esg["000660"] <= 1.0


def test_load_esg_scores_rejects_missing_scores_in_validated_mode():
    with pytest.raises(ValueError, match="ESG risk score unavailable"):
        load_esg_scores()

    with pytest.raises(ValueError, match="missing tickers: 000660"):
        load_esg_scores({"005930": 0.42})


def test_optimize_portfolio_sample():
    """Verify portfolio optimization using sample data."""
    holdings = [
        {"ticker": "005930", "quantity": 70, "average_price": 70000},
        {"ticker": "000660", "quantity": 30, "average_price": 180000},
    ]

    result = optimize_portfolio(
        holdings=holdings,
        price_data=SAMPLE_CSV_PATH,
        risk_priority="balanced",
        data_mode="sample"
    )

    # Required fields check
    assert "current_weights" in result
    assert "recommended_weights" in result
    assert "current_total_risk" in result
    assert "optimized_total_risk" in result
    assert "risk_reduction_rate" in result
    assert "company_risks" in result
    assert "explanation" in result
    assert "data_status" in result
    assert "warnings" in result
    assert "model_metadata" in result

    # Weight constraints check (20% to 80%)
    rec_sam = result["recommended_weights"]["005930"]
    rec_sk = result["recommended_weights"]["000660"]
    assert 0.20 <= rec_sam <= 0.80
    assert 0.20 <= rec_sk <= 0.80
    assert pytest.approx(rec_sam + rec_sk) == 1.0

    # Korean explanations check
    assert len(result["explanation"]) >= 1
    assert any("삼성전자" in exp or "포트폴리오" in exp for exp in result["explanation"])

    # Korean warnings check
    assert any("기대수익률" in w for w in result["warnings"])
    assert any("반도체 산업" in w for w in result["warnings"])


def test_optimize_portfolio_invalid_priority():
    """Verify error on invalid risk priority."""
    holdings = [
        {"ticker": "005930", "quantity": 50, "average_price": 70000},
        {"ticker": "000660", "quantity": 50, "average_price": 140000},
    ]
    with pytest.raises(ValueError, match="유효하지 않은 risk_priority입니다"):
        optimize_portfolio(
            holdings=holdings,
            price_data=SAMPLE_CSV_PATH,
            risk_priority="invalid_priority"
        )
