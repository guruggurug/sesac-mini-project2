from fastapi import APIRouter, HTTPException

from app.core.runtime import market_dashboard_service
from app.core.schemas import MarketQuotesResponse
from app.services.market_quotes import MarketQuoteError


router = APIRouter()


@router.get("/market/quotes", response_model=MarketQuotesResponse)
def get_market_quotes():
    try:
        return market_dashboard_service.get_quotes()
    except MarketQuoteError as error:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "MARKET_QUOTES_UNAVAILABLE",
                "message": str(error),
            },
        ) from error
