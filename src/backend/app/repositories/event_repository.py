import os
from app.core.config import BASE_DIR
from app.utils.csv_validator import validate_csv_file
from app.core.exceptions import CSVValidationError

class EventRepository:
    """
    ESG 및 준법 사건 데이터를 로딩하고 관리하는 레포지토리
    """
    def __init__(self):
        self.reviewed_path = os.path.join(BASE_DIR, "data", "reviewed", "events.csv")
        self.sample_path = os.path.join(BASE_DIR, "data", "sample", "events.sample.csv")

    def load_data(self) -> tuple[list[dict], str, str | None]:
        """
        사건 데이터를 로드합니다.
        reviewed 데이터 로딩 시도 -> 실패 시 sample 데이터로 폴백.
        반환값: (데이터 리스트, data_status, warning_message)
        """
        # 1. reviewed 데이터 시도
        if os.path.exists(self.reviewed_path):
            try:
                data = validate_csv_file(self.reviewed_path, "event")
                return data, "reviewed", None
            except CSVValidationError as e:
                warning = f"reviewed 사건 데이터 검증 실패로 샘플 데이터로 폴백했습니다. 에러: {e.message}"
                try:
                    data = validate_csv_file(self.sample_path, "event")
                    return data, "fallback", warning
                except Exception:
                    raise CSVValidationError(
                        code="EVENT_LOAD_FAILURE",
                        message="reviewed 및 sample 사건 데이터를 모두 로드하는 데 실패했습니다."
                    )
        
        # 2. reviewed 파일이 없는 경우 sample 로딩
        try:
            data = validate_csv_file(self.sample_path, "event")
            return data, "sample", None
        except Exception as e:
            raise CSVValidationError(
                code="EVENT_LOAD_FAILURE",
                message=f"sample 사건 데이터 로드 실패: {str(e)}"
            )
            
    def get_model_ready_events(self, events: list[dict]) -> list[dict]:
        """
        모델 연산에 반영 가능한 사건들만 필터링 (confirmed, sanctioned, approved resolved)
        rumor와 reported는 필터링하여 제외시킵니다.
        """
        model_ready_statuses = {"confirmed", "sanctioned", "resolved"}
        return [
            evt for evt in events 
            if evt.get("status") in model_ready_statuses 
            and evt.get("review_status") == "approved"
        ]
