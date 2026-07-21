import os
import pandas as pd
from app.core.config import BASE_DIR
from app.utils.csv_validator import validate_csv_file
from app.core.exceptions import CSVValidationError

class PriceRepository:
    """
    일별 주가 데이터를 로딩하고 관리하는 레포지토리
    """
    def __init__(self):
        self.reviewed_path = os.path.join(BASE_DIR, "data", "reviewed", "stock_prices.csv")
        self.sample_path = os.path.join(BASE_DIR, "data", "sample", "stock_prices.sample.csv")

    def load_data(self) -> tuple[list[dict], str, str | None]:
        """
        주가 데이터를 로드합니다.
        reviewed 데이터 로딩 시도 -> 실패 시 sample 데이터로 폴백.
        반환값: (데이터 리스트, data_status, warning_message)
        """
        # 1. reviewed 데이터 시도
        if os.path.exists(self.reviewed_path):
            try:
                data = validate_csv_file(self.reviewed_path, "price")
                return data, "reviewed", None
            except CSVValidationError as e:
                warning = f"reviewed 주가 데이터 검증 실패로 샘플 데이터로 폴백했습니다. 에러: {e.message}"
                try:
                    data = validate_csv_file(self.sample_path, "price")
                    return data, "fallback", warning
                except Exception:
                    raise CSVValidationError(
                        code="PRICE_LOAD_FAILURE",
                        message="reviewed 및 sample 주가 데이터를 모두 로드하는 데 실패했습니다."
                    )
        
        # 2. reviewed 파일이 없는 경우 sample 로딩
        try:
            data = validate_csv_file(self.sample_path, "price")
            return data, "sample", None
        except Exception as e:
            raise CSVValidationError(
                code="PRICE_LOAD_FAILURE",
                message=f"sample 주가 데이터 로드 실패: {str(e)}"
            )

    def load_data_as_df(self) -> tuple[pd.DataFrame, str, str | None]:
        """
        주가 데이터를 Pandas DataFrame으로 반환합니다.
        """
        data_list, data_status, warning = self.load_data()
        df = pd.DataFrame(data_list)
        
        # 날짜 타입 변환 및 인덱스 설정 등을 수행
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values(by=["ticker", "date"])
            
        return df, data_status, warning
