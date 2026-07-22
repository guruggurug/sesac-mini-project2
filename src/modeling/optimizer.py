"""
Portfolio Weight Grid-Search Optimization Engine Module for Data B.
Implements 20%-80% weight constraint 1% grid search, dynamic ESG scoring, and multi-factor objective function.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import yaml
import os

from src.modeling.price import validate_price_data, calculate_daily_returns
from src.modeling.downside import calculate_cvar, calculate_company_downside_risks, filter_price_period
from src.modeling.esg import calculate_esg_risk, load_yaml_config, get_reviewed_sources

TICKER_SAMSUNG = "005930"
TICKER_SK = "000660"

# Fallback defaults in case config files are missing
DEFAULT_RISK_PRIORITY_WEIGHTS = {
    "loss_minimization": {"alpha": 0.72, "beta": 0.18, "gamma": 0.10},
    "balanced": {"alpha": 0.63, "beta": 0.27, "gamma": 0.10},
    "esg_focused": {"alpha": 0.45, "beta": 0.45, "gamma": 0.10},
    "conservative": {"alpha": 0.72, "beta": 0.18, "gamma": 0.10},
}


def load_risk_profile_weights() -> dict:
    """Load risk profile weights from configuration file or return default."""
    config_path = Path("config/risk_profile_weights.yaml")
    if not config_path.exists():
        config_path = Path(__file__).resolve().parent.parent.parent / "config" / "risk_profile_weights.yaml"
    
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or DEFAULT_RISK_PRIORITY_WEIGHTS
        except Exception:
            return DEFAULT_RISK_PRIORITY_WEIGHTS
    return DEFAULT_RISK_PRIORITY_WEIGHTS


def load_esg_scores(
    esg_input: Optional[Union[str, Path, pd.DataFrame, Dict[str, float]]] = None
) -> Dict[str, float]:
    """
    Interface to read ESG risk scores for Samsung and SK Hynix.
    Returns normalized ESG risk scores in [0, 1] range.
    """
    default_esg = {
        TICKER_SAMSUNG: 0.42,
        TICKER_SK: 0.55,
    }

    if esg_input is None:
        return default_esg

    if isinstance(esg_input, dict):
        return {
            TICKER_SAMSUNG: float(esg_input.get(TICKER_SAMSUNG, default_esg[TICKER_SAMSUNG])),
            TICKER_SK: float(esg_input.get(TICKER_SK, default_esg[TICKER_SK])),
        }

    df_esg = pd.DataFrame()
    if isinstance(esg_input, (str, Path)):
        if os.path.exists(esg_input):
            df_esg = pd.read_csv(esg_input)
    elif isinstance(esg_input, pd.DataFrame):
        df_esg = esg_input

    if not df_esg.empty:
        try:
            config_dir = Path("config")
            if not config_dir.exists():
                config_dir = Path(__file__).resolve().parent.parent.parent / "config"
            data_dir = Path("data/reviewed")
            if not data_dir.exists():
                data_dir = Path(__file__).resolve().parent.parent.parent / "data" / "reviewed"

            scoring_rules = load_yaml_config(config_dir / "esg_scoring_rules.yaml")
            materiality_weights = load_yaml_config(config_dir / "materiality_weights.yaml")
            event_rules = load_yaml_config(config_dir / "event_penalty_rules.yaml")
            reviewed_sources = get_reviewed_sources(data_dir / "sources.csv")
            
            events_path = data_dir / "events.csv"
            events_df = pd.read_csv(events_path) if events_path.exists() else pd.DataFrame()
            
            esg_results = calculate_esg_risk(
                indicators_df=df_esg,
                events_df=events_df,
                scoring_rules=scoring_rules,
                materiality_weights=materiality_weights,
                event_rules=event_rules,
                reviewed_sources=reviewed_sources
            )
            return {
                TICKER_SAMSUNG: esg_results[TICKER_SAMSUNG]["esg_risk_score"],
                TICKER_SK: esg_results[TICKER_SK]["esg_risk_score"]
            }
        except Exception:
            return default_esg
            
    return default_esg


def resolve_risk_profile(
    risk_priority: str = "balanced",
    alpha: Optional[float] = None,
    beta: Optional[float] = None,
    gamma: Optional[float] = None,
    custom_alpha: Optional[float] = None,
    custom_beta: Optional[float] = None,
    custom_gamma: Optional[float] = None
) -> Dict[str, float]:
    """
    Resolve and validate objective function weights (alpha, beta, gamma).
    """
    if alpha is None and custom_alpha is not None:
        alpha = custom_alpha
    if beta is None and custom_beta is not None:
        beta = custom_beta
    if gamma is None and custom_gamma is not None:
        gamma = custom_gamma

    if alpha is not None and beta is not None and gamma is not None:
        if alpha < 0 or beta < 0 or gamma < 0:
            raise ValueError("목적함수 가중치(alpha, beta, gamma)는 모두 0 이상이어야 합니다.")
        total_w = alpha + beta + gamma
        if abs(total_w - 1.0) > 1e-4:
            raise ValueError(f"목적함수 가중치의 합은 1.0이어야 합니다 (현재 합계: {round(total_w, 4)}).")
        return {"alpha": float(alpha), "beta": float(beta), "gamma": float(gamma)}

    profile_weights = load_risk_profile_weights()
    
    if risk_priority not in profile_weights:
        raise ValueError(
            f"유효하지 않은 risk_priority입니다: '{risk_priority}'. "
            "('loss_minimization', 'balanced', 'esg_focused' 중 선택)"
        )

    return profile_weights[risk_priority]


def classify_risk_level(total_risk: float) -> str:
    """Classify total risk into low / medium / high label."""
    if total_risk < 0.40:
        return "low"
    elif total_risk < 0.50:
        return "medium"
    else:
        return "high"


def generate_korean_explanations(
    current_weights: Dict[str, float],
    recommended_weights: Dict[str, float],
    company_risks: Dict[str, Any],
    risk_priority: str
) -> List[str]:
    """Generate 1-3 Korean rule-based explanation sentences for recommended portfolio weights."""
    explanations = []

    sam_diff = recommended_weights[TICKER_SAMSUNG] - current_weights[TICKER_SAMSUNG]

    if abs(sam_diff) < 0.02:
        explanations.append("현재 보유 비중이 종합 위험 관점에서 최적 수준에 근접해 유지 전략을 추천합니다.")
    elif sam_diff > 0:
        explanations.append(
            f"삼성전자의 가격 하방위험과 ESG 위험도가 상대적으로 우수하여 보유 비중을 {round(current_weights[TICKER_SAMSUNG]*100, 1)}%에서 {round(recommended_weights[TICKER_SAMSUNG]*100, 1)}%로 상향 조정을 추천합니다."
        )
    else:
        explanations.append(
            f"SK하이닉스의 하방위험 대비 삼성전자 비중 과다를 조정하여, 삼성전자 추천 비중을 {round(recommended_weights[TICKER_SAMSUNG]*100, 1)}%로 비중 조정을 추천합니다."
        )

    if risk_priority in ["loss_minimization", "conservative"]:
        explanations.append("손실 최소화 기조에 따라 과거 가격 하방위험(CVaR 95%)을 최우선으로 반영했습니다.")
    elif risk_priority == "esg_focused":
        explanations.append("ESG 중시 기조에 따라 기업의 ESG 관리위험도 점수에 높은 가중치를 부여했습니다.")
    else:
        explanations.append("가격 하방위험과 ESG 관리위험을 균형 있게 고려하여 포트폴리오 위험을 최적화했습니다.")

    explanations.append("과도한 매매 비용 및 리밸런싱 부담을 줄이기 위해 턴오버 페널티를 안정적으로 반영했습니다.")

    return explanations[:3]


def optimize_portfolio(
    holdings: List[Dict[str, Any]],
    price_data: Union[str, Path, pd.DataFrame],
    esg_input: Optional[Union[str, Path, pd.DataFrame, Dict[str, float]]] = None,
    risk_priority: str = "balanced",
    current_prices: Optional[Dict[str, float]] = None,
    custom_alpha: Optional[float] = None,
    custom_beta: Optional[float] = None,
    custom_gamma: Optional[float] = None,
    data_mode: str = "sample",
    min_weight: float = 0.20,
    max_weight: float = 0.80,
    grid_step: float = 0.01,
    cvar_confidence: float = 0.95,
    # Compatibility arguments for backend
    turnover_weight: Optional[float] = None,
    downside_weight: Optional[float] = None,
    esg_weight: Optional[float] = None,
    knowledge_stage: Optional[str] = None,
    price_period_years: int = 3,
    **kwargs
) -> Dict[str, Any]:
    """
    Run 1% grid search portfolio optimization over 20%-80% weight bounds.
    """
    # Map compatibility parameters if custom ones are None
    if custom_alpha is None and downside_weight is not None:
        custom_alpha = downside_weight
    if custom_beta is None and esg_weight is not None:
        custom_beta = esg_weight
    if custom_gamma is None and turnover_weight is not None:
        custom_gamma = turnover_weight

    # 1. Resolve risk profile weights
    policy = resolve_risk_profile(risk_priority, alpha=custom_alpha, beta=custom_beta, gamma=custom_gamma)
    alpha, beta, gamma = policy["alpha"], policy["beta"], policy["gamma"]

    # 2. Validate price data & calculate daily returns
    prices_df = validate_price_data(price_data)
    returns_df = calculate_daily_returns(prices_df)

    # 3. Filter price and returns to specified period
    prices_df = filter_price_period(prices_df, years=price_period_years)
    returns_df = returns_df.loc[returns_df.index.intersection(prices_df.index)]

    if len(prices_df) < 2:
        raise ValueError("선택한 기간 동안의 거래일 데이터가 부족하여 최적화를 수행할 수 없습니다.")

    # 4. Parse current weights using CURRENT_PRICE (Market Value = quantity * current_price)
    current_val = {TICKER_SAMSUNG: 0.0, TICKER_SK: 0.0}
    has_holdings_count = 0

    for item in holdings:
        ticker = str(item.get("ticker", item.get("company_id", ""))).zfill(6)
        if ticker not in [TICKER_SAMSUNG, TICKER_SK]:
            continue

        qty = float(item.get("quantity", 0.0))
        if qty < 0:
            raise ValueError("보유 수량은 0 이상이어야 합니다.")
        if qty > 0:
            has_holdings_count += 1
        
        # Priority: current_price -> current_prices param -> latest price from prices_df -> average_price
        cur_px = item.get("current_price")
        if cur_px is None and current_prices and ticker in current_prices:
            cur_px = current_prices[ticker]
        if cur_px is None and ticker in prices_df.columns:
            cur_px = prices_df[ticker].iloc[-1]
        if cur_px is None:
            cur_px = item.get("average_price", 0.0)

        current_val[ticker] = qty * float(cur_px)

    if has_holdings_count == 0 and len(holdings) > 0:
        # Both holdings are 0 shares -> raise error
        raise ValueError("보유 주식이 없습니다. 수량을 최소 1주 이상 입력해야 합니다.")

    total_current_val = sum(current_val.values())

    if total_current_val <= 0:
        raise ValueError("보유 주식 수량 및 현재가 기반 총 평가금액이 0 이하입니다.")

    curr_w_sam = current_val[TICKER_SAMSUNG] / total_current_val
    curr_w_sk = current_val[TICKER_SK] / total_current_val

    current_weights = {
        TICKER_SAMSUNG: round(curr_w_sam, 4),
        TICKER_SK: round(curr_w_sk, 4),
    }

    # 5. Load dynamic ESG scores or fallback
    esg_scores = {}
    esg_metadata = {}
    
    # Locate configuration paths
    config_dir = Path("config")
    if not config_dir.exists():
        config_dir = Path(__file__).resolve().parent.parent.parent / "config"
    
    data_dir = Path("data/reviewed")
    if not data_dir.exists():
        data_dir = Path(__file__).resolve().parent.parent.parent / "data" / "reviewed"

    if isinstance(esg_input, pd.DataFrame) and not esg_input.empty:
        # Dynamic calculation
        try:
            scoring_rules = load_yaml_config(config_dir / "esg_scoring_rules.yaml")
            materiality_weights = load_yaml_config(config_dir / "materiality_weights.yaml")
            event_rules = load_yaml_config(config_dir / "event_penalty_rules.yaml")
            reviewed_sources = get_reviewed_sources(data_dir / "sources.csv")
            
            # Find default events file
            events_path = data_dir / "events.csv"
            events_df = pd.read_csv(events_path) if events_path.exists() else pd.DataFrame()
            
            esg_results = calculate_esg_risk(
                indicators_df=esg_input,
                events_df=events_df,
                scoring_rules=scoring_rules,
                materiality_weights=materiality_weights,
                event_rules=event_rules,
                reviewed_sources=reviewed_sources
            )
            
            for ticker in [TICKER_SAMSUNG, TICKER_SK]:
                esg_scores[ticker] = esg_results[ticker]["esg_risk_score"]
                esg_metadata[ticker] = esg_results[ticker]
        except Exception as e:
            if data_mode == "reviewed":
                raise ValueError(f"ESG 실제 데이터 계산 중 치명적인 오류가 발생했습니다: {str(e)}")
            # Fallback for sample mode
            esg_scores = {TICKER_SAMSUNG: 0.42, TICKER_SK: 0.55}
    elif isinstance(esg_input, dict):
        esg_scores = {
            TICKER_SAMSUNG: float(esg_input.get(TICKER_SAMSUNG, 0.42)),
            TICKER_SK: float(esg_input.get(TICKER_SK, 0.55)),
        }
    else:
        # Reviewed mode should not quietly use sample values
        if data_mode == "reviewed":
            raise ValueError("검증 완료 모드에서 실제 ESG 데이터입력이 제공되지 않았습니다.")
        esg_scores = {TICKER_SAMSUNG: 0.42, TICKER_SK: 0.55}

    # 6. Company individual downside risks
    comp_downside = calculate_company_downside_risks(
        returns_df, prices_df, cvar_confidence=cvar_confidence, years=price_period_years
    )

    # 7. Grid Search over Samsung weight range [min_weight, max_weight]
    weights_grid = np.arange(min_weight, max_weight + (grid_step / 2.0), grid_step)
    weights_grid = np.round(weights_grid, 4)

    raw_cvars = []
    candidate_records = []

    for w_sam in weights_grid:
        w_sk = round(1.0 - w_sam, 4)
        port_returns = w_sam * returns_df[TICKER_SAMSUNG] + w_sk * returns_df[TICKER_SK]
        cvar_val = calculate_cvar(port_returns, confidence_level=cvar_confidence)
        raw_cvars.append(cvar_val)
        candidate_records.append((w_sam, w_sk, cvar_val))

    max_cvar = max(raw_cvars) if max(raw_cvars) > 0 else 1.0

    best_candidate = None
    min_total_risk = float("inf")
    all_grid_results = []

    # Evaluate grid candidates
    for w_sam, w_sk, cvar_val in candidate_records:
        norm_cvar = cvar_val / max_cvar
        esg_risk = w_sam * esg_scores[TICKER_SAMSUNG] + w_sk * esg_scores[TICKER_SK]
        turnover = abs(w_sam - curr_w_sam) + abs(w_sk - curr_w_sk)

        total_risk = alpha * norm_cvar + beta * esg_risk + gamma * turnover
        
        all_grid_results.append({
            "w_samsung": w_sam,
            "w_skhynix": w_sk,
            "raw_cvar": round(cvar_val, 4),
            "normalized_cvar": round(norm_cvar, 4),
            "portfolio_esg_risk": round(esg_risk, 4),
            "turnover": round(turnover, 4),
            "total_objective": round(total_risk, 4)
        })

        if total_risk < min_total_risk:
            min_total_risk = total_risk
            best_candidate = {
                "w_sam": round(float(w_sam), 4),
                "w_sk": round(float(w_sk), 4),
                "total_risk": round(float(total_risk), 4),
            }

    # Save grid results to CSV for validation
    os.makedirs("data/processed", exist_ok=True)
    pd.DataFrame(all_grid_results).to_csv("data/processed/optimization_grid_results.csv", index=False)

    # 8. Equal-objective tie-breaking and Near-optimal range
    # Find candidates with total_risk close to min_total_risk (tolerance of 0.005)
    tolerance = 0.005
    near_opts = [
        r for r in all_grid_results if r["total_objective"] <= min_total_risk + tolerance
    ]
    
    # Tie-breaking: choose the one closest to current Samsung weight
    best_near_opt = min(near_opts, key=lambda x: abs(x["w_samsung"] - curr_w_sam))
    
    recommended_weights = {
        TICKER_SAMSUNG: best_near_opt["w_samsung"],
        TICKER_SK: best_near_opt["w_skhynix"],
    }
    optimized_total_risk = best_near_opt["total_objective"]

    samsung_min = min(r["w_samsung"] for r in near_opts)
    samsung_max = max(r["w_samsung"] for r in near_opts)

    # 9. Calculate EXACT current portfolio total risk (turnover = 0 for current weight)
    curr_port_returns = curr_w_sam * returns_df[TICKER_SAMSUNG] + curr_w_sk * returns_df[TICKER_SK]
    curr_cvar = calculate_cvar(curr_port_returns, confidence_level=cvar_confidence)
    curr_norm_cvar = curr_cvar / max_cvar
    curr_esg_risk = curr_w_sam * esg_scores[TICKER_SAMSUNG] + curr_w_sk * esg_scores[TICKER_SK]
    current_total_risk = round(alpha * curr_norm_cvar + beta * curr_esg_risk, 4)

    risk_reduction_rate = round(
        (current_total_risk - optimized_total_risk) / current_total_risk, 4
    ) if current_total_risk > 0 else 0.0

    # 10. Compute Recommendation Confidence
    # Combine completeness and mismatch indicators
    if esg_metadata:
        avg_completeness = np.mean([esg_metadata[t]["data_completeness"] for t in esg_metadata])
        any_scope_mismatch = any([esg_metadata[t]["scope_mismatch"] for t in esg_metadata])
        
        if avg_completeness >= 0.83 and not any_scope_mismatch:
            recommendation_confidence = "high"
        elif avg_completeness >= 0.58:
            recommendation_confidence = "medium"
        else:
            recommendation_confidence = "low"
    else:
        recommendation_confidence = "medium" if data_mode != "sample" else "low"

    # Company risk objects
    company_risks = {}
    for ticker in [TICKER_SAMSUNG, TICKER_SK]:
        esg_score = esg_scores[ticker]
        cvar_val = comp_downside[ticker]["cvar"]
        norm_cvar = cvar_val / max_cvar
        ticker_risk = round(alpha * norm_cvar + beta * esg_score, 4)
        
        company_risks[ticker] = {
            "esg_risk": round(esg_score, 4),
            "downside_risk": cvar_val,
            "total_risk": ticker_risk,
            "risk_level": classify_risk_level(ticker_risk),
            "data_confidence": esg_metadata.get(ticker, {}).get("data_confidence", "medium" if data_mode != "sample" else "low"),
            "data_completeness": esg_metadata.get(ticker, {}).get("data_completeness", 1.0),
            "scope_mismatch": esg_metadata.get(ticker, {}).get("scope_mismatch", False)
        }

    explanations = generate_korean_explanations(
        current_weights, recommended_weights, company_risks, risk_priority
    )

    warnings = [
        "이 결과는 미래 주가나 기대수익률 예측이 아닙니다.",
        "삼성전자와 SK하이닉스 모두 반도체 산업에 속하므로 산업 집중위험이 유지됩니다.",
    ]
    if data_mode == "sample":
        warnings.append("현재 샘플 데이터를 사용하여 최적화를 수행했습니다.")
    
    any_mismatch = any(company_risks[t]["scope_mismatch"] for t in company_risks)
    if any_mismatch:
        warnings.append("지속가능보고서 공시 범위 불일치(Scope Mismatch) 위험 지표가 포함되어 있습니다.")

    date_strings = [str(d)[:10] for d in prices_df.index]

    return {
        "current_weights": current_weights,
        "recommended_weights": recommended_weights,
        "current_total_risk": current_total_risk,
        "optimized_total_risk": optimized_total_risk,
        "risk_reduction_rate": risk_reduction_rate,
        "current_cvar": round(curr_cvar, 4),
        "optimized_cvar": round(best_near_opt["raw_cvar"], 4),
        "current_esg_risk": round(curr_esg_risk, 4),
        "optimized_esg_risk": round(best_near_opt["portfolio_esg_risk"], 4),
        "turnover": round(best_near_opt["turnover"], 4),
        "company_risks": company_risks,
        "recommendation_confidence": recommendation_confidence,
        "near_optimal_range": {
            "samsung_min": round(samsung_min, 2),
            "samsung_max": round(samsung_max, 2)
        },
        "explanation": explanations,
        "data_status": data_mode,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "warnings": warnings,
        "model_metadata": {
            "cvar_confidence_level": cvar_confidence,
            "minimum_weight": min_weight,
            "maximum_weight": max_weight,
            "grid_step": grid_step,
            "risk_priority": risk_priority,
            "price_period_start": date_strings[0],
            "price_period_end": date_strings[-1],
        },
    }
