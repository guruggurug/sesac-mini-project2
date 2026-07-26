"""Open DART disclosure collection and candidate normalization.

This module deliberately stops before processed snapshot publication. Every successful
API response is persisted under the runtime raw boundary before candidate conversion.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import time
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from pathlib import PurePosixPath
from typing import Callable, Protocol
from xml.etree import ElementTree

import httpx

from app.core.config import (
    DART_API_KEY,
    DART_BASE_URL,
    DART_MAX_ATTEMPTS,
    DART_RETRY_BACKOFF_SECONDS,
    DART_TIMEOUT_SECONDS,
    ISSUE_RUNTIME_DATA_DIR,
)
from app.utils.csv_validator import validate_candidate_rows
from app.utils.issue_rules import (
    candidate_classification_rule,
    candidate_content_hash,
    candidate_dedup_key,
    canonicalize_url,
    normalize_text,
)


DART_LIST_PATH = "/list.json"
DART_VIEWER_URL = "https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt_no}"
DART_FALLBACK_URL = "https://dart.fss.or.kr/"
MAX_DOCUMENT_ARCHIVE_BYTES = 25 * 1024 * 1024
MAX_DOCUMENT_FILES = 500
MAX_DOCUMENT_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_DOCUMENT_TEXT_CHARS = 5_000_000


@dataclass(frozen=True)
class DartCompany:
    company_id: str
    company_name: str
    corp_code: str


DART_COMPANIES = (
    DartCompany("005930", "삼성전자", "00126380"),
    DartCompany("000660", "SK하이닉스", "00164779"),
)


class HttpClient(Protocol):
    def get(self, url: str, **kwargs): ...


class DartProviderError(RuntimeError):
    """Sanitized provider error that never embeds request URLs or responses."""

    def __init__(self, code: str, *, retryable: bool) -> None:
        self.code = code
        self.retryable = retryable
        super().__init__(f"Open DART request failed ({code})")


class DartConfigurationError(DartProviderError):
    def __init__(self) -> None:
        super().__init__("DART_API_KEY_MISSING", retryable=False)


@dataclass(frozen=True)
class DartRawPage:
    company: DartCompany
    begin_date: str
    end_date: str
    page_no: int
    page_count: int
    collected_at: datetime
    payload: dict


@dataclass(frozen=True)
class RuntimeArtifact:
    path: Path
    content_hash: str


@dataclass(frozen=True)
class NormalizedCandidateBatch:
    candidates: list[dict]
    dedup_keys: list[tuple[str, ...]]


@dataclass(frozen=True)
class DartCollectionBatch:
    company: DartCompany
    raw_artifact: RuntimeArtifact
    candidate_artifact: RuntimeArtifact
    candidates: list[dict]
    dedup_keys: list[tuple[str, ...]]
    document_artifacts: dict[str, RuntimeArtifact] | None = None
    total_pages: int = 1


@dataclass(frozen=True)
class DartDocumentArchive:
    receipt_no: str
    collected_at: datetime
    content: bytes


@dataclass(frozen=True)
class DartDocumentResult:
    artifact: RuntimeArtifact
    text: str


class DartDisclosureProvider:
    """Synchronous Open DART list adapter with bounded retries."""

    RETRYABLE_API_STATUSES = {"020", "800", "900"}

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://opendart.fss.or.kr/api",
        timeout_seconds: float = 5.0,
        max_attempts: int = 3,
        retry_backoff_seconds: float = 0.25,
        client: HttpClient | None = None,
        sleep: Callable[[float], None] = time.sleep,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        if not api_key:
            raise DartConfigurationError()
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least one")
        if retry_backoff_seconds < 0:
            raise ValueError("retry_backoff_seconds cannot be negative")

        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._max_attempts = max_attempts
        self._retry_backoff_seconds = retry_backoff_seconds
        self._client = client or httpx.Client()
        self._sleep = sleep
        self._now = now

    def fetch_company(
        self,
        company: DartCompany,
        begin_date: date | str,
        end_date: date | str,
        *,
        page_no: int = 1,
        page_count: int = 100,
    ) -> DartRawPage:
        begin = _dart_date(begin_date)
        end = _dart_date(end_date)
        if begin > end:
            raise ValueError("begin_date cannot be after end_date")
        if page_no < 1:
            raise ValueError("page_no must be at least one")
        if not 1 <= page_count <= 100:
            raise ValueError("page_count must be between 1 and 100")

        params = {
            "crtfc_key": self._api_key,
            "corp_code": company.corp_code,
            "bgn_de": begin,
            "end_de": end,
            "last_reprt_at": "N",
            "sort": "date",
            "sort_mth": "desc",
            "page_no": page_no,
            "page_count": page_count,
        }

        for attempt in range(1, self._max_attempts + 1):
            try:
                payload = self._request(params)
                collected_at = self._now()
                if collected_at.tzinfo is None or collected_at.utcoffset() is None:
                    raise ValueError("provider clock must return a timezone-aware datetime")
                return DartRawPage(
                    company=company,
                    begin_date=begin,
                    end_date=end,
                    page_no=page_no,
                    page_count=page_count,
                    collected_at=collected_at,
                    payload=payload,
                )
            except DartProviderError as error:
                if not error.retryable or attempt == self._max_attempts:
                    raise
                self._sleep(self._retry_backoff_seconds * (2 ** (attempt - 1)))

        raise AssertionError("unreachable retry loop")

    def _request(self, params: dict) -> dict:
        try:
            response = self._client.get(
                f"{self._base_url}{DART_LIST_PATH}",
                params=params,
                timeout=self._timeout_seconds,
            )
        except (httpx.TimeoutException, TimeoutError) as error:
            raise DartProviderError("DART_TIMEOUT", retryable=True) from error
        except (httpx.RequestError, OSError) as error:
            raise DartProviderError("DART_NETWORK_ERROR", retryable=True) from error
        except Exception as error:
            raise DartProviderError("DART_CLIENT_ERROR", retryable=False) from error

        status_code = int(getattr(response, "status_code", 0))
        if status_code >= 500:
            raise DartProviderError("DART_HTTP_5XX", retryable=True)
        if status_code >= 400 or status_code < 200:
            raise DartProviderError("DART_HTTP_4XX", retryable=False)

        try:
            payload = response.json()
        except Exception as error:
            raise DartProviderError("DART_INVALID_JSON", retryable=False) from error
        if not isinstance(payload, dict):
            raise DartProviderError("DART_INVALID_RESPONSE", retryable=False)

        api_status = str(payload.get("status") or "")
        if api_status == "013":
            return payload
        if api_status != "000":
            raise DartProviderError(
                f"DART_API_{api_status or 'UNKNOWN'}",
                retryable=api_status in self.RETRYABLE_API_STATUSES,
            )
        if not isinstance(payload.get("list"), list):
            raise DartProviderError("DART_INVALID_RESPONSE", retryable=False)
        return payload


class DartDocumentProvider:
    """Download an official disclosure ZIP with bounded, sanitized retries."""

    RETRYABLE_API_STATUSES = DartDisclosureProvider.RETRYABLE_API_STATUSES

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://opendart.fss.or.kr/api",
        timeout_seconds: float = 5.0,
        max_attempts: int = 3,
        retry_backoff_seconds: float = 0.25,
        client: HttpClient | None = None,
        sleep: Callable[[float], None] = time.sleep,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        if not api_key:
            raise DartConfigurationError()
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least one")
        if retry_backoff_seconds < 0:
            raise ValueError("retry_backoff_seconds cannot be negative")

        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._max_attempts = max_attempts
        self._retry_backoff_seconds = retry_backoff_seconds
        self._client = client or httpx.Client()
        self._sleep = sleep
        self._now = now

    def fetch(self, receipt_no: str) -> DartDocumentArchive:
        receipt = str(receipt_no).strip()
        if re.fullmatch(r"[0-9]{14}", receipt) is None:
            raise ValueError("DART document receipt number must contain 14 digits")

        for attempt in range(1, self._max_attempts + 1):
            try:
                content = self._request(receipt)
                collected_at = self._now()
                if collected_at.tzinfo is None or collected_at.utcoffset() is None:
                    raise ValueError(
                        "document provider clock must return a timezone-aware datetime"
                    )
                return DartDocumentArchive(receipt, collected_at, content)
            except DartProviderError as error:
                if not error.retryable or attempt == self._max_attempts:
                    raise
                self._sleep(self._retry_backoff_seconds * (2 ** (attempt - 1)))

        raise AssertionError("unreachable document retry loop")

    def _request(self, receipt_no: str) -> bytes:
        try:
            response = self._client.get(
                f"{self._base_url}/document.xml",
                params={
                    "crtfc_key": self._api_key,
                    "rcept_no": receipt_no,
                },
                timeout=self._timeout_seconds,
            )
        except (httpx.TimeoutException, TimeoutError) as error:
            raise DartProviderError("DART_DOCUMENT_TIMEOUT", retryable=True) from error
        except (httpx.RequestError, OSError) as error:
            raise DartProviderError(
                "DART_DOCUMENT_NETWORK_ERROR", retryable=True
            ) from error
        except Exception as error:
            raise DartProviderError(
                "DART_DOCUMENT_CLIENT_ERROR", retryable=False
            ) from error

        status_code = int(getattr(response, "status_code", 0))
        if status_code >= 500:
            raise DartProviderError("DART_DOCUMENT_HTTP_5XX", retryable=True)
        if status_code >= 400 or status_code < 200:
            raise DartProviderError("DART_DOCUMENT_HTTP_4XX", retryable=False)

        content = bytes(getattr(response, "content", b""))
        if len(content) > MAX_DOCUMENT_ARCHIVE_BYTES:
            raise DartProviderError("DART_DOCUMENT_TOO_LARGE", retryable=False)
        if not _is_zip_content(content):
            code = _document_error_code(content)
            raise DartProviderError(
                f"DART_DOCUMENT_{code}",
                retryable=code in self.RETRYABLE_API_STATUSES,
            )
        return content


class DartDocumentStore:
    """Persist the untouched ZIP response before parsing its contents."""

    def __init__(self, runtime_root: str | Path) -> None:
        self._root = Path(runtime_root) / "raw" / "dart" / "documents"
        self._receipt_index: dict[str, Path] | None = None

    def save(self, archive: DartDocumentArchive) -> RuntimeArtifact:
        digest = hashlib.sha256(archive.content).hexdigest()
        directory = self._root / archive.collected_at.date().isoformat()
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / f"{archive.receipt_no}_{digest[:12]}.zip"
        _atomic_write(target, archive.content)
        if self._receipt_index is not None:
            self._receipt_index[archive.receipt_no] = target
        return RuntimeArtifact(target, digest)

    def load(self, receipt_no: str) -> tuple[RuntimeArtifact, bytes] | None:
        """Return a previously verified archive so interrupted backfills can resume."""
        receipt = str(receipt_no).strip()
        if re.fullmatch(r"[0-9]{14}", receipt) is None:
            raise ValueError("DART document receipt number must contain 14 digits")
        if self._receipt_index is None:
            self._receipt_index = {}
            for path in sorted(self._root.glob("*/*.zip")):
                stored_receipt = path.name.partition("_")[0]
                if re.fullmatch(r"[0-9]{14}", stored_receipt):
                    self._receipt_index[stored_receipt] = path
        path = self._receipt_index.get(receipt)
        if path is not None:
            content = path.read_bytes()
            if _is_zip_content(content):
                digest = hashlib.sha256(content).hexdigest()
                if path.stem == f"{receipt}_{digest[:12]}":
                    return RuntimeArtifact(path, digest), content
            self._receipt_index.pop(receipt, None)
        return None


class DartDocumentTextExtractor:
    """Extract bounded text from an official DART ZIP without writing members."""

    TEXT_SUFFIXES = {".xml", ".html", ".htm", ".txt"}

    def extract(self, content: bytes) -> str:
        if not _is_zip_content(content):
            raise ValueError("DART document response is not a ZIP archive")

        text_parts: list[str] = []
        total_uncompressed = 0
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            members = archive.infolist()
            if len(members) > MAX_DOCUMENT_FILES:
                raise ValueError("DART document archive contains too many files")

            for member in members:
                if member.is_dir():
                    continue
                _validate_document_member(member)
                total_uncompressed += member.file_size
                if total_uncompressed > MAX_DOCUMENT_UNCOMPRESSED_BYTES:
                    raise ValueError("DART document archive expands beyond the limit")
                suffix = Path(member.filename).suffix.lower()
                if suffix not in self.TEXT_SUFFIXES:
                    continue
                decoded = _decode_document_bytes(archive.read(member))
                extracted = _markup_text(decoded)
                if extracted:
                    text_parts.append(extracted)

        if not text_parts:
            raise ValueError("DART document archive contains no readable text")
        combined = " ".join(text_parts)
        combined = re.sub(r"\s+", " ", combined).strip()
        if len(combined) > MAX_DOCUMENT_TEXT_CHARS:
            combined = combined[:MAX_DOCUMENT_TEXT_CHARS]
        return combined


class DartDocumentService:
    """Download, persist, then safely extract one official disclosure."""

    def __init__(
        self,
        provider: DartDocumentProvider,
        store: DartDocumentStore,
        extractor: DartDocumentTextExtractor | None = None,
    ) -> None:
        self._provider = provider
        self._store = store
        self._extractor = extractor or DartDocumentTextExtractor()

    def fetch_and_extract(self, receipt_no: str) -> DartDocumentResult:
        cached = self._store.load(receipt_no)
        if cached is not None:
            artifact, content = cached
            return DartDocumentResult(artifact, self._extractor.extract(content))
        archive = self._provider.fetch(receipt_no)
        artifact = self._store.save(archive)
        text = self._extractor.extract(archive.content)
        return DartDocumentResult(artifact, text)


class DartRawStore:
    """Persist sanitized request metadata and the untouched JSON response."""

    def __init__(self, runtime_root: str | Path) -> None:
        self._root = Path(runtime_root) / "raw" / "dart"

    def save(self, page: DartRawPage) -> RuntimeArtifact:
        envelope = {
            "provider": "open_dart",
            "collected_at": page.collected_at.isoformat(),
            "request": {
                "company_id": page.company.company_id,
                "corp_code": page.company.corp_code,
                "begin_date": page.begin_date,
                "end_date": page.end_date,
                "page_no": page.page_no,
                "page_count": page.page_count,
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
        directory = self._root / page.collected_at.date().isoformat()
        directory.mkdir(parents=True, exist_ok=True)
        timestamp = page.collected_at.strftime("%H%M%S%f")
        target = directory / (
            f"{page.company.company_id}_{timestamp}_{digest[:12]}.json"
        )
        _atomic_write(target, content)
        return RuntimeArtifact(target, digest)


class DartCandidateNormalizer:
    """Convert an already persisted DART response into Data A candidate rows."""

    def normalize(self, page: DartRawPage) -> NormalizedCandidateBatch:
        candidates: list[dict] = []
        active_keys: set[tuple[str, ...]] = set()

        for index, raw_item in enumerate(page.payload.get("list", []), start=1):
            candidate = self._normalize_item(page, raw_item, index)
            if candidate["validation_status"] != "rejected":
                dedup_key = candidate_dedup_key(candidate)
                if dedup_key in active_keys:
                    candidate = {
                        **candidate,
                        "validation_status": "rejected",
                        "matched_event_id": None,
                        "rejection_reason": "duplicate_dart_candidate",
                    }
                else:
                    active_keys.add(dedup_key)
            candidates.append(candidate)

        validate_candidate_rows(candidates)
        return NormalizedCandidateBatch(
            candidates=candidates,
            dedup_keys=[candidate_dedup_key(row) for row in candidates],
        )

    def _normalize_item(
        self,
        page: DartRawPage,
        raw_item: object,
        index: int,
    ) -> dict:
        item = raw_item if isinstance(raw_item, dict) else {}
        reason = _candidate_rejection_reason(page.company, item)
        receipt = str(item.get("rcept_no") or "").strip()
        title = str(item.get("report_nm") or "").strip()
        receipt_date = str(item.get("rcept_dt") or "").strip()

        if reason is None:
            published_at = datetime.strptime(receipt_date, "%Y%m%d").date().isoformat()
            url = DART_VIEWER_URL.format(receipt_no=receipt)
            external_id: str | None = receipt
            safe_title = title[:500]
        else:
            published_at = page.collected_at.date().isoformat()
            valid_receipt = re.fullmatch(r"[0-9]{14}", receipt) is not None
            url = (
                DART_VIEWER_URL.format(receipt_no=receipt)
                if valid_receipt
                else DART_FALLBACK_URL
            )
            external_id = receipt if valid_receipt else None
            safe_title = (title or "Open DART rejected disclosure")[:500]

        normalized_title = normalize_text(safe_title) or "opendartrejecteddisclosure"
        description_parts = [
            str(item.get("flr_nm") or "").strip(),
            str(item.get("rm") or "").strip(),
        ]
        description = " | ".join(part for part in description_parts if part)
        if not description:
            description = safe_title

        candidate = {
            "candidate_id": _candidate_id(page.company, receipt, index),
            "company_id": page.company.company_id,
            "company_name": page.company.company_name,
            "detection_source_type": "dart_disclosure",
            "source_name": "dart.fss.or.kr",
            "external_id": external_id,
            "query": f"{page.company.company_name} Open DART disclosure",
            "title": safe_title,
            "normalized_title": normalized_title[:500],
            "published_at": published_at,
            "collected_at": page.collected_at.isoformat(),
            "url": url,
            "canonical_url": canonicalize_url(url),
            "description": description[:2000],
            "content_hash": "",
            "validation_status": "rejected" if reason else "pending",
            "matched_event_id": None,
            "rejection_reason": reason,
        }
        candidate["content_hash"] = candidate_content_hash(candidate)
        return candidate


class DartCandidateStore:
    """Persist schema-shaped candidate rows outside the active processed snapshot."""

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
        self._root = Path(runtime_root) / "candidate" / "dart"

    def save(
        self,
        page: DartRawPage,
        batch: NormalizedCandidateBatch,
        raw_artifact: RuntimeArtifact,
    ) -> RuntimeArtifact:
        validate_candidate_rows(batch.candidates)
        directory = self._root / page.collected_at.date().isoformat()
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


class DartCollectionService:
    """Collection boundary: provider -> raw artifact -> candidate artifact."""

    def __init__(
        self,
        provider: DartDisclosureProvider,
        raw_store: DartRawStore,
        candidate_store: DartCandidateStore,
        normalizer: DartCandidateNormalizer | None = None,
        document_service: DartDocumentService | None = None,
    ) -> None:
        self._provider = provider
        self._raw_store = raw_store
        self._candidate_store = candidate_store
        self._normalizer = normalizer or DartCandidateNormalizer()
        self._document_service = document_service

    def collect_company(
        self,
        company: DartCompany,
        begin_date: date | str,
        end_date: date | str,
        *,
        page_no: int = 1,
        page_count: int = 100,
    ) -> DartCollectionBatch:
        page = self._provider.fetch_company(
            company,
            begin_date,
            end_date,
            page_no=page_no,
            page_count=page_count,
        )
        raw_artifact = self._raw_store.save(page)
        normalized = self._normalizer.normalize(page)
        document_artifacts = self._enrich_from_documents(normalized)
        candidate_artifact = self._candidate_store.save(
            page,
            normalized,
            raw_artifact,
        )
        return DartCollectionBatch(
            company=company,
            raw_artifact=raw_artifact,
            candidate_artifact=candidate_artifact,
            candidates=normalized.candidates,
            dedup_keys=normalized.dedup_keys,
            document_artifacts=document_artifacts,
            total_pages=_response_total_pages(page.payload),
        )

    def _enrich_from_documents(
        self,
        batch: NormalizedCandidateBatch,
    ) -> dict[str, RuntimeArtifact]:
        if self._document_service is None:
            return {}

        artifacts: dict[str, RuntimeArtifact] = {}
        for candidate in batch.candidates:
            if candidate["validation_status"] == "rejected":
                continue
            receipt = str(candidate.get("external_id") or "")
            try:
                document = self._document_service.fetch_and_extract(receipt)
                artifacts[receipt] = document.artifact
                _apply_document_evidence(candidate, document.text)
            except DartProviderError as error:
                if error.code not in {"DART_DOCUMENT_013", "DART_DOCUMENT_014"}:
                    raise
                candidate.update(
                    validation_status="rejected",
                    matched_event_id=None,
                    rejection_reason=error.code.lower()[:500],
                )
            except Exception as error:
                code = str(
                    getattr(error, "code", "DART_DOCUMENT_EXTRACTION_FAILED")
                )
                candidate.update(
                    validation_status="rejected",
                    matched_event_id=None,
                    rejection_reason=code.lower()[:500],
                )

        validate_candidate_rows(batch.candidates)
        return artifacts

    def collect_all(
        self,
        begin_date: date | str,
        end_date: date | str,
        *,
        page_count: int = 100,
    ) -> list[DartCollectionBatch]:
        return [
            self.collect_company(
                company,
                begin_date,
                end_date,
                page_count=page_count,
            )
            for company in DART_COMPANIES
        ]


def build_dart_collection_service() -> DartCollectionService:
    """Build the internal adapter from environment-backed application settings."""
    provider = DartDisclosureProvider(
        api_key=DART_API_KEY,
        base_url=DART_BASE_URL,
        timeout_seconds=DART_TIMEOUT_SECONDS,
        max_attempts=DART_MAX_ATTEMPTS,
        retry_backoff_seconds=DART_RETRY_BACKOFF_SECONDS,
    )
    document_service = DartDocumentService(
        DartDocumentProvider(
            api_key=DART_API_KEY,
            base_url=DART_BASE_URL,
            timeout_seconds=DART_TIMEOUT_SECONDS,
            max_attempts=DART_MAX_ATTEMPTS,
            retry_backoff_seconds=DART_RETRY_BACKOFF_SECONDS,
        ),
        DartDocumentStore(ISSUE_RUNTIME_DATA_DIR),
    )
    return DartCollectionService(
        provider,
        DartRawStore(ISSUE_RUNTIME_DATA_DIR),
        DartCandidateStore(ISSUE_RUNTIME_DATA_DIR),
        document_service=document_service,
    )


def _dart_date(value: date | str) -> str:
    if isinstance(value, date):
        return value.strftime("%Y%m%d")
    parsed = datetime.strptime(str(value), "%Y%m%d")
    return parsed.strftime("%Y%m%d")


def _response_total_pages(payload: dict) -> int:
    try:
        total_pages = int(payload.get("total_page", 1))
    except (TypeError, ValueError) as error:
        raise DartProviderError("DART_INVALID_RESPONSE", retryable=False) from error
    return max(1, total_pages)


def _candidate_rejection_reason(company: DartCompany, item: dict) -> str | None:
    if str(item.get("corp_code") or "").strip() != company.corp_code:
        return "dart_company_mismatch"
    stock_code = str(item.get("stock_code") or "").strip()
    if stock_code and stock_code != company.company_id:
        return "dart_stock_code_mismatch"
    if str(item.get("corp_name") or "").strip() != company.company_name:
        return "dart_company_name_mismatch"
    if re.fullmatch(r"[0-9]{14}", str(item.get("rcept_no") or "").strip()) is None:
        return "invalid_dart_receipt_number"
    title = str(item.get("report_nm") or "").strip()
    if not title:
        return "missing_dart_report_title"
    try:
        datetime.strptime(str(item.get("rcept_dt") or "").strip(), "%Y%m%d")
    except ValueError:
        return "invalid_dart_receipt_date"
    return None


def _candidate_id(company: DartCompany, receipt: str, index: int) -> str:
    identity = f"{company.company_id}|{receipt}|{index}"
    numeric = int(hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16], 16)
    return f"CND-{numeric:020d}"


class _DocumentTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in {"script", "style"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth and data.strip():
            self.parts.append(data)


def _is_zip_content(content: bytes) -> bool:
    try:
        return bool(content) and zipfile.is_zipfile(io.BytesIO(content))
    except (OSError, zipfile.BadZipFile):
        return False


def _document_error_code(content: bytes) -> str:
    try:
        root = ElementTree.fromstring(content)
        status = root.findtext(".//status")
    except ElementTree.ParseError:
        status = None
    normalized = str(status or "INVALID_RESPONSE").strip()
    return normalized if re.fullmatch(r"[0-9]{3}", normalized) else "INVALID_RESPONSE"


def _validate_document_member(member: zipfile.ZipInfo) -> None:
    normalized_name = member.filename.replace("\\", "/")
    path = PurePosixPath(normalized_name)
    if (
        not normalized_name
        or "\x00" in normalized_name
        or path.is_absolute()
        or ".." in path.parts
    ):
        raise ValueError("unsafe path in DART document archive")
    if member.flag_bits & 0x1:
        raise ValueError("encrypted DART document archive member is not allowed")
    if member.file_size < 0:
        raise ValueError("invalid DART document archive member size")


def _decode_document_bytes(content: bytes) -> str:
    declared = re.search(
        br"encoding\s*=\s*['\"]([A-Za-z0-9._-]+)['\"]",
        content[:250],
        flags=re.IGNORECASE,
    )
    encodings = []
    if declared:
        encodings.append(declared.group(1).decode("ascii", errors="ignore"))
    encodings.extend(["utf-8", "cp949", "euc-kr"])
    for encoding in dict.fromkeys(encodings):
        try:
            return content.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    return content.decode("utf-8", errors="replace")


def _markup_text(value: str) -> str:
    parser = _DocumentTextParser()
    parser.feed(value)
    parser.close()
    return re.sub(r"\s+", " ", unescape(" ".join(parser.parts))).strip()


def _apply_document_evidence(candidate: dict, document_text: str) -> None:
    body_rule = candidate_classification_rule(
        document_text,
        pattern_field="body_pattern",
    )
    if body_rule is None:
        candidate.update(
            validation_status="rejected",
            matched_event_id=None,
            rejection_reason="dart_document_no_approved_esg_event_match",
        )
        return

    pattern = re.compile(str(body_rule["body_pattern"]), flags=re.IGNORECASE)
    match = pattern.search(document_text)
    if match is None:
        raise AssertionError("classification rule matched without a text span")
    start = max(0, match.start() - 750)
    end = min(len(document_text), match.end() + 750)
    excerpt = re.sub(r"\s+", " ", document_text[start:end]).strip()
    title_rule = candidate_classification_rule(str(candidate.get("title") or ""))
    match_source = (
        "DART_TITLE_MATCH"
        if title_rule and title_rule["rule_id"] == body_rule["rule_id"]
        else "DART_BODY_MATCH"
    )
    candidate["description"] = (
        f"{match_source}[{body_rule['rule_id']}]: {excerpt}"
    )[:2000]


def _atomic_write(target: Path, content: bytes) -> None:
    temporary = target.with_suffix(f"{target.suffix}.tmp")
    with temporary.open("wb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, target)
