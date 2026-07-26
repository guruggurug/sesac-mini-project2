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
    build_similar_event_groups,
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


def test_analyze_single_event_uses_market_event_date():
    prices_df = pd.DataFrame(
        {"005930": [100.0, 110.0, 121.0]},
        index=pd.date_range("2024-01-01", periods=3),
    )
    event = {
        "event_id": "EVT-MARKET-DATE",
        "company_id": "005930",
        "event_date": "2024-01-01",
        "market_event_date": "2024-01-02",
        "status": "confirmed",
        "summary": "시장 공개일 검증",
    }

    result = analyze_single_event_reaction(event, prices_df, window_days=1)

    assert result["event_date"] == "2024-01-01"
    assert result["market_event_date"] == "2024-01-02"
    assert result["reaction_start_date"] == "2024-01-02"
    assert result["return_1d"] == 0.1


def test_analyze_all_events_sample():
    """Integration test for analyze_all_events with sample files."""
    assert SAMPLE_PRICES_PATH.exists()
    assert SAMPLE_EVENTS_PATH.exists()

    results = analyze_all_events(
        SAMPLE_EVENTS_PATH,
        SAMPLE_PRICES_PATH,
        filter_model_eligible_only=True,
    )

    assert isinstance(results, list)
    assert len(results) >= 1


def test_similar_event_groups_compare_same_esg_classification():
    events = [
        {
            "event_id": "EVT-1",
            "event_category": "occupational_safety",
            "event_subcategory": "workplace_incident",
            "linked_indicator_id": "S01",
            "event_date": "2024-01-01",
        },
        {
            "event_id": "EVT-2",
            "event_category": "occupational_safety",
            "event_subcategory": "workplace_incident",
            "linked_indicator_id": "S01",
            "event_date": "2025-01-01",
        },
        {
            "event_id": "EVT-3",
            "event_category": "cybersecurity",
            "event_subcategory": "personal_data_breach",
            "linked_indicator_id": "S04",
            "event_date": "2025-02-01",
        },
    ]
    reactions = [
        {
            "event_id": "EVT-1",
            "return_1d": -0.02,
            "return_3d": -0.04,
            "return_5d": -0.06,
            "abnormal_return_5d": -0.05,
            "event_relative_min_return": -0.08,
        },
        {
            "event_id": "EVT-2",
            "return_1d": 0.01,
            "return_3d": -0.02,
            "return_5d": -0.04,
            "abnormal_return_5d": -0.03,
            "event_relative_min_return": -0.05,
        },
    ]

    groups = build_similar_event_groups(events, reactions)
    safety = next(
        group
        for group in groups
        if group["linked_indicator_id"] == "S01"
    )

    assert safety["event_ids"] == ["EVT-1", "EVT-2"]
    assert safety["event_count"] == 2
    assert safety["analyzed_event_count"] == 2
    assert safety["average_return_5d"] == -0.05
    assert safety["worst_event_relative_return"] == -0.08
