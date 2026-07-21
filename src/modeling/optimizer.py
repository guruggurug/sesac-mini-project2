"""
Portfolio Weight Grid-Search Optimization Engine Module for Data B.
Implements 20%-80% weight constraint 1% grid search and multi-factor objective function.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from src.modeling.price import validate_price_data, calculate_daily_returns
from src.modeling.downside import calculate_cvar, calculate_company_downside_risks

TICKER_SAMSUNG = "005930"
TICKER_SK = "000660"

# Policy weights for risk priority (alpha: CVaR, beta: ESG, gamma: Turnover)
RISK_PRIORITY_WEIGHTS = {
    "conservative": {"alpha": 0.72, "beta": 0.18, "gamma": 0.10},
    "balanced": {"alpha": 0.63, "beta": 0.27, "gamma": 0.10},
    "esg_focused": {"alpha": 0.45, "beta": 0.45, "gamma": 0.10},
}


def load_esg_scores(
    esg_input: Optional[Union[str, Path, pd.DataFrame, Dict[str, float]]] = None
) -> Dict[str, float]:
    """
    Interface to read ESG risk scores for Samsung and SK Hynix.
    Returns normalized ESG risk scores in [0, 1] range (higher = higher risk).
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

    if isinstance(esg_input, (str, Path)):
        path = Path(esg_input)
        if not path.exists():
            return default_esg
        df = pd.read_csv(path)
    elif isinstance(esg_input, pd.DataFrame):
        df = esg_input.copy()
    else:
        return default_esg

    scores = {}
    ticker_col = "ticker" if "ticker" in df.columns else ("company_id" if "company_id" in df.columns else None)
    score_col = "esg_risk_score" if "esg_risk_score" in df.columns else ("score" if "score" in df.columns else None)

    if ticker_col and score_col:
        df[ticker_col] = df[ticker_col].astype(str).str.zfill(6)
        for ticker in [TICKER_SAMSUNG, TICKER_SK]:
            matched = df[df[ticker_col] == ticker]
            if not matched.empty:
                val = float(matched[score_col].iloc[0])
                scores[ticker] = val

    return {
        TICKER_SAMSUNG: scores.get(TICKER_SAMSUNG, default_esg[TICKER_SAMSUNG]),
        TICKER_SK: scores.get(TICKER_SK, default_esg[TICKER_SK]),
    }


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

    if risk_priority == "conservative":
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
    data_mode: str = "sample",
    min_weight: float = 0.20,
    max_weight: float = 0.80,
    grid_step: float = 0.01,
    cvar_confidence: float = 0.95
) -> Dict[str, Any]:
    """
    Run 1% grid search portfolio optimization over 20%-80% weight bounds.

    Args:
        holdings: Current holdings list e.g. [{'ticker': '005930', 'quantity': 70, 'average_price': 70000}, ...]
        price_data: Stock price CSV path or DataFrame
        esg_input: ESG risk scores input
        risk_priority: 'conservative', 'balanced', or 'esg_focused'
        data_mode: 'sample', 'reviewed', or 'fallback'
        min_weight: Minimum weight constraint (default 0.20)
        max_weight: Maximum weight constraint (default 0.80)
        grid_step: Grid step increment (default 0.01)
        cvar_confidence: Historical CVaR confidence level (default 0.95)

    Returns:
        Dict[str, Any]: Optimization result dictionary matching portfolio-optimize-response.schema.json
    """
    if risk_priority not in RISK_PRIORITY_WEIGHTS:
        raise ValueError(f"유효하지 않은 risk_priority입니다: {risk_priority}. ('conservative', 'balanced', 'esg_focused' 중 선택)")

    # 1. Parse current weights from holdings
    current_val = {}
    for item in holdings:
        ticker = str(item["ticker"]).zfill(6)
        qty = float(item.get("quantity", 0))
        avg_px = float(item.get("average_price", 0))
        current_val[ticker] = qty * avg_px

    total_current_val = sum(current_val.values())
    if total_current_val <= 0:
        raise ValueError("보유 주식 수량과 평단가의 곱(총 보유 금액)이 0 이하입니다.")

    curr_w_sam = current_val.get(TICKER_SAMSUNG, 0.0) / total_current_val
    curr_w_sk = current_val.get(TICKER_SK, 0.0) / total_current_val

    current_weights = {
        TICKER_SAMSUNG: round(curr_w_sam, 4),
        TICKER_SK: round(curr_w_sk, 4),
    }

    # 2. Validate price data & calculate daily returns
    prices_df = validate_price_data(price_data)
    returns_df = calculate_daily_returns(prices_df)

    # 3. Load ESG scores
    esg_scores = load_esg_scores(esg_input)

    # 4. Company individual downside risks
    comp_downside = calculate_company_downside_risks(returns_df, prices_df, cvar_confidence=cvar_confidence)

    # 5. Grid Search over Samsung weight range [min_weight, max_weight]
    weights_grid = np.arange(min_weight, max_weight + (grid_step / 2.0), grid_step)
    
    weights_grid = np.round(weights_grid, 4)

    policy = RISK_PRIORITY_WEIGHTS[risk_priority]
    alpha, beta, gamma = policy["alpha"], policy["beta"], policy["gamma"]

    # Pre-calculate candidate portfolio return series and raw CVaR for normalization
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
    current_total_risk = 0.0

    # Grid search evaluation
    for w_sam, w_sk, cvar_val in candidate_records:
        norm_cvar = cvar_val / max_cvar
        esg_risk = w_sam * esg_scores[TICKER_SAMSUNG] + w_sk * esg_scores[TICKER_SK]
        turnover = abs(w_sam - curr_w_sam) + abs(w_sk - curr_w_sk)

        total_risk = alpha * norm_cvar + beta * esg_risk + gamma * turnover

        # Track current portfolio total risk
        if abs(w_sam - round(curr_w_sam, 2)) < 0.005 and current_total_risk == 0.0:
            current_total_risk = round(total_risk, 4)

        if total_risk < min_total_risk:
            min_total_risk = total_risk
            best_candidate = {
                "w_sam": round(float(w_sam), 4),
                "w_sk": round(float(w_sk), 4),
                "total_risk": round(float(total_risk), 4),
            }

    if current_total_risk == 0.0:
        # Fallback evaluation for current weight if exact grid match wasn't set
        curr_cvar = calculate_cvar(
            curr_w_sam * returns_df[TICKER_SAMSUNG] + curr_w_sk * returns_df[TICKER_SK],
            confidence_level=cvar_confidence
        )
        curr_norm_cvar = curr_cvar / max_cvar
        curr_esg_risk = curr_w_sam * esg_scores[TICKER_SAMSUNG] + curr_w_sk * esg_scores[TICKER_SK]
        current_total_risk = round(alpha * curr_norm_cvar + beta * curr_esg_risk, 4)

    recommended_weights = {
        TICKER_SAMSUNG: best_candidate["w_sam"],
        TICKER_SK: best_candidate["w_sk"],
    }
    optimized_total_risk = best_candidate["total_risk"]

    risk_reduction_rate = round(
        (current_total_risk - optimized_total_risk) / current_total_risk, 4
    ) if current_total_risk > 0 else 0.0

    # Company risk objects
    company_risks = {
        TICKER_SAMSUNG: {
            "esg_risk": round(esg_scores[TICKER_SAMSUNG], 4),
            "downside_risk": comp_downside[TICKER_SAMSUNG]["cvar_95"],
            "total_risk": round(alpha * (comp_downside[TICKER_SAMSUNG]["cvar_95"] / max_cvar) + beta * esg_scores[TICKER_SAMSUNG], 4),
            "risk_level": classify_risk_level(alpha * (comp_downside[TICKER_SAMSUNG]["cvar_95"] / max_cvar) + beta * esg_scores[TICKER_SAMSUNG]),
            "data_confidence": "high",
        },
        TICKER_SK: {
            "esg_risk": round(esg_scores[TICKER_SK], 4),
            "downside_risk": comp_downside[TICKER_SK]["cvar_95"],
            "total_risk": round(alpha * (comp_downside[TICKER_SK]["cvar_95"] / max_cvar) + beta * esg_scores[TICKER_SK], 4),
            "risk_level": classify_risk_level(alpha * (comp_downside[TICKER_SK]["cvar_95"] / max_cvar) + beta * esg_scores[TICKER_SK]),
            "data_confidence": "medium",
        },
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

    date_strings = [str(d)[:10] for d in prices_df.index]

    return {
        "current_weights": current_weights,
        "recommended_weights": recommended_weights,
        "current_total_risk": current_total_risk,
        "optimized_total_risk": optimized_total_risk,
        "risk_reduction_rate": risk_reduction_rate,
        "company_risks": company_risks,
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
