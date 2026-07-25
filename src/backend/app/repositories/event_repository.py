from pathlib import Path

from app.core.config import BASE_DIR, ISSUE_RUNTIME_DATA_DIR
from app.utils.csv_validator import validate_csv_file, validate_data_a_bundle
from app.core.exceptions import CSVValidationError
from app.services.issue_snapshot_publisher import (
    SnapshotPointerError,
    read_active_snapshot,
)

class EventRepository:
    """
    ESG 및 준법 사건 데이터를 로딩하고 관리하는 레포지토리
    """
    def __init__(
        self,
        base_dir: str | Path = BASE_DIR,
        runtime_root: str | Path = ISSUE_RUNTIME_DATA_DIR,
    ):
        self.base_dir = Path(base_dir)
        self.runtime_root = Path(runtime_root)
        self.processed_path = str(
            self.base_dir / "data" / "processed" / "events.csv"
        )
        self.sample_path = str(
            self.base_dir / "data" / "sample" / "events.sample.csv"
        )

    def load_data(self) -> tuple[list[dict], str, str | None]:
        """
        사건 데이터를 로드합니다.
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
            active.root / "data" / "processed" / "events.csv"
            if active
            else None
        )
        if active_processed_path and active_processed_path.exists():
            try:
                data = validate_data_a_bundle(str(active.root))["events"]
                return data, "validated", None
            except CSVValidationError as e:
                warning = f"processed 사건 데이터 자동 검증 실패로 샘플 데이터로 폴백했습니다. 에러: {e.message}"
                try:
                    data = validate_csv_file(self.sample_path, "event")
                    return data, "fallback", warning
                except Exception:
                    raise CSVValidationError(
                        code="EVENT_LOAD_FAILURE",
                        message="processed 및 sample 사건 데이터를 모두 로드하는 데 실패했습니다."
                    )
        
        # 2. No runtime pointer: use the checked-in bootstrap snapshot.
        if pointer_warning is None and Path(self.processed_path).exists():
            try:
                return validate_csv_file(self.processed_path, "event"), "validated", None
            except CSVValidationError as e:
                pointer_warning = (
                    "checked-in event bootstrap 자동 검증 실패: "
                    f"{e.message}"
                )

        # 3. processed 파일이 없거나 active pointer가 손상된 경우 sample 로딩
        try:
            data = validate_csv_file(self.sample_path, "event")
            if pointer_warning:
                return data, "fallback", pointer_warning
            return data, "sample", None
        except Exception as e:
            raise CSVValidationError(
                code="EVENT_LOAD_FAILURE",
                message=f"sample 사건 데이터 로드 실패: {str(e)}"
            )
            
    def get_model_ready_events(self, events: list[dict]) -> list[dict]:
        """
        자동 검증 규칙상 모델에 반영 가능한 사건만 필터링합니다.
        공식 출처가 확인된 confirmed, resolved만 허용합니다.
        """
        model_ready_statuses = {"confirmed", "resolved"}
        return [
            evt for evt in events 
            if evt.get("status") in model_ready_statuses
            and evt.get("authority_confirmed") is True
            and bool(evt.get("official_source_url"))
        ]
