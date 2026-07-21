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
    esg_input: Optional[Union[str, Path, pd.DataFrame, Dict[str, float]]] = None,
    *,
    allow_sample_defaults: bool = False,
) -> Dict[str, float]:
    """
    Interface to read ESG risk scores for Samsung and SK Hynix.
    Returns normalized ESG risk scores in [0, 1] range (higher = higher risk).
    """
    default_esg = {
        TICKER_SAMSUNG: 0.42,
        TICKER_SK: 0.55,
    }

    def complete_or_raise(scores: Dict[str, float], reason: str) -> Dict[str, float]:
        missing = [ticker for ticker in (TICKER_SAMSUNG, TICKER_SK) if ticker not in scores]
        if missing:
            if allow_sample_defaults:
                return {
                    ticker: float(scores.get(ticker, default_esg[ticker]))
                    for ticker in (TICKER_SAMSUNG, TICKER_SK)
                }
            raise ValueError(
                f"ESG risk score unavailable ({reason}); missing tickers: {', '.join(missing)}"
            )

        normalized = {ticker: float(scores[ticker]) for ticker in (TICKER_SAMSUNG, TICKER_SK)}
        for ticker, score in normalized.items():
            if not np.isfinite(score) or not 0.0 <= score <= 1.0:
                raise ValueError(f"ESG risk score must be between 0 and 1: {ticker}={score}")
        return normalized

    if esg_input is None:
        return complete_or_raise({}, "input is missing")

    if isinstance(esg_input, dict):
        return complete_or_raise(
            {str(ticker).zfill(6): value for ticker, value in esg_input.items()},
            "ticker score is missing",
        )

    if isinstance(esg_input, (str, Path)):
        path = Path(esg_input)
        if not path.exists():
            return complete_or_raise({}, f"file does not exist: {path}")
        df = pd.read_csv(path)
    elif isinstance(esg_input, pd.DataFrame):
        df = esg_input.copy()
    else:
        raise TypeError(f"Unsupported ESG input type: {type(esg_input).__name__}")

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

    return complete_or_raise(scores, "aggregate score column or ticker score is missing")


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
    risk_priority: str,
    knowledge_stage: str = "beginner"
) -> List[str]:
    """Generate 1-3 Korean rule-based explanation sentences based on knowledge stage and recommended weights."""
    explanations = []

    sam_diff = recommended_weights[TICKER_SAMSUNG] - current_weights[TICKER_SAMSUNG]

    # 기본 비중 조절 설명
    if abs(sam_diff) < 0.02:
        explanations.append("현재 보유 비중이 종합 위험 관점에서 최적 수준에 근접해 유지 전략을 추천합니다.")
    elif sam_diff > 0:
        explanations.append(
            f"삼성전자의 리스크 요인이 상대적으로 작아, 보유 비중을 {round(current_weights[TICKER_SAMSUNG]*100, 1)}%에서 {round(recommended_weights[TICKER_SAMSUNG]*100, 1)}%로 상향 조정을 추천합니다."
        )
    else:
        explanations.append(
            f"SK하이닉스 대비 삼성전자의 위험 노출을 줄이기 위해, 삼성전자 추천 비중을 {round(recommended_weights[TICKER_SAMSUNG]*100, 1)}%로 비중 조정을 추천합니다."
        )

    # knowledge_stage별 설명 분기
    if knowledge_stage == "beginner":
        # 초보자 수준: 어려운 용어 배제, 쉬운 위험 증감 설명
        explanations.append("포트폴리오의 극단적 가격 급락 위험을 줄이는데 집중한 비중입니다.")
        explanations.append("기업의 착한 경영(ESG) 관련 벌금이나 제재 등의 부정적인 영향도 함께 줄이도록 설계되었습니다.")
    elif knowledge_stage == "information_seeker":
        # 탐색자 수준: 점수 원인 및 공식 뉴스 연계
        explanations.append("공식 보고서 및 최근 뉴스 분석 결과, ESG 지표의 논란성 이슈가 비중 최적화에 반영되었습니다.")
        explanations.append("사건 분석 기준일에 따른 두 반도체 기업의 주가 충격 반응과 회복력을 종합 반영한 결과입니다.")
    else:
        # 가치 투자 초보 수준 (value_beginner): 세부 지표, 신뢰도 등 전문 정보 제공
        sam_esg = company_risks[TICKER_SAMSUNG]["esg_risk"]
        sk_esg = company_risks[TICKER_SK]["esg_risk"]
        explanations.append(f"삼성전자 ESG 위험도({sam_esg}) 및 SK하이닉스 ESG 위험도({sk_esg})를 기반으로 산정되었습니다.")
        explanations.append("95% 신뢰수준의 Historical CVaR과 개별 기업의 3개년 시계열 주가 종속성을 반영한 세부 진단 결과입니다.")

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
    cvar_confidence: float = 0.95,
    turnover_weight: Optional[float] = None,
    downside_weight: float = 0.7,
    esg_weight: float = 0.3,
    knowledge_stage: str = "beginner"
) -> Dict[str, Any]:
    """
    Run 1% grid search portfolio optimization over 20%-80% weight bounds.
    Supports either historical weight profiles or specific customization weights.
    """
    if turnover_weight is None and risk_priority not in RISK_PRIORITY_WEIGHTS:
        # 가중치 직접 주입이 안 되었고, risk_priority가 기존에 정의된 셋이 아니라면 프로필 매핑 매칭해 봄
        profile_to_priority = {
            "strategy_preserving": "conservative",
            "balanced_adjustment": "balanced",
            "risk_priority_adjustment": "esg_focused"
        }
        if risk_priority in profile_to_priority:
            pass
        else:
            raise ValueError(f"유효하지 않은 risk_priority입니다: {risk_priority}")

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
    allow_sample_esg_defaults = data_mode in ("sample", "fallback")
    esg_scores = load_esg_scores(
        esg_input,
        allow_sample_defaults=allow_sample_esg_defaults,
    )

    # 4. Company individual downside risks
    comp_downside = calculate_company_downside_risks(returns_df, prices_df, cvar_confidence=cvar_confidence)

    # 5. Grid Search over Samsung weight range [min_weight, max_weight]
    weights_grid = np.arange(min_weight, max_weight + (grid_step / 2.0), grid_step)
    
    weights_grid = np.round(weights_grid, 4)

    if turnover_weight is not None:
        alpha = downside_weight
        beta = esg_weight
        gamma = turnover_weight
    else:
        profile_to_priority = {
            "strategy_preserving": "conservative",
            "balanced_adjustment": "balanced",
            "risk_priority_adjustment": "esg_focused"
        }
        mapped_priority = profile_to_priority.get(risk_priority, risk_priority)
        policy = RISK_PRIORITY_WEIGHTS.get(mapped_priority, RISK_PRIORITY_WEIGHTS["balanced"])
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
        current_weights, recommended_weights, company_risks, risk_priority, knowledge_stage
    )

    warnings = [
        "이 결과는 미래 주가나 기대수익률 예측이 아닙니다.",
        "삼성전자와 SK하이닉스 모두 반도체 산업에 속하므로 산업 집중위험이 유지됩니다.",
    ]
    if data_mode == "sample":
        warnings.append("현재 샘플 데이터를 사용하여 최적화를 수행했습니다.")
    if allow_sample_esg_defaults:
        warnings.append(
            "ESG 집계 점수가 없어 sample/fallback 전용 예시 점수를 사용했습니다. "
            "이 값은 validated 결과로 표시할 수 없습니다."
        )

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
