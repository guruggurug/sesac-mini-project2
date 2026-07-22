import os

# 현재 파일 위치: src/backend/app/core/config.py
# 5 depth 상위로 이동하여 프로젝트 루트 경로 계산
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
        )
    )
)

FRONTEND_STATIC_DIR = os.path.join(BASE_DIR, "src", "frontend", "static")
FRONTEND_TEMPLATES_DIR = os.path.join(BASE_DIR, "src", "frontend", "templates")

# Portfolio optimization default weights and turnover profile weights
DEFAULT_DOWNSIDE_WEIGHT = 0.7
DEFAULT_ESG_WEIGHT = 0.3

TURNOVER_WEIGHTS = {
    "strategy_preserving": 0.20,
    "balanced_adjustment": 0.10,
    "risk_priority_adjustment": 0.02,
}

# Internal market-data settings. Public realtime API contracts remain pending.
MARKET_QUOTE_CACHE_TTL_SECONDS = float(os.getenv("MARKET_QUOTE_CACHE_TTL_SECONDS", "15"))
MARKET_QUOTE_TIMEOUT_SECONDS = float(os.getenv("MARKET_QUOTE_TIMEOUT_SECONDS", "5"))
KIS_APP_KEY = os.getenv("KIS_APP_KEY", "")
KIS_APP_SECRET = os.getenv("KIS_APP_SECRET", "")
KIS_BASE_URL = os.getenv(
    "KIS_BASE_URL",
    "https://openapi.koreainvestment.com:9443",
)
RUNTIME_STATE_DB_PATH = os.getenv(
    "RUNTIME_STATE_DB_PATH",
    os.path.join(BASE_DIR, "data", "runtime", "state.db"),
)
