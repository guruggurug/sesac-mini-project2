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


def filter_price_period(
    prices_df: pd.DataFrame,
    years: int = 3
) -> pd.DataFrame:
    """
    Filter price DataFrame to trailing N years from the last available date.

    Args:
        prices_df: Pivoted DataFrame of stock prices.
        years: Period in years (e.g. 1, 3, 5).

    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    if prices_df.empty:
        return prices_df

    end_date = prices_df.index.max()
    start_date = end_date - pd.DateOffset(years=years)
    
    # Filter the dataframe
    filtered_df = prices_df[prices_df.index >= start_date]
    return filtered_df


def calculate_company_downside_risks(
    returns_df: pd.DataFrame,
    prices_df: pd.DataFrame,
    cvar_confidence: float = 0.95,
    years: int = 3
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate company-level downside risk metrics for all tickers over a filtered period.

    Args:
        returns_df: Pivoted DataFrame of daily returns.
        prices_df: Pivoted DataFrame of stock prices.
        cvar_confidence: CVaR confidence level (default 0.95).
        years: Period in years (default 3).

    Returns:
        Dict[str, Dict[str, Any]]: Nested dictionary containing cvar, max_drawdown, downside_deviation per ticker.
    """
    # 1. Filter prices and returns to specified period
    filtered_prices = filter_price_period(prices_df, years=years)
    filtered_returns = returns_df.loc[returns_df.index.intersection(filtered_prices.index)]

    if filtered_returns.empty or len(filtered_prices) < 2:
        raise ValueError("선택한 기간 동안의 거래일 데이터가 부족하여 하방위험을 계산할 수 없습니다.")

    results: Dict[str, Dict[str, Any]] = {}
    
    # Calculate period metadata
    start_dt = str(filtered_prices.index.min())[:10]
    end_dt = str(filtered_prices.index.max())[:10]
    obs_count = len(filtered_prices)

    for ticker in filtered_prices.columns:
        ret_series = filtered_returns[ticker]
        px_series = filtered_prices[ticker]

        cvar_val = calculate_cvar(ret_series, confidence_level=cvar_confidence)
        mdd_val = calculate_mdd(px_series)
        ds_dev_val = calculate_downside_deviation(ret_series, target_return=0.0)

        # Also support 95% explicitly for legacy compatibility if confidence level changes
        cvar_95_val = cvar_val if cvar_confidence == 0.95 else calculate_cvar(ret_series, confidence_level=0.95)

        results[str(ticker)] = {
            "cvar": round(cvar_val, 4),
            "cvar_95": round(cvar_95_val, 4),
            "max_drawdown": round(mdd_val, 4),
            "downside_deviation": round(ds_dev_val, 4),
            "price_period_start": start_dt,
            "price_period_end": end_dt,
            "number_of_observations": obs_count,
            "analysis_period": f"{years}y",
            "confidence_level": cvar_confidence
        }

    return results
