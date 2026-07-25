from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Iterable
from zoneinfo import ZoneInfo

from app.core.schemas import PortfolioHolding, PortfolioSummaryResponse
from app.services.market_quotes import InternalQuote, MarketQuoteService


STOCK_NAMES = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
}
STATUS_RANK = {"live": 0, "cached": 1, "fallback": 2}
SEOUL = ZoneInfo("Asia/Seoul")


def _quote_status(quote: InternalQuote) -> str:
    if quote.source.startswith("last_known_good:"):
        return "fallback"
    if quote.source == "local_repository":
        return "fallback"
    return "live"


def calculate_portfolio_summary(
    holdings: Iterable[PortfolioHolding],
    quote_service: MarketQuoteService,
    *,
    source_data_status: str,
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> PortfolioSummaryResponse:
    holding_list = list(holdings)
    snapshot_lookup = getattr(
        quote_service,
        "get_snapshot_quote",
        quote_service.get_quote,
    )
    quotes = {
        holding.ticker: snapshot_lookup(holding.ticker)
        for holding in holding_list
    }

    raw_positions = []
    for holding in holding_list:
        quote = quotes[holding.ticker]
        purchase_value = holding.quantity * holding.average_price
        market_value = holding.quantity * quote.price
        unrealized_profit_loss = market_value - purchase_value
        raw_positions.append(
            {
                "ticker": holding.ticker,
                "stock_name": STOCK_NAMES[holding.ticker],
                "quantity": holding.quantity,
                "average_price": holding.average_price,
                "current_price": quote.price,
                "purchase_value": purchase_value,
                "market_value": market_value,
                "unrealized_profit_loss": unrealized_profit_loss,
                "return_rate": unrealized_profit_loss / purchase_value,
            }
        )

    total_purchase_value = sum(
        position["purchase_value"] for position in raw_positions
    )
    total_market_value = sum(position["market_value"] for position in raw_positions)
    total_unrealized_profit_loss = total_market_value - total_purchase_value

    positions = []
    assigned_weight = 0.0
    for index, position in enumerate(raw_positions):
        if index == len(raw_positions) - 1:
            current_weight = round(1.0 - assigned_weight, 6)
        else:
            current_weight = round(
                position["market_value"] / total_market_value,
                6,
            )
            assigned_weight += current_weight
        positions.append(
            {
                **position,
                "purchase_value": round(position["purchase_value"], 6),
                "market_value": round(position["market_value"], 6),
                "unrealized_profit_loss": round(
                    position["unrealized_profit_loss"],
                    6,
                ),
                "return_rate": round(position["return_rate"], 6),
                "current_weight": current_weight,
            }
        )

    quote_statuses = [_quote_status(quote) for quote in quotes.values()]
    price_status = max(quote_statuses, key=STATUS_RANK.__getitem__)
    data_status = (
        "fallback"
        if price_status == "fallback"
        else source_data_status
        if source_data_status in {"sample", "validated", "fallback"}
        else "fallback"
    )
    warnings = []
    if price_status == "fallback":
        warnings.append(
            "실시간 시세를 사용할 수 없어 마지막 검증 종가 또는 마지막 정상 가격으로 평가했습니다."
        )

    return PortfolioSummaryResponse(
        positions=positions,
        total_purchase_value=round(total_purchase_value, 6),
        total_market_value=round(total_market_value, 6),
        total_unrealized_profit_loss=round(total_unrealized_profit_loss, 6),
        total_return_rate=round(
            total_unrealized_profit_loss / total_purchase_value,
            6,
        ),
        prices_as_of=min(
            quote.fetched_at for quote in quotes.values()
        ).astimezone(SEOUL),
        price_status=price_status,
        data_status=data_status,
        generated_at=now().astimezone(SEOUL),
        warnings=warnings,
    )
