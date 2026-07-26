"""Atomic publication boundary for complete, validated Data A bundles."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from uuid import uuid4

from app.core.config import BASE_DIR, ISSUE_RUNTIME_DATA_DIR
from app.utils.csv_validator import validate_data_a_bundle


ACTIVE_POINTER_FILE = "current.json"
SNAPSHOT_PREFIX = "issues-"
BUNDLE_FILES = (
    Path("data/candidate/news_candidates.csv"),
    Path("data/processed/sources.csv"),
    Path("data/processed/event_sources.csv"),
    Path("data/processed/events.csv"),
    Path("data/processed/esg_indicators.csv"),
)


class SnapshotPublicationError(RuntimeError):
    """Publication failure with a stable internal stage code."""

    def __init__(self, stage: str, message: str) -> None:
        self.stage = stage
        self.code = f"ISSUE_SNAPSHOT_{stage.upper()}_FAILED"
        super().__init__(message)


class SnapshotPointerError(RuntimeError):
    """The active pointer is malformed or references an unsafe snapshot path."""


@dataclass(frozen=True)
class ActiveSnapshot:
    version: str
    root: Path
    published_at: str


@dataclass(frozen=True)
class SnapshotPublicationResult:
    snapshot_updated: bool
    published_snapshot_version: str | None
    published_at: str | None
    candidate_items: int
    validated_items: int
    rejected_items: int
    published_items: int


def read_active_snapshot(runtime_root: str | Path = ISSUE_RUNTIME_DATA_DIR) -> ActiveSnapshot | None:
    """Resolve the immutable snapshot named by the atomic active pointer."""
    root = Path(runtime_root)
    pointer_path = root / ACTIVE_POINTER_FILE
    if not pointer_path.is_file():
        return None

    try:
        payload = json.loads(pointer_path.read_text(encoding="utf-8"))
        version = payload["version"]
        published_at = payload["published_at"]
        relative_path = Path(payload["path"])
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise SnapshotPointerError("active issue snapshot pointer is invalid") from error

    if (
        not isinstance(version, str)
        or not version.startswith(SNAPSHOT_PREFIX)
        or not isinstance(published_at, str)
        or relative_path != Path("snapshots") / version
    ):
        raise SnapshotPointerError("active issue snapshot pointer is invalid")

    snapshot_root = (root / relative_path).resolve()
    snapshots_root = (root / "snapshots").resolve()
    if snapshots_root not in snapshot_root.parents or not snapshot_root.is_dir():
        raise SnapshotPointerError("active issue snapshot is unavailable")
    return ActiveSnapshot(version, snapshot_root, published_at)


def resolve_data_a_bundle_root(
    runtime_root: str | Path = ISSUE_RUNTIME_DATA_DIR,
    fallback_root: str | Path = BASE_DIR,
) -> Path:
    """Use the active immutable snapshot, or the checked-in bootstrap bundle."""
    active = read_active_snapshot(runtime_root)
    return active.root if active else Path(fallback_root)


class IssueSnapshotPublisher:
    """Stage and validate a full bundle before one atomic pointer replacement."""

    def __init__(
        self,
        runtime_root: str | Path = ISSUE_RUNTIME_DATA_DIR,
        *,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        replace: Callable[[str | Path, str | Path], None] = os.replace,
        copy_file: Callable[[str | Path, str | Path], object] = shutil.copyfile,
    ) -> None:
        self._runtime_root = Path(runtime_root)
        self._now = now
        self._replace = replace
        self._copy_file = copy_file

    def publish(self, bundle_root: str | Path) -> SnapshotPublicationResult:
        source_root = Path(bundle_root)
        try:
            manifest = _bundle_manifest(source_root)
            version = _content_version(source_root, manifest)
        except Exception as error:
            if isinstance(error, SnapshotPublicationError):
                raise
            raise SnapshotPublicationError("staging", "failed to read Data A bundle") from error

        staging_root = (
            self._runtime_root
            / "staging"
            / uuid4().hex[:12]
        )
        target_root = self._runtime_root / "snapshots" / version
        try:
            self._copy_bundle(source_root, staging_root, manifest)
        except Exception as error:
            _remove_generated_tree(staging_root)
            raise SnapshotPublicationError(
                "staging", "failed to build staged Data A bundle"
            ) from error

        try:
            bundle = validate_data_a_bundle(str(staging_root))
        except Exception as error:
            _remove_generated_tree(staging_root)
            raise SnapshotPublicationError(
                "validation", "staged Data A bundle did not pass validation"
            ) from error

        counts = _candidate_counts(bundle["candidates"])
        try:
            active = read_active_snapshot(self._runtime_root)
            if active and active.version == version:
                _remove_generated_tree(staging_root)
                return SnapshotPublicationResult(
                    snapshot_updated=False,
                    published_snapshot_version=None,
                    published_at=None,
                    candidate_items=counts["candidate_items"],
                    validated_items=counts["validated_items"],
                    rejected_items=counts["rejected_items"],
                    published_items=0,
                )

            target_root.parent.mkdir(parents=True, exist_ok=True)
            if target_root.exists():
                if _content_version(target_root, _bundle_manifest(target_root)) != version:
                    raise SnapshotPublicationError(
                        "publishing", "snapshot version collision detected"
                    )
                validate_data_a_bundle(str(target_root))
                _remove_generated_tree(staging_root)
            else:
                self._replace(staging_root, target_root)

            published_at = self._publication_time()
            self._replace_active_pointer(version, published_at)
        except SnapshotPublicationError:
            _remove_generated_tree(staging_root)
            raise
        except Exception as error:
            _remove_generated_tree(staging_root)
            raise SnapshotPublicationError(
                "publishing", "failed to activate validated Data A snapshot"
            ) from error

        return SnapshotPublicationResult(
            snapshot_updated=True,
            published_snapshot_version=version,
            published_at=published_at,
            candidate_items=counts["candidate_items"],
            validated_items=counts["validated_items"],
            rejected_items=counts["rejected_items"],
            published_items=counts["validated_items"],
        )

    def _copy_bundle(
        self,
        source_root: Path,
        staging_root: Path,
        manifest: tuple[Path, ...],
    ) -> None:
        for relative_path in manifest:
            source = source_root / relative_path
            target = staging_root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            self._copy_file(source, target)

    def _publication_time(self) -> str:
        published_at = self._now()
        if published_at.tzinfo is None or published_at.utcoffset() is None:
            raise SnapshotPublicationError(
                "publishing", "publisher clock must return a timezone-aware datetime"
            )
        return published_at.isoformat()

    def _replace_active_pointer(self, version: str, published_at: str) -> None:
        self._runtime_root.mkdir(parents=True, exist_ok=True)
        pointer_path = self._runtime_root / ACTIVE_POINTER_FILE
        temporary = self._runtime_root / f".{ACTIVE_POINTER_FILE}.{uuid4().hex}.tmp"
        payload = {
            "path": f"snapshots/{version}",
            "published_at": published_at,
            "version": version,
        }
        try:
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                json.dump(payload, handle, ensure_ascii=False, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            self._replace(temporary, pointer_path)
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def _bundle_manifest(root: Path) -> tuple[Path, ...]:
    required = list(BUNDLE_FILES)
    sources_path = root / "data/processed/sources.csv"
    if not sources_path.is_file():
        raise SnapshotPublicationError("staging", "sources.csv is missing")

    raw_root = (root / "data/raw/reports").resolve()
    evidence: set[Path] = set()
    try:
        with sources_path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                file_name = str(row.get("file_name") or "")
                candidate = (raw_root / file_name).resolve()
                if not file_name or raw_root not in candidate.parents:
                    raise SnapshotPublicationError(
                        "staging", "source evidence path is unsafe"
                    )
                evidence.add(candidate.relative_to(root.resolve()))
    except (OSError, csv.Error) as error:
        raise SnapshotPublicationError("staging", "sources.csv cannot be read") from error

    manifest = tuple(sorted(set(required) | evidence, key=lambda path: path.as_posix()))
    missing = [path.as_posix() for path in manifest if not (root / path).is_file()]
    if missing:
        raise SnapshotPublicationError(
            "staging", f"Data A bundle files are missing: {', '.join(missing)}"
        )
    return manifest


def _content_version(root: Path, manifest: tuple[Path, ...]) -> str:
    digest = hashlib.sha256()
    for relative_path in manifest:
        digest.update(relative_path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        with (root / relative_path).open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        digest.update(b"\0")
    return f"{SNAPSHOT_PREFIX}{digest.hexdigest()[:24]}"


def _candidate_counts(candidates: list[dict]) -> dict[str, int]:
    return {
        "candidate_items": len(candidates),
        "validated_items": sum(
            row["validation_status"] == "validated" for row in candidates
        ),
        "rejected_items": sum(
            row["validation_status"] == "rejected" for row in candidates
        ),
    }


def _remove_generated_tree(path: Path) -> None:
    try:
        if path.exists():
            shutil.rmtree(path)
    except OSError:
        pass
