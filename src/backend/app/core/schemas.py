from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

class PurchaseReason(str, Enum):
    price_or_recommendation = "price_or_recommendation"
    news_and_industry = "news_and_industry"
    value_and_risk_analysis = "value_and_risk_analysis"

class KnowledgeStage(str, Enum):
    beginner = "beginner"
    information_seeker = "information_seeker"
    value_beginner = "value_beginner"

class RebalancingProfile(str, Enum):
    strategy_preserving = "strategy_preserving"
    balanced_adjustment = "balanced_adjustment"
    risk_priority_adjustment = "risk_priority_adjustment"

class TurnoverLevel(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"

class AnalysisSettings(BaseModel):
    purchase_reason: PurchaseReason
    knowledge_stage: KnowledgeStage
    rebalancing_profile: RebalancingProfile
    turnover_level: TurnoverLevel
    turnover_weight: float
    downside_weight: float
    esg_weight: float
    profile_selection_method: str = "user_selected"
    settings_version: str = "v3.0"


class PortfolioHolding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticker: Literal["005930", "000660"]
    quantity: float = Field(gt=0)
    average_price: float = Field(gt=0)


class PortfolioSummaryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    holdings: list[PortfolioHolding] = Field(min_length=1, max_length=2)

    @model_validator(mode="after")
    def reject_duplicate_tickers(self):
        tickers = [holding.ticker for holding in self.holdings]
        if len(tickers) != len(set(tickers)):
            raise ValueError("같은 종목을 중복 입력할 수 없습니다.")
        return self


class PortfolioPosition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticker: Literal["005930", "000660"]
    stock_name: Literal["삼성전자", "SK하이닉스"]
    quantity: float = Field(gt=0)
    average_price: float = Field(gt=0)
    current_price: float = Field(gt=0)
    purchase_value: float = Field(ge=0)
    market_value: float = Field(ge=0)
    unrealized_profit_loss: float
    return_rate: float
    current_weight: float = Field(ge=0, le=1)


class PortfolioSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    positions: list[PortfolioPosition] = Field(min_length=1, max_length=2)
    total_purchase_value: float = Field(ge=0)
    total_market_value: float = Field(ge=0)
    total_unrealized_profit_loss: float
    total_return_rate: float
    prices_as_of: datetime
    price_status: Literal["live", "cached", "fallback"]
    data_status: Literal["sample", "validated", "fallback"]
    generated_at: datetime
    warnings: list[str]


class MarketQuoteItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instrument_id: Literal["KOSPI", "KOSDAQ", "005930", "000660"]
    instrument_type: Literal["index", "equity"]
    name: str
    current_value: float = Field(gt=0)
    previous_close: float = Field(gt=0)
    change: float
    change_rate: float
    unit: Literal["points", "KRW"]
    market_status: Literal["open", "closed", "delayed", "unavailable"]
    price_status: Literal["live", "cached", "fallback"]
    as_of: datetime
    source: str
    source_url: str
    is_stale: bool


class MarketQuotesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quotes: list[MarketQuoteItem] = Field(min_length=4, max_length=4)
    polling_enabled: bool
    refresh_interval_seconds: int | None
    data_status: Literal["sample", "validated", "fallback"]
    generated_at: datetime
    warnings: list[str]


class SyncIssuesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requested_by: Literal["user"]
    reason: Literal["manual_refresh"]
    client_request_id: str | None = Field(
        default=None,
        min_length=8,
        max_length=100,
        pattern=r"^[A-Za-z0-9._-]+$",
    )


class SyncFailedSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    message: str


class SyncStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sync_id: str
    sync_type: Literal["scheduled", "manual"]
    status: Literal["queued", "running", "success", "partial_success", "failed"]
    stage: Literal[
        "queued",
        "collecting",
        "normalizing",
        "validating",
        "publishing",
        "recalculating",
        "completed",
    ]
    is_existing_run: bool
    requested_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    last_success_at: datetime | None
    next_scheduled_at: datetime
    manual_refresh_cooldown_seconds: Literal[600] = 600
    manual_refresh_available_at: datetime | None
    collected_items: int = Field(ge=0)
    candidate_items: int = Field(ge=0)
    validated_items: int = Field(ge=0)
    rejected_items: int = Field(ge=0)
    published_items: int = Field(ge=0)
    new_items: int = Field(ge=0)
    updated_items: int = Field(ge=0)
    snapshot_updated: bool
    published_snapshot_version: str | None
    published_at: datetime | None
    recalculation_triggered: bool
    recalculation_status: Literal[
        "not_requested", "queued", "running", "success", "failed"
    ]
    recalculated_at: datetime | None
    failure_stage: Literal[
        "collecting",
        "normalizing",
        "validating",
        "publishing",
        "recalculating",
    ] | None
    failed_sources: list[SyncFailedSource]
    previous_result_retained: bool
    data_status: Literal["sample", "validated", "fallback"]
    message: str
    warnings: list[str]


class SyncCooldownResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error_code: Literal["SYNC_COOLDOWN_ACTIVE"]
    message: str
    retry_after_seconds: int = Field(ge=1, le=600)
    next_allowed_at: datetime
