from fastapi import APIRouter

router = APIRouter(tags=["Data"])

@router.post("/data/refresh")
def refresh_data():
    """
    원시(raw) 또는 후보(candidate) 데이터 갱신 (Mock)
    """
    return {
        "status": "success",
        "message": "Data refresh triggered successfully (Mock mode)",
        "data_status": "sample"
    }
