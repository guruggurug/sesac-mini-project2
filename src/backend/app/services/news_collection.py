"""Provider-neutral news collection and Data A candidate normalization."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Protocol
from urllib.parse import urlsplit

from app.services.dart_disclosures import DartCompany, RuntimeArtifact
from app.utils.csv_validator import validate_candidate_rows
from app.utils.issue_rules import (
    candidate_content_hash,
    candidate_dedup_key,
    canonicalize_url,
    normalize_text,
)


NEWS_FALLBACK_URL = "https://invalid.local/"


@dataclass(frozen=True)
class NewsArticle:
    title: str
    published_at: str
    url: str
    description: str
    external_id: str | None = None


@dataclass(frozen=True)
class NewsRawPage:
    provider_name: str
    company: DartCompany
    query: str
    begin_date: str
    end_date: str
    collected_at: datetime
    payload: object
    articles: tuple[NewsArticle, ...]


@dataclass(frozen=True)
class NormalizedNewsCandidateBatch:
    candidates: list[dict]
    dedup_keys: list[tuple[str, ...]]


@dataclass(frozen=True)
class NewsCollectionBatch:
    company: DartCompany
    raw_artifact: RuntimeArtifact
    candidate_artifact: RuntimeArtifact
    candidates: list[dict]
    dedup_keys: list[tuple[str, ...]]


class NewsProvider(Protocol):
    """Provider adapters return metadata already allowed for local retention."""

    def fetch_company(
        self,
        company: DartCompany,
        query: str,
        begin_date: date,
        end_date: date,
    ) -> NewsRawPage: ...


class NewsRawStore:
    """Persist the provider response before any candidate transformation."""

    def __init__(self, runtime_root: str | Path) -> None:
        self._root = Path(runtime_root) / "raw" / "news"

    def save(self, page: NewsRawPage) -> RuntimeArtifact:
        _validate_page(page)
        envelope = {
            "provider": page.provider_name,
            "collected_at": page.collected_at.isoformat(),
            "request": {
                "company_id": page.company.company_id,
                "query": page.query,
                "begin_date": page.begin_date,
                "end_date": page.end_date,
            },
            "response": page.payload,
        }
        content = json.dumps(
            envelope,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(content).hexdigest()
        directory = (
            self._root
            / _safe_provider_name(page.provider_name)
            / page.collected_at.date().isoformat()
        )
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / (
            f"{page.company.company_id}_{page.collected_at:%H%M%S%f}_{digest[:12]}.json"
        )
        _atomic_write(target, content)
        return RuntimeArtifact(target, digest)


class NewsCandidateNormalizer:
    """Convert normalized provider articles into schema-valid pending candidates."""

    def normalize(self, page: NewsRawPage) -> NormalizedNewsCandidateBatch:
        _validate_page(page)
        candidates: list[dict] = []
        active_keys: set[tuple[str, ...]] = set()

        for index, article in enumerate(page.articles, start=1):
            candidate = self._normalize_article(page, article, index)
            if candidate["validation_status"] != "rejected":
                key = candidate_dedup_key(candidate)
                if key in active_keys:
                    candidate.update(
                        validation_status="rejected",
                        matched_event_id=None,
                        rejection_reason="duplicate_news_candidate",
                    )
                else:
                    active_keys.add(key)
            candidates.append(candidate)

        validate_candidate_rows(candidates)
        return NormalizedNewsCandidateBatch(
            candidates=candidates,
            dedup_keys=[candidate_dedup_key(row) for row in candidates],
        )

    def _normalize_article(
        self,
        page: NewsRawPage,
        article: NewsArticle,
        index: int,
    ) -> dict:
        title = str(article.title or "").strip()
        description = str(article.description or "").strip()
        external_id = str(article.external_id).strip() if article.external_id else None
        published_at, date_error = _published_date(
            article.published_at,
            fallback=page.collected_at.date(),
        )
        url, source_name, url_error = _news_url(article.url)
        errors = [
            reason
            for reason in (
                "missing_news_title" if not title else None,
                date_error,
                url_error,
            )
            if reason
        ]

        safe_title = (title or "Rejected news candidate")[:500]
        safe_description = (description or safe_title)[:2000]
        candidate = {
            "candidate_id": _news_candidate_id(page, article, index),
            "company_id": page.company.company_id,
            "company_name": page.company.company_name,
            "detection_source_type": "news",
            "source_name": source_name,
            "external_id": external_id[:200] if external_id else None,
            "query": page.query[:300],
            "title": safe_title,
            "normalized_title": (
                normalize_text(safe_title) or "rejectednewscandidate"
            )[:500],
            "published_at": published_at,
            "collected_at": page.collected_at.isoformat(),
            "url": url,
            "canonical_url": canonicalize_url(url),
            "description": safe_description,
            "content_hash": "",
            "validation_status": "rejected" if errors else "pending",
            "matched_event_id": None,
            "rejection_reason": "|".join(errors)[:500] if errors else None,
        }
        candidate["content_hash"] = candidate_content_hash(candidate)
        return candidate


class NewsCandidateStore:
    """Persist candidate CSV outside the active processed snapshot."""

    FIELDS = (
        "candidate_id",
        "company_id",
        "company_name",
        "detection_source_type",
        "source_name",
        "external_id",
        "query",
        "title",
        "normalized_title",
        "published_at",
        "collected_at",
        "url",
        "canonical_url",
        "description",
        "content_hash",
        "validation_status",
        "matched_event_id",
        "rejection_reason",
    )

    def __init__(self, runtime_root: str | Path) -> None:
        self._root = Path(runtime_root) / "candidate" / "news"

    def save(
        self,
        page: NewsRawPage,
        batch: NormalizedNewsCandidateBatch,
        raw_artifact: RuntimeArtifact,
    ) -> RuntimeArtifact:
        validate_candidate_rows(batch.candidates)
        directory = (
            self._root
            / _safe_provider_name(page.provider_name)
            / page.collected_at.date().isoformat()
        )
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / f"{raw_artifact.path.stem}.csv"
        temporary = target.with_suffix(".csv.tmp")
        with temporary.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.FIELDS)
            writer.writeheader()
            writer.writerows(batch.candidates)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        content = target.read_bytes()
        return RuntimeArtifact(target, hashlib.sha256(content).hexdigest())


class NewsCollectionService:
    """Collection boundary: provider metadata -> raw artifact -> candidates."""

    def __init__(
        self,
        provider: NewsProvider,
        raw_store: NewsRawStore,
        candidate_store: NewsCandidateStore,
        normalizer: NewsCandidateNormalizer | None = None,
    ) -> None:
        self._provider = provider
        self._raw_store = raw_store
        self._candidate_store = candidate_store
        self._normalizer = normalizer or NewsCandidateNormalizer()

    def collect_company(
        self,
        company: DartCompany,
        query: str,
        begin_date: date,
        end_date: date,
    ) -> NewsCollectionBatch:
        if begin_date > end_date:
            raise ValueError("news begin_date cannot be after end_date")
        page = self._provider.fetch_company(company, query, begin_date, end_date)
        raw_artifact = self._raw_store.save(page)
        _validate_provider_result(page, company, query, begin_date, end_date)
        normalized = self._normalizer.normalize(page)
        candidate_artifact = self._candidate_store.save(
            page,
            normalized,
            raw_artifact,
        )
        return NewsCollectionBatch(
            company=company,
            raw_artifact=raw_artifact,
            candidate_artifact=candidate_artifact,
            candidates=normalized.candidates,
            dedup_keys=normalized.dedup_keys,
        )


def _validate_page(page: NewsRawPage) -> None:
    if not page.provider_name.strip():
        raise ValueError("news provider_name is required")
    if not page.query.strip():
        raise ValueError("news query is required")
    if page.collected_at.tzinfo is None or page.collected_at.utcoffset() is None:
        raise ValueError("news collection clock must be timezone-aware")
    begin = date.fromisoformat(page.begin_date)
    end = date.fromisoformat(page.end_date)
    if begin > end:
        raise ValueError("news begin_date cannot be after end_date")


def _published_date(value: str, *, fallback: date) -> tuple[str, str | None]:
    text = str(value or "").strip()
    try:
        return date.fromisoformat(text[:10]).isoformat(), None
    except ValueError:
        return fallback.isoformat(), "invalid_news_date"


def _news_url(value: str) -> tuple[str, str, str | None]:
    text = str(value or "").strip()
    parsed = urlsplit(text)
    if (
        parsed.scheme.lower() in {"http", "https"}
        and parsed.netloc
        and parsed.username is None
        and parsed.password is None
        and len(parsed.netloc) <= 200
        and len(text) <= 1000
    ):
        return text, parsed.netloc.lower(), None
    return NEWS_FALLBACK_URL, "invalid.local", "invalid_news_url"


def _validate_provider_result(
    page: NewsRawPage,
    company: DartCompany,
    query: str,
    begin_date: date,
    end_date: date,
) -> None:
    if page.company != company:
        raise ValueError("news provider returned a different company")
    if page.query != query:
        raise ValueError("news provider returned a different query")
    if page.begin_date != begin_date.isoformat():
        raise ValueError("news provider returned a different begin_date")
    if page.end_date != end_date.isoformat():
        raise ValueError("news provider returned a different end_date")


def _news_candidate_id(
    page: NewsRawPage,
    article: NewsArticle,
    index: int,
) -> str:
    identity = "|".join(
        (
            page.provider_name,
            page.company.company_id,
            str(article.external_id or article.url),
            str(index),
        )
    )
    numeric = int(hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16], 16)
    return f"CND-{numeric:020d}"


def _safe_provider_name(value: str) -> str:
    normalized = re.sub(r"[^0-9a-z._-]+", "-", value.strip().lower()).strip("-")
    return normalized or "provider"


def _atomic_write(target: Path, content: bytes) -> None:
    temporary = target.with_suffix(f"{target.suffix}.tmp")
    with temporary.open("wb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, target)
