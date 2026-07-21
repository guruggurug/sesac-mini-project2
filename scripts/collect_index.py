"""
This script collects daily close prices and returns for the Philadelphia Semiconductor Index (SOX)
from Yahoo Finance for the last 3 years, validates the collected data,
and saves it to data/index_prices.csv.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import yfinance as yf

# 1. 설정 상수 (Configuration Constants)
TICKER_SYMBOL = "^SOX"
INDEX_ID = "SOX"
SOURCE_URL = "https://finance.yahoo.com/quote/%5ESOX"
DATA_DIR = "data"
TEMP_FILE_PATH = os.path.join(DATA_DIR, "index_prices_new.csv")
TARGET_FILE_PATH = os.path.join(DATA_DIR, "index_prices.csv")
REQUIRED_COLS = ["date", "index_id", "close", "return", "source_url", "collected_at"]

# 2. collect()
def collect() -> pd.DataFrame:
    """
    Downloads historical data for ^SOX from yfinance for the last 3 years
    and formats it according to the schema.
    """
    today = datetime.now()
    # 최근 3년 일별 종가
    start_date = (today - timedelta(days=3 * 365)).strftime("%Y-%m-%d")
    end_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    
    print(f"Downloading {TICKER_SYMBOL} data from {start_date} to {today.strftime('%Y-%m-%d')}...")
    
    ticker = yf.Ticker(TICKER_SYMBOL)
    df = ticker.history(start=start_date, end=end_date)
    
    if df.empty:
        raise ValueError(f"No price data retrieved for symbol {TICKER_SYMBOL}.")
        
    df = df.reset_index()
    
    # Format and transform
    df['date'] = df['Date'].dt.strftime('%Y-%m-%d')
    df['index_id'] = INDEX_ID
    df['close'] = df['Close'].round(2)
    # Calculate daily return based on close price
    df['return'] = df['Close'].pct_change().round(6)
    df['source_url'] = SOURCE_URL
    
    # collected_at in KST ISO format (e.g. 2026-07-20T21:47:54+09:00)
    kst = timezone(timedelta(hours=9))
    collected_at_val = datetime.now(kst).isoformat(timespec='seconds')
    df['collected_at'] = collected_at_val
    
    # Order by date ascending
    df = df.sort_values(by='date').reset_index(drop=True)
    
    # Filter columns and retain order
    df = df[REQUIRED_COLS]
    
    return df

# 3. validate()
def validate(file_path: str) -> bool:
    """
    Validates the CSV file against the requirements.
    Returns True if valid, raises ValueError or returns False otherwise.
    """
    print(f"Validating {file_path}...")
    if not os.path.exists(file_path):
        raise ValueError(f"File {file_path} does not exist.")
        
    df = pd.read_csv(file_path, encoding='utf-8-sig')
    
    # Rule 1: Required columns exist
    missing_cols = [col for col in REQUIRED_COLS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
        
    # Rule 2: Date ordered ascending
    dates = pd.to_datetime(df['date'])
    if not dates.is_monotonic_increasing:
        raise ValueError("Dates are not sorted in ascending order.")
        
    # Rule 3: No duplicate (date, index_id)
    duplicates = df[df.duplicated(subset=['date', 'index_id'])]
    if not duplicates.empty:
        raise ValueError(f"Duplicate (date, index_id) entries found:\n{duplicates}")
        
    # Rule 4: close > 0 (no close <= 0)
    invalid_close = df[df['close'] <= 0]
    if not invalid_close.empty:
        raise ValueError(f"Invalid close prices (<= 0) found:\n{invalid_close}")
        
    # Rule 5: |return| <= 0.30
    invalid_returns = df[df['return'].abs() > 0.30]
    if not invalid_returns.empty:
        raise ValueError(f"Improbably large daily returns (> 30%) found:\n{invalid_returns}")
        
    # Rule 6: Minimum row count (행 수 >= 627)
    row_count = len(df)
    min_rows = 627
    if row_count < min_rows:
        raise ValueError(f"Insufficient data: row count {row_count} is less than required minimum {min_rows}.")
        
    # Rule 7: Only the first row's return is NaN (empty in CSV). All other returns must be valid.
    null_count = df['return'].isna().sum()
    if null_count != 1:
        null_indices = df[df['return'].isna()].index.tolist()
        raise ValueError(f"Expected exactly 1 null value in 'return', found {null_count} at index/indices: {null_indices}")
        
    if not pd.isna(df.loc[0, 'return']):
        raise ValueError("The missing return must be on the first trading day.")
        
    # Log warning as required: return 결측은 첫 거래일 1건만 정상(경고 기록)
    print("[경고] 첫 거래일의 return이 결측(NaN)으로 수집되었습니다. (정상 케이스)")
    
    print(f"Verification passed: {row_count} rows, date range {df['date'].min()} to {df['date'].max()}.")
    return True

# 4. main()
def main():
    """
    Main logic to coordinate download, temp save, validation, and swap.
    """
    try:
        # Ensure directories exist
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # 1. Collect data
        df = collect()
        
        # 2. Save to temporary file with utf-8-sig
        df.to_csv(TEMP_FILE_PATH, index=False, encoding='utf-8-sig')
        print(f"Data saved to temporary file: {TEMP_FILE_PATH}")
        
        # 3. Validate temporary file
        validate(TEMP_FILE_PATH)
        
        # 4. If validation passes, swap files
        if os.path.exists(TARGET_FILE_PATH):
            os.remove(TARGET_FILE_PATH)
        os.rename(TEMP_FILE_PATH, TARGET_FILE_PATH)
        print(f"[통과] {TARGET_FILE_PATH} created successfully.")
        
        # Print summary
        final_df = pd.read_csv(TARGET_FILE_PATH, encoding='utf-8-sig')
        print(f"Total Rows: {len(final_df)}")
        print(f"Date Range: {final_df['date'].min()} to {final_df['date'].max()}")
        print("\nFirst 5 Rows:")
        print(final_df.head(5))
        
    except Exception as e:
        print(f"[오류] Collection failed: {e}", file=sys.stderr)
        # Clean up temp file if exists
        if os.path.exists(TEMP_FILE_PATH):
            try:
                os.remove(TEMP_FILE_PATH)
            except Exception:
                pass
        sys.exit(1)

if __name__ == '__main__':
    main()
