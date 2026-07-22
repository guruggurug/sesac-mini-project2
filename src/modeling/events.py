"""
Historical Event Reaction Analysis Module for Data B.
Calculates post-event returns (1d, 3d, 5d), maximum drawdown, recovery period, benchmark comparison, and chart data.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np

from src.modeling.price import validate_price_data

COMPANY_NAME_MAP = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
}


def find_reaction_start_date(
    event_date_str: str,
    trading_dates: pd.DatetimeIndex
) -> Optional[pd.Timestamp]:
    """
    Find the exact event date or the first subsequent trading day if event_date falls on a weekend/holiday.
    """
    event_dt = pd.to_datetime(event_date_str)
    subsequent_dates = trading_dates[trading_dates >= event_dt]
    
    if subsequent_dates.empty:
        return None
    
    return subsequent_dates[0]


def analyze_single_event_reaction(
    event: Dict[str, Any],
    prices_df: pd.DataFrame,
    index_prices: Optional[pd.Series] = None,
    window_days: int = 10
) -> Dict[str, Any]:
    """
    Analyze stock price reaction and benchmark abnormal returns following a single event.

    Args:
        event: Dictionary containing event data fields.
        prices_df: Pivoted stock prices DataFrame indexed by date.
        index_prices: Series of benchmark index prices (e.g. SOX).
        window_days: Number of trading days to track post-event for chart returns (default 10).

    Returns:
        Dict[str, Any]: Event reaction analysis object.
    """
    ticker = str(event.get("ticker", event.get("company_id", ""))).zfill(6)
    if ticker not in prices_df.columns:
        raise ValueError(f"주가 데이터에서 종목 코드 '{ticker}'를 찾을 수 없습니다.")

    event_id = str(event.get("event_id", ""))
    # Priority: market_event_date -> event_date
    event_date_str = str(event.get("market_event_date") or event.get("event_date") or "")
    if not event_date_str or event_date_str == "nan" or event_date_str == "None":
        event_date_str = str(event.get("event_date", ""))
        
    if not event_date_str or event_date_str == "nan":
        raise ValueError("사건 날짜 정보가 존재하지 않습니다.")

    trading_dates = prices_df.index
    reaction_start_dt = find_reaction_start_date(event_date_str, trading_dates)

    if reaction_start_dt is None:
        raise ValueError(f"사건 일자({event_date_str}) 이후의 거래일 주가 데이터가 없습니다.")

    # Find position of start date in price series
    start_pos = trading_dates.get_loc(reaction_start_dt)
    px_series = prices_df[ticker]
    total_len = len(px_series)

    p0 = px_series.iloc[start_pos]
    if p0 <= 0:
        raise ValueError(f"사건 반응 시작일의 주가가 0 이하입니다: {p0}")

    # 1. 10-day returns window for chart data
    end_pos = min(start_pos + window_days + 1, total_len)
    window_prices = px_series.iloc[start_pos:end_pos]
    cum_returns = (window_prices - p0) / p0

    r1d = round(float(cum_returns.iloc[1]), 4) if len(cum_returns) > 1 else None
    r3d = round(float(cum_returns.iloc[3]), 4) if len(cum_returns) > 3 else None
    r5d = round(float(cum_returns.iloc[5]), 4) if len(cum_returns) > 5 else None

    # 2. Event relative minimum return (worst cumulative return in window)
    event_relative_min_return = round(float(cum_returns.min()), 4)

    # 3. Peak-to-trough drawdown in the window (standard MDD)
    cum_max_win = window_prices.cummax()
    drawdowns_win = (cum_max_win - window_prices) / cum_max_win
    window_max_drawdown = round(float(drawdowns_win.max()), 4)

    # 4. Recovery days: search up to 60 trading days post-event
    recovery_days: Optional[int] = None
    recovery_search_len = min(start_pos + 61, total_len)
    search_prices = px_series.iloc[start_pos:recovery_search_len]
    for day_idx in range(1, len(search_prices)):
        if search_prices.iloc[day_idx] >= p0:
            recovery_days = day_idx
            break

    # 5. Benchmark abnormal returns (using SOX index_prices if available)
    ar1d, ar3d, ar5d = None, None, None
    benchmark_name = None
    
    if index_prices is not None and not index_prices.empty:
        # Align index prices to our stock trading dates index
        benchmark_name = "SOX"
        aligned_bench = index_prices.reindex(window_prices.index, method="ffill")
        b0 = aligned_bench.iloc[0] if len(aligned_bench) > 0 else 0.0
        
        if b0 > 0:
            bench_cum_returns = (aligned_bench - b0) / b0
            abnormal_returns = cum_returns - bench_cum_returns
            
            ar1d = round(float(abnormal_returns.iloc[1]), 4) if len(abnormal_returns) > 1 else None
            ar3d = round(float(abnormal_returns.iloc[3]), 4) if len(abnormal_returns) > 3 else None
            ar5d = round(float(abnormal_returns.iloc[5]), 4) if len(abnormal_returns) > 5 else None

    # Build chart_data array
    chart_data = [
        {
            "day": k,
            "cumulative_return": round(float(cum_returns.iloc[k]), 4),
            "date": str(trading_dates[start_pos + k])[:10],
        }
        for k in range(len(cum_returns))
    ]

    return {
        "event_id": event_id,
        "company_id": ticker,
        "company_name": COMPANY_NAME_MAP.get(ticker, str(event.get("company_name", ticker))),
        "event_date": str(event.get("event_date", event_date_str)),
        "market_event_date": event_date_str,
        "reaction_start_date": str(reaction_start_dt)[:10],
        "return_1d": r1d,
        "return_3d": r3d,
        "return_5d": r5d,
        "event_relative_min_return": event_relative_min_return,
        "window_max_drawdown": window_max_drawdown,
        "max_drawdown": event_relative_min_return,  # Backward compatibility
        "recovery_days": recovery_days,
        "abnormal_return_1d": ar1d,
        "abnormal_return_3d": ar3d,
        "abnormal_return_5d": ar5d,
        "benchmark_name": benchmark_name,
        "status": str(event.get("status", "confirmed")),
        "summary": str(event.get("summary", "")),
        "chart_data": chart_data,
    }


def analyze_all_events(
    events_input: Union[str, Path, pd.DataFrame],
    price_data: Union[str, Path, pd.DataFrame],
    index_prices_input: Optional[Union[str, Path, pd.DataFrame]] = None,
    window_days: int = 10,
    filter_model_eligible_only: bool = True
) -> List[Dict[str, Any]]:
    """
    Run post-event reaction analysis for automatically verified, model-eligible events.

    Args:
        events_input: Path to events CSV or pandas DataFrame.
        price_data: Path to stock prices CSV or validated prices DataFrame.
        index_prices_input: Optional path to index prices CSV or DataFrame.
        window_days: Window length in trading days (default 10).
        filter_model_eligible_only: Whether to require a verified status, authority confirmation,
            and an official source URL (default True).

    Returns:
        List[Dict[str, Any]]: List of event reaction analysis results.
    """
    if isinstance(events_input, (str, Path)):
        file_path = Path(events_input)
        if not file_path.exists():
            raise ValueError(f"사건 데이터 파일을 찾을 수 없습니다: {file_path}")
        events_df = pd.read_csv(file_path)
    elif isinstance(events_input, pd.DataFrame):
        events_df = events_input.copy()
    else:
        raise ValueError("사건 입력값은 파일 경로 문자열, Path 객체 또는 pandas DataFrame이어야 합니다.")

    if events_df.empty:
        return []

    # Validate & pivot price data
    prices_df = validate_price_data(price_data)

    # Load benchmark prices
    index_series = None
    if index_prices_input is not None:
        try:
            if isinstance(index_prices_input, (str, Path)):
                idx_df = pd.read_csv(index_prices_input)
            elif isinstance(index_prices_input, pd.DataFrame):
                idx_df = index_prices_input.copy()
            else:
                idx_df = pd.DataFrame()
            
            if not idx_df.empty and "date" in idx_df.columns and "close" in idx_df.columns:
                idx_df["date"] = pd.to_datetime(idx_df["date"])
                # Philadelphia Semiconductor Index is SOX
                sox_df = idx_df[idx_df["index_id"] == "SOX"].sort_values("date")
                if not sox_df.empty:
                    index_series = sox_df.set_index("date")["close"]
        except Exception:
            index_series = None

    # Apply the automatic model-eligibility gate used by the backend repository.
    if filter_model_eligible_only:
        eligible_statuses = {"confirmed", "resolved"}
        events_df = events_df[
            events_df["status"].isin(eligible_statuses)
            & (events_df["authority_confirmed"] == True)
            & events_df["official_source_url"].notna()
            & (events_df["official_source_url"].astype(str).str.len() > 0)
        ]

    # Filter status: confirmed, sanctioned, resolved, reported
    if "status" in events_df.columns:
        events_df = events_df[events_df["status"].isin(["confirmed", "sanctioned", "resolved", "reported"])]

    results = []
    for _, row in events_df.iterrows():
        try:
            reaction = analyze_single_event_reaction(
                event=row.to_dict(),
                prices_df=prices_df,
                index_prices=index_series,
                window_days=window_days
            )
            results.append(reaction)
        except ValueError as exc:
            # Skip or record warning for events outside price date range
            results.append({
                "event_id": str(row.get("event_id", "")),
                "company_id": str(row.get("company_id", row.get("ticker", ""))).zfill(6),
                "event_date": str(row.get("event_date", "")),
                "market_event_date": str(row.get("market_event_date", row.get("event_date", ""))),
                "status": str(row.get("status", "unknown")),
                "error": str(exc),
                "analyzed": False,
            })

    return results
