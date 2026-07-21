from fastapi.templating import Jinja2Templates
from app.core.config import FRONTEND_TEMPLATES_DIR

# 공통 config를 기준으로 Jinja2 templates 설정
templates = Jinja2Templates(directory=FRONTEND_TEMPLATES_DIR)
