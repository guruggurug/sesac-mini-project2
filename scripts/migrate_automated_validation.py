"""Migrate legacy human-review fields to the automated-validation contract."""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))

from app.utils.issue_rules import (  # noqa: E402
    calculate_event_severity,
    candidate_content_hash,
    canonicalize_url,
    load_issue_rules,
    normalize_text,
)


COMPANY_IDS = {"삼성전자": "005930", "SK하이닉스": "000660"}
SOURCE_COMPANY_IDS = {
    "SRC-0001": "005930",
    "SRC-0002": "005930",
    "SRC-0003": "005930",
    "SRC-0004": "000660",
    "SRC-0005": "000660",
    "SRC-0006": "005930",
    "SRC-0007": "005930",
    "SRC-0008": "000660",
    "SRC-0009": "000660",
    "SRC-0010": "005930",
}
CANDIDATE_EVENT_IDS = {
    "CND-0001": "EVT-0001",
    "CND-0002": "EVT-0002",
    "CND-0003": "EVT-0003",
    "CND-0004": "EVT-0004",
}


def rewrite_csv(
    relative_path: str,
    *,
    remove_columns: set[str] | None = None,
    rename_columns: dict[str, str] | None = None,
    replacements: dict[str, dict[str, str]] | None = None,
) -> None:
    path = ROOT / relative_path
    remove_columns = remove_columns or set()
    rename_columns = rename_columns or {}
    replacements = replacements or {}

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise ValueError(f"CSV header is missing: {path}")
        original_fields = reader.fieldnames
        rows = list(reader)

    fields = [
        rename_columns.get(field, field)
        for field in original_fields
        if field not in remove_columns
    ]
    migrated_rows: list[dict[str, str]] = []
    for row in rows:
        migrated: dict[str, str] = {}
        for field in original_fields:
            if field in remove_columns:
                continue
            target_field = rename_columns.get(field, field)
            value = row.get(field, "")
            value = replacements.get(target_field, {}).get(value, value)
            migrated[target_field] = value
        migrated_rows.append(migrated)

    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(migrated_rows)
    temporary.replace(path)


def migrate_event_csv(relative_path: str) -> None:
    path = ROOT / relative_path
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise ValueError(f"CSV header is missing: {path}")
        original_fields = [field for field in reader.fieldnames if field != "review_status"]
        rows = list(reader)

    fields = list(original_fields)
    if "detection_source_type" not in fields:
        fields.insert(fields.index("status"), "detection_source_type")
    if "enforcement_action" not in fields:
        fields.insert(fields.index("status") + 1, "enforcement_action")
    if "severity_rule_version" not in fields:
        fields.insert(fields.index("severity") + 1, "severity_rule_version")

    rules = load_issue_rules()

    migrated_rows: list[dict[str, str]] = []
    for row in rows:
        migrated = {field: row.get(field, "") for field in original_fields}
        original_status = migrated.get("status", "")
        resolved_date = migrated.get("resolved_date", "")

        if not migrated.get("detection_source_type"):
            official_url = migrated.get("official_source_url", "")
            migrated["detection_source_type"] = (
                "dart_disclosure" if "dart.fss.or.kr" in official_url else "news"
            )
        if not migrated.get("enforcement_action"):
            if original_status == "sanctioned":
                evidence = " ".join(
                    migrated.get(field, "")
                    for field in ("summary", "severity_evidence", "note")
                )
                if "과태료" in evidence or "과징금" in evidence:
                    migrated["enforcement_action"] = "fine"
                elif "시정명령" in evidence or "시정조치" in evidence:
                    migrated["enforcement_action"] = "corrective_order"
                else:
                    migrated["enforcement_action"] = "sanctioned"
            elif original_status == "resolved":
                migrated["enforcement_action"] = "fine"
            else:
                migrated["enforcement_action"] = "no_action"

        if migrated.get("enforcement_action") == "none":
            migrated["enforcement_action"] = "no_action"

        if original_status == "sanctioned":
            migrated["status"] = "resolved" if resolved_date else "confirmed"
        elif original_status == "rumor":
            raise ValueError(f"Rumor must not be normalized into event data: {path}")

        migrated["severity"], _ = calculate_event_severity(migrated, rules)
        migrated["severity_rule_version"] = rules["version"]

        migrated_rows.append(migrated)

    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(migrated_rows)
    temporary.replace(path)


def _external_id(url: str) -> str:
    query = parse_qs(urlsplit(url).query)
    for key in ("rcpNo", "articleNo", "bbs_seq", "report_data_no", "nttId", "idx"):
        if query.get(key):
            return query[key][0]
    return ""


def migrate_candidate_csv(relative_path: str) -> None:
    path = ROOT / relative_path
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise ValueError(f"CSV header is missing: {path}")
        rows = list(reader)

    fields = [
        "candidate_id", "company_id", "company_name", "detection_source_type",
        "source_name", "external_id", "query", "title", "normalized_title",
        "published_at", "collected_at", "url", "canonical_url", "description",
        "content_hash", "validation_status", "matched_event_id", "rejection_reason",
    ]
    migrated_rows: list[dict[str, str]] = []
    for row in rows:
        company_name = row["company_name"]
        url = row["url"]
        host = urlsplit(url).netloc.lower()
        migrated: dict[str, str] = {
            "candidate_id": row["candidate_id"],
            "company_id": COMPANY_IDS[company_name],
            "company_name": company_name,
            "detection_source_type": "dart_disclosure" if host == "dart.fss.or.kr" else "news",
            "source_name": host,
            "external_id": _external_id(url),
            "query": row["query"],
            "title": row["title"],
            "normalized_title": normalize_text(row["title"]),
            "published_at": row["published_at"],
            "collected_at": row.get("collected_at") or "2026-07-22T00:00:00+09:00",
            "url": url,
            "canonical_url": canonicalize_url(url),
            "description": row["description"],
            "content_hash": "",
            "validation_status": "",
            "matched_event_id": "",
            "rejection_reason": "",
        }
        migrated["content_hash"] = candidate_content_hash(migrated)
        matched_event_id = CANDIDATE_EVENT_IDS.get(row["candidate_id"])
        if matched_event_id:
            migrated["validation_status"] = "validated"
            migrated["matched_event_id"] = matched_event_id
        else:
            migrated["validation_status"] = "rejected"
            migrated["rejection_reason"] = "공식 출처와 일치하는 처리 사건 없음"
        migrated_rows.append(migrated)

    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(migrated_rows)
    temporary.replace(path)


def migrate_source_csv(relative_path: str) -> None:
    path = ROOT / relative_path
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise ValueError(f"CSV header is missing: {path}")
        rows = list(reader)

    fields = [
        "source_id", "company_id", "organization_name", "source_type",
        "document_title", "publication_year", "external_id", "file_name", "url",
        "validation_method", "content_hash", "validated", "note",
    ]
    migrated_rows = []
    for row in rows:
        url = row["url"]
        migrated_rows.append({
            "source_id": row["source_id"],
            "company_id": SOURCE_COMPANY_IDS.get(row["source_id"], ""),
            "organization_name": row.get("organization_name") or row.get("company_name", ""),
            "source_type": row["source_type"],
            "document_title": row["document_title"],
            "publication_year": row["publication_year"],
            "external_id": _external_id(url),
            "file_name": row.get("file_name", ""),
            "url": url,
            "validation_method": "dart_receipt" if "dart.fss.or.kr" in url else "official_domain",
            "content_hash": row.get("content_hash", ""),
            "validated": "true",
            "note": row["note"],
        })

    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(migrated_rows)
    temporary.replace(path)


def migrate_event_source_csv(relative_path: str) -> None:
    path = ROOT / relative_path
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise ValueError(f"CSV header is missing: {path}")
        rows = list(reader)
    role_map = {
        "government_disclosure": "official_confirmation",
        "regulator_disclosure": "official_confirmation",
        "company_briefing": "company_response",
    }
    for row in rows:
        row["source_role"] = role_map.get(row["source_role"], row["source_role"])
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=reader.fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def main() -> None:
    rewrite_csv(
        "data/processed/esg_indicators.csv",
        remove_columns={"review_status"},
        replacements={"note": {"원문 검수 완료": "자동 출처 검증 완료"}},
    )
    for relative_path in (
        "data/processed/events.csv",
        "data/sample/events.sample.csv",
    ):
        migrate_event_csv(relative_path)

    for relative_path in ("data/sample/esg_indicators.sample.csv",):
        rewrite_csv(relative_path, remove_columns={"review_status"})

    migrate_candidate_csv("data/candidate/news_candidates.csv")
    migrate_source_csv("data/processed/sources.csv")
    migrate_event_source_csv("data/processed/event_sources.csv")
    for relative_path in (
        "data/processed/stock_prices.csv",
        "data/prices.csv",
    ):
        rewrite_csv(
            relative_path,
            replacements={
                "data_status": {"reviewed": "validated"},
                "note": {
                    "SK하이닉스 3개년 일별 주가 수집 검수 완료 데이터": "SK하이닉스 3개년 일별 주가 자동 검증 완료 데이터",
                    "삼성전자 3개년 일별 주가 수집 검수 완료 데이터": "삼성전자 3개년 일별 주가 자동 검증 완료 데이터",
                },
            },
        )


if __name__ == "__main__":
    main()
