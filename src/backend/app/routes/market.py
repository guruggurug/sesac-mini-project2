from fastapi import APIRouter, HTTPException

from app.core.runtime import market_dashboard_service
from app.core.schemas import MarketQuotesResponse
from app.services.market_quotes import MarketQuoteError


router = APIRouter()


@router.get("/market/quotes", response_model=MarketQuotesResponse)
def get_market_quotes():
    # Refresh runs in one background worker. The public request only reads the
    # latest in-memory/SQLite snapshot and never waits for KIS network I/O.
    request_refresh = getattr(market_dashboard_service, "request_refresh", None)
    if callable(request_refresh):
        request_refresh()
    try:
        return market_dashboard_service.get_quotes()
    except MarketQuoteError as error:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "MARKET_QUOTES_UNAVAILABLE",
                "message": "신뢰 가능한 시장 스냅샷이 아직 준비되지 않았습니다.",
            },
        ) from error
