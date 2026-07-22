from app.core.config import (
    KIS_APP_KEY,
    KIS_APP_SECRET,
    KIS_BASE_URL,
    MARKET_QUOTE_CACHE_TTL_SECONDS,
    MARKET_QUOTE_TIMEOUT_SECONDS,
)
from app.core.runtime import runtime_state_repository
from app.services.kis_market_data import KISMarketDataProvider
from app.services.market_quotes import (
    MarketQuoteService,
    RepositoryPriceAdapter,
    SQLiteLastKnownGoodAdapter,
    UnavailableMarketDataProvider,
)


def _build_provider():
    if KIS_APP_KEY and KIS_APP_SECRET:
        return KISMarketDataProvider(
            app_key=KIS_APP_KEY,
            app_secret=KIS_APP_SECRET,
            base_url=KIS_BASE_URL,
        )
    return UnavailableMarketDataProvider()


_DEFAULT_SERVICE = MarketQuoteService(
    provider=_build_provider(),
    local_adapter=RepositoryPriceAdapter(),
    last_known_good_adapter=SQLiteLastKnownGoodAdapter(
        runtime_state_repository
    ),
    cache_ttl_seconds=MARKET_QUOTE_CACHE_TTL_SECONDS,
    provider_timeout_seconds=MARKET_QUOTE_TIMEOUT_SECONDS,
)


def get_realtime_price(
    ticker: str,
    *,
    service: MarketQuoteService | None = None,
) -> float:
    """Compatibility wrapper for existing internal stock-price call sites."""
    return (service or _DEFAULT_SERVICE).get_quote(ticker).price
