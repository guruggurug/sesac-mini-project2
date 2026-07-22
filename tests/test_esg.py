"""
Unit tests for dynamic ESG risk scoring module (esg.py).
"""

import pandas as pd
import pytest
from src.modeling.esg import calculate_esg_risk


@pytest.fixture
def sample_indicators():
    return pd.DataFrame([
        # Samsung E01 greenhouse gas (higher_is_worse)
        {"company_id": "005930", "company_name": "삼성전자", "indicator_id": "E01", "category": "E", 
         "indicator_name": "온실가스", "raw_value": 15.0, "raw_unit": "tCO2e", "period": "2026", 
         "business_scope": "DS", "geography": "Korea", "source_id": "SRC-0001", "source_title": "Report", 
         "source_page": 1, "source_url": "http://x.com", "assurance": "third_party_assured", 
         "scope_mismatch": False, "availability": "available", "data_confidence": "high", 
         "risk_direction": "higher_is_worse", "review_status": "approved", "note": ""},
        # SK Hynix E01
        {"company_id": "000660", "company_name": "SK하이닉스", "indicator_id": "E01", "category": "E", 
         "indicator_name": "온실가스", "raw_value": 18.0, "raw_unit": "tCO2e", "period": "2026", 
         "business_scope": "semiconductor", "geography": "Korea", "source_id": "SRC-0004", "source_title": "Report", 
         "source_page": 1, "source_url": "http://x.com", "assurance": "not_assured", 
         "scope_mismatch": True, "availability": "available", "data_confidence": "medium", 
         "risk_direction": "higher_is_worse", "review_status": "approved", "note": ""},
        # Samsung E02 water reuse (higher_is_better)
        {"company_id": "005930", "company_name": "삼성전자", "indicator_id": "E02", "category": "E", 
         "indicator_name": "용수재이용", "raw_value": 60.0, "raw_unit": "%", "period": "2026", 
         "business_scope": "DS", "geography": "Korea", "source_id": "SRC-0001", "source_title": "Report", 
         "source_page": 1, "source_url": "http://x.com", "assurance": "third_party_assured", 
         "scope_mismatch": False, "availability": "available", "data_confidence": "high", 
         "risk_direction": "higher_is_better", "review_status": "approved", "note": ""},
        # SK Hynix E02
        {"company_id": "000660", "company_name": "SK하이닉스", "indicator_id": "E02", "category": "E", 
         "indicator_name": "용수재이용", "raw_value": 80.0, "raw_unit": "%", "period": "2026", 
         "business_scope": "semiconductor", "geography": "Korea", "source_id": "SRC-0004", "source_title": "Report", 
         "source_page": 1, "source_url": "http://x.com", "assurance": "third_party_assured", 
         "scope_mismatch": False, "availability": "available", "data_confidence": "high", 
         "risk_direction": "higher_is_better", "review_status": "approved", "note": ""},
    ])


@pytest.fixture
def sample_events():
    return pd.DataFrame([
        # Samsung workplace accident (S01)
        {"event_id": "EVT-0001", "company_id": "005930", "company_name": "삼성전자", 
         "event_category": "occupational_safety", "event_subcategory": "accident", 
         "event_date": "2024-05-27", "event_date_type": "occurrence_date", "business_unit": "DS", 
         "status": "sanctioned", "severity": 4, "authority_confirmed": True, 
         "official_source_url": "http://gov.com", "news_url": "http://news.com", "summary": "Accident", 
         "review_status": "approved", "note": "", "linked_indicator_id": "S01", 
         "evidence_confidence": "high", "resolved_date": "2024-09-26", "market_event_date": "2024-05-28", 
         "market_event_date_type": "first_public_report_date"}
    ])


@pytest.fixture
def scoring_rules():
    return {
        "E01": {"min_bound": 0.0, "max_bound": 30.0, "default_exposure": 0.8},
        "E02": {"min_bound": 0.0, "max_bound": 100.0, "default_exposure": 0.8},
        "uncertainty_penalties": {
            "scope_mismatch": 0.08,
            "no_assurance": 0.03,
            "non_official_source": 0.05,
            "missing_quantitative_value": 0.07
        }
    }


@pytest.fixture
def materiality_weights():
    # Only E01 and E02 are populated
    return {
        "E01": 0.50,
        "E02": 0.50
    }


@pytest.fixture
def event_rules():
    return {
        "severity_multipliers": {4: 0.25},
        "status_multipliers": {"sanctioned": 1.5},
        "evidence_confidence_multipliers": {"high": 1.0},
        "recency_decay": {"within_365_days": 1.0}
    }


def test_calculate_esg_risk_basic(sample_indicators, scoring_rules, materiality_weights, event_rules):
    """Verify dynamic ESG calculation with basic indicators."""
    res = calculate_esg_risk(
        indicators_df=sample_indicators,
        events_df=pd.DataFrame(),
        scoring_rules=scoring_rules,
        materiality_weights=materiality_weights,
        event_rules=event_rules,
        reference_date="2026-07-22"
    )

    assert "005930" in res
    assert "000660" in res

    sam_result = res["005930"]
    # E01 normalized value: 15.0 / 30.0 = 0.50 (higher is worse -> risk = 0.50)
    # E02 normalized value: 60.0 / 100.0 = 0.60 (higher is better -> risk = 0.40)
    # E01 Management: 1.0 - 0.50 + 0.1 (assurance bonus) = 0.60
    # E01 Residual Risk: 0.8 (exposure) * (1 - 0.60) = 0.32
    # E02 Management: 1.0 - 0.40 + 0.1 = 0.70
    # E02 Residual Risk: 0.8 * (1 - 0.70) = 0.24
    # Weighted average: 0.5 * 0.32 + 0.5 * 0.24 = 0.28 (since other indicators are missing and re-normalized)
    
    assert sam_result["esg_risk_score"] == pytest.approx(0.28, abs=0.01)
    assert sam_result["data_confidence"] == "high"


def test_calculate_esg_risk_uncertainty_penalty(sample_indicators, scoring_rules, materiality_weights, event_rules):
    """Verify that uncertainty penalties are correctly added to SK Hynix E01."""
    res = calculate_esg_risk(
        indicators_df=sample_indicators,
        events_df=pd.DataFrame(),
        scoring_rules=scoring_rules,
        materiality_weights=materiality_weights,
        event_rules=event_rules,
        reference_date="2026-07-22"
    )

    sk_result = res["000660"]
    # SK E01 has scope_mismatch = True (+0.08) and assurance = not_assured (+0.03)
    # These should be added to the E01 issue risk.
    # Check E01 results specifically
    e01_res = next(x for x in sk_result["indicator_results"] if x["indicator_id"] == "E01")
    assert e01_res["data_uncertainty"] == pytest.approx(0.11, abs=0.001)
