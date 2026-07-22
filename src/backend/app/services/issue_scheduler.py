from __future__ import annotations

import asyncio
from datetime import datetime, time, timedelta
from typing import Callable
from zoneinfo import ZoneInfo

from app.repositories.runtime_state_repository import RuntimeStateRepository
from app.services.sync_coordinator import IssueSyncCoordinator, SyncExecutionResult


SEOUL = ZoneInfo("Asia/Seoul")


class DailyIssueScheduler:
    """Durable once-per-Seoul-day scheduler for the shared sync coordinator."""

    def __init__(
        self,
        repository: RuntimeStateRepository,
        coordinator: IssueSyncCoordinator,
        *,
        hour: int = 4,
        minute: int = 0,
        now: Callable[[], datetime] = lambda: datetime.now(SEOUL),
        schedule_key: str = "daily-issues",
    ) -> None:
        if not 0 <= hour <= 23 or not 0 <= minute <= 59:
            raise ValueError("invalid scheduler hour or minute")
        self._repository = repository
        self._coordinator = coordinator
        self._scheduled_time = time(hour, minute, tzinfo=SEOUL)
        self._now = now
        self._schedule_key = schedule_key
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task | None = None

    async def run_due_once(self) -> SyncExecutionResult | None:
        current = self._seoul_now()
        scheduled = datetime.combine(
            current.date(), self._scheduled_time
        )
        if current < scheduled:
            return None
        claimed = self._repository.claim_daily_schedule(
            schedule_key=self._schedule_key,
            schedule_date=current.date(),
            now=current,
        )
        if not claimed:
            return None
        return await self._coordinator.execute("scheduled")

    async def start(self) -> None:
        if self._task is None or self._task.done():
            self._stop_event.clear()
            self._task = asyncio.create_task(self.run_forever())

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task is not None:
            await self._task
            self._task = None

    async def run_forever(self) -> None:
        await self.run_due_once()
        while not self._stop_event.is_set():
            delay = max((self._next_run() - self._seoul_now()).total_seconds(), 0.0)
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=delay)
            except asyncio.TimeoutError:
                await self.run_due_once()

    def _next_run(self) -> datetime:
        current = self._seoul_now()
        candidate = datetime.combine(current.date(), self._scheduled_time)
        if candidate <= current:
            candidate += timedelta(days=1)
        return candidate

    def _seoul_now(self) -> datetime:
        current = self._now()
        if current.tzinfo is None or current.utcoffset() is None:
            raise ValueError("scheduler clock must return a timezone-aware datetime")
        return current.astimezone(SEOUL)
