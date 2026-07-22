"""
Historical Event Reaction Analysis Module for Data B.
Calculates post-event returns (1d, 3d, 5d), maximum drawdown, recovery period, and chart data.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import pandas as pd

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

    Args:
        event_date_str: YYYY-MM-DD date string.
        trading_dates: DatetimeIndex of available trading days.

    Returns:
        Optional[pd.Timestamp]: Matched trading day timestamp, or None if outside date range.
    """
    event_dt = pd.to_datetime(event_date_str)
    subsequent_dates = trading_dates[trading_dates >= event_dt]
    
    if subsequent_dates.empty:
        return None
    
    return subsequent_dates[0]


def analyze_single_event_reaction(
    event: Dict[str, Any],
    prices_df: pd.DataFrame,
    window_days: int = 10
) -> Dict[str, Any]:
    """
    Analyze stock price reaction following a single event.

    Args:
        event: Dictionary or series containing event data fields.
        prices_df: Pivoted stock prices DataFrame indexed by date.
        window_days: Number of trading days to track post-event (default 10).

    Returns:
        Dict[str, Any]: Event reaction analysis object containing 1d, 3d, 5d returns, MDD, recovery days, and chart data.
    """
    ticker = str(event.get("ticker", event.get("company_id", ""))).zfill(6)
    if ticker not in prices_df.columns:
        raise ValueError(f"주가 데이터에서 종목 코드 '{ticker}'를 찾을 수 없습니다.")

    event_id = str(event.get("event_id", ""))
    event_date_str = str(event.get("market_event_date") or event.get("event_date", ""))

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

    # End position for window
    end_pos = min(start_pos + window_days + 1, total_len)
    window_prices = px_series.iloc[start_pos:end_pos]

    # Calculate cumulative returns over window
    cum_returns = (window_prices - p0) / p0

    # 1-day, 3-day, 5-day returns
    r1d = round(float(cum_returns.iloc[1]), 4) if len(cum_returns) > 1 else None
    r3d = round(float(cum_returns.iloc[3]), 4) if len(cum_returns) > 3 else None
    r5d = round(float(cum_returns.iloc[5]), 4) if len(cum_returns) > 5 else None

    # Post-event maximum drawdown (worst negative return in window)
    max_drawdown = round(float(cum_returns.min()), 4)

    # Recovery days: count trading days until price recovers to >= P0
    recovery_days: Optional[int] = None
    for day_idx in range(1, len(window_prices)):
        if window_prices.iloc[day_idx] >= p0:
            recovery_days = day_idx
            break

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
        "max_drawdown": max_drawdown,
        "recovery_days": recovery_days,
        "status": str(event.get("status", "confirmed")),
        "summary": str(event.get("summary", "")),
        "chart_data": chart_data,
    }


def analyze_all_events(
    events_input: Union[str, Path, pd.DataFrame],
    price_data: Union[str, Path, pd.DataFrame],
    window_days: int = 10,
    filter_model_eligible_only: bool = True
) -> List[Dict[str, Any]]:
    """
    Run post-event reaction analysis for automatically verified, model-eligible events.

    Args:
        events_input: Path to events CSV or pandas DataFrame.
        price_data: Path to stock prices CSV or validated prices DataFrame.
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

    # Apply the automatic model-eligibility gate used by the backend repository.
    if filter_model_eligible_only:
        eligible_statuses = {"confirmed", "resolved"}
        events_df = events_df[
            events_df["status"].isin(eligible_statuses)
            & (events_df["authority_confirmed"] == True)
            & events_df["official_source_url"].notna()
            & (events_df["official_source_url"].astype(str).str.len() > 0)
        ]

    results = []
    for _, row in events_df.iterrows():
        try:
            reaction = analyze_single_event_reaction(row.to_dict(), prices_df, window_days=window_days)
            results.append(reaction)
        except ValueError as exc:
            # Record warning for events outside price data range
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
