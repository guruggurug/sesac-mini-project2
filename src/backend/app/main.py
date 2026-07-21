from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import FRONTEND_STATIC_DIR
from app.core.exceptions import CSVValidationError, csv_validation_exception_handler
from app.routes.health import router as health_router
from app.routes.portfolio import router as portfolio_router
from app.routes.risk import router as risk_router
from app.routes.issues import router as issues_router
from app.routes.data import router as data_router

app = FastAPI(
    title="Chip Buddy API",
    description="삼성전자와 SK하이닉스 투자 위험 분석 및 포트폴리오 최적화 API MVP",
    version="0.1.0"
)

# 세션 미들웨어 설정 (암호화 쿠키 세션)
app.add_middleware(
    SessionMiddleware,
    secret_key="chip-buddy-secret-key-super-secure-mvp-12345",
    session_cookie="chip_buddy_session"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 커스텀 예외 핸들러 등록
app.add_exception_handler(CSVValidationError, csv_validation_exception_handler)

# 정적 파일 마운트 (절대 경로 적용)
app.mount("/static", StaticFiles(directory=FRONTEND_STATIC_DIR), name="static")

# 라우터 등록
app.include_router(health_router)
app.include_router(portfolio_router)  # GET / 와 POST /portfolio/optimize 포함
app.include_router(risk_router)
app.include_router(issues_router)
app.include_router(data_router)
