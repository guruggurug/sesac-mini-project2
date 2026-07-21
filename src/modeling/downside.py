"""
Downside Risk Metrics Module for Data B.
Calculates Historical CVaR 95%, Maximum Drawdown (MDD), and Downside Deviation.
"""

from typing import Dict, Any, Union
import numpy as np
import pandas as pd


def calculate_cvar(
    returns_series: pd.Series,
    confidence_level: float = 0.95
) -> float:
    """
    Calculate Historical CVaR (Conditional Value at Risk) at specified confidence level.

    Args:
        returns_series: Series of daily percentage returns.
        confidence_level: Confidence level (e.g. 0.95 for 95% CVaR).

    Returns:
        float: Positive magnitude representing average tail loss in worst (1 - confidence_level) quantile.
    """
    clean_returns = returns_series.dropna()
    if clean_returns.empty:
        raise ValueError("수익률 데이터가 비어 있어 CVaR를 계산할 수 없습니다.")

    if not (0.0 < confidence_level < 1.0):
        raise ValueError(f"CVaR 신뢰수준은 0과 1 사이이어야 합니다 (입력값: {confidence_level}).")

    tail_alpha = 1.0 - confidence_level
    var_threshold = clean_returns.quantile(tail_alpha)
    
    tail_losses = clean_returns[clean_returns <= var_threshold]
    if tail_losses.empty:
        cvar_val = var_threshold
    else:
        cvar_val = tail_losses.mean()

    # Risk value returned as positive loss magnitude
    return float(abs(cvar_val))


def calculate_mdd(
    prices_series: pd.Series
) -> float:
    """
    Calculate Maximum Drawdown (MDD) from price series.

    Args:
        prices_series: Series of stock prices over time.

    Returns:
        float: Maximum peak-to-trough decline as a positive decimal (e.g. 0.25 for 25%).
    """
    clean_prices = prices_series.dropna()
    if clean_prices.empty or len(clean_prices) < 2:
        raise ValueError("2개 미만의 주가 데이터로는 MDD를 계산할 수 없습니다.")

    cum_max = clean_prices.cummax()
    drawdowns = (cum_max - clean_prices) / cum_max
    max_dd = drawdowns.max()

    return float(max_dd)


def calculate_downside_deviation(
    returns_series: pd.Series,
    target_return: float = 0.0
) -> float:
    """
    Calculate Downside Deviation (semi-deviation) relative to target return.

    Args:
        returns_series: Series of daily percentage returns.
        target_return: Threshold return rate (default 0.0).

    Returns:
        float: Downside deviation as a positive decimal.
    """
    clean_returns = returns_series.dropna()
    if clean_returns.empty:
        raise ValueError("수익률 데이터가 비어 있어 하방편차를 계산할 수 없습니다.")

    underperformance = np.minimum(clean_returns - target_return, 0.0)
    squared_losses = np.square(underperformance)
    downside_dev = np.sqrt(np.mean(squared_losses))

    return float(downside_dev)


def calculate_company_downside_risks(
    returns_df: pd.DataFrame,
    prices_df: pd.DataFrame,
    cvar_confidence: float = 0.95
) -> Dict[str, Dict[str, float]]:
    """
    Calculate company-level downside risk metrics for all tickers.

    Args:
        returns_df: Pivoted DataFrame of daily returns.
        prices_df: Pivoted DataFrame of stock prices.
        cvar_confidence: CVaR confidence level (default 0.95).

    Returns:
        Dict[str, Dict[str, float]]: Nested dictionary containing cvar_95, max_drawdown, downside_deviation per ticker.
    """
    results: Dict[str, Dict[str, float]] = {}

    for ticker in returns_df.columns:
        ret_series = returns_df[ticker]
        px_series = prices_df[ticker]

        cvar_val = calculate_cvar(ret_series, confidence_level=cvar_confidence)
        mdd_val = calculate_mdd(px_series)
        ds_dev_val = calculate_downside_deviation(ret_series, target_return=0.0)

        results[str(ticker)] = {
            "cvar_95": round(cvar_val, 4),
            "max_drawdown": round(mdd_val, 4),
            "downside_deviation": round(ds_dev_val, 4),
        }

    return results
