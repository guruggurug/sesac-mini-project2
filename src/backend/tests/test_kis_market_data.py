from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.kis_market_data import KISMarketDataProvider
from app.services.market_quotes import MarketQuoteError


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self.payload


class FakeClient:
    def __init__(self, quote_payloads):
        self.quote_payloads = list(quote_payloads)
        self.posts = []
        self.gets = []

    def post(self, url, **kwargs):
        self.posts.append((url, kwargs))
        return FakeResponse({"access_token": "test-token", "expires_in": 3600})

    def get(self, url, **kwargs):
        self.gets.append((url, kwargs))
        item = self.quote_payloads.pop(0)
        return item if isinstance(item, FakeResponse) else FakeResponse(item)


def make_provider(client, clock=None):
    return KISMarketDataProvider(
        app_key="test-app-key",
        app_secret="test-app-secret",
        base_url="https://kis.example.test/",
        client=client,
        clock=clock or (lambda: 100.0),
        sleeper=lambda _: None,
    )


def test_stock_quote_uses_official_kis_request_mapping_and_timeout():
    client = FakeClient(
        [{"rt_cd": "0", "output": {"stck_prpr": "81234", "stck_sdpr": "80000"}}]
    )
    provider = make_provider(client)

    assert provider.fetch_price("005930", 3.0) == 81234.0
    url, request = client.gets[0]
    assert url.endswith("/uapi/domestic-stock/v1/quotations/inquire-price")
    assert request["headers"]["tr_id"] == "FHKST01010100"
    assert request["headers"]["authorization"] == "Bearer test-token"
    assert request["params"] == {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": "005930",
    }
    assert request["timeout"] == 3.0


@pytest.mark.parametrize(
    ("instrument_id", "index_code"),
    [("KOSPI", "0001"), ("KOSDAQ", "1001")],
)
def test_index_quote_uses_official_kis_index_mapping(instrument_id, index_code):
    client = FakeClient(
        [
            {
                "rt_cd": "0",
                "output": {
                    "bstp_nmix_prpr": "3210.55",
                    "bstp_nmix_prdy_vrss": "12.43",
                    "prdy_vrss_sign": "2",
                },
            }
        ]
    )
    provider = make_provider(client)

    assert provider.fetch_price(instrument_id, 5.0) == 3210.55
    url, request = client.gets[0]
    assert url.endswith("/uapi/domestic-stock/v1/quotations/inquire-index-price")
    assert request["headers"]["tr_id"] == "FHPUP02100000"
    assert request["params"] == {
        "FID_COND_MRKT_DIV_CODE": "U",
        "FID_INPUT_ISCD": index_code,
    }


def test_index_previous_close_is_derived_from_signed_change():
    client = FakeClient(
        [
            {
                "rt_cd": "0",
                "output": {
                    "bstp_nmix_prpr": "800.00",
                    "bstp_nmix_prdy_vrss": "5.25",
                    "prdy_vrss_sign": "5",
                },
            }
        ]
    )
    provider = make_provider(client)

    quote = provider.fetch_quote("KOSDAQ", 5.0)

    assert quote.current_value == 800.0
    assert quote.previous_close == 805.25


def test_access_token_is_reused_before_expiry():
    client = FakeClient(
        [
            {"rt_cd": "0", "output": {"stck_prpr": "80000", "stck_sdpr": "79000"}},
            {"rt_cd": "0", "output": {"stck_prpr": "200000", "stck_sdpr": "198000"}},
        ]
    )
    provider = make_provider(client)

    provider.fetch_price("005930", 3.0)
    provider.fetch_price("000660", 3.0)

    assert len(client.posts) == 1
    assert len(client.gets) == 2


def test_failed_token_request_enters_cooldown():
    clock = [100.0]

    class FailingTokenClient:
        def __init__(self):
            self.posts = 0

        def post(self, url, **kwargs):
            self.posts += 1
            raise TimeoutError("token request timed out")

        def get(self, url, **kwargs):
            raise AssertionError("quote request must not run without a token")

    client = FailingTokenClient()
    provider = KISMarketDataProvider(
        app_key="test-app-key",
        app_secret="test-app-secret",
        client=client,
        clock=lambda: clock[0],
        token_failure_cooldown_seconds=15,
        sleeper=lambda _: None,
    )

    with pytest.raises(MarketQuoteError, match="access token request failed"):
        provider.fetch_price("KOSPI", 1.0)
    with pytest.raises(MarketQuoteError, match="cooling down"):
        provider.fetch_price("KOSDAQ", 1.0)
    assert client.posts == 1

    clock[0] = 115.0
    with pytest.raises(MarketQuoteError, match="access token request failed"):
        provider.fetch_price("KOSPI", 1.0)
    assert client.posts == 2


def test_kis_error_response_does_not_return_an_invented_price():
    client = FakeClient([{"rt_cd": "1", "msg_cd": "EGW00123", "output": {}}])
    provider = make_provider(client)

    with pytest.raises(MarketQuoteError, match="EGW00123"):
        provider.fetch_price("005930", 3.0)


def test_transient_server_error_is_retried_once():
    client = FakeClient(
        [
            FakeResponse({}, status_code=500),
            {
                "rt_cd": "0",
                "output": {"stck_prpr": "81234", "stck_sdpr": "80000"},
            },
        ]
    )
    provider = make_provider(client)

    assert provider.fetch_price("005930", 3.0) == 81234.0
    assert len(client.gets) == 2


def test_kis_credentials_are_required():
    with pytest.raises(ValueError, match="app key and app secret"):
        KISMarketDataProvider(app_key="", app_secret="")
