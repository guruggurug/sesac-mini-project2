import sys
from fastapi import APIRouter, HTTPException
from app.core.config import BASE_DIR

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import pandas as pd
from datetime import datetime
from app.repositories.esg_repository import ESGRepository
from app.repositories.price_repository import PriceRepository
from src.modeling.price import calculate_daily_returns
from src.modeling.downside import calculate_company_downside_risks
from src.modeling.optimizer import classify_risk_level

router = APIRouter(tags=["Risk"])

@router.post("/risk/esg")
def calculate_esg_risk():
    """
    두 기업의 ESG 위험 수준 계산
    """
    esg_repo = ESGRepository()
    try:
        esg_data, esg_status, esg_warn = esg_repo.load_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ESG 데이터 로드 실패: {str(e)}")
        
    result = {}
    company_rows = {"005930": [], "000660": []}
    for row in esg_data:
        ticker = str(row.get("company_id", row.get("ticker", ""))).zfill(6)
        if ticker in ("005930", "000660"):
            company_rows[ticker].append(row)

    confidence_order = {"low": 0, "medium": 1, "high": 2}
    for ticker, rows in company_rows.items():
        score_rows = [row for row in rows if row.get("esg_risk_score") not in (None, "")]
        mismatch_values = []
        for row in rows:
            mismatch = row.get("scope_mismatch", False)
            mismatch_values.append(mismatch.lower() == "true" if isinstance(mismatch, str) else bool(mismatch))

        confidences = [
            row.get("data_confidence")
            for row in rows
            if row.get("data_confidence") in confidence_order
        ]
        data_confidence = min(confidences, key=confidence_order.get) if confidences else "low"

        if score_rows:
            esg_risk = float(score_rows[0]["esg_risk_score"])
            risk_level = classify_risk_level(esg_risk)
        else:
            esg_risk = None
            risk_level = "unavailable"

        result[ticker] = {
            "company_name": rows[0].get("company_name") if rows else ("삼성전자" if ticker == "005930" else "SK하이닉스"),
            "esg_risk": round(esg_risk, 4) if esg_risk is not None else None,
            "risk_level": risk_level,
            "data_confidence": data_confidence,
            "scope_mismatch": any(mismatch_values),
        }
            
    result["data_status"] = esg_status
    if esg_warn:
        result["warning"] = esg_warn
    if any(company["esg_risk"] is None for company in result.values() if isinstance(company, dict)):
        result["warning"] = (
            f"{result.get('warning') + ' ' if result.get('warning') else ''}"
            "ESG 지표 원천값은 검증되었지만 Data B 집계 점수가 아직 없어 ESG 위험을 unavailable로 표시합니다."
        )
        
    return result

@router.post("/risk/downside")
def calculate_downside_risk():
    """
    Historical CVaR 기반 가격 하방 위험 계산 (실시간 가격 결합)
    """
    price_repo = PriceRepository()
    try:
        price_df, price_status, price_warn = price_repo.load_data_as_df()
        from src.modeling.price import validate_price_data
        pivoted_price_df = validate_price_data(price_df)
        
        # 오늘자 실시간 현재가를 시계열 맨 끝에 병합
        from app.utils.realtime_price import get_realtime_price
        realtime_sam = get_realtime_price("005930")
        realtime_sk = get_realtime_price("000660")
        
        today = pd.Timestamp(datetime.now().date())
        if today not in pivoted_price_df.index:
            new_row = pd.DataFrame(
                [[realtime_sam, realtime_sk]], 
                columns=["005930", "000660"], 
                index=[today]
            )
            pivoted_price_df = pd.concat([pivoted_price_df, new_row])
        else:
            pivoted_price_df.loc[today, "005930"] = realtime_sam
            pivoted_price_df.loc[today, "000660"] = realtime_sk
            
        returns_df = calculate_daily_returns(pivoted_price_df)
        downside_risks = calculate_company_downside_risks(returns_df, pivoted_price_df, cvar_confidence=0.95)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"하방 위험 계산 실패: {str(e)}")
        
    result = {}
    for ticker, metrics in downside_risks.items():
        cvar_val = metrics["cvar_95"]
        result[ticker] = {
            "company_name": "삼성전자" if ticker == "005930" else "SK하이닉스",
            "downside_risk": round(cvar_val, 4),
            "risk_level": classify_risk_level(cvar_val),
            "data_confidence": "high" if ticker == "005930" else "medium"
        }
        
    result["data_status"] = price_status
    if price_warn:
        result["warning"] = price_warn
        
    return result

