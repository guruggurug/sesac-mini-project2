"""Run a credential-safe Open DART collection smoke test in temporary storage."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "src" / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import (  # noqa: E402
    DART_API_KEY,
    DART_BASE_URL,
    DART_MAX_ATTEMPTS,
    DART_RETRY_BACKOFF_SECONDS,
    DART_TIMEOUT_SECONDS,
)
from app.services.dart_disclosures import (  # noqa: E402
    DartCandidateStore,
    DartCollectionService,
    DartDisclosureProvider,
    DartDocumentProvider,
    DartDocumentService,
    DartDocumentStore,
    DartRawStore,
)
from app.services.issue_bundle_normalizer import (  # noqa: E402
    DailyDartIssueCollector,
    DataAIssueBundleNormalizer,
)
from app.services.issue_sync_workflow import IssueCollectionResult  # noqa: E402
from app.utils.csv_validator import validate_data_a_bundle  # noqa: E402
from app.utils.issue_rules import candidate_classification_rule  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lookback-days", type=int, default=1)
    parser.add_argument("--document-receipt")
    args = parser.parse_args()

    if not DART_API_KEY:
        print("status=configuration_error")
        print("error_code=DART_API_KEY_MISSING")
        return 2

    with tempfile.TemporaryDirectory(prefix="chip-buddy-dart-smoke-") as temp_dir:
        if args.document_receipt:
            document = DartDocumentService(
                DartDocumentProvider(
                    api_key=DART_API_KEY,
                    base_url=DART_BASE_URL,
                    timeout_seconds=DART_TIMEOUT_SECONDS,
                    max_attempts=DART_MAX_ATTEMPTS,
                    retry_backoff_seconds=DART_RETRY_BACKOFF_SECONDS,
                ),
                DartDocumentStore(temp_dir),
            ).fetch_and_extract(args.document_receipt)
            rule = candidate_classification_rule(
                document.text,
                pattern_field="body_pattern",
            )
            print("status=success")
            print(f"archive_bytes={document.artifact.path.stat().st_size}")
            print(f"archive_hash_valid={len(document.artifact.content_hash) == 64}")
            print(f"extracted_text_chars={len(document.text)}")
            print(
                "classification_rule="
                + (str(rule["rule_id"]) if rule else "none")
            )
            return 0

        provider = DartDisclosureProvider(
            api_key=DART_API_KEY,
            base_url=DART_BASE_URL,
            timeout_seconds=DART_TIMEOUT_SECONDS,
            max_attempts=DART_MAX_ATTEMPTS,
            retry_backoff_seconds=DART_RETRY_BACKOFF_SECONDS,
        )
        service = DartCollectionService(
            provider,
            DartRawStore(temp_dir),
            DartCandidateStore(temp_dir),
            document_service=DartDocumentService(
                DartDocumentProvider(
                    api_key=DART_API_KEY,
                    base_url=DART_BASE_URL,
                    timeout_seconds=DART_TIMEOUT_SECONDS,
                    max_attempts=DART_MAX_ATTEMPTS,
                    retry_backoff_seconds=DART_RETRY_BACKOFF_SECONDS,
                ),
                DartDocumentStore(temp_dir),
            ),
        )
        result = DailyDartIssueCollector(
            service,
            lookback_days=args.lookback_days,
        ).collect()
        batches = result.payload
        raw_artifacts_valid = all(
            batch.evidence_path.is_file() and len(batch.evidence_hash) == 64
            for batch in batches
        )
        pending_items = sum(
            row["validation_status"] == "pending"
            for batch in batches
            for row in batch.candidates
        )
        rejected_items = sum(
            row["validation_status"] == "rejected"
            for batch in batches
            for row in batch.candidates
        )
        document_artifacts = sum(
            len(batch.item_evidence)
            for batch in batches
        )
        document_artifacts_valid = all(
            path.is_file() and len(content_hash) == 64
            for batch in batches
            for path, content_hash in batch.item_evidence.values()
        )
        baseline = validate_data_a_bundle(str(ROOT))
        normalizer = DataAIssueBundleNormalizer(
            current_bundle_root=lambda: ROOT,
            runtime_root=temp_dir,
        )
        prepared = normalizer.normalize(
            IssueCollectionResult(
                payload=batches,
                collected_items=result.collected_items,
                status=result.status,
            )
        )
        try:
            normalized = validate_data_a_bundle(str(prepared.bundle_root))
            normalized_validated = sum(
                row["validation_status"] == "validated"
                for row in normalized["candidates"]
            )
            normalized_rejected = sum(
                row["validation_status"] == "rejected"
                for row in normalized["candidates"]
            )
            added_events = len(normalized["events"]) - len(baseline["events"])
        finally:
            prepared.cleanup()

        print(f"status={result.status}")
        print(f"company_batches={len(batches)}")
        print(f"collected_items={result.collected_items}")
        print(f"pending_items={pending_items}")
        print(f"rejected_items={rejected_items}")
        print(f"raw_artifacts_valid={raw_artifacts_valid}")
        print(f"document_artifacts={document_artifacts}")
        print(f"document_artifacts_valid={document_artifacts_valid}")
        print(f"bundle_validated_items={normalized_validated}")
        print(f"bundle_rejected_items={normalized_rejected}")
        print(f"bundle_added_events={added_events}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
