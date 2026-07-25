from fastapi import APIRouter, BackgroundTasks, HTTPException, Response
from fastapi.responses import JSONResponse

from app.core.runtime import (
    issue_sync_coordinator,
    runtime_state_repository,
    sync_status_service,
)
from app.core.schemas import (
    SyncCooldownResponse,
    SyncIssuesRequest,
    SyncStatusResponse,
)


router = APIRouter(tags=["Issue Sync"])


@router.post(
    "/sync/issues",
    response_model=SyncStatusResponse,
    responses={429: {"model": SyncCooldownResponse}},
)
async def request_issue_sync(
    payload: SyncIssuesRequest,
    background_tasks: BackgroundTasks,
    response: Response,
):
    if payload.client_request_id:
        prior = runtime_state_repository.get_sync_run_by_client_request_id(
            payload.client_request_id
        )
        if prior is not None:
            response.status_code = 200
            return sync_status_service.build(prior, is_existing_run=True)

    active = runtime_state_repository.get_latest_sync_run()
    if active and active["status"] in {"queued", "running"}:
        response.status_code = 200
        return sync_status_service.build(active, is_existing_run=True)

    cooldown = sync_status_service.cooldown()
    if cooldown is not None:
        retry_after, next_allowed = cooldown
        body = SyncCooldownResponse(
            error_code="SYNC_COOLDOWN_ACTIVE",
            message="수동 새로고침은 완료 후 10분에 한 번 실행할 수 있습니다.",
            retry_after_seconds=retry_after,
            next_allowed_at=next_allowed,
        )
        return JSONResponse(
            status_code=429,
            headers={"Retry-After": str(retry_after)},
            content=body.model_dump(mode="json"),
        )

    queued = issue_sync_coordinator.queue(
        "manual",
        client_request_id=payload.client_request_id,
    )
    if queued.acquired:
        background_tasks.add_task(issue_sync_coordinator.run_queued, queued)
        response.status_code = 202
    else:
        response.status_code = 200
    run = runtime_state_repository.get_sync_run(queued.sync_id)
    if run is None:
        raise HTTPException(status_code=500, detail="동기화 상태를 저장하지 못했습니다.")
    return sync_status_service.build(
        run,
        is_existing_run=not queued.acquired,
    )


@router.get("/sync/status", response_model=SyncStatusResponse)
def get_issue_sync_status(sync_id: str | None = None):
    status = sync_status_service.get_run(sync_id)
    if status is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "SYNC_NOT_FOUND",
                "message": "조회할 이슈 동기화 기록이 없습니다.",
            },
        )
    return status
