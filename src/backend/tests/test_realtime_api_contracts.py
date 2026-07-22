import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_DIR = ROOT / "schemas" / "api"
EXAMPLE_DIR = SCHEMA_DIR / "examples"

CONTRACTS = [
    ("market-quotes-response.schema.json", "market-quotes-response.example.json"),
    ("portfolio-summary-request.schema.json", "portfolio-summary-request.example.json"),
    ("portfolio-summary-response.schema.json", "portfolio-summary-response.example.json"),
    ("sync-issues-request.schema.json", "sync-issues-request.example.json"),
    ("sync-status-response.schema.json", "sync-status-response.example.json"),
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("schema_name,example_name", CONTRACTS)
def test_contract_schema_and_example_are_valid(schema_name: str, example_name: str) -> None:
    schema = load_json(SCHEMA_DIR / schema_name)
    example = load_json(EXAMPLE_DIR / example_name)

    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(example)


def test_market_quotes_example_has_exact_required_instruments() -> None:
    example = load_json(EXAMPLE_DIR / "market-quotes-response.example.json")
    instrument_ids = [quote["instrument_id"] for quote in example["quotes"]]

    assert set(instrument_ids) == {"KOSPI", "KOSDAQ", "005930", "000660"}
    assert len(instrument_ids) == len(set(instrument_ids)) == 4


def test_fallback_market_quote_must_be_marked_stale() -> None:
    schema = load_json(SCHEMA_DIR / "market-quotes-response.schema.json")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    fallback = load_json(EXAMPLE_DIR / "market-quotes-response.example.json")
    fallback["quotes"][0]["price_status"] = "fallback"

    assert list(validator.iter_errors(fallback))

    fallback["quotes"][0]["is_stale"] = True
    validator.validate(fallback)


def test_portfolio_request_allows_one_holding_but_rejects_duplicate_ticker() -> None:
    schema = load_json(SCHEMA_DIR / "portfolio-summary-request.schema.json")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    one_holding = {
        "holdings": [{"ticker": "005930", "quantity": 1, "average_price": 70000}]
    }
    duplicate = {
        "holdings": [
            {"ticker": "005930", "quantity": 1, "average_price": 70000},
            {"ticker": "005930", "quantity": 2, "average_price": 71000},
        ]
    }

    validator.validate(one_holding)
    assert list(validator.iter_errors(duplicate))


def test_portfolio_summary_example_arithmetic_is_consistent() -> None:
    example = load_json(EXAMPLE_DIR / "portfolio-summary-response.example.json")
    positions = example["positions"]

    assert sum(position["purchase_value"] for position in positions) == example["total_purchase_value"]
    assert sum(position["market_value"] for position in positions) == example["total_market_value"]
    assert sum(position["unrealized_profit_loss"] for position in positions) == example["total_unrealized_profit_loss"]
    assert sum(position["current_weight"] for position in positions) == pytest.approx(1.0, abs=0.000001)


def test_sync_state_requires_timestamps_that_match_status() -> None:
    schema = load_json(SCHEMA_DIR / "sync-status-response.schema.json")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    success = load_json(EXAMPLE_DIR / "sync-status-response.example.json")
    invalid_running = deepcopy(success)
    invalid_running["status"] = "running"

    assert list(validator.iter_errors(invalid_running))

    valid_running = deepcopy(invalid_running)
    valid_running["stage"] = "validating"
    valid_running["completed_at"] = None
    valid_running["snapshot_updated"] = False
    valid_running["published_items"] = 0
    valid_running["published_snapshot_version"] = None
    valid_running["published_at"] = None
    valid_running["recalculation_triggered"] = False
    valid_running["recalculation_status"] = "not_requested"
    valid_running["recalculated_at"] = None
    validator.validate(valid_running)


def test_sync_success_without_new_snapshot_is_explicit() -> None:
    schema = load_json(SCHEMA_DIR / "sync-status-response.schema.json")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    no_change = load_json(EXAMPLE_DIR / "sync-status-response.example.json")
    no_change["snapshot_updated"] = False
    no_change["published_items"] = 0
    no_change["published_snapshot_version"] = None
    no_change["published_at"] = None
    no_change["recalculation_triggered"] = False
    no_change["recalculation_status"] = "not_requested"
    no_change["recalculated_at"] = None

    validator.validate(no_change)


def test_sync_snapshot_update_requires_publication_evidence() -> None:
    schema = load_json(SCHEMA_DIR / "sync-status-response.schema.json")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    invalid = load_json(EXAMPLE_DIR / "sync-status-response.example.json")
    invalid["published_snapshot_version"] = None

    assert list(validator.iter_errors(invalid))
