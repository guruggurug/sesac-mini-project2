"""Internal issue sync workflow from collection through optional recalculation."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Literal, Protocol

from app.services.issue_snapshot_publisher import (
    SnapshotPublicationResult,
    resolve_data_a_bundle_root,
)
from app.utils.csv_validator import validate_data_a_bundle


TerminalSuccessStatus = Literal["success", "partial_success"]


@dataclass(frozen=True)
class IssueCollectionResult:
    payload: object
    collected_items: int
    status: TerminalSuccessStatus = "success"


@dataclass(frozen=True)
class PreparedIssueBundle:
    bundle_root: Path
    cleanup: Callable[[], None] | None = None


@dataclass(frozen=True)
class RecalculationResult:
    recalculated_at: str
    snapshot_version: str


@dataclass(frozen=True)
class IssueSyncWorkflowResult:
    status: TerminalSuccessStatus
    collected_items: int
    snapshot_updated: bool
    published_snapshot_version: str | None
    published_at: str | None
    candidate_items: int
    validated_items: int
    rejected_items: int
    published_items: int
    recalculation_triggered: bool
    recalculation_status: Literal["not_required", "completed"]
    recalculated_at: str | None


class IssueCollector(Protocol):
    def collect(self) -> IssueCollectionResult: ...


class IssueBundleNormalizer(Protocol):
    def normalize(self, collection: IssueCollectionResult) -> PreparedIssueBundle: ...


class SnapshotPublisher(Protocol):
    def publish(self, bundle_root: str | Path) -> SnapshotPublicationResult: ...


class RecalculationAdapter(Protocol):
    async def recalculate(
        self, *, snapshot_version: str, published_at: str
    ) -> RecalculationResult: ...


class IssueSyncWorkflowError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class RecalculationUnavailable(IssueSyncWorkflowError):
    def __init__(self) -> None:
        super().__init__(
            "ISSUE_RECALCULATION_UNAVAILABLE",
            "scoring-relevant snapshot was published but recalculation is unavailable",
        )


class InternalIssueSyncWorkflow:
    """Run deterministic stages and request Data B only after atomic publication."""

    def __init__(
        self,
        collector: IssueCollector,
        normalizer: IssueBundleNormalizer,
        publisher: SnapshotPublisher,
        *,
        recalculation: RecalculationAdapter | None = None,
        current_bundle_root: Callable[[], Path] = resolve_data_a_bundle_root,
    ) -> None:
        self._collector = collector
        self._normalizer = normalizer
        self._publisher = publisher
        self._recalculation = recalculation
        self._current_bundle_root = current_bundle_root

    async def run(self, report_stage: Callable[[str], None]) -> IssueSyncWorkflowResult:
        prepared: PreparedIssueBundle | None = None
        try:
            try:
                collection = self._collector.collect()
            except Exception as error:
                raise _stage_error("COLLECTION", error) from error

            report_stage("normalizing")
            try:
                prepared = self._normalizer.normalize(collection)
            except Exception as error:
                raise _stage_error("NORMALIZATION", error) from error

            report_stage("validating")
            try:
                validate_data_a_bundle(str(prepared.bundle_root))
                scoring_relevant = scoring_relevant_bundle_changed(
                    self._current_bundle_root(), prepared.bundle_root
                )
            except Exception as error:
                raise _stage_error("VALIDATION", error) from error

            report_stage("publishing")
            try:
                publication = self._publisher.publish(prepared.bundle_root)
            except Exception as error:
                code = str(getattr(error, "code", "ISSUE_SYNC_PUBLICATION_FAILED"))
                raise IssueSyncWorkflowError(code, "atomic snapshot publication failed") from error

            recalculation_triggered = False
            recalculated_at = None
            if publication.snapshot_updated and scoring_relevant:
                report_stage("recalculating")
                if self._recalculation is None:
                    raise RecalculationUnavailable()
                recalculation_triggered = True
                try:
                    requested_version = _required(publication.published_snapshot_version)
                    result = await self._recalculation.recalculate(
                        snapshot_version=requested_version,
                        published_at=_required(publication.published_at),
                    )
                except Exception as error:
                    code = str(getattr(error, "code", "ISSUE_RECALCULATION_FAILED"))
                    raise IssueSyncWorkflowError(code, "snapshot recalculation failed") from error
                if result.snapshot_version != requested_version:
                    raise IssueSyncWorkflowError(
                        "ISSUE_RECALCULATION_VERSION_MISMATCH",
                        "recalculation result does not match the published snapshot",
                    )
                recalculated_at = _aware_timestamp(result.recalculated_at)

            return IssueSyncWorkflowResult(
                status=collection.status,
                collected_items=collection.collected_items,
                snapshot_updated=publication.snapshot_updated,
                published_snapshot_version=publication.published_snapshot_version,
                published_at=publication.published_at,
                candidate_items=publication.candidate_items,
                validated_items=publication.validated_items,
                rejected_items=publication.rejected_items,
                published_items=publication.published_items,
                recalculation_triggered=recalculation_triggered,
                recalculation_status=("completed" if recalculation_triggered else "not_required"),
                recalculated_at=recalculated_at,
            )
        finally:
            if prepared is not None and prepared.cleanup is not None:
                prepared.cleanup()


def scoring_relevant_bundle_changed(previous_root: Path, next_root: Path) -> bool:
    """Compare only fields consumed by event eligibility and ESG aggregation."""
    previous_events = _model_event_rows(previous_root)
    next_events = _model_event_rows(next_root)
    if previous_events != next_events:
        return True
    return _scoring_esg_rows(previous_root) != _scoring_esg_rows(next_root)


def _model_event_rows(root: Path) -> tuple[tuple[str, ...], ...]:
    rows = _read_csv(root / "data/processed/events.csv")
    fields = (
        "event_id",
        "company_id",
        "event_category",
        "event_date",
        "status",
        "enforcement_action",
        "severity",
        "authority_confirmed",
        "official_source_url",
        "linked_indicator_id",
        "resolved_date",
        "market_event_date",
    )
    eligible = [row for row in rows if _event_is_model_eligible(row)]
    return tuple(sorted(tuple(row.get(field, "") for field in fields) for row in eligible))


def _scoring_esg_rows(root: Path) -> tuple[tuple[str, ...], ...]:
    rows = _read_csv(root / "data/processed/esg_indicators.csv")
    fields = (
        "company_id",
        "indicator_id",
        "raw_value",
        "raw_unit",
        "period",
        "business_scope",
        "geography",
        "scope_mismatch",
        "availability",
        "data_confidence",
        "risk_direction",
        "target_value",
        "target_unit",
        "target_year",
        "baseline_value",
        "baseline_year",
    )
    return tuple(sorted(tuple(row.get(field, "") for field in fields) for row in rows))


def _event_is_model_eligible(row: dict[str, str]) -> bool:
    return (
        row.get("status") in {"confirmed", "resolved"}
        and row.get("authority_confirmed", "").strip().lower() == "true"
        and bool(row.get("official_source_url", "").strip())
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _stage_error(stage: str, error: Exception) -> IssueSyncWorkflowError:
    code = str(getattr(error, "code", f"ISSUE_SYNC_{stage}_FAILED"))
    return IssueSyncWorkflowError(code, f"issue sync {stage.lower()} failed")


def _required(value: str | None) -> str:
    if not value:
        raise IssueSyncWorkflowError(
            "ISSUE_SYNC_PUBLICATION_RESULT_INVALID",
            "updated publication is missing required metadata",
        )
    return value


def _aware_timestamp(value: str) -> str:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise IssueSyncWorkflowError(
            "ISSUE_RECALCULATION_RESULT_INVALID",
            "recalculation timestamp must include timezone information",
        )
    return value
