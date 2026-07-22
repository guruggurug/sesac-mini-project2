from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from time import monotonic
from typing import Callable, Protocol

from app.repositories.price_repository import PriceRepository
from app.repositories.runtime_state_repository import RuntimeStateRepository


SUPPORTED_INSTRUMENTS = {"KOSPI", "KOSDAQ", "005930", "000660"}


class MarketQuoteError(RuntimeError):
    """Raised when no trustworthy price is available for an instrument."""


class MarketDataProvider(Protocol):
    def fetch_price(self, instrument_id: str, timeout_seconds: float) -> float:
        """Return a positive latest price or raise an exception."""


class LocalPriceAdapter(Protocol):
    def latest_close(self, instrument_id: str) -> float:
        """Return the latest local close for a stock instrument."""


@dataclass(frozen=True)
class InternalQuote:
    instrument_id: str
    price: float
    source: str
    fetched_at: datetime


@dataclass(frozen=True)
class _CacheEntry:
    quote: InternalQuote
    expires_at: float


class LastKnownGoodAdapter(Protocol):
    def save_quote(self, quote: InternalQuote) -> None:
        """Persist a successful provider quote."""

    def load_quote(self, instrument_id: str) -> InternalQuote | None:
        """Load the latest successfully persisted provider quote."""


class UnavailableMarketDataProvider:
    """MVP placeholder used until an approved Korean-market provider is configured."""

    def fetch_price(self, instrument_id: str, timeout_seconds: float) -> float:
        raise MarketQuoteError(
            f"No external market-data provider is configured for {instrument_id}"
        )


class RepositoryPriceAdapter:
    """Adapts the existing validated price repository to latest-close lookup."""

    def __init__(self, repository: PriceRepository | None = None) -> None:
        self._repository = repository or PriceRepository()

    def latest_close(self, instrument_id: str) -> float:
        frame, _, _ = self._repository.load_data_as_df()
        tickers = frame["ticker"].astype(str).str.zfill(6)
        rows = frame[tickers == instrument_id]
        if rows.empty:
            raise MarketQuoteError(f"No local price available for {instrument_id}")

        price = float(rows.iloc[-1]["close"])
        if price <= 0:
            raise MarketQuoteError(f"Invalid local price for {instrument_id}")
        return price


class SQLiteLastKnownGoodAdapter:
    def __init__(self, repository: RuntimeStateRepository) -> None:
        self._repository = repository

    def save_quote(self, quote: InternalQuote) -> None:
        self._repository.save_market_quote(
            instrument_id=quote.instrument_id,
            price=quote.price,
            source=quote.source,
            as_of=quote.fetched_at,
        )

    def load_quote(self, instrument_id: str) -> InternalQuote | None:
        stored = self._repository.load_market_quote(instrument_id)
        if stored is None:
            return None
        return InternalQuote(
            instrument_id=stored.instrument_id,
            price=stored.price,
            source=f"last_known_good:{stored.source}",
            fetched_at=stored.as_of,
        )


class MarketQuoteService:
    """Internal quote lookup with provider timeout, TTL cache, and stock fallback."""

    def __init__(
        self,
        provider: MarketDataProvider,
        local_adapter: LocalPriceAdapter,
        last_known_good_adapter: LastKnownGoodAdapter | None = None,
        *,
        cache_ttl_seconds: float = 15.0,
        provider_timeout_seconds: float = 5.0,
        clock: Callable[[], float] = monotonic,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        if cache_ttl_seconds < 0:
            raise ValueError("cache_ttl_seconds must be non-negative")
        if provider_timeout_seconds <= 0:
            raise ValueError("provider_timeout_seconds must be positive")

        self._provider = provider
        self._local_adapter = local_adapter
        self._last_known_good_adapter = last_known_good_adapter
        self._cache_ttl_seconds = cache_ttl_seconds
        self._provider_timeout_seconds = provider_timeout_seconds
        self._clock = clock
        self._now = now
        self._cache: dict[str, _CacheEntry] = {}
        self._lock = Lock()

    def get_quote(self, instrument_id: str) -> InternalQuote:
        if instrument_id not in SUPPORTED_INSTRUMENTS:
            raise ValueError(f"Unsupported instrument_id: {instrument_id}")

        cached = self._get_cached(instrument_id)
        if cached is not None:
            return cached

        try:
            price = self._provider.fetch_price(
                instrument_id,
                timeout_seconds=self._provider_timeout_seconds,
            )
            quote = self._make_quote(
                instrument_id,
                price,
                getattr(self._provider, "source_name", "provider"),
            )
        except Exception as provider_error:
            if self._last_known_good_adapter is not None:
                stored_quote = self._last_known_good_adapter.load_quote(instrument_id)
                if stored_quote is not None:
                    self._put_cached(stored_quote)
                    return stored_quote
            if instrument_id not in {"005930", "000660"}:
                raise MarketQuoteError(
                    f"Provider lookup failed for {instrument_id}"
                ) from provider_error
            try:
                price = self._local_adapter.latest_close(instrument_id)
                quote = self._make_quote(instrument_id, price, "local_repository")
            except Exception as local_error:
                raise MarketQuoteError(
                    f"Provider and local lookup failed for {instrument_id}"
                ) from local_error

        if self._last_known_good_adapter is not None:
            try:
                self._last_known_good_adapter.save_quote(quote)
            except Exception as persistence_error:
                raise MarketQuoteError(
                    f"Unable to persist last-known-good quote for {instrument_id}"
                ) from persistence_error
        self._put_cached(quote)
        return quote

    def clear_cache(self) -> None:
        with self._lock:
            self._cache.clear()

    def _get_cached(self, instrument_id: str) -> InternalQuote | None:
        current = self._clock()
        with self._lock:
            entry = self._cache.get(instrument_id)
            if entry is None:
                return None
            if current >= entry.expires_at:
                self._cache.pop(instrument_id, None)
                return None
            return entry.quote

    def _put_cached(self, quote: InternalQuote) -> None:
        entry = _CacheEntry(
            quote=quote,
            expires_at=self._clock() + self._cache_ttl_seconds,
        )
        with self._lock:
            self._cache[quote.instrument_id] = entry

    def _make_quote(self, instrument_id: str, price: float, source: str) -> InternalQuote:
        numeric_price = float(price)
        if numeric_price <= 0:
            raise MarketQuoteError(f"Invalid price for {instrument_id}")
        return InternalQuote(
            instrument_id=instrument_id,
            price=numeric_price,
            source=source,
            fetched_at=self._now(),
        )
