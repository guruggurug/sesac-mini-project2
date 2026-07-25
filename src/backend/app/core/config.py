import os
import secrets
import sys

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

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

ENV_FILE_PATH = os.path.join(BASE_DIR, ".env")


def load_project_environment(env_file_path: str = ENV_FILE_PATH) -> bool:
    """Load local secrets without overriding deployment environment values."""
    return load_dotenv(dotenv_path=env_file_path, override=False)


def resolve_project_path(path: str) -> str:
    """Resolve relative runtime paths from the repository root, not the shell cwd."""
    return path if os.path.isabs(path) else os.path.join(BASE_DIR, path)


load_project_environment()

APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
IS_RAILWAY = bool(os.getenv("RAILWAY_ENVIRONMENT_ID"))
IS_PRODUCTION = APP_ENV == "production" or IS_RAILWAY

FRONTEND_STATIC_DIR = os.path.join(BASE_DIR, "src", "frontend", "static")
FRONTEND_TEMPLATES_DIR = os.path.join(BASE_DIR, "src", "frontend", "templates")

_configured_session_secret = os.getenv("SESSION_SECRET_KEY", "").strip()
SESSION_SECRET_KEY = _configured_session_secret or secrets.token_urlsafe(48)
SESSION_SECRET_IS_EPHEMERAL = not bool(_configured_session_secret)
SESSION_COOKIE_HTTPS_ONLY = IS_PRODUCTION


def parse_origin_allowlist(raw_value: str) -> list[str]:
    return list(
        dict.fromkeys(
            origin.strip().rstrip("/")
            for origin in raw_value.split(",")
            if origin.strip()
        )
    )


_default_cors_origins = (
    ""
    if IS_PRODUCTION
    else "http://localhost:5173,http://127.0.0.1:5173"
)
CORS_ALLOWED_ORIGINS = parse_origin_allowlist(
    os.getenv("CORS_ALLOWED_ORIGINS", _default_cors_origins)
)

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
MARKET_REFRESH_INTERVAL_SECONDS = int(
    os.getenv("MARKET_REFRESH_INTERVAL_SECONDS", "15")
)
ENABLE_MARKET_REFRESH_ON_STARTUP = os.getenv(
    "ENABLE_MARKET_REFRESH_ON_STARTUP",
    "true" if os.getenv("RAILWAY_ENVIRONMENT_ID") else "false",
).lower() == "true"
KIS_APP_KEY = os.getenv("KIS_APP_KEY", "")
KIS_APP_SECRET = os.getenv("KIS_APP_SECRET", "")
KIS_MIN_REQUEST_INTERVAL_SECONDS = float(
    os.getenv("KIS_MIN_REQUEST_INTERVAL_SECONDS", "1.0")
)
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
