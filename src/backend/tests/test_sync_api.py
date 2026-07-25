from datetime import datetime
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

from fastapi import FastAPI
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, FormatChecker
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.routes.sync as sync_route
from app.repositories.runtime_state_repository import RuntimeStateRepository
from app.services.issue_sync_workflow import IssueSyncWorkflowResult
from app.services.sync_coordinator import (
    IssueSyncCoordinator,
    UnavailableIssueSyncWorkflow,
)
from app.services.sync_status import SyncStatusService


SEOUL = ZoneInfo("Asia/Seoul")
NOW = datetime(2026, 7, 25, 11, 0, tzinfo=SEOUL)
ROOT = Path(__file__).resolve().parents[3]


class SuccessfulWorkflow:
    async def run(self, report_stage):
        report_stage("normalizing")
        report_stage("validating")
        report_stage("publishing")
        return IssueSyncWorkflowResult(
            status="success",
            collected_items=4,
            snapshot_updated=False,
            published_snapshot_version=None,
            published_at=None,
            candidate_items=3,
            validated_items=2,
            rejected_items=1,
            published_items=0,
            recalculation_triggered=False,
            recalculation_status="not_required",
            recalculated_at=None,
        )


def make_client(tmp_path, workflow=None):
    repository = RuntimeStateRepository(tmp_path / "runtime.db")
    ids = iter(
        [
            "SYNC-20260725-first",
            "SYNC-20260725-second",
            "SYNC-20260725-third",
        ]
    )
    coordinator = IssueSyncCoordinator(
        repository,
        workflow or SuccessfulWorkflow(),
        now=lambda: NOW,
        sync_id_factory=lambda: next(ids),
        owner_token_factory=lambda: "owner",
    )
    status_service = SyncStatusService(
        repository,
        schedule_hour=4,
        schedule_minute=0,
        now=lambda: NOW,
    )
    sync_route.runtime_state_repository = repository
    sync_route.issue_sync_coordinator = coordinator
    sync_route.sync_status_service = status_service
    app = FastAPI()
    app.include_router(sync_route.router)
    return TestClient(app), repository


def test_manual_sync_returns_queued_then_persists_terminal_status(tmp_path):
    client, _ = make_client(tmp_path)

    queued = client.post(
        "/sync/issues",
        json={
            "requested_by": "user",
            "reason": "manual_refresh",
            "client_request_id": "request-001",
        },
    )
    completed = client.get("/sync/status", params={"sync_id": queued.json()["sync_id"]})

    assert queued.status_code == 202
    assert queued.json()["status"] == "queued"
    assert queued.json()["stage"] == "queued"
    assert completed.status_code == 200
    assert completed.json()["status"] == "success"
    assert completed.json()["collected_items"] == 4
    assert completed.json()["validated_items"] == 2
    assert completed.json()["manual_refresh_cooldown_seconds"] == 600

    schema = json.loads(
        (ROOT / "schemas/api/sync-status-response.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    ).validate(completed.json())


def test_client_request_id_reuses_run_before_cooldown(tmp_path):
    client, _ = make_client(tmp_path)
    payload = {
        "requested_by": "user",
        "reason": "manual_refresh",
        "client_request_id": "same-request",
    }

    first = client.post("/sync/issues", json=payload)
    reused = client.post("/sync/issues", json=payload)

    assert first.status_code == 202
    assert reused.status_code == 200
    assert reused.json()["sync_id"] == first.json()["sync_id"]
    assert reused.json()["is_existing_run"] is True


def test_completed_manual_run_enforces_ten_minute_cooldown(tmp_path):
    client, _ = make_client(tmp_path)
    client.post(
        "/sync/issues",
        json={
            "requested_by": "user",
            "reason": "manual_refresh",
            "client_request_id": "first-request",
        },
    )

    response = client.post(
        "/sync/issues",
        json={
            "requested_by": "user",
            "reason": "manual_refresh",
            "client_request_id": "second-request",
        },
    )

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "600"
    assert response.json()["error_code"] == "SYNC_COOLDOWN_ACTIVE"
    assert response.json()["retry_after_seconds"] == 600


def test_unconfigured_workflow_reports_failure_and_retains_previous_data(tmp_path):
    client, _ = make_client(tmp_path, UnavailableIssueSyncWorkflow())

    queued = client.post(
        "/sync/issues",
        json={
            "requested_by": "user",
            "reason": "manual_refresh",
            "client_request_id": "failure-request",
        },
    )
    status = client.get("/sync/status", params={"sync_id": queued.json()["sync_id"]})

    assert status.json()["status"] == "failed"
    assert status.json()["failure_stage"] == "collecting"
    assert status.json()["data_status"] == "fallback"
    assert status.json()["previous_result_retained"] is True
    assert "외부 이슈 수집 설정" in status.json()["message"]


def test_status_returns_404_when_no_history_exists(tmp_path):
    client, _ = make_client(tmp_path)

    response = client.get("/sync/status")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "SYNC_NOT_FOUND"
