from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import json
from pathlib import Path
import sqlite3


ACTIVE_SYNC_STATUSES = {"queued", "running"}
TERMINAL_SYNC_STATUSES = {"success", "partial_success", "failed"}


@dataclass(frozen=True)
class StoredMarketQuote:
    instrument_id: str
    price: float
    source: str
    as_of: datetime
    stored_at: datetime


@dataclass(frozen=True)
class SyncLockResult:
    acquired: bool
    sync_id: str
    owner_token: str | None


@dataclass(frozen=True)
class StoredModelRecalculation:
    snapshot_version: str
    published_at: datetime
    model_version: str
    input_hash: str
    result: dict
    recalculated_at: datetime


class RuntimeStateRepository:
    """SQLite persistence for last-known-good quotes and the singleton sync lock."""

    def __init__(self, database_path: str | Path) -> None:
        self._database_path = Path(database_path)
        self._initialized = False

    def save_market_quote(
        self,
        *,
        instrument_id: str,
        price: float,
        source: str,
        as_of: datetime,
        stored_at: datetime | None = None,
    ) -> None:
        numeric_price = float(price)
        if numeric_price <= 0:
            raise ValueError("price must be positive")
        source_time = _require_aware(as_of, "as_of")
        saved_time = _require_aware(
            stored_at or datetime.now(timezone.utc),
            "stored_at",
        )
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO market_quote_lkg (
                    instrument_id, price, source, as_of, stored_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(instrument_id) DO UPDATE SET
                    price = excluded.price,
                    source = excluded.source,
                    as_of = excluded.as_of,
                    stored_at = excluded.stored_at
                """,
                (
                    instrument_id,
                    numeric_price,
                    source,
                    source_time.isoformat(),
                    saved_time.isoformat(),
                ),
            )

    def load_market_quote(self, instrument_id: str) -> StoredMarketQuote | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT instrument_id, price, source, as_of, stored_at
                FROM market_quote_lkg
                WHERE instrument_id = ?
                """,
                (instrument_id,),
            ).fetchone()
        if row is None:
            return None
        return StoredMarketQuote(
            instrument_id=row["instrument_id"],
            price=float(row["price"]),
            source=row["source"],
            as_of=datetime.fromisoformat(row["as_of"]),
            stored_at=datetime.fromisoformat(row["stored_at"]),
        )

    def save_model_recalculation(
        self,
        *,
        snapshot_version: str,
        published_at: datetime,
        model_version: str,
        input_hash: str,
        result: dict,
        recalculated_at: datetime | None = None,
    ) -> StoredModelRecalculation:
        if not snapshot_version.startswith("issues-"):
            raise ValueError("snapshot_version must identify an issue snapshot")
        published_time = _require_aware(published_at, "published_at")
        calculated_time = _require_aware(
            recalculated_at or datetime.now(timezone.utc),
            "recalculated_at",
        )
        payload = json.dumps(
            result,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO model_recalculations (
                    snapshot_version, published_at, model_version, input_hash,
                    result_json, recalculated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_version,
                    published_time.isoformat(),
                    model_version,
                    input_hash,
                    payload,
                    calculated_time.isoformat(),
                ),
            )
        stored = self.load_model_recalculation(
            snapshot_version=snapshot_version,
            model_version=model_version,
            input_hash=input_hash,
        )
        if stored is None:
            raise RuntimeError("model recalculation could not be persisted")
        return stored

    def load_model_recalculation(
        self,
        *,
        snapshot_version: str,
        model_version: str,
        input_hash: str,
    ) -> StoredModelRecalculation | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT snapshot_version, published_at, model_version, input_hash,
                       result_json, recalculated_at
                FROM model_recalculations
                WHERE snapshot_version = ? AND model_version = ? AND input_hash = ?
                """,
                (snapshot_version, model_version, input_hash),
            ).fetchone()
        return _stored_recalculation(row)

    def load_latest_model_recalculation(
        self, snapshot_version: str
    ) -> StoredModelRecalculation | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT snapshot_version, published_at, model_version, input_hash,
                       result_json, recalculated_at
                FROM model_recalculations
                WHERE snapshot_version = ?
                ORDER BY recalculated_at DESC, model_version DESC, input_hash DESC
                LIMIT 1
                """,
                (snapshot_version,),
            ).fetchone()
        return _stored_recalculation(row)

    def acquire_sync_lock(
        self,
        *,
        sync_id: str,
        sync_type: str,
        owner_token: str,
        now: datetime | None = None,
    ) -> SyncLockResult:
        if sync_type not in {"scheduled", "manual"}:
            raise ValueError("sync_type must be scheduled or manual")
        current = _require_aware(now or datetime.now(timezone.utc), "now")
        timestamp = current.isoformat()

        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            lock_row = connection.execute(
                "SELECT sync_id, owner_token FROM sync_lock WHERE lock_name = 'issues'"
            ).fetchone()
            if lock_row is not None:
                connection.commit()
                return SyncLockResult(
                    acquired=False,
                    sync_id=lock_row["sync_id"],
                    owner_token=lock_row["owner_token"],
                )

            connection.execute(
                """
                INSERT INTO sync_runs (
                    sync_id, sync_type, status, stage, created_at,
                    started_at, completed_at, heartbeat_at, error_code
                ) VALUES (?, ?, 'queued', 'queued', ?, NULL, NULL, ?, NULL)
                """,
                (sync_id, sync_type, timestamp, timestamp),
            )
            connection.execute(
                """
                INSERT INTO sync_lock (
                    lock_name, sync_id, owner_token, acquired_at, heartbeat_at
                ) VALUES ('issues', ?, ?, ?, ?)
                """,
                (sync_id, owner_token, timestamp, timestamp),
            )
            connection.commit()
            return SyncLockResult(True, sync_id, owner_token)
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def mark_sync_running(
        self,
        *,
        sync_id: str,
        owner_token: str,
        now: datetime | None = None,
    ) -> None:
        timestamp = _require_aware(now or datetime.now(timezone.utc), "now").isoformat()
        with self._connect() as connection:
            updated = connection.execute(
                """
                UPDATE sync_runs
                SET status = 'running', stage = 'collecting',
                    started_at = COALESCE(started_at, ?), heartbeat_at = ?
                WHERE sync_id = ? AND status = 'queued'
                  AND EXISTS (
                      SELECT 1 FROM sync_lock
                      WHERE lock_name = 'issues' AND sync_id = ? AND owner_token = ?
                  )
                """,
                (timestamp, timestamp, sync_id, sync_id, owner_token),
            ).rowcount
            if updated != 1:
                raise RuntimeError("sync lock ownership or queued state is invalid")
            connection.execute(
                """
                UPDATE sync_lock SET heartbeat_at = ?
                WHERE lock_name = 'issues' AND sync_id = ? AND owner_token = ?
                """,
                (timestamp, sync_id, owner_token),
            )

    def heartbeat_sync(
        self,
        *,
        sync_id: str,
        owner_token: str,
        stage: str,
        now: datetime | None = None,
    ) -> None:
        timestamp = _require_aware(now or datetime.now(timezone.utc), "now").isoformat()
        with self._connect() as connection:
            updated = connection.execute(
                """
                UPDATE sync_runs SET stage = ?, heartbeat_at = ?
                WHERE sync_id = ? AND status = 'running'
                  AND EXISTS (
                      SELECT 1 FROM sync_lock
                      WHERE lock_name = 'issues' AND sync_id = ? AND owner_token = ?
                  )
                """,
                (stage, timestamp, sync_id, sync_id, owner_token),
            ).rowcount
            if updated != 1:
                raise RuntimeError("sync lock ownership or running state is invalid")
            connection.execute(
                """
                UPDATE sync_lock SET heartbeat_at = ?
                WHERE lock_name = 'issues' AND sync_id = ? AND owner_token = ?
                """,
                (timestamp, sync_id, owner_token),
            )

    def complete_sync(
        self,
        *,
        sync_id: str,
        owner_token: str,
        status: str,
        error_code: str | None = None,
        now: datetime | None = None,
    ) -> None:
        if status not in TERMINAL_SYNC_STATUSES:
            raise ValueError("status must be a terminal sync status")
        timestamp = _require_aware(now or datetime.now(timezone.utc), "now").isoformat()
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            lock_row = connection.execute(
                """
                SELECT 1 FROM sync_lock
                WHERE lock_name = 'issues' AND sync_id = ? AND owner_token = ?
                """,
                (sync_id, owner_token),
            ).fetchone()
            if lock_row is None:
                raise RuntimeError("sync lock ownership is invalid")
            updated = connection.execute(
                """
                UPDATE sync_runs
                SET status = ?, stage = 'completed', completed_at = ?,
                    heartbeat_at = ?, error_code = ?
                WHERE sync_id = ? AND status IN ('queued', 'running')
                """,
                (status, timestamp, timestamp, error_code, sync_id),
            ).rowcount
            if updated != 1:
                raise RuntimeError("active sync state is invalid")
            connection.execute(
                "DELETE FROM sync_lock WHERE lock_name = 'issues'"
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def recover_interrupted_syncs(self, now: datetime | None = None) -> int:
        """Fail active jobs and release the durable lock during application startup."""
        timestamp = _require_aware(now or datetime.now(timezone.utc), "now").isoformat()
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            updated = connection.execute(
                """
                UPDATE sync_runs
                SET status = 'failed', stage = 'completed', completed_at = ?,
                    heartbeat_at = ?, error_code = 'SERVER_RESTART_INTERRUPTED'
                WHERE status IN ('queued', 'running')
                """,
                (timestamp, timestamp),
            ).rowcount
            connection.execute("DELETE FROM sync_lock WHERE lock_name = 'issues'")
            connection.commit()
            return updated
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get_sync_run(self, sync_id: str) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM sync_runs WHERE sync_id = ?",
                (sync_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def claim_daily_schedule(
        self,
        *,
        schedule_key: str,
        schedule_date: date,
        now: datetime | None = None,
    ) -> bool:
        """Atomically claim a scheduled execution date across processes."""
        timestamp = _require_aware(now or datetime.now(timezone.utc), "now").isoformat()
        with self._connect() as connection:
            inserted = connection.execute(
                """
                INSERT OR IGNORE INTO scheduler_claims (
                    schedule_key, schedule_date, claimed_at
                ) VALUES (?, ?, ?)
                """,
                (schedule_key, schedule_date.isoformat(), timestamp),
            ).rowcount
        return inserted == 1

    def _connect(self) -> sqlite3.Connection:
        self._ensure_initialized()
        connection = sqlite3.connect(self._database_path, timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._database_path, timeout=5.0)
        try:
            connection.executescript(
                """
                PRAGMA journal_mode = WAL;
                CREATE TABLE IF NOT EXISTS market_quote_lkg (
                    instrument_id TEXT PRIMARY KEY,
                    price REAL NOT NULL CHECK (price > 0),
                    source TEXT NOT NULL,
                    as_of TEXT NOT NULL,
                    stored_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sync_runs (
                    sync_id TEXT PRIMARY KEY,
                    sync_type TEXT NOT NULL CHECK (sync_type IN ('scheduled', 'manual')),
                    status TEXT NOT NULL CHECK (
                        status IN ('queued', 'running', 'success', 'partial_success', 'failed')
                    ),
                    stage TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    heartbeat_at TEXT NOT NULL,
                    error_code TEXT
                );
                CREATE TABLE IF NOT EXISTS sync_lock (
                    lock_name TEXT PRIMARY KEY CHECK (lock_name = 'issues'),
                    sync_id TEXT NOT NULL UNIQUE,
                    owner_token TEXT NOT NULL,
                    acquired_at TEXT NOT NULL,
                    heartbeat_at TEXT NOT NULL,
                    FOREIGN KEY (sync_id) REFERENCES sync_runs(sync_id)
                );
                CREATE TABLE IF NOT EXISTS scheduler_claims (
                    schedule_key TEXT NOT NULL,
                    schedule_date TEXT NOT NULL,
                    claimed_at TEXT NOT NULL,
                    PRIMARY KEY (schedule_key, schedule_date)
                );
                CREATE TABLE IF NOT EXISTS model_recalculations (
                    snapshot_version TEXT NOT NULL,
                    published_at TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    input_hash TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    recalculated_at TEXT NOT NULL,
                    PRIMARY KEY (snapshot_version, model_version, input_hash)
                );
                """
            )
            connection.commit()
            self._initialized = True
        finally:
            connection.close()


def _require_aware(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must include timezone information")
    return value


def _stored_recalculation(row: sqlite3.Row | None) -> StoredModelRecalculation | None:
    if row is None:
        return None
    return StoredModelRecalculation(
        snapshot_version=row["snapshot_version"],
        published_at=datetime.fromisoformat(row["published_at"]),
        model_version=row["model_version"],
        input_hash=row["input_hash"],
        result=json.loads(row["result_json"]),
        recalculated_at=datetime.fromisoformat(row["recalculated_at"]),
    )
