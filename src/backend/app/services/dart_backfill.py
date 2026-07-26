"""Paged Open DART range collection shared by backfill and daily sync."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable, Iterable

from app.services.dart_disclosures import (
    DART_COMPANIES,
    DartCollectionBatch,
    DartCollectionService,
    DartCompany,
)
from app.services.issue_bundle_normalizer import adapt_dart_batch
from app.services.issue_sync_workflow import IssueCollectionResult


DART_BACKFILL_START_DATE = date(2023, 7, 21)
DART_MAX_RANGE_DAYS = 90


@dataclass(frozen=True)
class DartCollectionWindow:
    begin_date: date
    end_date: date


def iter_dart_windows(
    begin_date: date,
    end_date: date,
    *,
    maximum_days: int = DART_MAX_RANGE_DAYS,
) -> Iterable[DartCollectionWindow]:
    """Yield inclusive, non-overlapping ranges accepted by Open DART."""
    if begin_date > end_date:
        raise ValueError("begin_date cannot be after end_date")
    if maximum_days < 1:
        raise ValueError("maximum_days must be positive")
    cursor = begin_date
    while cursor <= end_date:
        window_end = min(end_date, cursor + timedelta(days=maximum_days - 1))
        yield DartCollectionWindow(cursor, window_end)
        cursor = window_end + timedelta(days=1)


class PagedDartIssueCollector:
    """Collect every result page and document for both approved companies."""

    def __init__(
        self,
        service: DartCollectionService,
        *,
        begin_date: date,
        end_date: date,
        companies: Iterable[DartCompany] = DART_COMPANIES,
        page_count: int = 100,
        maximum_range_days: int = DART_MAX_RANGE_DAYS,
        on_batch: Callable[[DartCollectionBatch], None] | None = None,
        fail_on_error: bool = False,
    ) -> None:
        if begin_date > end_date:
            raise ValueError("begin_date cannot be after end_date")
        if not 1 <= page_count <= 100:
            raise ValueError("page_count must be between 1 and 100")
        self._service = service
        self._begin_date = begin_date
        self._end_date = end_date
        self._companies = tuple(companies)
        self._page_count = page_count
        self._maximum_range_days = maximum_range_days
        self._on_batch = on_batch
        self._fail_on_error = fail_on_error

    def collect(self) -> IssueCollectionResult:
        batches = []
        failures: list[Exception] = []
        for window in iter_dart_windows(
            self._begin_date,
            self._end_date,
            maximum_days=self._maximum_range_days,
        ):
            for company in self._companies:
                try:
                    for batch in self._collect_company_window(company, window):
                        batches.append(adapt_dart_batch(batch))
                        if self._on_batch is not None:
                            self._on_batch(batch)
                except Exception as error:
                    failures.append(error)

        if failures and (self._fail_on_error or not batches):
            raise failures[0]
        return IssueCollectionResult(
            payload=tuple(batches),
            collected_items=sum(len(batch.candidates) for batch in batches),
            status="partial_success" if failures else "success",
        )

    def _collect_company_window(
        self,
        company: DartCompany,
        window: DartCollectionWindow,
    ) -> Iterable[DartCollectionBatch]:
        page_no = 1
        while True:
            batch = self._service.collect_company(
                company,
                window.begin_date,
                window.end_date,
                page_no=page_no,
                page_count=self._page_count,
            )
            yield batch
            total_pages = _total_pages(batch)
            if page_no >= total_pages:
                break
            page_no += 1


def _total_pages(batch: DartCollectionBatch) -> int:
    """Read validated pagination metadata from the collection batch."""
    value = getattr(batch, "total_pages", 1)
    try:
        total_pages = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError("Open DART total_page is invalid") from error
    if total_pages < 1:
        return 1
    return total_pages
