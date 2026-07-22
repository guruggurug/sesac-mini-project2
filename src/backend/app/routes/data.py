from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["Data"])

@router.post("/data/refresh")
def refresh_data():
    """
    External collection is owned by BE-RT-03 and is not implemented yet.

    Never return a false success: until collection, validation, atomic
    publication, and locking are connected, this endpoint is unavailable.
    """
    raise HTTPException(
        status_code=501,
        detail={
            "code": "ISSUE_SYNC_NOT_IMPLEMENTED",
            "message": "일일 공시·뉴스 수집 및 원자적 발행 경로가 아직 구현되지 않았습니다.",
        },
    )
