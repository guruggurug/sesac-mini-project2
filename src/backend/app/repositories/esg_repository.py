import os
from app.core.config import BASE_DIR
from app.utils.csv_validator import validate_csv_file
from app.core.exceptions import CSVValidationError

class ESGRepository:
    """
    ESG indicators 데이터를 로딩하고 관리하는 레포지토리
    """
    def __init__(self):
        self.reviewed_path = os.path.join(BASE_DIR, "data", "reviewed", "esg_indicators.csv")
        self.sample_path = os.path.join(BASE_DIR, "data", "sample", "esg_indicators.sample.csv")

    def load_data(self) -> tuple[list[dict], str, str | None]:
        """
        ESG 데이터를 로드합니다.
        reviewed 데이터 로딩 시도 -> 실패 시 sample 데이터로 폴백.
        반환값: (데이터 리스트, data_status, warning_message)
        """
        # 1. reviewed 데이터 시도
        if os.path.exists(self.reviewed_path):
            try:
                data = validate_csv_file(self.reviewed_path, "esg")
                return data, "reviewed", None
            except CSVValidationError as e:
                # 검증 실패 시 sample로 폴백하고 경고 메시지 반환
                warning = f"reviewed ESG 데이터 검증 실패로 샘플 데이터로 폴백했습니다. 에러: {e.message}"
                try:
                    data = validate_csv_file(self.sample_path, "esg")
                    return data, "fallback", warning
                except Exception:
                    # 샘플 로드마저 실패하는 경우
                    raise CSVValidationError(
                        code="ESG_LOAD_FAILURE",
                        message="reviewed 및 sample ESG 데이터를 모두 로드하는 데 실패했습니다."
                    )
        
        # 2. reviewed 파일이 아예 없는 경우 sample로 로딩
        try:
            data = validate_csv_file(self.sample_path, "esg")
            return data, "sample", None
        except Exception as e:
            raise CSVValidationError(
                code="ESG_LOAD_FAILURE",
                message=f"sample ESG 데이터 로드 실패: {str(e)}"
            )
