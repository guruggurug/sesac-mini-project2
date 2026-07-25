from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable
from zoneinfo import ZoneInfo

from app.core.schemas import SyncFailedSource, SyncStatusResponse
from app.repositories.runtime_state_repository import RuntimeStateRepository


SEOUL = ZoneInfo("Asia/Seoul")
COOLDOWN_SECONDS = 600


class SyncStatusService:
    def __init__(
        self,
        repository: RuntimeStateRepository,
        *,
        schedule_hour: int,
        schedule_minute: int,
        now: Callable[[], datetime] = lambda: datetime.now(SEOUL),
    ) -> None:
        self._repository = repository
        self._schedule_hour = schedule_hour
        self._schedule_minute = schedule_minute
        self._now = now

    def get_run(
        self, sync_id: str | None = None, *, is_existing_run: bool = False
    ) -> SyncStatusResponse | None:
        run = (
            self._repository.get_sync_run(sync_id)
            if sync_id
            else self._repository.get_latest_sync_run()
        )
        if run is None:
            return None
        return self.build(run, is_existing_run=is_existing_run)

    def build(
        self, run: dict, *, is_existing_run: bool = False
    ) -> SyncStatusResponse:
        result = run.get("result") or {}
        status = run["status"]
        error_code = run.get("error_code")
        failure_stage = self._failure_stage(error_code) if status == "failed" else None
        recalculation_triggered = bool(result.get("recalculation_triggered", False))
        recalculation_status = {
            "completed": "success",
            "not_required": "not_requested",
        }.get(result.get("recalculation_status"), "not_requested")
        if failure_stage == "recalculating":
            recalculation_triggered = True
            recalculation_status = "failed"

        latest_success = self._repository.get_latest_successful_sync()
        manual_available_at = self._manual_available_at(run)
        previous_retained = status in {"failed", "partial_success"}
        data_status = "fallback" if previous_retained else "validated"
        failed_sources = (
            [
                SyncFailedSource(
                    source_id="issue-sync",
                    message=error_code or "ISSUE_SYNC_WORKFLOW_FAILED",
                )
            ]
            if status == "failed"
            else []
        )

        return SyncStatusResponse(
            sync_id=run["sync_id"],
            sync_type=run["sync_type"],
            status=status,
            stage=run["stage"],
            is_existing_run=is_existing_run,
            requested_at=self._parse(run["created_at"]),
            started_at=self._parse_optional(run.get("started_at")),
            completed_at=self._parse_optional(run.get("completed_at")),
            last_success_at=(
                self._parse_optional(latest_success.get("completed_at"))
                if latest_success
                else None
            ),
            next_scheduled_at=self._next_scheduled_at(),
            manual_refresh_available_at=manual_available_at,
            collected_items=int(result.get("collected_items", 0)),
            candidate_items=int(result.get("candidate_items", 0)),
            validated_items=int(result.get("validated_items", 0)),
            rejected_items=int(result.get("rejected_items", 0)),
            published_items=int(result.get("published_items", 0)),
            new_items=int(result.get("new_items", 0)),
            updated_items=int(result.get("updated_items", 0)),
            snapshot_updated=bool(result.get("snapshot_updated", False)),
            published_snapshot_version=result.get("published_snapshot_version"),
            published_at=self._parse_optional(result.get("published_at")),
            recalculation_triggered=recalculation_triggered,
            recalculation_status=recalculation_status,
            recalculated_at=self._parse_optional(result.get("recalculated_at")),
            failure_stage=failure_stage,
            failed_sources=failed_sources,
            previous_result_retained=previous_retained,
            data_status=data_status,
            message=self._message(status, error_code, result),
            warnings=(
                ["기존 검증 이슈와 이전 계산 결과를 계속 표시합니다."]
                if previous_retained
                else []
            ),
        )

    def cooldown(self) -> tuple[int, datetime] | None:
        latest = self._repository.get_latest_completed_manual_sync()
        if latest is None or not latest.get("completed_at"):
            return None
        next_allowed = self._parse(latest["completed_at"]) + timedelta(
            seconds=COOLDOWN_SECONDS
        )
        remaining = int((next_allowed - self._current()).total_seconds())
        if remaining <= 0:
            return None
        return min(remaining + 1, COOLDOWN_SECONDS), next_allowed

    def _manual_available_at(self, run: dict) -> datetime | None:
        if run["sync_type"] == "manual":
            base = run.get("completed_at") or run["created_at"]
            return self._parse(base) + timedelta(seconds=COOLDOWN_SECONDS)
        cooldown = self.cooldown()
        return cooldown[1] if cooldown else None

    def _next_scheduled_at(self) -> datetime:
        current = self._current()
        candidate = current.replace(
            hour=self._schedule_hour,
            minute=self._schedule_minute,
            second=0,
            microsecond=0,
        )
        if candidate <= current:
            candidate += timedelta(days=1)
        return candidate

    def _current(self) -> datetime:
        current = self._now()
        if current.tzinfo is None or current.utcoffset() is None:
            raise ValueError("sync status clock must include timezone")
        return current.astimezone(SEOUL)

    @staticmethod
    def _parse(value: str) -> datetime:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("stored sync timestamp must include timezone")
        return parsed

    @classmethod
    def _parse_optional(cls, value: str | None) -> datetime | None:
        return cls._parse(value) if value else None

    @staticmethod
    def _failure_stage(error_code: str | None) -> str:
        code = (error_code or "").upper()
        if "RECALCUL" in code:
            return "recalculating"
        if "PUBLISH" in code or "SNAPSHOT" in code:
            return "publishing"
        if "VALIDAT" in code:
            return "validating"
        if "NORMAL" in code:
            return "normalizing"
        return "collecting"

    @staticmethod
    def _message(status: str, error_code: str | None, result: dict) -> str:
        if status == "queued":
            return "이슈 동기화 요청이 대기열에 등록되었습니다."
        if status == "running":
            return "공시·뉴스·ESG 이슈를 확인하고 있습니다."
        if status == "success":
            if result.get("snapshot_updated"):
                return "검증된 최신 이슈 스냅샷을 발행했습니다."
            return "새로 반영할 검증 이슈가 없습니다."
        if status == "partial_success":
            return "일부 단계가 실패해 이전 검증 결과를 유지합니다."
        if error_code == "ISSUE_SYNC_WORKFLOW_NOT_CONFIGURED":
            return "외부 이슈 수집 설정이 없어 새로고침을 실행할 수 없습니다."
        return "이슈 동기화에 실패해 이전 검증 결과를 유지합니다."
