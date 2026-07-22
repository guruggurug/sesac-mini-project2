"""
Dynamic ESG Risk Scoring Module for Data B.
Calculates Residual Risk, controversy penalties, uncertainty penalties, and weighted ESG scores.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Union, Optional, List
import pandas as pd
import numpy as np

# Default directories relative to workspace root
DEFAULT_WORKSPACE_DIR = Path("c:/Users/jkim1/Sesac/sesac_pjt/Investment App")
DEFAULT_CONFIG_DIR = DEFAULT_WORKSPACE_DIR / "config"
DEFAULT_DATA_DIR = DEFAULT_WORKSPACE_DIR / "data" / "reviewed"


def load_yaml_config(file_path: Path) -> dict:
    """Load a YAML configuration file safely."""
    if not file_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_reviewed_sources(sources_path: Path) -> set:
    """Load reviewed source IDs from sources.csv."""
    if not sources_path.exists():
        return set()
    try:
        df = pd.read_csv(sources_path)
        # Handle reviewed as boolean or string 'true'
        reviewed_df = df[df["reviewed"].astype(str).str.lower() == "true"]
        return set(reviewed_df["source_id"].astype(str).unique())
    except Exception:
        return set()


def calculate_esg_risk(
    indicators_df: pd.DataFrame,
    events_df: pd.DataFrame,
    scoring_rules: dict,
    materiality_weights: dict,
    event_rules: dict,
    reviewed_sources: set = None,
    reference_date: str = "2026-07-22"
) -> Dict[str, Any]:
    """
    Calculate company-level and indicator-level ESG risk scores.
    
    Args:
        indicators_df: DataFrame containing ESG indicators.
        events_df: DataFrame containing historical events.
        scoring_rules: Scoring rules dict from esg_scoring_rules.yaml.
        materiality_weights: Materiality weights dict from materiality_weights.yaml.
        event_rules: Event penalty rules dict from event_penalty_rules.yaml.
        reviewed_sources: Set of reviewed official source IDs.
        reference_date: Analysis date to compute recency decay.

    Returns:
        Dict[str, Any]: Dictionary containing ESG scores per company.
    """
    if indicators_df.empty:
        raise ValueError("ESG 지표 데이터가 비어 있습니다.")

    if reviewed_sources is None:
        reviewed_sources = set()

    ref_dt = pd.to_datetime(reference_date)
    companies = ["005930", "000660"]
    results = {}

    # Standardize data columns
    ind_df = indicators_df.copy()
    ind_df["company_id"] = ind_df["company_id"].astype(str).str.zfill(6)
    ind_df["indicator_id"] = ind_df["indicator_id"].astype(str).str.upper()

    evt_df = events_df.copy() if not events_df.empty else pd.DataFrame()
    if not evt_df.empty:
        evt_df["company_id"] = evt_df["company_id"].astype(str).str.zfill(6)
        if "linked_indicator_id" in evt_df.columns:
            evt_df["linked_indicator_id"] = evt_df["linked_indicator_id"].astype(str).str.upper()

    for company in companies:
        company_rows = ind_df[ind_df["company_id"] == company]
        if company_rows.empty:
            continue

        # Get latest records per indicator_id (normally 2024)
        latest_rows = []
        for ind_id in company_rows["indicator_id"].unique():
            ind_rows = company_rows[company_rows["indicator_id"] == ind_id]
            # Filter to approved rows first
            approved_rows = ind_rows[ind_rows["review_status"] == "approved"]
            if approved_rows.empty:
                continue
            # Pick latest period (year)
            latest_row = approved_rows.sort_values("period", ascending=False).iloc[0]
            latest_rows.append(latest_row)

        if not latest_rows:
            continue

        latest_df = pd.DataFrame(latest_rows)

        indicator_results = []
        available_material_sum = 0.0
        weighted_total_risk = 0.0

        # Group by E, S, G for categorical scores
        cat_data = {"E": [], "S": [], "G": []}

        # 12 expected indicators
        all_indicator_ids = ["E01", "E02", "E03", "E04", "E05", "S01", "S02", "S03", "S04", "G01", "G02", "G03"]

        for ind_id in all_indicator_ids:
            # Check availability
            row_match = latest_df[latest_df["indicator_id"] == ind_id]
            weight = float(materiality_weights.get(ind_id, 0.0))
            category = ind_id[0]

            if row_match.empty or row_match.iloc[0]["availability"] == "unavailable":
                # Handle unavailable indicators (Data Uncertainty Penalty applies, re-normalize weights)
                indicator_results.append({
                    "indicator_id": ind_id,
                    "indicator_name": scoring_rules.get(ind_id, {}).get("name", "지표명 미정"),
                    "category": category,
                    "availability": "unavailable",
                    "issue_risk": 0.5,  # Neutral default for missing
                    "data_uncertainty": scoring_rules.get("uncertainty_penalties", {}).get("missing_quantitative_value", 0.07),
                    "materiality_weight": weight
                })
                continue

            row = row_match.iloc[0]
            raw_val = row["raw_value"]
            risk_dir = row["risk_direction"]
            assurance = row["assurance"]
            scope_mismatch = bool(row["scope_mismatch"])
            period = str(row["period"])
            source_id = str(row["source_id"])

            # 1. Normalization
            rule = scoring_rules.get(ind_id, {})
            min_b = float(rule.get("min_bound", 0.0))
            max_b = float(rule.get("max_bound", 100.0))
            default_exp = float(rule.get("default_exposure", 0.5))

            if max_b == min_b:
                norm_val = 0.0
            else:
                norm_val = (raw_val - min_b) / (max_b - min_b)
            norm_val = max(0.0, min(1.0, norm_val))

            if risk_dir == "higher_is_better":
                norm_risk = 1.0 - norm_val
            else:
                norm_risk = norm_val

            # 2. Trend & Management bonus
            # Trend: find early periods for same company & indicator
            hist_rows = company_rows[(company_rows["indicator_id"] == ind_id) & (company_rows["review_status"] == "approved")]
            trend_bonus = 0.0
            if len(hist_rows) >= 2:
                sorted_hist = hist_rows.sort_values("period")
                val_earliest = sorted_hist.iloc[0]["raw_value"]
                val_latest = sorted_hist.iloc[-1]["raw_value"]

                if risk_dir == "higher_is_worse" and val_latest < val_earliest:
                    trend_bonus = 0.1
                elif risk_dir == "higher_is_better" and val_latest > val_earliest:
                    trend_bonus = 0.1

            assurance_bonus = 0.0
            if assurance == "third_party_assured":
                assurance_bonus = 0.1
            elif assurance == "internally_verified":
                assurance_bonus = 0.05

            base_management = 1.0 - norm_risk
            management = max(0.0, min(1.0, base_management + trend_bonus + assurance_bonus))

            # 3. Residual Risk
            residual_risk = default_exp * (1.0 - management)

            # 4. Controversy Penalty from events linked to this indicator
            controversy_penalty = 0.0
            if not evt_df.empty:
                company_events = evt_df[
                    (evt_df["company_id"] == company) & 
                    (evt_df["linked_indicator_id"] == ind_id)
                ]
                if "review_status" in company_events.columns:
                    company_events = company_events[company_events["review_status"] == "approved"]
                
                for _, evt in company_events.iterrows():
                    status = str(evt.get("status", "confirmed"))
                    severity = int(evt.get("severity", 3))
                    confidence = str(evt.get("evidence_confidence", "high"))
                    
                    # Look up multipliers
                    sev_mult = float(event_rules.get("severity_multipliers", {}).get(severity, 0.12))
                    stat_mult = float(event_rules.get("status_multipliers", {}).get(status, 1.0))
                    conf_mult = float(event_rules.get("evidence_confidence_multipliers", {}).get(confidence, 1.0))
                    
                    # Calculate recency decay
                    evt_date_str = str(evt.get("market_event_date", evt.get("event_date", reference_date)))
                    try:
                        evt_dt = pd.to_datetime(evt_date_str)
                        days_elapsed = (ref_dt - evt_dt).days
                    except Exception:
                        days_elapsed = 0
                        
                    if days_elapsed <= 365:
                        decay = float(event_rules.get("recency_decay", {}).get("within_365_days", 1.0))
                    elif days_elapsed <= 730:
                        decay = float(event_rules.get("recency_decay", {}).get("within_730_days", 0.5))
                    else:
                        decay = float(event_rules.get("recency_decay", {}).get("older_than_730_days", 0.2))
                        
                    penalty = sev_mult * stat_mult * conf_mult * decay
                    controversy_penalty += penalty
            
            # Cap controversy penalty at 0.5 per indicator
            controversy_penalty = min(0.5, controversy_penalty)

            # 5. Data Uncertainty Penalty
            uncertainty = 0.0
            rules_unc = scoring_rules.get("uncertainty_penalties", {})
            if scope_mismatch:
                uncertainty += float(rules_unc.get("scope_mismatch", 0.08))
            if assurance in ["not_assured", "unknown"]:
                uncertainty += float(rules_unc.get("no_assurance", 0.03))
            if source_id not in reviewed_sources and not source_id.startswith("SRC-"):
                uncertainty += float(rules_unc.get("non_official_source", 0.05))
                
            try:
                period_year = int(period[:4])
                ref_year = int(reference_date[:4])
                diff_year = ref_year - period_year
                if diff_year == 1:
                    uncertainty += float(rules_unc.get("period_mismatch_1y", 0.03))
                elif diff_year >= 2:
                    uncertainty += float(rules_unc.get("period_mismatch_2y", 0.05))
            except Exception:
                pass

            # 6. Issue Risk
            issue_risk = max(0.0, min(1.0, residual_risk + controversy_penalty + uncertainty))

            # Store results
            indicator_results.append({
                "indicator_id": ind_id,
                "indicator_name": row["indicator_name"],
                "category": category,
                "availability": "available",
                "exposure": round(default_exp, 4),
                "management": round(management, 4),
                "residual_risk": round(residual_risk, 4),
                "controversy_penalty": round(controversy_penalty, 4),
                "data_uncertainty": round(uncertainty, 4),
                "issue_risk": round(issue_risk, 4),
                "materiality_weight": weight
            })

            available_material_sum += weight
            weighted_total_risk += weight * issue_risk
            cat_data[category].append((weight, issue_risk))

        # Renormalize overall score
        if available_material_sum > 0:
            esg_risk_score = round(weighted_total_risk / available_material_sum, 4)
        else:
            esg_risk_score = 0.5

        # Categorical scores (renormalized per category)
        cat_scores = {}
        for cat, list_vals in cat_data.items():
            cat_w_sum = sum(w for w, _ in list_vals)
            cat_risk_sum = sum(w * r for w, r in list_vals)
            if cat_w_sum > 0:
                cat_scores[cat] = round(cat_risk_sum / cat_w_sum, 4)
            else:
                cat_scores[cat] = 0.5

        # Compute data confidence & completeness
        avail_count = sum(1 for item in indicator_results if item["availability"] == "available")
        data_completeness = round(avail_count / len(all_indicator_ids), 4)

        has_scope_mismatch = any(
            item.get("indicator_id") in latest_df["indicator_id"].values and
            bool(latest_df[latest_df["indicator_id"] == item["indicator_id"]].iloc[0]["scope_mismatch"])
            for item in indicator_results if item["availability"] == "available"
        )

        if data_completeness >= 0.83 and not has_scope_mismatch:
            data_confidence = "high"
        elif data_completeness >= 0.58:
            data_confidence = "medium"
        else:
            data_confidence = "low"

        results[company] = {
            "company_id": company,
            "esg_risk_score": esg_risk_score,
            "environment_risk": cat_scores["E"],
            "social_risk": cat_scores["S"],
            "governance_risk": cat_scores["G"],
            "data_confidence": data_confidence,
            "data_completeness": data_completeness,
            "scope_mismatch": has_scope_mismatch,
            "indicator_results": indicator_results
        }

    return results


def run_esg_scoring_pipeline(
    indicators_path: Union[str, Path] = None,
    events_path: Union[str, Path] = None,
    sources_path: Union[str, Path] = None,
    config_dir: Union[str, Path] = None,
    reference_date: str = "2026-07-22"
) -> Dict[str, Any]:
    """Helper to run the ESG scoring pipeline from file paths."""
    # Resolve default paths
    ind_path = Path(indicators_path or DEFAULT_DATA_DIR / "esg_indicators.csv")
    evt_path = Path(events_path or DEFAULT_DATA_DIR / "events.csv")
    src_path = Path(sources_path or DEFAULT_DATA_DIR / "sources.csv")
    cfg_dir = Path(config_dir or DEFAULT_CONFIG_DIR)

    # Load YAML configs
    scoring_rules = load_yaml_config(cfg_dir / "esg_scoring_rules.yaml")
    materiality_weights = load_yaml_config(cfg_dir / "materiality_weights.yaml")
    event_rules = load_yaml_config(cfg_dir / "event_penalty_rules.yaml")

    # Load CSV data
    if not ind_path.exists():
        raise FileNotFoundError(f"ESG indicators CSV가 존재하지 않습니다: {ind_path}")
    
    indicators_df = pd.read_csv(ind_path)
    
    events_df = pd.read_csv(evt_path) if evt_path.exists() else pd.DataFrame()
    reviewed_sources = get_reviewed_sources(src_path)

    return calculate_esg_risk(
        indicators_df=indicators_df,
        events_df=events_df,
        scoring_rules=scoring_rules,
        materiality_weights=materiality_weights,
        event_rules=event_rules,
        reviewed_sources=reviewed_sources,
        reference_date=reference_date
    )
