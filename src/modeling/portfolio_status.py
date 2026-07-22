"""
Portfolio Status Scoring & Summary Generation Module for Data B.
Calculates 0-100 portfolio score, traffic-light signals, and generates rule-based Korean summaries.
"""

from typing import Dict, Any, List

TICKER_SAMSUNG = "005930"
TICKER_SK = "000660"


def calculate_portfolio_status(optimization_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate portfolio health score, traffic light signal, and return Korean summary sentences.

    Args:
        optimization_result: Dictionary returned from optimize_portfolio.

    Returns:
        Dict[str, Any]: Portfolio status dictionary containing score, signal, label, and summary.
    """
    current_total_risk = float(optimization_result.get("current_total_risk", 0.5))
    current_weights = optimization_result.get("current_weights", {TICKER_SAMSUNG: 0.5, TICKER_SK: 0.5})
    recommended_weights = optimization_result.get("recommended_weights", {TICKER_SAMSUNG: 0.5, TICKER_SK: 0.5})
    risk_reduction_rate = float(optimization_result.get("risk_reduction_rate", 0.0))
    company_risks = optimization_result.get("company_risks", {})

    # 1. Calculate Score: round((1 - Current Total Risk) * 100)
    score = round((1.0 - current_total_risk) * 100)
    score = max(0, min(100, score))

    # 2. Determine Signal and Label
    if score >= 70:
        signal = "green"
        label = "안정적인 포트폴리오 상태"
    elif score >= 40:
        signal = "yellow"
        label = "비중 조정 검토 필요"
    else:
        signal = "red"
        label = "적극적인 위험 관리 필요"

    # 3. Generate Rule-Based Korean Summary
    summary = []

    # Weight check
    sam_w = current_weights.get(TICKER_SAMSUNG, 0.0)
    sk_w = current_weights.get(TICKER_SK, 0.0)
    if abs(sam_w - sk_w) < 0.1:
        summary.append("현재 삼성전자와 SK하이닉스 보유 비중이 고르게 분산되어 있습니다.")
    elif sam_w > sk_w:
        summary.append("현재 포트폴리오는 삼성전자 비중이 상대적으로 높습니다.")
    else:
        summary.append("현재 포트폴리오는 SK하이닉스 비중이 상대적으로 높습니다.")

    # Core risk considerations
    summary.append("가격 하방위험(CVaR)과 ESG 관리위험을 종합적으로 분석 및 반영했습니다.")

    # Optimization benefits
    if risk_reduction_rate > 0.01:
        reduction_pct = round(risk_reduction_rate * 100, 1)
        summary.append(f"추천 비중으로 조정할 경우 포트폴리오의 종합 위험이 약 {reduction_pct}% 감소합니다.")
    else:
        summary.append("현재 비중이 최적 추천 비중에 가깝게 유지되고 있어 추가 조정에 따른 위험 감소 효과는 크지 않습니다.")

    # Specific company warnings
    high_risk_companies = []
    for ticker, risk_info in company_risks.items():
        name = "삼성전자" if ticker == TICKER_SAMSUNG else "SK하이닉스"
        if risk_info.get("risk_level") == "high":
            high_risk_companies.append(name)
            
    if high_risk_companies:
        summary.append(f"{', '.join(high_risk_companies)}의 하방위험 혹은 ESG 지표 수준이 취약하므로 모니터링이 권장됩니다.")

    return {
        "portfolio_status_score": score,
        "signal": signal,
        "label": label,
        "summary": summary
    }
