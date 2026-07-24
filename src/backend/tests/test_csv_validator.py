import os
import sys
from copy import deepcopy

import jsonschema
import pytest


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import BASE_DIR
from app.utils.csv_validator import (
    ESG_SCHEMA_PATH,
    EVENTS_SCHEMA_PATH,
    load_schema,
    validate_csv_file,
)


def test_processed_esg_nullable_numbers_are_cast_and_validated():
    rows = validate_csv_file(
        os.path.join(BASE_DIR, "data", "processed", "esg_indicators.csv"),
        "esg",
    )

    assert len(rows) == 64
    assert isinstance(rows[0]["raw_value"], float)
    assert isinstance(rows[0]["target_value"], float)
    assert isinstance(rows[0]["baseline_value"], float)


def test_sample_esg_matches_current_schema():
    rows = validate_csv_file(
        os.path.join(BASE_DIR, "data", "sample", "esg_indicators.sample.csv"),
        "esg",
    )

    assert len(rows) == 2
    assert {row["source_id"] for row in rows} == {"SRC-0001", "SRC-0004"}


def test_sample_events_match_current_schema():
    rows = validate_csv_file(
        os.path.join(BASE_DIR, "data", "sample", "events.sample.csv"),
        "event",
    )

    assert len(rows) == 2
    assert rows[0]["resolved_date"] is None
    assert {row["linked_indicator_id"] for row in rows} == {"S01", "G03"}


def test_esg_unavailable_requires_null_and_never_zero():
    schema = load_schema(ESG_SCHEMA_PATH)
    unavailable = deepcopy(schema["examples"][0])
    unavailable["availability"] = "unavailable"
    unavailable["raw_value"] = None

    jsonschema.validate(instance=unavailable, schema=schema)

    invalid_zero = deepcopy(unavailable)
    invalid_zero["raw_value"] = 0
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_zero, schema=schema)


def test_esg_available_requires_numeric_raw_value():
    schema = load_schema(ESG_SCHEMA_PATH)
    available_without_value = deepcopy(schema["examples"][0])
    available_without_value["raw_value"] = None

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=available_without_value, schema=schema)


def test_event_status_is_separate_from_enforcement_action():
    schema = load_schema(EVENTS_SCHEMA_PATH)
    event = deepcopy(schema["examples"][0])
    event["status"] = "confirmed"
    event["enforcement_action"] = "sanctioned"

    jsonschema.validate(instance=event, schema=schema)

    invalid_status = deepcopy(event)
    invalid_status["status"] = "sanctioned"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_status, schema=schema)
