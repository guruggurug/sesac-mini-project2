from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Callable, Literal, Protocol
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.repositories.runtime_state_repository import RuntimeStateRepository
from app.services.issue_sync_workflow import IssueSyncWorkflowResult


class IssueSyncWorkflow(Protocol):
    async def run(
        self, report_stage: Callable[[str], None]
    ) -> IssueSyncWorkflowResult | Literal["success", "partial_success"]:
        """Collect, validate, publish, and return deterministic internal metadata."""


class SyncWorkflowUnavailable(RuntimeError):
    code = "ISSUE_SYNC_WORKFLOW_NOT_CONFIGURED"


class UnavailableIssueSyncWorkflow:
    async def run(self, report_stage: Callable[[str], None]) -> IssueSyncWorkflowResult:
        raise SyncWorkflowUnavailable(
            "Issue collection and atomic publication workflow is not configured"
        )


@dataclass(frozen=True)
class SyncExecutionResult:
    sync_id: str
    acquired: bool
    status: str
    error_code: str | None = None
    workflow_result: IssueSyncWorkflowResult | None = None


@dataclass(frozen=True)
class QueuedSync:
    sync_id: str
    acquired: bool
    status: str
    owner_token: str | None = None


class IssueSyncCoordinator:
    """Runs manual and scheduled issue sync through one durable-lock boundary."""

    def __init__(
        self,
        repository: RuntimeStateRepository,
        workflow: IssueSyncWorkflow,
        *,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        sync_id_factory: Callable[[], str] | None = None,
        owner_token_factory: Callable[[], str] = lambda: str(uuid4()),
    ) -> None:
        self._repository = repository
        self._workflow = workflow
        self._now = now
        self._sync_id_factory = sync_id_factory
        self._owner_token_factory = owner_token_factory

    def queue(
        self,
        sync_type: Literal["scheduled", "manual"],
        *,
        client_request_id: str | None = None,
    ) -> QueuedSync:
        if client_request_id:
            existing = self._repository.get_sync_run_by_client_request_id(
                client_request_id
            )
            if existing is not None:
                return QueuedSync(
                    sync_id=existing["sync_id"],
                    acquired=False,
                    status=existing["status"],
                )

        sync_id = (
            self._sync_id_factory()
            if self._sync_id_factory is not None
            else self._default_sync_id()
        )
        owner_token = self._owner_token_factory()
        lock = self._repository.acquire_sync_lock(
            sync_id=sync_id,
            sync_type=sync_type,
            owner_token=owner_token,
            client_request_id=client_request_id,
            now=self._now(),
        )
        if not lock.acquired:
            existing = self._repository.get_sync_run(lock.sync_id)
            return QueuedSync(
                sync_id=lock.sync_id,
                acquired=False,
                status=existing["status"] if existing else "running",
            )
        return QueuedSync(sync_id, True, "queued", owner_token)

    async def run_queued(self, queued: QueuedSync) -> SyncExecutionResult:
        if not queued.acquired or queued.owner_token is None:
            return SyncExecutionResult(
                queued.sync_id,
                False,
                queued.status,
            )

        self._repository.mark_sync_running(
            sync_id=queued.sync_id,
            owner_token=queued.owner_token,
            now=self._now(),
        )

        def report_stage(stage: str) -> None:
            self._repository.heartbeat_sync(
                sync_id=queued.sync_id,
                owner_token=queued.owner_token,
                stage=stage,
                now=self._now(),
            )

        try:
            outcome = await self._workflow.run(report_stage)
            workflow_result = (
                outcome if isinstance(outcome, IssueSyncWorkflowResult) else None
            )
            status = outcome.status if workflow_result is not None else outcome
            if status not in {"success", "partial_success"}:
                raise RuntimeError("workflow returned an invalid terminal status")
        except Exception as error:
            error_code = getattr(error, "code", "ISSUE_SYNC_WORKFLOW_FAILED")
            self._repository.complete_sync(
                sync_id=queued.sync_id,
                owner_token=queued.owner_token,
                status="failed",
                error_code=str(error_code),
                now=self._now(),
            )
            return SyncExecutionResult(
                queued.sync_id,
                True,
                "failed",
                str(error_code),
            )

        self._repository.complete_sync(
            sync_id=queued.sync_id,
            owner_token=queued.owner_token,
            status=status,
            result=asdict(workflow_result) if workflow_result is not None else None,
            now=self._now(),
        )
        return SyncExecutionResult(
            queued.sync_id,
            True,
            status,
            workflow_result=workflow_result,
        )

    async def execute(
        self, sync_type: Literal["scheduled", "manual"]
    ) -> SyncExecutionResult:
        return await self.run_queued(self.queue(sync_type))

    def _default_sync_id(self) -> str:
        current = self._now()
        if current.tzinfo is None or current.utcoffset() is None:
            raise ValueError("sync clock must return a timezone-aware datetime")
        date_key = current.astimezone(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d")
        return f"SYNC-{date_key}-{uuid4().hex[:12]}"
