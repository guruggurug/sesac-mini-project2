"""
Unit tests for portfolio weight grid-search optimization engine (DATA-B-03 Phase 1 Refinements).
"""

from pathlib import Path
import pytest
import pandas as pd

from src.modeling.optimizer import optimize_portfolio, load_esg_scores, resolve_risk_profile


SAMPLE_CSV_PATH = Path("data/sample/stock_prices.sample.csv").resolve()


def balanced_holdings():
    return [
        {
            "ticker": "005930",
            "quantity": 10,
            "average_price": 70000,
            "current_price": 100000,
        },
        {
            "ticker": "000660",
            "quantity": 10,
            "average_price": 180000,
            "current_price": 100000,
        },
    ]


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


def test_resolve_risk_profile():
    """Verify PRD risk profile resolution and custom weight validation."""
    p1 = resolve_risk_profile("loss_minimization")
    assert p1["alpha"] == 0.72
    assert p1["beta"] == 0.18

    p2 = resolve_risk_profile("balanced")
    assert p2["alpha"] == 0.63
    assert p2["beta"] == 0.27

    p3 = resolve_risk_profile("esg_focused")
    assert p3["alpha"] == 0.45
    assert p3["beta"] == 0.45

    # Legacy alias
    p4 = resolve_risk_profile("conservative")
    assert p4["alpha"] == 0.72

    # Custom weights valid
    p_custom = resolve_risk_profile(custom_alpha=0.5, custom_beta=0.4, custom_gamma=0.1)
    assert p_custom["alpha"] == 0.5

    # Invalid custom sum
    with pytest.raises(ValueError, match="목적함수 가중치의 합은 1.0이어야 합니다"):
        resolve_risk_profile(custom_alpha=0.5, custom_beta=0.5, custom_gamma=0.5)

    # Invalid negative weight
    with pytest.raises(ValueError, match="목적함수 가중치.*모두 0 이상이어야 합니다"):
        resolve_risk_profile(custom_alpha=-0.1, custom_beta=0.8, custom_gamma=0.3)


def test_optimize_portfolio_current_price_weighting():
    """Verify that current_price determines current weight, not average_price."""
    # Holdings with average_price vs current_price
    holdings = [
        {"ticker": "005930", "quantity": 10, "average_price": 70000, "current_price": 100000},  # 1,000,000 KRW
        {"ticker": "000660", "quantity": 10, "average_price": 180000, "current_price": 100000}, # 1,000,000 KRW
    ]

    result = optimize_portfolio(
        holdings=holdings,
        price_data=SAMPLE_CSV_PATH,
        risk_priority="balanced"
    )

    # Equal market value (100k vs 100k) should yield 50:50 current weight
    assert pytest.approx(result["current_weights"]["005930"]) == 0.50
    assert pytest.approx(result["current_weights"]["000660"]) == 0.50


def test_optimize_portfolio_single_stock_holding():
    """Verify single-stock holding (100% Samsung) operates cleanly."""
    holdings = [
        {"ticker": "005930", "quantity": 100, "average_price": 70000, "current_price": 80000},
    ]

    result = optimize_portfolio(
        holdings=holdings,
        price_data=SAMPLE_CSV_PATH,
        risk_priority="loss_minimization"
    )

    assert result["current_weights"]["005930"] == 1.0
    assert result["current_weights"]["000660"] == 0.0

    # Recommended weights must still adhere to [0.20, 0.80] bounds
    rec_sam = result["recommended_weights"]["005930"]
    assert 0.20 <= rec_sam <= 0.80


def test_optimize_portfolio_empty_holdings_error():
    """Verify error when total market value across holdings is zero."""
    holdings = [
        {"ticker": "005930", "quantity": 0, "average_price": 0},
        {"ticker": "000660", "quantity": 0, "average_price": 0},
    ]

    with pytest.raises(ValueError, match="보유 주식이 없습니다"):
        optimize_portfolio(holdings=holdings, price_data=SAMPLE_CSV_PATH)


def test_validated_optimization_rejects_missing_esg_aggregate():
    with pytest.raises(ValueError, match="missing tickers: 000660"):
        optimize_portfolio(
            holdings=balanced_holdings(),
            price_data=SAMPLE_CSV_PATH,
            esg_input={"005930": 0.4},
            data_mode="validated",
        )


def test_optimizer_is_side_effect_free_by_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    optimize_portfolio(
        holdings=balanced_holdings(),
        price_data=SAMPLE_CSV_PATH,
        esg_input={"005930": 0.4, "000660": 0.5},
        data_mode="validated",
    )

    assert not (tmp_path / "data/processed/optimization_grid_results.csv").exists()


def test_optimizer_writes_grid_only_to_explicit_output(tmp_path):
    output_path = tmp_path / "batch" / "optimization_grid_results.csv"

    result = optimize_portfolio(
        holdings=balanced_holdings(),
        price_data=SAMPLE_CSV_PATH,
        esg_input={"005930": 0.4, "000660": 0.5},
        data_mode="validated",
        grid_results_output=output_path,
    )

    grid = pd.read_csv(output_path)
    assert len(grid) == 61
    assert result["recommended_weights"]["005930"] + result["recommended_weights"]["000660"] == pytest.approx(1.0)
    assert 0.2 <= result["recommended_weights"]["005930"] <= 0.8


def test_optimizer_is_deterministic_for_same_inputs():
    kwargs = {
        "holdings": balanced_holdings(),
        "price_data": SAMPLE_CSV_PATH,
        "esg_input": {"005930": 0.4, "000660": 0.5},
        "data_mode": "validated",
    }

    first = optimize_portfolio(**kwargs)
    second = optimize_portfolio(**kwargs)

    for key in (
        "recommended_weights",
        "current_total_risk",
        "optimized_total_risk",
        "risk_reduction_rate",
        "near_optimal_range",
    ):
        assert first[key] == second[key]
