from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Literal, Protocol
from uuid import uuid4

from app.repositories.runtime_state_repository import RuntimeStateRepository


TerminalSuccessStatus = Literal["success", "partial_success"]


class IssueSyncWorkflow(Protocol):
    async def run(self, report_stage: Callable[[str], None]) -> TerminalSuccessStatus:
        """Collect, validate, publish, and return a non-failed terminal status."""


class SyncWorkflowUnavailable(RuntimeError):
    code = "ISSUE_SYNC_WORKFLOW_NOT_CONFIGURED"


class UnavailableIssueSyncWorkflow:
    async def run(self, report_stage: Callable[[str], None]) -> TerminalSuccessStatus:
        raise SyncWorkflowUnavailable(
            "Issue collection and atomic publication workflow is not configured"
        )


@dataclass(frozen=True)
class SyncExecutionResult:
    sync_id: str
    acquired: bool
    status: str
    error_code: str | None = None


class IssueSyncCoordinator:
    """Runs manual and scheduled issue sync through one durable-lock boundary."""

    def __init__(
        self,
        repository: RuntimeStateRepository,
        workflow: IssueSyncWorkflow,
        *,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        sync_id_factory: Callable[[], str] = lambda: f"sync-{uuid4()}",
        owner_token_factory: Callable[[], str] = lambda: str(uuid4()),
    ) -> None:
        self._repository = repository
        self._workflow = workflow
        self._now = now
        self._sync_id_factory = sync_id_factory
        self._owner_token_factory = owner_token_factory

    async def execute(self, sync_type: Literal["scheduled", "manual"]) -> SyncExecutionResult:
        sync_id = self._sync_id_factory()
        owner_token = self._owner_token_factory()
        lock = self._repository.acquire_sync_lock(
            sync_id=sync_id,
            sync_type=sync_type,
            owner_token=owner_token,
            now=self._now(),
        )
        if not lock.acquired:
            existing = self._repository.get_sync_run(lock.sync_id)
            return SyncExecutionResult(
                sync_id=lock.sync_id,
                acquired=False,
                status=existing["status"] if existing else "running",
            )

        self._repository.mark_sync_running(
            sync_id=sync_id,
            owner_token=owner_token,
            now=self._now(),
        )

        def report_stage(stage: str) -> None:
            self._repository.heartbeat_sync(
                sync_id=sync_id,
                owner_token=owner_token,
                stage=stage,
                now=self._now(),
            )

        try:
            status = await self._workflow.run(report_stage)
            if status not in {"success", "partial_success"}:
                raise RuntimeError("workflow returned an invalid terminal status")
        except Exception as error:
            error_code = getattr(error, "code", "ISSUE_SYNC_WORKFLOW_FAILED")
            self._repository.complete_sync(
                sync_id=sync_id,
                owner_token=owner_token,
                status="failed",
                error_code=str(error_code),
                now=self._now(),
            )
            return SyncExecutionResult(sync_id, True, "failed", str(error_code))

        self._repository.complete_sync(
            sync_id=sync_id,
            owner_token=owner_token,
            status=status,
            now=self._now(),
        )
        return SyncExecutionResult(sync_id, True, status)
