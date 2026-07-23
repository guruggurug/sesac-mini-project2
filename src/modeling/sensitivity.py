"""
Sensitivity Analysis Module for Data B.
Varies parameters (period, confidence level, risk profiles, turnover weights) to test recommendation stability.
"""

import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Union, Optional

from src.modeling.optimizer import optimize_portfolio


def run_sensitivity_analysis(
    holdings: List[Dict[str, Any]],
    price_data: Union[str, Path, pd.DataFrame],
    esg_input: Optional[Union[str, Path, pd.DataFrame]] = None,
    output_dir: Union[str, Path] = "data/processed",
    data_mode: str = "reviewed"
) -> Dict[str, Any]:
    """
    Run sensitivity analysis over multiple parameter combinations and save the results.
    
    Args:
        holdings: Portfolio holdings.
        price_data: Stock prices.
        esg_input: ESG indicator records.
        output_dir: Output directory path.
        data_mode: 'reviewed' or 'sample'.

    Returns:
        Dict[str, Any]: Summary dictionary of the sensitivity analysis.
    """
    out_dir = Path(output_dir)
    os.makedirs(out_dir, exist_ok=True)

    periods = [1, 3, 5]
    confidences = [0.90, 0.95, 0.975]
    profiles = ["loss_minimization", "balanced", "esg_focused"]
    gammas = [0.02, 0.10, 0.20]  # low, default, high turnover weights

    records = []

    for y in periods:
        for conf in confidences:
            for prof in profiles:
                for gam in gammas:
                    try:
                        res = optimize_portfolio(
                            holdings=holdings,
                            price_data=price_data,
                            esg_input=esg_input,
                            risk_priority=prof,
                            custom_gamma=gam,
                            cvar_confidence=conf,
                            price_period_years=y,
                            data_mode=data_mode
                        )
                        
                        rec = {
                            "analysis_period_years": y,
                            "cvar_confidence": conf,
                            "risk_priority": prof,
                            "turnover_weight_gamma": gam,
                            "rec_weight_samsung": res["recommended_weights"]["005930"],
                            "rec_weight_skhynix": res["recommended_weights"]["000660"],
                            "optimized_total_risk": res["optimized_total_risk"],
                            "optimized_cvar": res["optimized_cvar"],
                            "optimized_esg_risk": res["optimized_esg_risk"],
                            "risk_reduction_rate": res["risk_reduction_rate"]
                        }
                        records.append(rec)
                    except Exception as e:
                        # Log error record
                        records.append({
                            "analysis_period_years": y,
                            "cvar_confidence": conf,
                            "risk_priority": prof,
                            "turnover_weight_gamma": gam,
                            "error": str(e)
                        })

    df = pd.DataFrame(records)
    csv_file = out_dir / "sensitivity_results.csv"
    df.to_csv(csv_file, index=False, encoding="utf-8-sig")

    # Generate summary stats (excluding errors)
    valid_df = df[df["error"].isna()] if "error" in df.columns else df
    
    if not valid_df.empty:
        sam_weights = valid_df["rec_weight_samsung"].astype(float)
        summary = {
            "total_runs": len(df),
            "successful_runs": len(valid_df),
            "failed_runs": len(df) - len(valid_df),
            "samsung_weight": {
                "mean": round(float(sam_weights.mean()), 4),
                "std": round(float(sam_weights.std()), 4) if len(sam_weights) > 1 else 0.0,
                "min": round(float(sam_weights.min()), 4),
                "max": round(float(sam_weights.max()), 4),
            },
            "stability_status": "stable" if (sam_weights.std() < 0.15 if len(sam_weights) > 1 else True) else "unstable",
            "korean_note": "민감도 테스트 완료. 분석 기간 및 투자 성향 조건 변화에 따른 비중 변동성이 안정 범위 이내입니다." if (sam_weights.std() < 0.15 if len(sam_weights) > 1 else True) else "분석 조건에 따른 추천 비중의 편차가 큽니다. 투자 결정을 내릴 때 매개변수 설정에 유의하십시오."
        }
    else:
        summary = {
            "total_runs": len(df),
            "successful_runs": 0,
            "failed_runs": len(df),
            "stability_status": "unknown",
            "korean_note": "오류로 인해 민감도 분석을 수행할 수 없습니다."
        }

    json_file = out_dir / "sensitivity_summary.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return summary
