"""
Unit tests for historical event reaction analysis module (DATA-B-04).
"""

from pathlib import Path
import pytest
import pandas as pd

from src.modeling.events import (
    find_reaction_start_date,
    analyze_single_event_reaction,
    analyze_all_events,
)

SAMPLE_PRICES_PATH = Path("data/sample/stock_prices.sample.csv")
SAMPLE_EVENTS_PATH = Path("data/sample/events.sample.csv")


def test_find_reaction_start_date():
    """Verify finding exact trading day or adjusting weekend to next trading day."""
    trading_dates = pd.DatetimeIndex(["2024-03-15", "2024-03-18", "2024-03-19", "2024-03-20"])

    # Friday exact match
    dt1 = find_reaction_start_date("2024-03-15", trading_dates)
    assert dt1 == pd.Timestamp("2024-03-15")

    # Saturday weekend adjustment -> Monday 03-18
    dt2 = find_reaction_start_date("2024-03-16", trading_dates)
    assert dt2 == pd.Timestamp("2024-03-18")

    # Sunday weekend adjustment -> Monday 03-18
    dt3 = find_reaction_start_date("2024-03-17", trading_dates)
    assert dt3 == pd.Timestamp("2024-03-18")

    # Out of range date
    dt4 = find_reaction_start_date("2025-01-01", trading_dates)
    assert dt4 is None


def test_analyze_single_event_reaction():
    """Verify single event post-event returns, max drawdown, and recovery period."""
    prices_df = pd.DataFrame({
        "005930": [100.0, 95.0, 92.0, 90.0, 97.0, 102.0, 105.0],
        "000660": [200.0, 198.0, 202.0, 205.0, 208.0, 210.0, 215.0],
    }, index=pd.date_range("2024-01-01", periods=7))

    event = {
        "event_id": "EVT-TEST",
        "company_id": "005930",
        "event_date": "2024-01-01",
        "status": "confirmed",
        "summary": "테스트 사건",
    }

    result = analyze_single_event_reaction(event, prices_df, window_days=5)

    assert result["event_id"] == "EVT-TEST"
    assert result["company_id"] == "005930"
    assert result["company_name"] == "삼성전자"
    assert result["reaction_start_date"] == "2024-01-01"

    # Day 1 return: (95 - 100) / 100 = -0.05
    assert result["return_1d"] == -0.05
    # Day 3 return: (90 - 100) / 100 = -0.10
    assert result["return_3d"] == -0.10
    # Day 5 return: (102 - 100) / 100 = 0.02
    assert result["return_5d"] == 0.02

    # Max drawdown in window: -0.10
    assert result["max_drawdown"] == -0.10

    # Recovery day: Day 5 (price becomes 102 >= 100)
    assert result["recovery_days"] == 5

    # Chart data list
    assert len(result["chart_data"]) == 6
    assert result["chart_data"][0]["day"] == 0
    assert result["chart_data"][0]["cumulative_return"] == 0.0


def test_analyze_all_events_sample():
    """Integration test for analyze_all_events with sample files."""
    assert SAMPLE_PRICES_PATH.exists()
    assert SAMPLE_EVENTS_PATH.exists()

    results = analyze_all_events(SAMPLE_EVENTS_PATH, SAMPLE_PRICES_PATH, filter_approved_only=True)

    assert isinstance(results, list)
    assert len(results) >= 1
