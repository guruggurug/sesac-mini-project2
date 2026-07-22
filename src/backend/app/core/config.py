import os

from dotenv import load_dotenv

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

ENV_FILE_PATH = os.path.join(BASE_DIR, ".env")


def load_project_environment(env_file_path: str = ENV_FILE_PATH) -> bool:
    """Load local secrets without overriding deployment environment values."""
    return load_dotenv(dotenv_path=env_file_path, override=False)


def resolve_project_path(path: str) -> str:
    """Resolve relative runtime paths from the repository root, not the shell cwd."""
    return path if os.path.isabs(path) else os.path.join(BASE_DIR, path)


load_project_environment()

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
DART_API_KEY = os.getenv("DART_API_KEY", "")
DART_BASE_URL = os.getenv(
    "DART_BASE_URL",
    "https://opendart.fss.or.kr/api",
)
DART_TIMEOUT_SECONDS = float(os.getenv("DART_TIMEOUT_SECONDS", "5"))
DART_MAX_ATTEMPTS = int(os.getenv("DART_MAX_ATTEMPTS", "3"))
DART_RETRY_BACKOFF_SECONDS = float(
    os.getenv("DART_RETRY_BACKOFF_SECONDS", "0.25")
)
ISSUE_RUNTIME_DATA_DIR = resolve_project_path(
    os.getenv("ISSUE_RUNTIME_DATA_DIR", "data/runtime/issues")
)
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
KIS_BASE_URL = os.getenv(
    "KIS_BASE_URL",
    "https://openapi.koreainvestment.com:9443",
)
RUNTIME_STATE_DB_PATH = resolve_project_path(
    os.getenv("RUNTIME_STATE_DB_PATH", "data/runtime/state.db")
)
ENABLE_ISSUE_SCHEDULER = os.getenv(
    "ENABLE_ISSUE_SCHEDULER", "false"
).lower() == "true"
ISSUE_SYNC_HOUR_KST = int(os.getenv("ISSUE_SYNC_HOUR_KST", "4"))
ISSUE_SYNC_MINUTE_KST = int(os.getenv("ISSUE_SYNC_MINUTE_KST", "0"))
