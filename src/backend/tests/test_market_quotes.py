from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import sys
from threading import Event, Lock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.market_quotes import (
    MarketQuoteError,
    MarketQuoteService,
    UnavailableMarketDataProvider,
)
from app.utils.realtime_price import get_realtime_price


class StubProvider:
    def __init__(self, prices=None, error=None):
        self.prices = prices or {}
        self.error = error
        self.calls = []

    def fetch_price(self, provider_symbol, timeout_seconds):
        self.calls.append((provider_symbol, timeout_seconds))
        if self.error:
            raise self.error
        return self.prices[provider_symbol]


class StubLocalAdapter:
    def __init__(self, prices=None, error=None):
        self.prices = prices or {}
        self.error = error
        self.calls = []

    def latest_close(self, instrument_id):
        self.calls.append(instrument_id)
        if self.error:
            raise self.error
        return self.prices[instrument_id]


class StubLastKnownGoodAdapter:
    def __init__(self, quotes=None):
        self.quotes = quotes or {}
        self.saved = []

    def save_quote(self, quote):
        self.saved.append(quote)
        self.quotes[quote.instrument_id] = quote

    def load_quote(self, instrument_id):
        return self.quotes.get(instrument_id)


def make_service(provider, local, clock, last_known_good=None):
    return MarketQuoteService(
        provider=provider,
        local_adapter=local,
        last_known_good_adapter=last_known_good,
        cache_ttl_seconds=10,
        provider_timeout_seconds=2.5,
        clock=lambda: clock[0],
        now=lambda: datetime(2026, 7, 22, tzinfo=timezone.utc),
    )


def test_provider_instrument_timeout_and_compatibility_wrapper():
    clock = [100.0]
    provider = StubProvider(prices={"005930": 81234.0})
    service = make_service(provider, StubLocalAdapter(), clock)

    assert get_realtime_price("005930", service=service) == 81234.0
    assert provider.calls == [("005930", 2.5)]


def test_mvp_default_provider_never_calls_an_external_service():
    provider = UnavailableMarketDataProvider()

    with pytest.raises(MarketQuoteError, match="No external market-data provider"):
        provider.fetch_price("005930", 3.0)


def test_cache_avoids_provider_call_until_ttl_expires():
    clock = [100.0]
    provider = StubProvider(prices={"KOSPI": 3300.0})
    service = make_service(provider, StubLocalAdapter(), clock)

    first = service.get_quote("KOSPI")
    clock[0] = 109.9
    second = service.get_quote("KOSPI")

    assert second is first
    assert len(provider.calls) == 1

    clock[0] = 110.0
    service.get_quote("KOSPI")
    assert len(provider.calls) == 2


def test_snapshot_read_never_calls_provider_and_uses_last_known_good():
    from app.services.market_quotes import InternalQuote

    stored = InternalQuote(
        instrument_id="KOSPI",
        price=3300.0,
        source="last_known_good:kis",
        fetched_at=datetime(2026, 7, 22, tzinfo=timezone.utc),
        previous_close=3290.0,
    )
    provider = StubProvider(error=AssertionError("provider must not run"))
    service = make_service(
        provider,
        StubLocalAdapter(),
        [100.0],
        StubLastKnownGoodAdapter({"KOSPI": stored}),
    )

    assert service.get_snapshot_quote("KOSPI") == stored
    assert provider.calls == []


def test_expired_memory_quote_is_returned_as_stale_without_refreshing():
    clock = [100.0]
    provider = StubProvider(prices={"KOSPI": 3300.0})
    service = make_service(provider, StubLocalAdapter(), clock)
    service.get_quote("KOSPI")

    clock[0] = 111.0
    snapshot = service.get_snapshot_quote("KOSPI")

    assert snapshot.price == 3300.0
    assert snapshot.source == "last_known_good:provider"
    assert len(provider.calls) == 1


def test_explicit_refresh_bypasses_unexpired_cache():
    clock = [100.0]
    provider = StubProvider(prices={"KOSPI": 3300.0})
    service = make_service(provider, StubLocalAdapter(), clock)

    service.get_quote("KOSPI")
    service.refresh_quote("KOSPI")

    assert len(provider.calls) == 2


def test_concurrent_identical_lookups_share_one_provider_request():
    class BlockingProvider:
        def __init__(self):
            self.started = Event()
            self.release = Event()
            self.call_lock = Lock()
            self.call_count = 0

        def fetch_price(self, instrument_id, timeout_seconds):
            with self.call_lock:
                self.call_count += 1
            self.started.set()
            assert self.release.wait(timeout=2)
            return 81234.0

    provider = BlockingProvider()
    service = make_service(provider, StubLocalAdapter(), [100.0])

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(service.get_quote, "005930")
            for _ in range(8)
        ]
        assert provider.started.wait(timeout=2)
        provider.release.set()
        quotes = [future.result(timeout=2) for future in futures]

    assert provider.call_count == 1
    assert {quote.price for quote in quotes} == {81234.0}


def test_stock_provider_failure_uses_local_repository_adapter():
    clock = [100.0]
    provider = StubProvider(error=TimeoutError("provider timed out"))
    local = StubLocalAdapter(prices={"000660": 291000.0})
    service = make_service(provider, local, clock)

    quote = service.get_quote("000660")

    assert quote.price == 291000.0
    assert quote.source == "local_repository"
    assert local.calls == ["000660"]


def test_successful_provider_quote_is_saved_as_last_known_good():
    clock = [100.0]
    last_known_good = StubLastKnownGoodAdapter()
    service = make_service(
        StubProvider(prices={"KOSPI": 3300.0}),
        StubLocalAdapter(),
        clock,
        last_known_good,
    )

    quote = service.get_quote("KOSPI")

    assert quote.price == 3300.0
    assert last_known_good.saved == [quote]


def test_index_provider_failure_uses_last_known_good_before_error():
    from app.services.market_quotes import InternalQuote

    stored = InternalQuote(
        instrument_id="KOSDAQ",
        price=850.25,
        source="last_known_good:kis",
        fetched_at=datetime(2026, 7, 22, tzinfo=timezone.utc),
    )
    service = make_service(
        StubProvider(error=TimeoutError("provider timed out")),
        StubLocalAdapter(),
        [100.0],
        StubLastKnownGoodAdapter({"KOSDAQ": stored}),
    )

    assert service.get_quote("KOSDAQ") == stored


def test_index_failure_does_not_invent_a_fallback_value():
    service = make_service(
        StubProvider(error=TimeoutError("provider timed out")),
        StubLocalAdapter(prices={"KOSPI": 1.0}),
        [100.0],
    )

    with pytest.raises(MarketQuoteError, match="Provider lookup failed"):
        service.get_quote("KOSPI")


def test_stock_failure_does_not_return_a_hard_coded_price():
    service = make_service(
        StubProvider(error=TimeoutError("provider timed out")),
        StubLocalAdapter(error=LookupError("no local data")),
        [100.0],
    )

    with pytest.raises(MarketQuoteError, match="Provider and local lookup failed"):
        service.get_quote("005930")


def test_unknown_instrument_is_rejected_before_provider_call():
    provider = StubProvider()
    service = make_service(provider, StubLocalAdapter(), [100.0])

    with pytest.raises(ValueError, match="Unsupported instrument_id"):
        service.get_quote("035420")
    assert provider.calls == []
