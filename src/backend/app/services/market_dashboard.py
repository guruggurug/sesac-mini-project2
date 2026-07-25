from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

from app.core.schemas import MarketQuoteItem, MarketQuotesResponse
from app.repositories.price_repository import PriceRepository
from app.services.market_quotes import MarketQuoteError, MarketQuoteService


KST = ZoneInfo("Asia/Seoul")
INSTRUMENTS = ("KOSPI", "KOSDAQ", "005930", "000660")
INSTRUMENT_META = {
    "KOSPI": ("index", "코스피", "points"),
    "KOSDAQ": ("index", "코스닥", "points"),
    "005930": ("equity", "삼성전자", "KRW"),
    "000660": ("equity", "SK하이닉스", "KRW"),
}
LOCAL_SOURCE_URL = "https://github.com/FinanceDataReader/FinanceDataReader"
KIS_SOURCE_URL = "https://apiportal.koreainvestment.com/"


class MarketDashboardService:
    def __init__(
        self,
        quote_service: MarketQuoteService,
        *,
        price_repository: PriceRepository | None = None,
        refresh_interval_seconds: int = 15,
        now=lambda: datetime.now(KST),
    ) -> None:
        if not 10 <= refresh_interval_seconds <= 30:
            raise ValueError("refresh_interval_seconds must be between 10 and 30")
        self._quote_service = quote_service
        self._price_repository = price_repository or PriceRepository()
        self._refresh_interval_seconds = refresh_interval_seconds
        self._now = now

    def get_quotes(self) -> MarketQuotesResponse:
        generated_at = self._now().astimezone(KST)
        market_open = self._is_market_open(generated_at)
        local_previous_closes = self._stock_previous_closes()
        items: list[MarketQuoteItem] = []
        warnings: list[str] = []

        for instrument_id in INSTRUMENTS:
            quote = self._quote_service.get_quote(instrument_id)
            previous_close = quote.previous_close
            if previous_close is None:
                previous_close = local_previous_closes.get(instrument_id)
            if previous_close is None:
                raise MarketQuoteError(
                    f"No trustworthy previous close available for {instrument_id}"
                )

            is_fallback = (
                quote.source == "local_repository"
                or quote.source.startswith("last_known_good:")
            )
            price_status = (
                "fallback"
                if is_fallback
                else ("live" if market_open else "cached")
            )
            if is_fallback:
                warnings.append(
                    f"{instrument_id}는 마지막 정상 또는 로컬 종가를 표시합니다."
                )

            change = quote.price - previous_close
            instrument_type, name, unit = INSTRUMENT_META[instrument_id]
            items.append(
                MarketQuoteItem(
                    instrument_id=instrument_id,
                    instrument_type=instrument_type,
                    name=name,
                    current_value=quote.price,
                    previous_close=previous_close,
                    change=change,
                    change_rate=change / previous_close,
                    unit=unit,
                    market_status=(
                        "closed"
                        if not market_open
                        else ("delayed" if is_fallback else "open")
                    ),
                    price_status=price_status,
                    as_of=quote.fetched_at,
                    source=quote.source,
                    source_url=quote.source_url
                    or (
                        LOCAL_SOURCE_URL
                        if is_fallback
                        else KIS_SOURCE_URL
                    ),
                    is_stale=is_fallback,
                )
            )

        return MarketQuotesResponse(
            quotes=items,
            polling_enabled=market_open,
            refresh_interval_seconds=(
                self._refresh_interval_seconds if market_open else None
            ),
            data_status=(
                "fallback"
                if any(item.price_status == "fallback" for item in items)
                else "validated"
            ),
            generated_at=generated_at,
            warnings=warnings,
        )

    def _stock_previous_closes(self) -> dict[str, float]:
        frame, _, _ = self._price_repository.load_data_as_df()
        result: dict[str, float] = {}
        tickers = frame["ticker"].astype(str).str.zfill(6)
        for ticker in ("005930", "000660"):
            rows = frame[tickers == ticker]
            if len(rows) >= 2:
                result[ticker] = float(rows.iloc[-2]["close"])
            elif len(rows) == 1:
                result[ticker] = float(rows.iloc[-1]["close"])
        return result

    @staticmethod
    def _is_market_open(current: datetime) -> bool:
        current_kst = current.astimezone(KST)
        return (
            current_kst.weekday() < 5
            and time(9, 0) <= current_kst.time() <= time(15, 30)
        )
