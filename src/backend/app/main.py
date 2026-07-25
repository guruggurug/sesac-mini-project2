import os
import sys
from contextlib import asynccontextmanager

# Ensure repository root is in sys.path so 'src' and 'app' packages resolve in all environments
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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import ENABLE_ISSUE_SCHEDULER, FRONTEND_STATIC_DIR
from app.core.runtime import daily_issue_scheduler, recover_runtime_state_after_restart
from app.core.exceptions import CSVValidationError, csv_validation_exception_handler
from app.routes.health import router as health_router
from app.routes.portfolio import router as portfolio_router
from app.routes.risk import router as risk_router
from app.routes.issues import router as issues_router
from app.routes.data import router as data_router
from app.routes.ui import router as ui_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    recover_runtime_state_after_restart()
    if ENABLE_ISSUE_SCHEDULER:
        await daily_issue_scheduler.start()
    try:
        yield
    finally:
        if ENABLE_ISSUE_SCHEDULER:
            await daily_issue_scheduler.stop()


app = FastAPI(
    title="Chip Buddy API",
    description="삼성전자와 SK하이닉스 투자 위험 분석 및 포트폴리오 최적화 API MVP",
    version="0.1.0",
    lifespan=lifespan,
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
app.include_router(ui_router)
app.include_router(health_router)
app.include_router(portfolio_router)  # GET / 와 POST /portfolio/optimize 포함
app.include_router(risk_router)
app.include_router(issues_router)
app.include_router(data_router)
