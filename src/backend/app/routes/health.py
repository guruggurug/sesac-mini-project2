from fastapi import APIRouter

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    """
    서버 헬스 체크 API
    """
    return {"status": "ok", "message": "FastAPI server is running"}
