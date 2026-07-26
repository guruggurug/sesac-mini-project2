from __future__ import annotations

import csv
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import BASE_DIR
from app.services.dart_disclosures import DART_COMPANIES
from app.services.issue_bundle_normalizer import (
    DataAIssueBundleNormalizer,
    adapt_news_batch,
)
from app.services.issue_sync_workflow import IssueCollectionResult
from app.services.news_collection import (
    NewsArticle,
    NewsCandidateNormalizer,
    NewsCandidateStore,
    NewsCollectionService,
    NewsRawPage,
    NewsRawStore,
)
from app.utils.csv_validator import validate_data_a_bundle
from app.utils.issue_rules import candidate_content_hash, canonicalize_url


ROOT = Path(BASE_DIR)
NOW = datetime(2026, 7, 26, 1, 0, tzinfo=timezone.utc)
COMPANY = DART_COMPANIES[0]


def page(*articles: NewsArticle) -> NewsRawPage:
    return NewsRawPage(
        provider_name="fixture-news",
        company=COMPANY,
        query="삼성전자 ESG",
        begin_date="2026-07-25",
        end_date="2026-07-26",
        collected_at=NOW,
        payload={"total": len(articles), "items": [{"id": item.external_id} for item in articles]},
        articles=tuple(articles),
    )


def article(
    *,
    external_id: str = "news-1",
    title: str = "삼성전자 ESG 기사",
    published_at: str = "2026-07-25",
    url: str = "https://news.example/article/1?utm_source=test&b=2",
    description: str = "ESG 관련 기사 설명",
) -> NewsArticle:
    return NewsArticle(
        external_id=external_id,
        title=title,
        published_at=published_at,
        url=url,
        description=description,
    )


class Provider:
    def __init__(self, result: NewsRawPage | None = None, error: Exception | None = None):
        self.result = result
        self.error = error
        self.calls = []

    def fetch_company(self, company, query, begin_date, end_date):
        self.calls.append((company, query, begin_date, end_date))
        if self.error:
            raise self.error
        return self.result


def service(tmp_path: Path, provider: Provider, normalizer=None) -> NewsCollectionService:
    return NewsCollectionService(
        provider,
        NewsRawStore(tmp_path),
        NewsCandidateStore(tmp_path),
        normalizer=normalizer,
    )


def test_news_collection_persists_raw_before_candidate_normalization(tmp_path):
    class FailingNormalizer:
        def normalize(self, raw_page):
            raise RuntimeError("injected")

    collector = service(
        tmp_path,
        Provider(page(article())),
        normalizer=FailingNormalizer(),
    )

    with pytest.raises(RuntimeError, match="injected"):
        collector.collect_company(
            COMPANY,
            "삼성전자 ESG",
            date(2026, 7, 25),
            date(2026, 7, 26),
        )

    assert len(list((tmp_path / "raw/news").rglob("*.json"))) == 1
    assert not (tmp_path / "candidate/news").exists()


def test_news_candidate_normalizes_url_hash_and_pending_status():
    source = article()

    normalized = NewsCandidateNormalizer().normalize(page(source))
    row = normalized.candidates[0]

    assert row["validation_status"] == "pending"
    assert row["detection_source_type"] == "news"
    assert row["source_name"] == "news.example"
    assert row["canonical_url"] == "https://news.example/article/1?b=2"
    assert row["content_hash"] == candidate_content_hash(row)
    assert row["canonical_url"] == canonicalize_url(row["url"])


def test_news_candidate_deduplicates_active_articles():
    duplicate = article()

    normalized = NewsCandidateNormalizer().normalize(page(duplicate, duplicate))

    assert normalized.candidates[0]["validation_status"] == "pending"
    assert normalized.candidates[1]["validation_status"] == "rejected"
    assert (
        normalized.candidates[1]["rejection_reason"]
        == "duplicate_news_candidate"
    )


def test_malformed_news_article_is_retained_as_schema_valid_rejection():
    malformed = article(
        title="",
        published_at="not-a-date",
        url="not-a-url",
        description="",
    )

    normalized = NewsCandidateNormalizer().normalize(page(malformed))
    row = normalized.candidates[0]

    assert row["validation_status"] == "rejected"
    assert row["source_name"] == "invalid.local"
    assert row["published_at"] == NOW.date().isoformat()
    assert "missing_news_title" in row["rejection_reason"]
    assert "invalid_news_date" in row["rejection_reason"]
    assert "invalid_news_url" in row["rejection_reason"]


def test_news_collection_writes_raw_and_candidate_artifacts(tmp_path):
    collector = service(tmp_path, Provider(page(article())))

    result = collector.collect_company(
        COMPANY,
        "삼성전자 ESG",
        date(2026, 7, 25),
        date(2026, 7, 26),
    )

    assert result.raw_artifact.path.is_file()
    assert result.candidate_artifact.path.is_file()
    assert len(result.raw_artifact.content_hash) == 64
    assert len(result.candidate_artifact.content_hash) == 64
    with result.candidate_artifact.path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        stored = list(csv.DictReader(handle))
    assert stored[0]["validation_status"] == "pending"


def test_provider_failure_does_not_create_raw_or_candidate_files(tmp_path):
    collector = service(tmp_path, Provider(error=RuntimeError("provider failed")))

    with pytest.raises(RuntimeError, match="provider failed"):
        collector.collect_company(
            COMPANY,
            "삼성전자 ESG",
            date(2026, 7, 25),
            date(2026, 7, 26),
        )

    assert not (tmp_path / "raw/news").exists()
    assert not (tmp_path / "candidate/news").exists()


def test_provider_scope_mismatch_preserves_raw_and_stops_candidates(tmp_path):
    wrong_page = NewsRawPage(
        provider_name="fixture-news",
        company=DART_COMPANIES[1],
        query="삼성전자 ESG",
        begin_date="2026-07-25",
        end_date="2026-07-26",
        collected_at=NOW,
        payload={"items": []},
        articles=(),
    )
    collector = service(tmp_path, Provider(wrong_page))

    with pytest.raises(ValueError, match="different company"):
        collector.collect_company(
            COMPANY,
            "삼성전자 ESG",
            date(2026, 7, 25),
            date(2026, 7, 26),
        )

    assert len(list((tmp_path / "raw/news").rglob("*.json"))) == 1
    assert not (tmp_path / "candidate/news").exists()


def test_news_candidate_cannot_publish_event_without_official_confirmation(tmp_path):
    collector = service(
        tmp_path / "collection",
        Provider(
            page(
                article(
                    title="삼성전자 반도체 사업장 중대재해 발생",
                    description="사업장 중대재해 발생 보도",
                )
            )
        ),
    )
    collected = collector.collect_company(
        COMPANY,
        "삼성전자 ESG",
        date(2026, 7, 25),
        date(2026, 7, 26),
    )
    normalizer = DataAIssueBundleNormalizer(
        current_bundle_root=lambda: ROOT,
        runtime_root=tmp_path / "runtime",
    )

    prepared = normalizer.normalize(
        IssueCollectionResult((adapt_news_batch(collected),), 1)
    )
    try:
        bundle = validate_data_a_bundle(str(prepared.bundle_root))
        news_row = next(
            row
            for row in bundle["candidates"]
            if row["external_id"] == "news-1"
        )
        assert news_row["validation_status"] == "rejected"
        assert news_row["matched_event_id"] is None
        assert news_row["rejection_reason"] == "official_confirmation_required"
        assert len(bundle["events"]) == len(
            validate_data_a_bundle(str(ROOT))["events"]
        )
    finally:
        prepared.cleanup()
