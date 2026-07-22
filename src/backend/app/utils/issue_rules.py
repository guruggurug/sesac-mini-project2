"""Deterministic candidate deduplication and event severity rules."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.core.config import BASE_DIR


RULES_PATH = Path(BASE_DIR) / "schemas" / "data" / "issue-pipeline-rules.json"


def load_issue_rules(path: Path = RULES_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_text(value: str) -> str:
    lowered = str(value).strip().lower()
    return re.sub(r"[^0-9a-z가-힣]+", "", lowered)


def canonicalize_url(url: str, rules: dict[str, Any] | None = None) -> str:
    rules = rules or load_issue_rules()
    url_rules = rules["candidate_deduplication"]["canonical_url"]
    parsed = urlsplit(url.strip())
    host = parsed.netloc.lower() if url_rules["lowercase_host"] else parsed.netloc
    removed = set(url_rules["remove_query_parameters"])
    query = urlencode(
        sorted((key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True) if key not in removed)
    )
    fragment = "" if url_rules["remove_fragment"] else parsed.fragment
    return urlunsplit((parsed.scheme.lower(), host, parsed.path, query, fragment))


def candidate_content_hash(candidate: dict[str, Any]) -> str:
    payload = "|".join(
        (
            str(candidate["company_id"]),
            normalize_text(candidate["title"]),
            str(candidate["published_at"]),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def candidate_dedup_key(candidate: dict[str, Any]) -> tuple[str, ...]:
    external_id = candidate.get("external_id")
    if external_id:
        return (
            "external_id",
            str(candidate["detection_source_type"]),
            str(candidate["source_name"]),
            str(external_id),
        )
    canonical_url = candidate.get("canonical_url") or canonicalize_url(str(candidate["url"]))
    if canonical_url:
        return ("canonical_url", str(canonical_url))
    content_hash = candidate.get("content_hash") or candidate_content_hash(candidate)
    return ("content_hash", str(candidate["company_id"]), str(content_hash))


def source_dedup_key(
    source: dict[str, Any], rules: dict[str, Any] | None = None
) -> tuple[str, ...]:
    rules = rules or load_issue_rules()
    source_rules = rules["source_deduplication"]
    fields = (
        source_rules["external_id_key"]
        if source.get("external_id")
        else source_rules["fallback_key"]
    )
    return tuple(str(source.get(field) or "") for field in fields)


def _event_text(event: dict[str, Any], fields: list[str]) -> set[str]:
    joined = " ".join(str(event.get(field) or "") for field in fields).lower()
    return {token for token in re.findall(r"[0-9a-z가-힣]+", joined) if token}


def event_token_similarity(
    left: dict[str, Any],
    right: dict[str, Any],
    rules: dict[str, Any] | None = None,
) -> float:
    rules = rules or load_issue_rules()
    fields = rules["event_deduplication"]["text_fields"]
    left_tokens = _event_text(left, fields)
    right_tokens = _event_text(right, fields)
    if not left_tokens and not right_tokens:
        return 1.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def events_are_duplicates(
    left: dict[str, Any],
    right: dict[str, Any],
    rules: dict[str, Any] | None = None,
) -> bool:
    rules = rules or load_issue_rules()
    dedup = rules["event_deduplication"]
    if any(left.get(field) != right.get(field) for field in dedup["identity_fields"]):
        return False

    left_date = date.fromisoformat(str(left[dedup["date_field"]]))
    right_date = date.fromisoformat(str(right[dedup["date_field"]]))
    if abs((left_date - right_date).days) > dedup["date_tolerance_days"]:
        return False

    return event_token_similarity(left, right, rules) >= dedup["minimum_token_similarity"]


def calculate_event_severity(
    event: dict[str, Any],
    rules: dict[str, Any] | None = None,
) -> tuple[int, list[str]]:
    rules = rules or load_issue_rules()
    severity_rules = rules["severity"]
    score = severity_rules["enforcement_base_score"].get(
        event.get("enforcement_action"), severity_rules["default_score"]
    )
    matched_keywords: list[str] = []
    text = " ".join(str(event.get(field) or "") for field in severity_rules["text_fields"]).lower()

    for rule in severity_rules["keyword_rules"]:
        for keyword in rule["keywords"]:
            keyword_text = text
            for phrase in severity_rules.get("negated_keyword_phrases", {}).get(
                keyword, []
            ):
                keyword_text = keyword_text.replace(phrase.lower(), "")
            if keyword.lower() in keyword_text:
                score = max(score, rule["score"])
                matched_keywords.append(keyword)

    return min(score, severity_rules["maximum_score"]), sorted(set(matched_keywords))
