from pathlib import Path

from app.core.config import BASE_DIR, ISSUE_RUNTIME_DATA_DIR
from app.utils.csv_validator import validate_csv_file, validate_data_a_bundle
from app.core.exceptions import CSVValidationError
from app.services.issue_snapshot_publisher import (
    SnapshotPointerError,
    read_active_snapshot,
)

class ESGRepository:
    """
    ESG indicators 데이터를 로딩하고 관리하는 레포지토리
    """
    def __init__(
        self,
        base_dir: str | Path = BASE_DIR,
        runtime_root: str | Path = ISSUE_RUNTIME_DATA_DIR,
    ):
        self.base_dir = Path(base_dir)
        self.runtime_root = Path(runtime_root)
        self.processed_path = str(
            self.base_dir / "data" / "processed" / "esg_indicators.csv"
        )
        self.sample_path = str(
            self.base_dir / "data" / "sample" / "esg_indicators.sample.csv"
        )

    def load_data(self) -> tuple[list[dict], str, str | None]:
        """
        ESG 데이터를 로드합니다.
        자동 검증된 processed 데이터 로딩 시도 -> 실패 시 sample 데이터로 폴백.
        반환값: (데이터 리스트, data_status, warning_message)
        """
        # 1. 자동 검증된 processed 데이터 시도
        try:
            active = read_active_snapshot(self.runtime_root)
        except SnapshotPointerError as e:
            active = None
            pointer_warning = str(e)
        else:
            pointer_warning = None

        active_processed_path = (
            active.root / "data" / "processed" / "esg_indicators.csv"
            if active
            else None
        )
        if active_processed_path and active_processed_path.exists():
            try:
                data = validate_data_a_bundle(str(active.root))["esg"]
                return data, "validated", None
            except CSVValidationError as e:
                # 검증 실패 시 sample로 폴백하고 경고 메시지 반환
                warning = f"processed ESG 데이터 자동 검증 실패로 샘플 데이터로 폴백했습니다. 에러: {e.message}"
                try:
                    data = validate_csv_file(self.sample_path, "esg")
                    return data, "fallback", warning
                except Exception:
                    # 샘플 로드마저 실패하는 경우
                    raise CSVValidationError(
                        code="ESG_LOAD_FAILURE",
                        message="processed 및 sample ESG 데이터를 모두 로드하는 데 실패했습니다."
                    )
        
        # 2. No runtime pointer: use the checked-in bootstrap snapshot.
        if pointer_warning is None and Path(self.processed_path).exists():
            try:
                return validate_csv_file(self.processed_path, "esg"), "validated", None
            except CSVValidationError as e:
                pointer_warning = (
                    "checked-in ESG bootstrap 자동 검증 실패: "
                    f"{e.message}"
                )

        # 3. processed 파일이 아예 없거나 active pointer가 손상된 경우 sample로 로딩
        try:
            data = validate_csv_file(self.sample_path, "esg")
            if pointer_warning:
                return data, "fallback", pointer_warning
            return data, "sample", None
        except Exception as e:
            raise CSVValidationError(
                code="ESG_LOAD_FAILURE",
                message=f"sample ESG 데이터 로드 실패: {str(e)}"
            )
