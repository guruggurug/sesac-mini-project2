import json
import os
import shutil
import sys
from copy import deepcopy
from pathlib import Path

import jsonschema
import pytest


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import BASE_DIR
from app.core.exceptions import CSVValidationError
from app.utils.csv_validator import (
    EVENTS_SCHEMA_PATH,
    FORMAT_CHECKER,
    load_schema,
    validate_csv_file,
    validate_data_a_bundle,
)
from app.utils.issue_rules import (
    calculate_event_severity,
    candidate_dedup_key,
    canonicalize_url,
    events_are_duplicates,
    load_issue_rules,
    source_dedup_key,
)


ROOT = Path(BASE_DIR)


def test_issue_rules_match_their_schema():
    rules = load_issue_rules()
    schema = json.loads(
        (ROOT / "schemas" / "data" / "issue-pipeline-rules.schema.json").read_text(
            encoding="utf-8"
        )
    )

    jsonschema.validate(instance=rules, schema=schema)


def test_candidate_source_and_event_source_csvs_match_contracts():
    candidates = validate_csv_file(
        str(ROOT / "data" / "candidate" / "news_candidates.csv"), "candidate"
    )
    sources = validate_csv_file(
        str(ROOT / "data" / "processed" / "sources.csv"), "source"
    )
    event_sources = validate_csv_file(
        str(ROOT / "data" / "processed" / "event_sources.csv"), "event_source"
    )

    assert len(candidates) == 6
    assert len(sources) == 6
    assert len(event_sources) == 4
    assert sum(row["validation_status"] == "validated" for row in candidates) == 3
    assert sum(row["validation_status"] == "rejected" for row in candidates) == 3


def test_complete_data_a_publish_bundle_is_referentially_valid():
    bundle = validate_data_a_bundle(str(ROOT))

    assert len(bundle["events"]) == 3
    assert len(bundle["esg"]) == 78
    assert sum(row["availability"] == "unavailable" for row in bundle["esg"]) == 24


def test_event_format_checker_rejects_invalid_date():
    schema = load_schema(EVENTS_SCHEMA_PATH)
    event = deepcopy(schema["examples"][0])
    event["event_date"] = "not-a-date"

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(event, schema, format_checker=FORMAT_CHECKER)


def test_bundle_rejects_modified_raw_artifact(tmp_path):
    copied_root = tmp_path / "project"
    shutil.copytree(ROOT / "data", copied_root / "data")
    shutil.copytree(ROOT / "schemas", copied_root / "schemas")
    artifact = (
        copied_root
        / "data"
        / "raw"
        / "reports"
        / "nssc_201_samsung_radiation.pdf"
    )
    artifact.write_bytes(artifact.read_bytes() + b"tampered")

    with pytest.raises(CSVValidationError) as error:
        validate_data_a_bundle(str(copied_root))

    assert error.value.code == "INVALID_SOURCE_CONTENT_HASH"


def test_candidate_url_canonicalization_and_dedup_are_deterministic():
    first = {
        "company_id": "005930",
        "detection_source_type": "news",
        "source_name": "example.com",
        "external_id": None,
        "url": "https://EXAMPLE.com/a?id=7&utm_source=test#top",
        "title": "동일 사건",
        "published_at": "2026-07-22",
    }
    second = deepcopy(first)
    second["url"] = "https://example.com/a?utm_medium=email&id=7"

    assert canonicalize_url(first["url"]) == "https://example.com/a?id=7"
    assert candidate_dedup_key(first) == candidate_dedup_key(second)


def test_external_id_dedup_is_scoped_by_source_name():
    first = {
        "detection_source_type": "news",
        "source_name": "one.example",
        "external_id": "123",
    }
    second = {**first, "source_name": "two.example"}

    assert candidate_dedup_key(first) != candidate_dedup_key(second)


def test_source_dedup_allows_distinct_documents_on_same_landing_page():
    first = {
        "validation_method": "official_domain",
        "external_id": None,
        "url": "https://example.com/reports",
        "document_title": "DS 지속가능경영보고서",
    }
    second = {**first, "document_title": "전사 지속가능경영보고서"}

    assert source_dedup_key(first) != source_dedup_key(second)


def test_event_duplicate_requires_identity_date_and_text_similarity():
    base = {
        "company_id": "005930",
        "event_category": "occupational_safety",
        "linked_indicator_id": "S01",
        "market_event_date": "2026-07-20",
        "summary": "반도체 사업장 안전사고 조사 결과",
        "severity_evidence": "근로자 중상 사고",
    }
    within_window = {**base, "market_event_date": "2026-07-22"}
    outside_window = {**base, "market_event_date": "2026-07-24"}
    different_category = {**base, "event_category": "cybersecurity"}

    assert events_are_duplicates(base, within_window)
    assert not events_are_duplicates(base, outside_window)
    assert not events_are_duplicates(base, different_category)


def test_processed_and_sample_severity_matches_rule_version_and_recalculation():
    rules = load_issue_rules()
    for relative_path in (
        "data/processed/events.csv",
        "data/sample/events.sample.csv",
    ):
        rows = validate_csv_file(str(ROOT / relative_path), "event")
        for row in rows:
            severity, _ = calculate_event_severity(row, rules)
            assert row["severity_rule_version"] == rules["version"]
            assert row["severity"] == severity


def test_severity_uses_highest_matching_rule_without_addition():
    rules = load_issue_rules()
    event = {
        "enforcement_action": "fine",
        "summary": "개인정보 유출 후 과태료 부과",
        "severity_evidence": "",
        "responsibility_evidence": "",
        "persistence_evidence": "",
    }
    fatal_event = {**event, "summary": "사망 사고와 과태료 부과"}

    assert calculate_event_severity(event, rules)[0] == 3
    assert calculate_event_severity(fatal_event, rules)[0] == 5
    assert calculate_event_severity(fatal_event, rules) == calculate_event_severity(
        fatal_event, rules
    )


def test_bundle_rejects_semantic_duplicate_events(tmp_path):
    copied_root = tmp_path / "project"
    shutil.copytree(ROOT / "data", copied_root / "data")
    shutil.copytree(ROOT / "schemas", copied_root / "schemas")
    
    events_path = copied_root / "data" / "processed" / "events.csv"
    lines = events_path.read_text(encoding="utf-8").splitlines()
    dup_row = lines[-1].replace("EVT-0005", "EVT-9999")
    events_path.write_text("\n".join(lines + [dup_row]) + "\n", encoding="utf-8")
    
    import hashlib
    payload = "005930|violation9999|2023-06-28"
    new_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    
    dup_cand_row = [
        "CND-9999", "005930", "\uc0bc\uc131\uc804\uc790", "news", "www.pipc.go.kr", "9999",
        "query9999", "violation9999", "violation9999",
        "2023-06-28", "2026-07-22T00:00:00+09:00",
        "https://www.pipc.go.kr/np/cop/bbs/selectBoardArticle.do?bbsId=BS074&mCode=C020010000&nttId=9999",
        "https://www.pipc.go.kr/np/cop/bbs/selectBoardArticle.do?bbsId=BS074&mCode=C020010000&nttId=9999",
        "description9999",
        new_hash, "validated", "EVT-9999", ""
    ]
    dup_cand = ",".join(dup_cand_row)
    
    candidates_path = copied_root / "data" / "candidate" / "news_candidates.csv"
    c_lines = candidates_path.read_text(encoding="utf-8").splitlines()
    candidates_path.write_text("\n".join(c_lines + [dup_cand]) + "\n", encoding="utf-8")

    ev_sources_path = copied_root / "data" / "processed" / "event_sources.csv"
    es_lines = ev_sources_path.read_text(encoding="utf-8").splitlines()
    dup_es = es_lines[-1].replace("EVT-0005", "EVT-9999")
    ev_sources_path.write_text("\n".join(es_lines + [dup_es]) + "\n", encoding="utf-8")

    with pytest.raises(CSVValidationError) as error:
        validate_data_a_bundle(str(copied_root))

    assert error.value.code == "INVALID_EVENT_SEMANTIC_DUPLICATE"
    assert "EVT-0005" in error.value.message
    assert "EVT-9999" in error.value.message


def test_bundle_rejects_orphan_events(tmp_path):
    copied_root = tmp_path / "project"
    shutil.copytree(ROOT / "data", copied_root / "data")
    shutil.copytree(ROOT / "schemas", copied_root / "schemas")
    
    events_path = copied_root / "data" / "processed" / "events.csv"
    lines = events_path.read_text(encoding="utf-8").splitlines()
    # Change date to make it not a duplicate of EVT-0005
    orphan_row = lines[-1].replace("EVT-0005", "EVT-9999").replace("2023-06-28", "2023-01-01")
    events_path.write_text("\n".join(lines + [orphan_row]) + "\n", encoding="utf-8")

    ev_sources_path = copied_root / "data" / "processed" / "event_sources.csv"
    es_lines = ev_sources_path.read_text(encoding="utf-8").splitlines()
    dup_es = es_lines[-1].replace("EVT-0005", "EVT-9999")
    ev_sources_path.write_text("\n".join(es_lines + [dup_es]) + "\n", encoding="utf-8")

    with pytest.raises(CSVValidationError) as error:
        validate_data_a_bundle(str(copied_root))

    assert error.value.code == "INVALID_EVENT_CANDIDATE_REFERENCE"
    assert "EVT-9999" in error.value.message


@pytest.mark.parametrize(
    "summary",
    [
        "사고가 발생했지만 사망 없음",
        "사망자는 없었으며 경상자만 확인됨",
        "사망으로 이어지지 않음",
    ],
)
def test_severity_ignores_explicitly_negated_fatality_keyword(summary):
    rules = load_issue_rules()
    event = {
        "enforcement_action": "investigation",
        "summary": summary,
        "severity_evidence": "집중점검 착수",
        "responsibility_evidence": "",
        "persistence_evidence": "",
    }

    score, matched_keywords = calculate_event_severity(event, rules)

    assert score == 2
    assert "사망" not in matched_keywords


def test_severity_still_counts_separate_non_negated_fatality_occurrence():
    rules = load_issue_rules()
    event = {
        "enforcement_action": "investigation",
        "summary": "초기 발표에서는 사망 없음으로 알려졌으나 이후 작업자 1명 사망 확인",
        "severity_evidence": "",
        "responsibility_evidence": "",
        "persistence_evidence": "",
    }

    assert calculate_event_severity(event, rules)[0] == 5
