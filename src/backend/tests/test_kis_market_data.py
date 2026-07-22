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
        return FakeResponse(self.quote_payloads.pop(0))


def make_provider(client, clock=None):
    return KISMarketDataProvider(
        app_key="test-app-key",
        app_secret="test-app-secret",
        base_url="https://kis.example.test/",
        client=client,
        clock=clock or (lambda: 100.0),
    )


def test_stock_quote_uses_official_kis_request_mapping_and_timeout():
    client = FakeClient([{"rt_cd": "0", "output": {"stck_prpr": "81234"}}])
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
        [{"rt_cd": "0", "output": {"bstp_nmix_prpr": "3210.55"}}]
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


def test_access_token_is_reused_before_expiry():
    client = FakeClient(
        [
            {"rt_cd": "0", "output": {"stck_prpr": "80000"}},
            {"rt_cd": "0", "output": {"stck_prpr": "200000"}},
        ]
    )
    provider = make_provider(client)

    provider.fetch_price("005930", 3.0)
    provider.fetch_price("000660", 3.0)

    assert len(client.posts) == 1
    assert len(client.gets) == 2


def test_kis_error_response_does_not_return_an_invented_price():
    client = FakeClient([{"rt_cd": "1", "msg_cd": "EGW00123", "output": {}}])
    provider = make_provider(client)

    with pytest.raises(MarketQuoteError, match="EGW00123"):
        provider.fetch_price("005930", 3.0)


def test_kis_credentials_are_required():
    with pytest.raises(ValueError, match="app key and app secret"):
        KISMarketDataProvider(app_key="", app_secret="")
