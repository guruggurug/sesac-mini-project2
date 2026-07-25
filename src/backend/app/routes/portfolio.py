from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from app.core.templates import templates
from typing import Optional

import logging
import sys
from app.core.config import BASE_DIR, TURNOVER_WEIGHTS, DEFAULT_DOWNSIDE_WEIGHT, DEFAULT_ESG_WEIGHT
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import pandas as pd
from datetime import datetime
from app.repositories.esg_repository import ESGRepository
from app.repositories.price_repository import PriceRepository
from app.utils.realtime_price import get_realtime_price
from src.modeling.optimizer import optimize_portfolio as run_optimize
from app.core.runtime import market_dashboard_service, market_quote_service
from app.core.schemas import (
    PurchaseReason,
    KnowledgeStage,
    RebalancingProfile,
    TurnoverLevel,
    AnalysisSettings,
    PortfolioSummaryRequest,
    PortfolioSummaryResponse,
)
from app.services.market_quotes import MarketQuoteError
from app.services.portfolio_summary import calculate_portfolio_summary

router = APIRouter()
logger = logging.getLogger(__name__)

def get_setup_page(request: Request):
    """
    최종 포트폴리오 자산 입력 페이지 반환 (세션 설정이 없을 경우 /diagnosis로 리다이렉트)
    """
    if "purchase_reason" not in request.session or "rebalancing_profile" not in request.session:
        return RedirectResponse(url="/diagnosis", status_code=303)
        
    return templates.TemplateResponse(
        request=request,
        name="portfolio_input.html",
        context={
            "purchase_reason": request.session.get("purchase_reason"),
            "knowledge_stage": request.session.get("knowledge_stage"),
            "rebalancing_profile": request.session.get("rebalancing_profile"),
            "turnover_level": request.session.get("turnover_level"),
            "data_status": request.session.get("data_status", "sample")
        }
    )

def get_diagnosis_question_page(request: Request):
    """
    1단계: 매수 이유 질문 페이지 반환
    """
    return templates.TemplateResponse(
        request=request,
        name="diagnosis_result.html",
        context={}
    )

@router.post("/diagnosis")
def post_diagnosis_question(request: Request, purchase_reason: str = Form(...)):
    """
    1단계 제출: 매수 이유 저장 및 설명 수준 결정 후 2단계 리다이렉트
    """
    if purchase_reason not in [r.value for r in PurchaseReason]:
        raise HTTPException(status_code=400, detail="유효하지 않은 매수 이유입니다.")
        
    mapping = {
        "price_or_recommendation": "beginner",
        "news_and_industry": "information_seeker",
        "value_and_risk_analysis": "value_beginner"
    }
    knowledge_stage = mapping[purchase_reason]
    
    request.session["purchase_reason"] = purchase_reason
    request.session["knowledge_stage"] = knowledge_stage
    
    return RedirectResponse(url="/rebalancing-profile", status_code=303)

def get_rebalancing_profile_page(request: Request):
    """
    2단계: 포트폴리오 조정 기준 선택 페이지 반환
    """
    if "purchase_reason" not in request.session:
        return RedirectResponse(url="/diagnosis", status_code=303)
        
    return templates.TemplateResponse(
        request=request,
        name="portfolio_edit.html",
        context={}
    )

@router.post("/rebalancing-profile")
def post_rebalancing_profile(request: Request, rebalancing_profile: str = Form(...)):
    """
    2단계 제출: 포트폴리오 조정 기준 저장 및 turnover_weight 결정 후 결과 리다이렉트
    """
    if rebalancing_profile not in [p.value for p in RebalancingProfile]:
        raise HTTPException(status_code=400, detail="유효하지 않은 조정 프로필입니다.")
        
    mapping_level = {
        "strategy_preserving": "high",
        "balanced_adjustment": "medium",
        "risk_priority_adjustment": "low"
    }
    turnover_level = mapping_level[rebalancing_profile]
    turnover_weight = TURNOVER_WEIGHTS[rebalancing_profile]
    
    request.session["rebalancing_profile"] = rebalancing_profile
    request.session["turnover_level"] = turnover_level
    request.session["turnover_weight"] = turnover_weight
    
    return RedirectResponse(url="/settings-result", status_code=303)

def get_settings_result_page(request: Request):
    """
    3단계: 설정 완료 확인 페이지 반환
    """
    if "rebalancing_profile" not in request.session:
        return RedirectResponse(url="/rebalancing-profile", status_code=303)
        
    return templates.TemplateResponse(
        request=request,
        name="diagnosis_result.html",
        context={
            "purchase_reason": request.session.get("purchase_reason"),
            "knowledge_stage": request.session.get("knowledge_stage"),
            "rebalancing_profile": request.session.get("rebalancing_profile"),
            "turnover_level": request.session.get("turnover_level")
        }
    )

@router.post("/portfolio/optimize", response_class=HTMLResponse)
def optimize_portfolio(
    request: Request,
    samsung_qty: Optional[int] = Form(0),
    samsung_price: Optional[float] = Form(None),
    sk_qty: Optional[int] = Form(0),
    sk_price: Optional[float] = Form(None),
    risk_priority: Optional[str] = Form(None)
):
    """
    포트폴리오 비중 최적화 요청 처리 (Form 전송 및 HTMX 응답)
    실시간 외부 주가 연동 반영
    """
    samsung_qty = samsung_qty or 0
    sk_qty = sk_qty or 0

    # 1. 입력 유효성 검사
    if samsung_qty < 0 or sk_qty < 0:
        raise HTTPException(status_code=400, detail="수량은 0 이상이어야 합니다.")

    # 2. 실시간 주가 조회
    realtime_sam = get_realtime_price("005930")
    realtime_sk = get_realtime_price("000660")

    samsung_eval = samsung_qty * realtime_sam
    sk_eval = sk_qty * realtime_sk
    total_eval = samsung_eval + sk_eval

    if total_eval <= 0:
        raise HTTPException(status_code=400, detail="보유 주식의 총 가치가 0 이하입니다. 수량을 입력해주세요.")

    # 세션에서 포트폴리오 조정 기준에 맞춰 turnover_weight 추출
    session_profile = request.session.get("rebalancing_profile", "balanced_adjustment")
    session_turnover_weight = request.session.get("turnover_weight", 0.10)
    session_knowledge_stage = request.session.get("knowledge_stage", "beginner")

    # 기존 API 호환을 위한 매핑 (risk_priority가 넘어온 경우)
    mapped_priority = risk_priority
    if risk_priority:
        if risk_priority == "min_loss":
            mapped_priority = "conservative"
        if mapped_priority not in ["conservative", "balanced", "esg_focused", "strategy_preserving", "balanced_adjustment", "risk_priority_adjustment"]:
            raise HTTPException(status_code=400, detail="유효하지 않은 투자 성향입니다.")
        
        # risk_priority가 주어졌다면 turnover_weight는 None으로 넘겨 legacy 가중치를 따르도록 함
        session_turnover_weight = None

    # 4. 데이터 로드 (Repositories 활용)
    esg_repo = ESGRepository()
    price_repo = PriceRepository()
    
    try:
        esg_data, esg_status, esg_warn = esg_repo.load_data()
        price_df, price_status, price_warn = price_repo.load_data_as_df()
    except Exception as error:
        logger.error("Portfolio input data loading failed (%s)", type(error).__name__)
        raise HTTPException(
            status_code=500,
            detail="포트폴리오 분석 데이터를 불러오지 못했습니다.",
        ) from error

    # 데이터 상태 판별
    if esg_status == "sample" or price_status == "sample":
        data_mode = "sample"
    elif esg_status == "fallback" or price_status == "fallback":
        data_mode = "fallback"
    else:
        data_mode = "validated"

    warnings = []
    if esg_warn:
        warnings.append(esg_warn)
    if price_warn:
        warnings.append(price_warn)

    # 5. 가격 시계열에 오늘자 실시간 주가 동적 결합 (long format)
    today_dt = pd.to_datetime(datetime.now().date())
    price_df["date"] = pd.to_datetime(price_df["date"])
    
    # 중복 제거
    price_df = price_df[price_df["date"] != today_dt]
    
    # 삼성전자 오늘 행
    sam_row = pd.DataFrame([{
        "date": today_dt,
        "company_id": "005930",
        "company_name": "삼성전자",
        "ticker": "005930",
        "open": realtime_sam,
        "high": realtime_sam,
        "low": realtime_sam,
        "close": realtime_sam,
        "adjusted_close": realtime_sam,
        "volume": 0,
        "currency": "KRW",
        "source_type": "exchange",
        "data_status": data_mode,
        "note": "실시간 외부 주가 연동"
    }])
    
    # SK하이닉스 오늘 행
    sk_row = pd.DataFrame([{
        "date": today_dt,
        "company_id": "000660",
        "company_name": "SK하이닉스",
        "ticker": "000660",
        "open": realtime_sk,
        "high": realtime_sk,
        "low": realtime_sk,
        "close": realtime_sk,
        "adjusted_close": realtime_sk,
        "volume": 0,
        "currency": "KRW",
        "source_type": "exchange",
        "data_status": data_mode,
        "note": "실시간 외부 주가 연동"
    }])
    
    price_df = pd.concat([price_df, sam_row, sk_row], ignore_index=True)

    # 6. 모델 호출을 위한 holdings 구성 (평단가로 실시간 현재가 주입 및 buy_reason 추가)
    purchase_reason = request.session.get("purchase_reason", "news_and_industry")
    purchase_reason_text_map = {
        "price_or_recommendation": "주가 흐름이나 주변 추천",
        "news_and_industry": "뉴스·실적·산업 전망",
        "value_and_risk_analysis": "기업가치와 장기 위험"
    }
    buy_reason = purchase_reason_text_map.get(purchase_reason, "기본 분석")

    holdings = [
        {"ticker": "005930", "quantity": samsung_qty, "average_price": realtime_sam, "buy_reason": buy_reason},
        {"ticker": "000660", "quantity": sk_qty, "average_price": realtime_sk, "buy_reason": buy_reason}
    ]

    esg_df = pd.DataFrame(esg_data)

    # 7. 최적화 엔진 구동 및 폴백 처리
    try:
        opt_result = run_optimize(
            holdings=holdings,
            price_data=price_df,
            esg_input=esg_df,
            risk_priority=mapped_priority or session_profile,
            data_mode=data_mode,
            turnover_weight=session_turnover_weight,
            downside_weight=DEFAULT_DOWNSIDE_WEIGHT,
            esg_weight=DEFAULT_ESG_WEIGHT,
            knowledge_stage=session_knowledge_stage
        )
    except Exception as error:
        try:
            sample_esg_data, _, _ = esg_repo.load_data()
            sample_price_df, _, _ = price_repo.load_data_as_df()
            sample_price_df["date"] = pd.to_datetime(sample_price_df["date"])
            sample_price_df = sample_price_df[sample_price_df["date"] != today_dt]
            
            # 샘플 데이터에도 오늘자 결합
            sample_price_df = pd.concat([sample_price_df, sam_row, sk_row], ignore_index=True)

            opt_result = run_optimize(
                holdings=holdings,
                price_data=sample_price_df,
                esg_input=pd.DataFrame(sample_esg_data),
                risk_priority=mapped_priority or session_profile,
                data_mode="fallback",
                turnover_weight=session_turnover_weight,
                downside_weight=DEFAULT_DOWNSIDE_WEIGHT,
                esg_weight=DEFAULT_ESG_WEIGHT,
                knowledge_stage=session_knowledge_stage
            )
            opt_result["warnings"] = opt_result.get("warnings", []) + [
                "최적화 계산 오류로 검증된 대체 데이터 경로를 사용했습니다."
            ]
        except Exception as fallback_error:
            logger.error(
                "Portfolio optimization and fallback failed (%s/%s)",
                type(error).__name__,
                type(fallback_error).__name__,
            )
            raise HTTPException(
                status_code=500,
                detail="포트폴리오 최적화와 대체 계산에 실패했습니다.",
            ) from fallback_error

    if warnings:
        opt_result["warnings"] = list(set(opt_result.get("warnings", []) + warnings))

    request.session["portfolio_holdings"] = [
        {
            "ticker": "005930",
            "quantity": samsung_qty,
            "average_price": samsung_price or realtime_sam,
        },
        {
            "ticker": "000660",
            "quantity": sk_qty,
            "average_price": sk_price or realtime_sk,
        },
    ]
    request.session["portfolio_holdings"] = [
        holding
        for holding in request.session["portfolio_holdings"]
        if holding["quantity"] > 0
    ]

    # ESG 데이터의 scope_mismatch 정보와 data_confidence를 매핑하여 템플릿에 제공
    for company_row in esg_data:
        ticker = str(company_row.get("company_id", company_row.get("ticker", ""))).zfill(6)
        if ticker in opt_result["company_risks"]:
            mismatch_val = company_row.get("scope_mismatch", False)
            if isinstance(mismatch_val, str):
                mismatch_val = mismatch_val.lower() == "true"
            opt_result["company_risks"][ticker]["scope_mismatch"] = mismatch_val
            opt_result["company_risks"][ticker]["data_confidence"] = company_row.get("data_confidence", "medium")

    # 8. HTML 조각 렌더링 응답 반환
    return templates.TemplateResponse(
        request=request,
        name="diagnosis_result.html",
        context={
            "data": opt_result,
            "data_status": opt_result.get("data_status", data_mode),
            "knowledge_stage": session_knowledge_stage,
        }
    )


@router.post(
    "/portfolio/summary",
    response_model=PortfolioSummaryResponse,
)
def get_portfolio_summary(payload: PortfolioSummaryRequest):
    try:
        request_refresh = getattr(
            market_dashboard_service,
            "request_refresh_for",
            None,
        )
        if callable(request_refresh):
            request_refresh(market_quote_service)
        return calculate_portfolio_summary(
            payload.holdings,
            market_quote_service,
            # This endpoint values holdings from market snapshots only. A
            # local/LKG quote is marked fallback by calculate_portfolio_summary.
            source_data_status="validated",
        )
    except MarketQuoteError as error:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "MARKET_QUOTE_UNAVAILABLE",
                "message": "현재가 또는 대체 가격을 불러올 수 없습니다.",
            },
        ) from error

@router.post("/portfolio/calculate")
def calculate_current_portfolio(
    samsung_qty: int = Form(...),
    samsung_price: float = Form(None),
    sk_qty: int = Form(...),
    sk_price: float = Form(None)
):
    """
    사용자 입력 수량을 기준으로 실시간 주가를 이용해 현재 포트폴리오 비중을 계산하여 반환
    """
    if samsung_qty < 0 or sk_qty < 0:
        raise HTTPException(status_code=400, detail="수량은 0 이상이어야 합니다.")
        
    realtime_sam = get_realtime_price("005930")
    realtime_sk = get_realtime_price("000660")

    samsung_eval = samsung_qty * realtime_sam
    sk_eval = sk_qty * realtime_sk
    total_eval = samsung_eval + sk_eval

    if total_eval <= 0:
        raise HTTPException(status_code=400, detail="총 자산 평가 금액이 0 이하입니다.")

    current_weights = {
        "005930": round(samsung_eval / total_eval, 4),
        "000660": round(sk_eval / total_eval, 4)
    }

    esg_repo = ESGRepository()
    price_repo = PriceRepository()
    try:
        _, esg_status, _ = esg_repo.load_data()
        _, price_status, _ = price_repo.load_data_as_df()
    except Exception:
        esg_status, price_status = "sample", "sample"
        
    if esg_status == "sample" or price_status == "sample":
        data_mode = "sample"
    elif esg_status == "fallback" or price_status == "fallback":
        data_mode = "fallback"
    else:
        data_mode = "validated"

    return {
        "current_weights": current_weights,
        "data_status": data_mode,
        "realtime_prices": {
            "005930": realtime_sam,
            "000660": realtime_sk
        }
    }
