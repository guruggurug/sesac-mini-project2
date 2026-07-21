from fastapi import Request
from fastapi.responses import JSONResponse

class CSVValidationError(Exception):
    """
    CSV 스키마 검증 실패 시 발생하는 커스텀 예외
    """
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)

def csv_validation_exception_handler(request: Request, exc: CSVValidationError):
    """
    CSVValidationError에 대한 FastAPI 예외 핸들러
    """
    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "code": exc.code,
                "message": exc.message
            }
        }
    )
