from __future__ import annotations

import asyncio
import csv
import hashlib
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import BASE_DIR
from app.repositories.runtime_state_repository import RuntimeStateRepository
from app.services.data_b_recalculation import (
    DataBRecalculationAdapter,
    DataBRecalculationError,
    MODEL_VERSION,
    load_active_recalculated_esg_scores,
)
from app.services.issue_snapshot_publisher import (
    IssueSnapshotPublisher,
    read_active_snapshot,
)


ROOT = Path(BASE_DIR)
PUBLISHED = datetime(2026, 7, 24, 1, 0, tzinfo=timezone.utc)
CALCULATED = PUBLISHED + timedelta(minutes=1)


def copy_valid_bundle(tmp_path: Path) -> Path:
    root = tmp_path / "bundle"
    shutil.copytree(ROOT / "data", root / "data")
    sources_path = root / "data/processed/sources.csv"
    raw_root = root / "data/raw/reports"
    raw_root.mkdir(parents=True, exist_ok=True)

    with sources_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        rows = list(reader)
    for row in rows:
        extra_note_parts = row.pop(None, [])
        if extra_note_parts:
            row["note"] = ",".join([row.get("note", ""), *extra_note_parts])
    hashes = {}
    short_names = {}
    for row in rows:
        original_name = row["file_name"]
        if original_name not in short_names:
            suffix = Path(original_name).suffix or ".bin"
            short_names[original_name] = f"fixture-{len(short_names) + 1:03d}{suffix}"
        file_name = short_names[original_name]
        if file_name not in hashes:
            payload = f"test evidence:{original_name}\n".encode("utf-8")
            (raw_root / file_name).write_bytes(payload)
            hashes[file_name] = hashlib.sha256(payload).hexdigest()
        row["file_name"] = file_name
        row["content_hash"] = hashes[file_name]
    with sources_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return root


def active_snapshot(tmp_path: Path):
    runtime = tmp_path / "runtime"
    bundle = copy_valid_bundle(tmp_path)
    IssueSnapshotPublisher(runtime, now=lambda: PUBLISHED).publish(bundle)
    return runtime, read_active_snapshot(runtime)


def price_loader():
    return (
        pd.DataFrame(
            [
                {"date": "2026-07-22", "ticker": "005930", "close": 80000},
                {"date": "2026-07-22", "ticker": "000660", "close": 200000},
                {"date": "2026-07-23", "ticker": "005930", "close": 81000},
                {"date": "2026-07-23", "ticker": "000660", "close": 198000},
            ]
        ),
        "validated",
        None,
    )


class OptimizerSpy:
    def __init__(self, error: Exception | None = None):
        self.error = error
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return {
            "recommended_weights": {"005930": 0.6, "000660": 0.4},
            "current_total_risk": 0.5,
            "optimized_total_risk": 0.4,
            "risk_reduction_rate": 0.2,
            "near_optimal_range": {"samsung_min": 0.55, "samsung_max": 0.65},
        }


def make_adapter(tmp_path, runtime, optimizer, **kwargs):
    return DataBRecalculationAdapter(
        RuntimeStateRepository(tmp_path / "state.db"),
        runtime_root=runtime,
        config_dir=ROOT / "config",
        price_loader=price_loader,
        optimizer=optimizer,
        current_weight_grid=(0.25, 0.75),
        profiles=("balanced",),
        now=lambda: CALCULATED,
        **kwargs,
    )


def test_real_esg_and_optimization_results_are_bound_to_active_snapshot(tmp_path):
    runtime, active = active_snapshot(tmp_path)
    optimizer = OptimizerSpy()
    adapter = make_adapter(tmp_path, runtime, optimizer)

    result = asyncio.run(
        adapter.recalculate(
            snapshot_version=active.version,
            published_at=active.published_at,
        )
    )

    assert result.snapshot_version == active.version
    assert result.recalculated_at == CALCULATED.isoformat()
    assert len(optimizer.calls) == 2
    assert all(call["data_mode"] == "validated" for call in optimizer.calls)
    stored = RuntimeStateRepository(tmp_path / "state.db").load_latest_model_recalculation(
        active.version
    )
    assert stored is not None
    assert stored.model_version == MODEL_VERSION
    assert stored.result["snapshot_version"] == active.version
    assert set(stored.result["esg_scores"]) == {"005930", "000660"}
    assert len(stored.result["optimization_grid"]) == 2
    with (active.root / "data/processed/events.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        expected_event_ids = {
            row["event_id"]
            for row in csv.DictReader(handle)
            if row["status"] in {"confirmed", "resolved"}
            and row["authority_confirmed"].lower() == "true"
            and row["official_source_url"]
        }
    assert set(stored.result["eligible_event_ids"]) == expected_event_ids
    scores, basis_version = load_active_recalculated_esg_scores(
        RuntimeStateRepository(tmp_path / "state.db"),
        runtime_root=runtime,
    )
    assert scores == stored.result["esg_scores"]
    assert basis_version == active.version


def test_duplicate_snapshot_recalculation_reuses_persisted_result(tmp_path):
    runtime, active = active_snapshot(tmp_path)
    optimizer = OptimizerSpy()
    adapter = make_adapter(tmp_path, runtime, optimizer)

    first = asyncio.run(
        adapter.recalculate(
            snapshot_version=active.version,
            published_at=active.published_at,
        )
    )
    second = asyncio.run(
        adapter.recalculate(
            snapshot_version=active.version,
            published_at=active.published_at,
        )
    )

    assert second == first
    assert len(optimizer.calls) == 2


def test_approved_optimizer_is_side_effect_free_and_persisted(tmp_path):
    runtime, active = active_snapshot(tmp_path)
    output_path = ROOT / "data/processed/optimization_grid_results.csv"
    before = output_path.read_bytes() if output_path.exists() else None
    adapter = DataBRecalculationAdapter(
        RuntimeStateRepository(tmp_path / "state.db"),
        runtime_root=runtime,
        config_dir=ROOT / "config",
        price_loader=price_loader,
        current_weight_grid=(0.5,),
        profiles=("balanced",),
        now=lambda: CALCULATED,
    )

    result = asyncio.run(
        adapter.recalculate(
            snapshot_version=active.version,
            published_at=active.published_at,
        )
    )

    stored = RuntimeStateRepository(
        tmp_path / "state.db"
    ).load_latest_model_recalculation(active.version)
    assert result.snapshot_version == active.version
    assert stored is not None
    weights = stored.result["optimization_grid"][0]["recommended_weights"]
    assert weights["005930"] + weights["000660"] == pytest.approx(1.0)
    assert 0.2 <= weights["005930"] <= 0.8
    after = output_path.read_bytes() if output_path.exists() else None
    assert after == before


def test_snapshot_version_mismatch_fails_before_calculation(tmp_path):
    runtime, active = active_snapshot(tmp_path)
    optimizer = OptimizerSpy()
    adapter = make_adapter(tmp_path, runtime, optimizer)

    with pytest.raises(DataBRecalculationError) as captured:
        asyncio.run(
            adapter.recalculate(
                snapshot_version="issues-" + "0" * 64,
                published_at=active.published_at,
            )
        )

    assert captured.value.code == "DATA_B_SNAPSHOT_VERSION_MISMATCH"
    assert optimizer.calls == []


def test_missing_validated_esg_aggregate_skips_optimization(tmp_path):
    runtime, active = active_snapshot(tmp_path)
    optimizer = OptimizerSpy()

    def missing_company(**kwargs):
        return {"005930": {"esg_risk_score": 0.3}}

    adapter = make_adapter(
        tmp_path,
        runtime,
        optimizer,
        esg_calculator=missing_company,
    )

    with pytest.raises(DataBRecalculationError) as captured:
        asyncio.run(
            adapter.recalculate(
                snapshot_version=active.version,
                published_at=active.published_at,
            )
        )

    assert captured.value.code == "DATA_B_ESG_AGGREGATE_MISSING"
    assert optimizer.calls == []


def test_optimizer_failure_preserves_published_snapshot_and_no_result(tmp_path):
    runtime, active = active_snapshot(tmp_path)
    optimizer = OptimizerSpy(RuntimeError("injected"))
    adapter = make_adapter(tmp_path, runtime, optimizer)

    with pytest.raises(DataBRecalculationError) as captured:
        asyncio.run(
            adapter.recalculate(
                snapshot_version=active.version,
                published_at=active.published_at,
            )
        )

    assert captured.value.code == "DATA_B_OPTIMIZATION_RECALCULATION_FAILED"
    assert read_active_snapshot(runtime) == active
    assert RuntimeStateRepository(
        tmp_path / "state.db"
    ).load_latest_model_recalculation(active.version) is None


def test_non_validated_price_input_is_explicit_failure(tmp_path):
    runtime, active = active_snapshot(tmp_path)
    adapter = DataBRecalculationAdapter(
        RuntimeStateRepository(tmp_path / "state.db"),
        runtime_root=runtime,
        config_dir=ROOT / "config",
        price_loader=lambda: (pd.DataFrame([{"close": 1}]), "fallback", "stale"),
        optimizer=OptimizerSpy(),
        current_weight_grid=(0.5,),
        profiles=("balanced",),
    )

    with pytest.raises(DataBRecalculationError) as captured:
        asyncio.run(
            adapter.recalculate(
                snapshot_version=active.version,
                published_at=active.published_at,
            )
        )

    assert captured.value.code == "DATA_B_PRICE_NOT_VALIDATED"
