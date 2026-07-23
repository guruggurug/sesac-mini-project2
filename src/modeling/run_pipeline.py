"""
Pipeline Execution Script for Data B.
Runs all modeling calculations end-to-end using reviewed data and writes results to data/processed/.
"""

import os
import json
import hashlib
from pathlib import Path
import pandas as pd
from datetime import datetime, timezone

from src.modeling.price import validate_price_data
from src.modeling.downside import calculate_company_downside_risks
from src.modeling.esg import run_esg_scoring_pipeline
from src.modeling.events import analyze_all_events
from src.modeling.optimizer import optimize_portfolio
from src.modeling.sensitivity import run_sensitivity_analysis


def file_hash(filepath: Path) -> str:
    """Compute MD5 hash of a file."""
    if not filepath.exists():
        return "missing"
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()


def main():
    print("칩버디 데이터 B 최종 파이프라인 구동 시작...")
    
    # Paths
    base_dir = Path(".")
    data_dir = base_dir / "data" / "processed"
    out_dir = base_dir / "data" / "processed"
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Load Reviewed Datasets
    ind_csv = data_dir / "esg_indicators.csv"
    evt_csv = data_dir / "events.csv"
    src_csv = data_dir / "sources.csv"
    price_csv = data_dir / "stock_prices.csv"
    index_csv = data_dir / "index_prices.csv"
    
    # Check existence
    for path in [ind_csv, evt_csv, src_csv, price_csv, index_csv]:
        if not path.exists():
            raise FileNotFoundError(f"필수 검수 파일이 누락되었습니다: {path}")

    # Load dataframes
    ind_df = pd.read_csv(ind_csv)
    evt_df = pd.read_csv(evt_csv)
    
    # 2. Compute dynamic ESG risk scores
    print("1. ESG 위험 점수 계산 중...")
    esg_results = run_esg_scoring_pipeline(
        indicators_path=ind_csv,
        events_path=evt_csv,
        sources_path=src_csv,
        config_dir=base_dir / "config"
    )
    with open(out_dir / "company_esg_risks.json", "w", encoding="utf-8") as f:
        json.dump(esg_results, f, ensure_ascii=False, indent=2)

    # 3. Compute downside risk metrics (cvar, mdd, downside_deviation)
    print("2. 가격 하방위험 점수 계산 중...")
    prices_df = validate_price_data(price_csv)
    returns_df = prices_df.pct_change().dropna()
    downside_results = calculate_company_downside_risks(
        returns_df=returns_df,
        prices_df=prices_df,
        cvar_confidence=0.95,
        years=3
    )
    with open(out_dir / "company_downside_risks.json", "w", encoding="utf-8") as f:
        json.dump(downside_results, f, ensure_ascii=False, indent=2)

    # 4. Compute event reactions & abnormal returns
    print("3. 역사적 사건 반응 분석 중...")
    event_reactions = analyze_all_events(
        events_input=evt_csv,
        price_data=price_csv,
        index_prices_input=index_csv,
        window_days=10,
        filter_model_eligible_only=True
    )
    with open(out_dir / "event_reactions.json", "w", encoding="utf-8") as f:
        json.dump({"events": event_reactions}, f, ensure_ascii=False, indent=2)

    # 5. Optimize default portfolio holdings (70 Samsung, 30 SK Hynix)
    print("4. 포트폴리오 비중 최적화 시뮬레이션 중...")
    holdings = [
        {"ticker": "005930", "quantity": 70, "average_price": 70000},
        {"ticker": "000660", "quantity": 30, "average_price": 180000}
    ]
    opt_result = optimize_portfolio(
        holdings=holdings,
        price_data=price_csv,
        esg_input=ind_df,
        risk_priority="balanced",
        data_mode="reviewed",
        cvar_confidence=0.95,
        price_period_years=3
    )
    with open(out_dir / "optimization_result.json", "w", encoding="utf-8") as f:
        json.dump(opt_result, f, ensure_ascii=False, indent=2)

    # 6. Run Sensitivity Analysis
    print("5. 매개변수 민감도 분석 중...")
    sensitivity_summary = run_sensitivity_analysis(
        holdings=holdings,
        price_data=price_csv,
        esg_input=ind_df,
        output_dir=out_dir,
        data_mode="reviewed"
    )

    # 7. Generate run metadata
    print("6. 파이프라인 구동 메타데이터 작성 중...")
    metadata = {
        "run_id": datetime.now(timezone.utc).strftime("RUN-%Y%m%d-%H%M%S"),
        "model_version": "v1.2-dynamic-esg",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_status": "reviewed",
        "input_files": {
            "esg_indicators": {
                "file": "esg_indicators.csv",
                "hash": file_hash(ind_csv)
            },
            "events": {
                "file": "events.csv",
                "hash": file_hash(evt_csv)
            },
            "stock_prices": {
                "file": "stock_prices.csv",
                "hash": file_hash(price_csv)
            },
            "index_prices": {
                "file": "index_prices.csv",
                "hash": file_hash(index_csv)
            }
        },
        "model_parameters": {
            "cvar_confidence": 0.95,
            "price_period_years": 3,
            "min_weight": 0.20,
            "max_weight": 0.80,
            "grid_step": 0.01
        }
    }
    with open(out_dir / "model_run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("칩버디 데이터 B 파이프라인 구동 완료! 결과가 data/processed/ 디렉터리에 저장되었습니다.")


if __name__ == "__main__":
    main()
