"""
Price Data Validation & Daily Returns Module for Data B.
"""

from pathlib import Path
from typing import Union
import pandas as pd


REQUIRED_TICKERS = ["005930", "000660"]
COMPANY_NAME_MAP = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
}


def validate_price_data(
    data_input: Union[str, Path, pd.DataFrame]
) -> pd.DataFrame:
    """
    Validate raw price dataset and return a pivoted DataFrame indexed by date.

    Args:
        data_input: Path to stock prices CSV or pandas DataFrame.

    Returns:
        pd.DataFrame: Pivoted DataFrame with 'date' index and columns ['005930', '000660'] containing prices.
    
    Raises:
        ValueError: If required columns or tickers are missing, or if data is malformed.
    """
    if isinstance(data_input, (str, Path)):
        file_path = Path(data_input)
        if not file_path.exists():
            raise ValueError(f"주가 파일을 찾을 수 없습니다: {file_path}")
        df = pd.read_csv(file_path)
    elif isinstance(data_input, pd.DataFrame):
        df = data_input.copy()
    else:
        raise ValueError("입력값은 파일 경로 문자열, Path 객체 또는 pandas DataFrame이어야 합니다.")

    if df.empty:
        raise ValueError("주가 데이터셋이 비어 있습니다.")

    # Check date column
    if "date" not in df.columns:
        raise ValueError("필수 열이 누락되었습니다: 'date'")
    
    # Check ticker / company_id column
    ticker_col = "ticker" if "ticker" in df.columns else ("company_id" if "company_id" in df.columns else None)
    if not ticker_col:
        raise ValueError("필수 종목 코드 열('ticker' 또는 'company_id')이 누락되었습니다.")

    # Check price column
    price_col = "adjusted_close" if "adjusted_close" in df.columns and df["adjusted_close"].notna().any() else ("close" if "close" in df.columns else None)
    if not price_col:
        raise ValueError("필수 가격 열('close' 또는 'adjusted_close')이 누락되었습니다.")

    # Filter tickers and ensure 6-digit zfill for stock codes
    df[ticker_col] = df[ticker_col].astype(str).str.zfill(6)
    present_tickers = set(df[ticker_col].unique())
    missing_tickers = [t for t in REQUIRED_TICKERS if t not in present_tickers]
    if missing_tickers:
        raise ValueError(f"필수 종목 코드가 데이터셋에 누락되었습니다: {missing_tickers}")

    # Convert date and sort
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # Check duplicates
    if df.duplicated(subset=["date", ticker_col]).any():
        raise ValueError("동일한 날짜와 종목 코드에 대한 중복 데이터가 존재합니다.")

    # Convert prices to numeric
    df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
    if df[price_col].isna().any():
        raise ValueError("가격 열에 유효하지 않거나 숫자가 아닌 값이 포함되어 있습니다.")

    if (df[price_col] <= 0).any():
        raise ValueError("주가는 양수이어야 합니다.")

    # Pivot to date x ticker matrix
    pivoted = df.pivot(index="date", columns=ticker_col, values=price_col)
    
    # Ensure required tickers exist in columns
    pivoted = pivoted[REQUIRED_TICKERS].dropna()

    if len(pivoted) < 2:
        raise ValueError("수익률 계산을 위한 공통 거래일 데이터가 부족합니다 (최소 2일 이상 필요).")

    return pivoted


def calculate_daily_returns(
    prices_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Calculate daily percentage returns for validated price series.

    Args:
        prices_df: Pivoted DataFrame with 'date' index and ticker columns.

    Returns:
        pd.DataFrame: Daily percentage returns r_t = (P_t / P_{t-1}) - 1
    """
    if prices_df.empty or len(prices_df) < 2:
        raise ValueError("2개 미만의 주가 데이터로는 일별 수익률을 계산할 수 없습니다.")

    returns_df = prices_df.pct_change().dropna()
    
    return returns_df
