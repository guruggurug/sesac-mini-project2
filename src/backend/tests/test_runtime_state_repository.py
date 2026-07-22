from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.repositories.runtime_state_repository import RuntimeStateRepository


NOW = datetime(2026, 7, 22, 9, 0, tzinfo=timezone.utc)


def test_last_known_good_quote_survives_repository_recreation(tmp_path):
    database = tmp_path / "runtime.db"
    first = RuntimeStateRepository(database)
    first.save_market_quote(
        instrument_id="KOSPI",
        price=3210.55,
        source="kis",
        as_of=NOW,
        stored_at=NOW + timedelta(seconds=1),
    )

    stored = RuntimeStateRepository(database).load_market_quote("KOSPI")

    assert stored is not None
    assert stored.price == 3210.55
    assert stored.source == "kis"
    assert stored.as_of == NOW


def test_last_known_good_upsert_replaces_the_previous_value(tmp_path):
    repository = RuntimeStateRepository(tmp_path / "runtime.db")
    repository.save_market_quote(
        instrument_id="005930", price=80000, source="kis", as_of=NOW
    )
    repository.save_market_quote(
        instrument_id="005930",
        price=81000,
        source="kis",
        as_of=NOW + timedelta(seconds=10),
    )

    assert repository.load_market_quote("005930").price == 81000


def test_only_one_sync_lock_can_be_acquired_across_repository_instances(tmp_path):
    database = tmp_path / "runtime.db"
    first = RuntimeStateRepository(database)
    second = RuntimeStateRepository(database)

    acquired = first.acquire_sync_lock(
        sync_id="sync-1", sync_type="manual", owner_token="owner-1", now=NOW
    )
    reused = second.acquire_sync_lock(
        sync_id="sync-2", sync_type="scheduled", owner_token="owner-2", now=NOW
    )

    assert acquired.acquired is True
    assert reused.acquired is False
    assert reused.sync_id == "sync-1"
    assert second.get_sync_run("sync-2") is None


def test_wrong_owner_cannot_start_or_complete_sync(tmp_path):
    repository = RuntimeStateRepository(tmp_path / "runtime.db")
    repository.acquire_sync_lock(
        sync_id="sync-1", sync_type="manual", owner_token="owner-1", now=NOW
    )

    with pytest.raises(RuntimeError, match="ownership"):
        repository.mark_sync_running(
            sync_id="sync-1", owner_token="owner-2", now=NOW
        )
    with pytest.raises(RuntimeError, match="ownership"):
        repository.complete_sync(
            sync_id="sync-1",
            owner_token="owner-2",
            status="failed",
            now=NOW,
        )


def test_terminal_sync_releases_lock_for_the_next_run(tmp_path):
    repository = RuntimeStateRepository(tmp_path / "runtime.db")
    repository.acquire_sync_lock(
        sync_id="sync-1", sync_type="manual", owner_token="owner-1", now=NOW
    )
    repository.mark_sync_running(
        sync_id="sync-1", owner_token="owner-1", now=NOW + timedelta(seconds=1)
    )
    repository.heartbeat_sync(
        sync_id="sync-1",
        owner_token="owner-1",
        stage="validating",
        now=NOW + timedelta(seconds=2),
    )
    repository.complete_sync(
        sync_id="sync-1",
        owner_token="owner-1",
        status="success",
        now=NOW + timedelta(seconds=3),
    )

    next_run = repository.acquire_sync_lock(
        sync_id="sync-2",
        sync_type="scheduled",
        owner_token="owner-2",
        now=NOW + timedelta(seconds=4),
    )

    assert next_run.acquired is True
    completed = repository.get_sync_run("sync-1")
    assert completed["status"] == "success"
    assert completed["stage"] == "completed"


def test_restart_recovery_fails_active_run_and_releases_lock(tmp_path):
    database = tmp_path / "runtime.db"
    before_restart = RuntimeStateRepository(database)
    before_restart.acquire_sync_lock(
        sync_id="sync-1", sync_type="manual", owner_token="owner-1", now=NOW
    )
    before_restart.mark_sync_running(
        sync_id="sync-1", owner_token="owner-1", now=NOW
    )

    after_restart = RuntimeStateRepository(database)
    assert after_restart.recover_interrupted_syncs(NOW + timedelta(minutes=1)) == 1
    recovered = after_restart.get_sync_run("sync-1")
    assert recovered["status"] == "failed"
    assert recovered["error_code"] == "SERVER_RESTART_INTERRUPTED"

    next_run = after_restart.acquire_sync_lock(
        sync_id="sync-2",
        sync_type="scheduled",
        owner_token="owner-2",
        now=NOW + timedelta(minutes=1),
    )
    assert next_run.acquired is True


def test_daily_schedule_claim_survives_repository_recreation(tmp_path):
    database = tmp_path / "runtime.db"
    first = RuntimeStateRepository(database)
    assert first.claim_daily_schedule(
        schedule_key="daily-issues", schedule_date=NOW.date(), now=NOW
    ) is True

    second = RuntimeStateRepository(database)
    assert second.claim_daily_schedule(
        schedule_key="daily-issues", schedule_date=NOW.date(), now=NOW
    ) is False
