from enum import Enum
from pydantic import BaseModel

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
