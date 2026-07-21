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
