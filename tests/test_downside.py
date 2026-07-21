"""
Unit tests for price validation and downside risk functions (DATA-B-01 & DATA-B-02).
"""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.modeling.price import validate_price_data, calculate_daily_returns
from src.modeling.downside import (
    calculate_cvar,
    calculate_mdd,
    calculate_downside_deviation,
    calculate_company_downside_risks,
)


SAMPLE_CSV_PATH = Path("data/sample/stock_prices.sample.csv")


def test_validate_price_data_sample():
    """Verify price validation on sample CSV dataset."""
    assert SAMPLE_CSV_PATH.exists()
    pivoted = validate_price_data(SAMPLE_CSV_PATH)
    
    assert isinstance(pivoted, pd.DataFrame)
    assert "005930" in pivoted.columns
    assert "000660" in pivoted.columns
    assert len(pivoted) >= 2


def test_validate_price_data_missing_column():
    """Verify ValueError when required column is missing."""
    invalid_df = pd.DataFrame({
        "company_id": ["005930"],
        "close": [70000]
    })
    with pytest.raises(ValueError, match="필수 열이 누락되었습니다"):
        validate_price_data(invalid_df)


def test_calculate_daily_returns():
    """Verify daily percentage return calculation."""
    df_prices = pd.DataFrame({
        "005930": [100.0, 110.0, 99.0],
        "000660": [200.0, 190.0, 190.0]
    }, index=pd.date_range("2024-01-01", periods=3))

    returns = calculate_daily_returns(df_prices)
    assert len(returns) == 2
    assert pytest.approx(returns.loc[pd.Timestamp("2024-01-02"), "005930"]) == 0.10
    assert pytest.approx(returns.loc[pd.Timestamp("2024-01-03"), "005930"]) == -0.10
    assert pytest.approx(returns.loc[pd.Timestamp("2024-01-02"), "000660"]) == -0.05


def test_calculate_cvar_positive_magnitude():
    """Verify Historical CVaR returns a positive float value representing tail loss."""
    # Returns with negative tail losses
    returns = pd.Series([0.01, 0.02, -0.01, -0.05, -0.10, 0.03, -0.02, -0.08, 0.01, 0.00])
    cvar = calculate_cvar(returns, confidence_level=0.80)
    
    assert cvar > 0.0
    assert isinstance(cvar, float)


def test_calculate_mdd():
    """Verify Maximum Drawdown calculation."""
    # Peak is 100, drops to 70 (MDD = 30%)
    prices = pd.Series([80, 100, 90, 70, 85, 95])
    mdd = calculate_mdd(prices)
    
    assert pytest.approx(mdd) == 0.30


def test_calculate_downside_deviation():
    """Verify Downside Deviation calculation."""
    returns = pd.Series([0.05, -0.03, 0.02, -0.04, 0.01])
    ds_dev = calculate_downside_deviation(returns, target_return=0.0)
    
    assert ds_dev > 0.0
    assert isinstance(ds_dev, float)


def test_calculate_company_downside_risks():
    """Verify aggregated company downside risk output format."""
    pivoted_prices = pd.DataFrame({
        "005930": [70000, 71000, 69000, 68000, 72000],
        "000660": [140000, 138000, 135000, 139000, 142000]
    }, index=pd.date_range("2024-01-01", periods=5))

    returns = calculate_daily_returns(pivoted_prices)
    risks = calculate_company_downside_risks(returns, pivoted_prices, cvar_confidence=0.95)

    assert "005930" in risks
    assert "000660" in risks
    assert "cvar_95" in risks["005930"]
    assert "max_drawdown" in risks["005930"]
    assert "downside_deviation" in risks["005930"]
    assert risks["005930"]["cvar_95"] >= 0.0
    assert risks["005930"]["max_drawdown"] >= 0.0
    assert risks["005930"]["downside_deviation"] >= 0.0
