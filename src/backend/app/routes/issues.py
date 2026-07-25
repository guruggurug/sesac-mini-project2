import logging
import sys
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from app.core.config import BASE_DIR
from app.core.templates import templates

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import pandas as pd
from app.repositories.event_repository import EventRepository
from app.repositories.price_repository import PriceRepository
from src.modeling.events import analyze_all_events

router = APIRouter(tags=["Issues"])
logger = logging.getLogger(__name__)

def get_issues_page(request: Request):
    """
    이슈 분석 대시보드 HTML 페이지 반환
    """
    event_repo = EventRepository()
    price_repo = PriceRepository()
    
    try:
        events, event_status, event_warn = event_repo.load_data()
        price_df, price_status, price_warn = price_repo.load_data_as_df()
    except Exception as error:
        logger.error("Issue page data loading failed (%s)", type(error).__name__)
        raise HTTPException(
            status_code=500,
            detail="이슈 데이터를 불러오지 못했습니다.",
        ) from error
        
    if event_status == "sample" or price_status == "sample":
        data_mode = "sample"
    elif event_status == "fallback" or price_status == "fallback":
        data_mode = "fallback"
    else:
        data_mode = "validated"
        
    events_df = pd.DataFrame(events)
    
    # 1. 현재 진행 중인 현안 목록 변환
    current_issues = []
    for evt in events:
        ticker = str(evt.get("company_id", evt.get("ticker", ""))).zfill(6)
        current_issues.append({
            "company_name": "삼성전자" if ticker == "005930" else "SK하이닉스",
            "event_date": evt.get("event_date", ""),
            "summary": evt.get("summary", ""),
            "status": evt.get("status", "unknown"),
            "official_source_url": evt.get("official_source_url", evt.get("news_url", "#"))
        })
        
    # 2. 과거 유사 사례 주가 영향 연산
    try:
        analyzed_events = analyze_all_events(
            events_input=events_df,
            price_data=price_df,
            window_days=10,
            filter_model_eligible_only=True
        )
    except Exception:
        analyzed_events = []
        
    clean_historical = []
    for evt in analyzed_events:
        if "error" not in evt:
            clean_historical.append(evt)
            
    return templates.TemplateResponse(
        request=request,
        name="issue_analysis.html",
        context={
            "current_issues": current_issues,
            "historical_issues": clean_historical,
            "data_status": data_mode
        }
    )


@router.get("/issues/current")
def get_current_issues():
    """
    실시간 또는 현재 진행 중인 반도체 기업 현안 및 이벤트 조회
    """
    event_repo = EventRepository()
    try:
        events, data_status, warning = event_repo.load_data()
    except Exception as error:
        logger.error("Current issue loading failed (%s)", type(error).__name__)
        raise HTTPException(
            status_code=500,
            detail="현재 이슈 데이터를 불러오지 못했습니다.",
        ) from error
        
    response = {
        "events": events,
        "data_status": data_status
    }
    if warning:
        response["warning"] = warning
        
    return response

@router.get("/issues/historical")
def get_historical_issues():
    """
    과거 유사 사건 및 주가 영향 데이터 조회
    """
    event_repo = EventRepository()
    price_repo = PriceRepository()
    
    try:
        events, event_status, event_warn = event_repo.load_data()
        price_df, price_status, price_warn = price_repo.load_data_as_df()
    except Exception as error:
        logger.error("Historical issue data loading failed (%s)", type(error).__name__)
        raise HTTPException(
            status_code=500,
            detail="과거 이슈 데이터를 불러오지 못했습니다.",
        ) from error
        
    # 데이터 상태 결정
    if event_status == "sample" or price_status == "sample":
        data_mode = "sample"
    elif event_status == "fallback" or price_status == "fallback":
        data_mode = "fallback"
    else:
        data_mode = "validated"
        
    events_df = pd.DataFrame(events)
    
    try:
        analyzed_events = analyze_all_events(
            events_input=events_df,
            price_data=price_df,
            window_days=10,
            filter_model_eligible_only=True
        )
    except Exception as error:
        logger.error("Historical issue analysis failed (%s)", type(error).__name__)
        raise HTTPException(
            status_code=500,
            detail="과거 사건 반응을 분석하지 못했습니다.",
        ) from error
        
    warnings = []
    if event_warn:
        warnings.append(event_warn)
    if price_warn:
        warnings.append(price_warn)
        
    clean_events = []
    for evt in analyzed_events:
        if "error" in evt:
            warnings.append(
                f"이벤트 {evt.get('event_id', 'unknown')} 분석 결과를 제공할 수 없습니다."
            )
        else:
            clean_events.append(evt)
            
    response = {
        "events": clean_events,
        "data_status": data_mode
    }
    if warnings:
        response["warnings"] = list(set(warnings))
        
    return response
