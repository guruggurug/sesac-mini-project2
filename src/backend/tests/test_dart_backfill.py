from datetime import date, datetime, timezone
import json
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.dart_backfill import (
    PagedDartIssueCollector,
    iter_dart_windows,
)
from app.services.dart_disclosures import (
    DART_COMPANIES,
    DartCollectionBatch,
    RuntimeArtifact,
)


NOW = datetime(2026, 7, 26, tzinfo=timezone.utc)


def test_backfill_windows_are_inclusive_non_overlapping_and_cover_start():
    windows = list(iter_dart_windows(date(2023, 7, 21), date(2024, 2, 1)))

    assert windows[0].begin_date == date(2023, 7, 21)
    assert windows[-1].end_date == date(2024, 2, 1)
    for previous, current in zip(windows, windows[1:]):
        assert current.begin_date == previous.end_date.fromordinal(
            previous.end_date.toordinal() + 1
        )
    assert all((window.end_date - window.begin_date).days < 90 for window in windows)


class FakePagedService:
    def __init__(self, root: Path):
        self.root = root
        self.calls = []

    def collect_company(
        self,
        company,
        begin_date,
        end_date,
        *,
        page_no=1,
        page_count=100,
    ):
        self.calls.append((company.company_id, begin_date, end_date, page_no))
        payload = {
            "status": "000",
            "total_page": 2,
            "list": [{"rcept_no": f"2026072600000{page_no}"}],
        }
        path = self.root / f"{company.company_id}-{page_no}.json"
        path.write_text(json.dumps({"response": payload}), encoding="utf-8")
        artifact = RuntimeArtifact(path, str(page_no) * 64)
        return DartCollectionBatch(
            company=company,
            raw_artifact=artifact,
            candidate_artifact=artifact,
            candidates=[
                {
                    "candidate_id": f"CND-{company.company_id}-{page_no}",
                    "external_id": payload["list"][0]["rcept_no"],
                }
            ],
            dedup_keys=[],
            total_pages=2,
        )


def test_backfill_collects_every_page_for_both_companies(tmp_path):
    service = FakePagedService(tmp_path)
    collector = PagedDartIssueCollector(
        service,
        begin_date=date(2026, 7, 1),
        end_date=date(2026, 7, 26),
    )

    result = collector.collect()

    assert result.status == "success"
    assert result.collected_items == 4
    assert [call[3] for call in service.calls] == [1, 2, 1, 2]
    assert {call[0] for call in service.calls} == {
        company.company_id for company in DART_COMPANIES
    }


def test_backfill_fail_closed_does_not_return_an_incomplete_collection(tmp_path):
    service = FakePagedService(tmp_path)
    original = service.collect_company

    def fail_one_company(company, *args, **kwargs):
        if company.company_id == "000660":
            raise RuntimeError("provider unavailable")
        return original(company, *args, **kwargs)

    service.collect_company = fail_one_company
    collector = PagedDartIssueCollector(
        service,
        begin_date=date(2026, 7, 1),
        end_date=date(2026, 7, 26),
        fail_on_error=True,
    )

    import pytest

    with pytest.raises(RuntimeError, match="provider unavailable"):
        collector.collect()
