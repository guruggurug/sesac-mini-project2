"""Snapshot-bound Data B ESG and portfolio-grid recalculation."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

import pandas as pd

from app.core.config import BASE_DIR, ISSUE_RUNTIME_DATA_DIR
from app.repositories.price_repository import PriceRepository
from app.repositories.runtime_state_repository import RuntimeStateRepository
from app.services.issue_snapshot_publisher import read_active_snapshot
from app.services.issue_sync_workflow import RecalculationResult
from app.utils.csv_validator import validate_data_a_bundle
from src.modeling.esg import calculate_esg_risk, load_yaml_config
from src.modeling.events import analyze_all_events, build_similar_event_groups
from src.modeling.optimizer import optimize_portfolio


MODEL_VERSION = "data-b-snapshot-v2"
COMPANY_IDS = ("005930", "000660")
OPTIMIZATION_PROFILES = ("loss_minimization", "balanced", "esg_focused")
DEFAULT_CURRENT_WEIGHT_GRID = tuple(index / 100 for index in range(101))


class DataBRecalculationError(RuntimeError):
    """Stable internal failure returned to the issue synchronization workflow."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class DataBRecalculationAdapter:
    """Recalculate only from the active validated issue snapshot."""

    def __init__(
        self,
        state_repository: RuntimeStateRepository,
        *,
        runtime_root: str | Path = ISSUE_RUNTIME_DATA_DIR,
        config_dir: str | Path = Path(BASE_DIR) / "config",
        price_loader: Callable[[], tuple[pd.DataFrame, str, str | None]] | None = None,
        esg_calculator: Callable[..., dict] = calculate_esg_risk,
        optimizer: Callable[..., dict] = optimize_portfolio,
        current_weight_grid: Iterable[float] = DEFAULT_CURRENT_WEIGHT_GRID,
        profiles: Iterable[str] = OPTIMIZATION_PROFILES,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self._state_repository = state_repository
        self._runtime_root = Path(runtime_root)
        self._config_dir = Path(config_dir)
        self._price_loader = price_loader or PriceRepository().load_data_as_df
        self._esg_calculator = esg_calculator
        self._optimizer = optimizer
        self._current_weight_grid = tuple(float(value) for value in current_weight_grid)
        self._profiles = tuple(profiles)
        self._now = now

    async def recalculate(
        self, *, snapshot_version: str, published_at: str
    ) -> RecalculationResult:
        active = read_active_snapshot(self._runtime_root)
        if active is None or active.version != snapshot_version:
            raise DataBRecalculationError(
                "DATA_B_SNAPSHOT_VERSION_MISMATCH",
                "published snapshot is not the active immutable snapshot",
            )

        published_time = _aware_datetime(published_at, "published_at")
        active_time = _aware_datetime(active.published_at, "active published_at")
        if active_time != published_time:
            raise DataBRecalculationError(
                "DATA_B_SNAPSHOT_TIME_MISMATCH",
                "published timestamp does not match the active snapshot",
            )

        scoring_rules, materiality_weights, event_rules, rules_hash = self._load_rules()
        try:
            price_df, price_status, _ = self._price_loader()
        except Exception as error:
            raise DataBRecalculationError(
                "DATA_B_PRICE_LOAD_FAILED",
                "validated price input could not be loaded",
            ) from error
        if price_status != "validated" or price_df.empty:
            raise DataBRecalculationError(
                "DATA_B_PRICE_NOT_VALIDATED",
                "validated price input is required for optimization recalculation",
            )

        price_hash = _dataframe_hash(price_df)
        input_hash = _input_hash(
            snapshot_version=snapshot_version,
            rules_hash=rules_hash,
            price_hash=price_hash,
            profiles=self._profiles,
            current_weight_grid=self._current_weight_grid,
        )
        existing = self._state_repository.load_model_recalculation(
            snapshot_version=snapshot_version,
            model_version=MODEL_VERSION,
            input_hash=input_hash,
        )
        if existing is not None:
            return RecalculationResult(
                recalculated_at=existing.recalculated_at.isoformat(),
                snapshot_version=existing.snapshot_version,
            )

        try:
            bundle = validate_data_a_bundle(str(active.root))
        except Exception as error:
            raise DataBRecalculationError(
                "DATA_B_ACTIVE_SNAPSHOT_INVALID",
                "active issue snapshot did not pass the Data A bundle contract",
            ) from error

        eligible_events = [
            event
            for event in bundle["events"]
            if event.get("status") in {"confirmed", "resolved"}
            and event.get("authority_confirmed") is True
            and bool(event.get("official_source_url"))
        ]
        validated_source_ids = {
            str(source["source_id"])
            for source in bundle["sources"]
            if source.get("validated") is True
        }

        try:
            esg_result = self._esg_calculator(
                indicators_df=pd.DataFrame(bundle["esg"]),
                events_df=pd.DataFrame(eligible_events),
                scoring_rules=scoring_rules,
                materiality_weights=materiality_weights,
                event_rules=event_rules,
                reviewed_sources=validated_source_ids,
                reference_date=published_time.date().isoformat(),
            )
            esg_scores = _required_esg_scores(esg_result)
        except DataBRecalculationError:
            raise
        except Exception as error:
            raise DataBRecalculationError(
                "DATA_B_ESG_RECALCULATION_FAILED",
                "ESG aggregate recalculation failed",
            ) from error

        try:
            optimization_grid = self._optimization_grid(price_df, esg_scores)
        except DataBRecalculationError:
            raise
        except Exception as error:
            raise DataBRecalculationError(
                "DATA_B_OPTIMIZATION_RECALCULATION_FAILED",
                "portfolio optimization grid recalculation failed",
            ) from error

        try:
            event_reactions = analyze_all_events(
                events_input=pd.DataFrame(eligible_events),
                price_data=price_df,
                index_prices_input=self._index_prices_path(),
                window_days=10,
                filter_model_eligible_only=True,
            )
            similar_event_groups = build_similar_event_groups(
                eligible_events,
                event_reactions,
            )
        except Exception as error:
            raise DataBRecalculationError(
                "DATA_B_EVENT_REACTION_RECALCULATION_FAILED",
                "historical event reaction recalculation failed",
            ) from error

        calculated_at = _aware_datetime(self._now(), "recalculated_at")
        result = {
            "snapshot_version": snapshot_version,
            "published_at": published_time.isoformat(),
            "model_version": MODEL_VERSION,
            "rules_hash": rules_hash,
            "price_data_hash": price_hash,
            "data_status": "validated",
            "eligible_event_ids": sorted(
                str(event["event_id"]) for event in eligible_events
            ),
            "company_esg_risks": esg_result,
            "esg_scores": esg_scores,
            "optimization_grid": optimization_grid,
            "event_reactions": event_reactions,
            "similar_event_groups": similar_event_groups,
        }
        stored = self._state_repository.save_model_recalculation(
            snapshot_version=snapshot_version,
            published_at=published_time,
            model_version=MODEL_VERSION,
            input_hash=input_hash,
            result=result,
            recalculated_at=calculated_at,
        )
        return RecalculationResult(
            recalculated_at=stored.recalculated_at.isoformat(),
            snapshot_version=stored.snapshot_version,
        )

    def _load_rules(self) -> tuple[dict, dict, dict, str]:
        paths = (
            self._config_dir / "esg_scoring_rules.yaml",
            self._config_dir / "materiality_weights.yaml",
            self._config_dir / "event_penalty_rules.yaml",
        )
        try:
            payloads = [path.read_bytes() for path in paths]
            rules = [load_yaml_config(path) for path in paths]
        except Exception as error:
            raise DataBRecalculationError(
                "DATA_B_RULES_UNAVAILABLE",
                "approved Data B rule configuration is unavailable",
            ) from error
        digest = hashlib.sha256()
        for path, payload in zip(paths, payloads):
            digest.update(path.name.encode("utf-8"))
            digest.update(b"\0")
            digest.update(payload)
            digest.update(b"\0")
        scoring_rules = dict(rules[0].get("indicators", {}))
        scoring_rules["uncertainty_penalties"] = rules[0].get(
            "uncertainty_penalties", {}
        )
        return scoring_rules, rules[1], rules[2], digest.hexdigest()

    def _optimization_grid(
        self, price_df: pd.DataFrame, esg_scores: dict[str, float]
    ) -> list[dict]:
        scenarios = []
        for current_samsung_weight in self._current_weight_grid:
            if not 0.0 <= current_samsung_weight <= 1.0:
                raise ValueError("current weight grid must stay between 0 and 1")
            holdings = [
                {
                    "ticker": "005930",
                    "quantity": current_samsung_weight,
                    "average_price": 1.0,
                    "current_price": 1.0,
                },
                {
                    "ticker": "000660",
                    "quantity": 1.0 - current_samsung_weight,
                    "average_price": 1.0,
                    "current_price": 1.0,
                },
            ]
            for profile in self._profiles:
                optimized = self._optimizer(
                    holdings=holdings,
                    price_data=price_df,
                    esg_input=esg_scores,
                    risk_priority=profile,
                    current_prices={"005930": 1.0, "000660": 1.0},
                    data_mode="validated",
                    grid_results_output=None,
                )
                scenarios.append(
                    {
                        "current_samsung_weight": round(
                            current_samsung_weight, 4
                        ),
                        "risk_priority": profile,
                        "recommended_weights": optimized["recommended_weights"],
                        "current_total_risk": optimized["current_total_risk"],
                        "optimized_total_risk": optimized["optimized_total_risk"],
                        "risk_reduction_rate": optimized["risk_reduction_rate"],
                        "near_optimal_range": optimized["near_optimal_range"],
                    }
                )
        return scenarios

    def _index_prices_path(self) -> Path | None:
        path = Path(BASE_DIR) / "data" / "processed" / "index_prices.csv"
        return path if path.exists() else None


def _required_esg_scores(result: dict) -> dict[str, float]:
    scores: dict[str, float] = {}
    missing = []
    for company_id in COMPANY_IDS:
        company = result.get(company_id)
        if not isinstance(company, dict) or "esg_risk_score" not in company:
            missing.append(company_id)
            continue
        score = float(company["esg_risk_score"])
        if not 0.0 <= score <= 1.0:
            raise DataBRecalculationError(
                "DATA_B_ESG_AGGREGATE_INVALID",
                f"ESG aggregate is outside the accepted range: {company_id}",
            )
        scores[company_id] = score
    if missing:
        raise DataBRecalculationError(
            "DATA_B_ESG_AGGREGATE_MISSING",
            f"required ESG aggregate is missing: {', '.join(missing)}",
        )
    return scores


def _aware_datetime(value: str | datetime, field_name: str) -> datetime:
    parsed = datetime.fromisoformat(value) if isinstance(value, str) else value
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DataBRecalculationError(
            "DATA_B_INVALID_TIMESTAMP",
            f"{field_name} must include timezone information",
        )
    return parsed


def _dataframe_hash(frame: pd.DataFrame) -> str:
    canonical = frame.copy()
    canonical.columns = [str(column) for column in canonical.columns]
    columns = sorted(canonical.columns)
    canonical = canonical[columns].astype(str).sort_values(columns).reset_index(drop=True)
    payload = canonical.to_csv(index=False, lineterminator="\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _input_hash(
    *,
    snapshot_version: str,
    rules_hash: str,
    price_hash: str,
    profiles: tuple[str, ...],
    current_weight_grid: tuple[float, ...],
) -> str:
    payload = json.dumps(
        {
            "snapshot_version": snapshot_version,
            "rules_hash": rules_hash,
            "price_hash": price_hash,
            "profiles": profiles,
            "current_weight_grid": current_weight_grid,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_active_recalculated_esg_scores(
    state_repository: RuntimeStateRepository,
    *,
    runtime_root: str | Path = ISSUE_RUNTIME_DATA_DIR,
) -> tuple[dict[str, float], str] | None:
    """Return scores only when the stored result matches the active snapshot."""
    active = read_active_snapshot(runtime_root)
    if active is None:
        return None
    stored = state_repository.load_latest_model_recalculation(active.version)
    if stored is None:
        return None
    result = stored.result
    if result.get("snapshot_version") != active.version:
        raise DataBRecalculationError(
            "DATA_B_STORED_RESULT_VERSION_MISMATCH",
            "stored model result does not match the active snapshot",
        )
    return _required_esg_scores(
        {
            company_id: {"esg_risk_score": score}
            for company_id, score in result.get("esg_scores", {}).items()
        }
    ), active.version
