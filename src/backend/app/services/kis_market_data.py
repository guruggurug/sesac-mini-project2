from __future__ import annotations

from threading import Lock
from time import monotonic
from typing import Callable, Protocol

import httpx

from app.services.market_quotes import MarketQuoteError


class HttpClient(Protocol):
    def post(self, url: str, **kwargs): ...
    def get(self, url: str, **kwargs): ...


class KISMarketDataProvider:
    """KIS REST adapter for the two stocks and two representative indices."""

    source_name = "kis"
    STOCKS = {"005930", "000660"}
    INDEX_CODES = {"KOSPI": "0001", "KOSDAQ": "1001"}
    STOCK_PATH = "/uapi/domestic-stock/v1/quotations/inquire-price"
    INDEX_PATH = "/uapi/domestic-stock/v1/quotations/inquire-index-price"
    TOKEN_PATH = "/oauth2/tokenP"

    def __init__(
        self,
        *,
        app_key: str,
        app_secret: str,
        base_url: str = "https://openapi.koreainvestment.com:9443",
        client: HttpClient | None = None,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if not app_key or not app_secret:
            raise ValueError("KIS app key and app secret are required")
        self._app_key = app_key
        self._app_secret = app_secret
        self._base_url = base_url.rstrip("/")
        self._client = client or httpx.Client()
        self._clock = clock
        self._access_token: str | None = None
        self._token_expires_at = 0.0
        self._token_lock = Lock()

    def fetch_price(self, instrument_id: str, timeout_seconds: float) -> float:
        token = self._get_access_token(timeout_seconds)
        path, tr_id, params, price_field = self._request_spec(instrument_id)
        response = self._client.get(
            f"{self._base_url}{path}",
            headers={
                "authorization": f"Bearer {token}",
                "appkey": self._app_key,
                "appsecret": self._app_secret,
                "tr_id": tr_id,
                "custtype": "P",
            },
            params=params,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("rt_cd") != "0":
            raise MarketQuoteError(
                f"KIS quote request failed for {instrument_id}: "
                f"{payload.get('msg_cd', 'UNKNOWN')}"
            )

        output = payload.get("output")
        if not isinstance(output, dict):
            raise MarketQuoteError(f"KIS quote output is missing for {instrument_id}")
        try:
            price = float(output[price_field])
        except (KeyError, TypeError, ValueError) as error:
            raise MarketQuoteError(
                f"KIS quote price is invalid for {instrument_id}"
            ) from error
        if price <= 0:
            raise MarketQuoteError(f"KIS quote price is invalid for {instrument_id}")
        return price

    def _get_access_token(self, timeout_seconds: float) -> str:
        current = self._clock()
        if self._access_token and current < self._token_expires_at:
            return self._access_token

        with self._token_lock:
            current = self._clock()
            if self._access_token and current < self._token_expires_at:
                return self._access_token

            response = self._client.post(
                f"{self._base_url}{self.TOKEN_PATH}",
                headers={"Content-Type": "application/json"},
                json={
                    "grant_type": "client_credentials",
                    "appkey": self._app_key,
                    "appsecret": self._app_secret,
                },
                timeout=timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            token = payload.get("access_token")
            if not token:
                raise MarketQuoteError("KIS access token response is invalid")

            try:
                expires_in = max(float(payload.get("expires_in", 3600)), 1.0)
            except (TypeError, ValueError):
                expires_in = 3600.0
            safety_margin = min(60.0, expires_in * 0.1)
            self._access_token = str(token)
            self._token_expires_at = current + expires_in - safety_margin
            return self._access_token

    def _request_spec(self, instrument_id: str):
        if instrument_id in self.STOCKS:
            return (
                self.STOCK_PATH,
                "FHKST01010100",
                {
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_INPUT_ISCD": instrument_id,
                },
                "stck_prpr",
            )
        index_code = self.INDEX_CODES.get(instrument_id)
        if index_code:
            return (
                self.INDEX_PATH,
                "FHPUP02100000",
                {
                    "FID_COND_MRKT_DIV_CODE": "U",
                    "FID_INPUT_ISCD": index_code,
                },
                "bstp_nmix_prpr",
            )
        raise ValueError(f"Unsupported KIS instrument_id: {instrument_id}")
