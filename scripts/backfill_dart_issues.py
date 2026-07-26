"""Backfill Open DART documents into the production issue snapshot.

The command uses the same classifier, validator, publisher, and Data B
recalculation adapter as the daily scheduler.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "src" / "backend"
for entry in (str(ROOT), str(BACKEND)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from app.core.runtime import build_internal_issue_sync_workflow
from app.services.dart_backfill import (
    DART_BACKFILL_START_DATE,
    PagedDartIssueCollector,
)
from app.services.dart_disclosures import build_dart_collection_service
from app.services.issue_bundle_normalizer import DataAIssueBundleNormalizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill all Samsung Electronics and SK hynix DART documents."
    )
    parser.add_argument(
        "--begin-date",
        type=date.fromisoformat,
        default=DART_BACKFILL_START_DATE,
    )
    parser.add_argument("--end-date", type=date.fromisoformat, default=date.today())
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Required guard before publishing and recalculating the active snapshot.",
    )
    return parser.parse_args()


async def run(args: argparse.Namespace) -> int:
    if not args.execute:
        print(
            f"planned_range={args.begin_date.isoformat()}..{args.end_date.isoformat()}"
        )
        print("status=not_started reason=execute_guard_required")
        return 2

    collector = PagedDartIssueCollector(
        build_dart_collection_service(),
        begin_date=args.begin_date,
        end_date=args.end_date,
        on_batch=lambda batch: print(
            "collected="
            f"{batch.company.company_id}:"
            f"{batch.raw_artifact.path.name}:"
            f"{len(batch.candidates)}"
        ),
        fail_on_error=True,
    )
    workflow = build_internal_issue_sync_workflow(
        collector,
        DataAIssueBundleNormalizer(),
    )
    result = await workflow.run(lambda stage: print(f"stage={stage}"))
    print(
        "result="
        f"{result.status} collected={result.collected_items} "
        f"validated={result.validated_items} rejected={result.rejected_items} "
        f"snapshot={result.published_snapshot_version or 'unchanged'} "
        f"recalculation={result.recalculation_status}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run(parse_args())))
