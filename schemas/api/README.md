# Realtime Market, Portfolio and Issue Sync API Contract

## Status and scope

- Contract task: `COMMON-RT-02`
- Status: `review`
- Scope: KOSPI, KOSDAQ, Samsung Electronics (`005930`), SK hynix (`000660`), and the daily/manual issue sync flow
- Approval required: Data A, Data B, Backend, and Frontend

This document defines the shared contract. It does not mean that the producer or consumer implementation is complete.

## Common conventions

- All timestamps use ISO 8601 with an explicit timezone. Production responses use Asia/Seoul (`+09:00`).
- Monetary values use KRW. Rates and weights use decimal notation: `0.01` means 1%.
- `data_status` describes the runtime state of the payload: `sample`, automatically `validated`, or `fallback`.
- `price_status` describes quote freshness: `live`, `cached`, or `fallback`.
- Every response exposes source time (`as_of` or `prices_as_of`) separately from response time (`generated_at`).
- `change_rate`, `return_rate`, and portfolio weights are decimals, not percentages.
- Sample examples must remain labeled `data_status: sample`.
- A legitimately undisclosed ESG value uses `availability: unavailable` with `raw_value: null`. Automatic validation failures are rejected candidates; they are never published as unavailable values and never converted to zero.

## GET `/market/quotes`

Returns exactly four dashboard quotes: KOSPI, KOSDAQ, Samsung Electronics, and SK hynix.

- Response: `market-quotes-response.schema.json`
- Success: `200 OK`
- The frontend polls at the returned `refresh_interval_seconds`, which must be between 10 and 30 seconds while the market is open.
- Outside market hours the last official close may be returned with `market_status: closed` and `price_status: cached`.
- If the provider fails, return the last known good value when available, set `price_status: fallback`, set `is_stale: true`, and add a warning. Do not present fallback data as live.
- If no current or fallback quote exists for all four instruments, return `503 Service Unavailable` rather than inventing a price.

## POST `/portfolio/summary`

Calculates the current portfolio valuation from user holdings and the same Samsung Electronics/SK hynix quote snapshot used by the market service.

- Request: `portfolio-summary-request.schema.json`
- Response: `portfolio-summary-response.schema.json`
- Success: `200 OK`
- Invalid holdings or duplicate tickers: `422 Unprocessable Entity`
- Unsupported ticker: `422 Unprocessable Entity`
- No usable current or fallback quote: `503 Service Unavailable`

Calculation rules per position:

```text
purchase_value = quantity × average_price
market_value = quantity × current_price
unrealized_profit_loss = market_value - purchase_value
return_rate = unrealized_profit_loss / purchase_value
current_weight = market_value / total_market_value
```

Portfolio totals are the sums of position values. `total_return_rate` is total unrealized profit/loss divided by total purchase value. Position weights must sum to 1 within a rounding tolerance of `0.000001`.

`prices_as_of` is the oldest source timestamp among the quotes used for the calculation. Aggregate `price_status` reports the least-fresh status used (`fallback` before `cached` before `live`). This prevents a partially stale portfolio from being labeled live.

`POST` is used because the user holdings are calculation input and must not be encoded in a cacheable query string.

## POST `/sync/issues`

Requests an on-demand check for new disclosures, news, and ESG issue status changes.

- Request: `sync-issues-request.schema.json`
- Response: `sync-status-response.schema.json`
- New job accepted: `202 Accepted`, `status: queued`
- Existing queued/running job reused: `200 OK`, the existing `sync_id`, and `is_existing_run: true`
- Invalid request: `422 Unprocessable Entity`

The daily scheduler and manual refresh call the same synchronization service. Only one issue synchronization job may run at a time. `client_request_id` supports client retry deduplication; the server-side active-job lock remains authoritative.

External refresh writes to `raw` or `candidate` first. The service then runs schema, official-source, event-status, evidence, and deduplication checks. Records that pass are atomically published to `processed` without a human-review step. `reported` events are news-only warnings and never affect scores. `confirmed` and `resolved` events can affect ESG risk only when official-source verification succeeds. Rumor-like records are discarded at the raw stage. Enforcement outcomes such as a fine or sanction are stored separately in `enforcement_action`.

## GET `/sync/status`

Returns the latest issue sync status. A `sync_id` query parameter may select a specific job.

- Response: `sync-status-response.schema.json`
- Success: `200 OK`
- Unknown `sync_id`: `404 Not Found`
- No sync history when the latest status is requested: `404 Not Found`

`stage` identifies the active or last completed pipeline phase: `queued`, `collecting`, `normalizing`, `validating`, `publishing`, `recalculating`, or `completed`.

State timestamps follow these rules:

- `queued`: `started_at` and `completed_at` are null.
- `running`: `started_at` is set and `completed_at` is null.
- `success`, `partial_success`, or `failed`: `stage` is `completed`, and both `started_at` and `completed_at` are set.

Terminal result semantics:

- `success`: collection and candidate validation completed; if valid changes existed, atomic processed publication also succeeded. No new data is still a success with `snapshot_updated: false`.
- `partial_success`: one or more sources failed, but all collected candidates were validated and any usable changes were safely published.
- `failed`: collection could not produce a usable result, automatic validation failed as a system operation, or atomic publication failed. The previous processed snapshot remains intact.

`collected_items`, `candidate_items`, `validated_items`, `rejected_items`, and `published_items` expose each pipeline boundary. `snapshot_updated`, `published_snapshot_version`, and `published_at` prove whether publication occurred. Rejected candidates are a normal validation result and do not by themselves make the job fail.

`recalculation_triggered`, `recalculation_status`, and `recalculated_at` distinguish issue publication from ESG and optimization recalculation. A sync may succeed without recalculation when no model-eligible event changed.

Recalculation is triggered only after an atomic processed snapshot is published and at least one scoring-relevant input changes:

- a new or changed `confirmed` or `resolved` event passes official-source verification;
- an existing event enters or leaves model eligibility because its status, official confirmation, or official source changes;
- a validated ESG indicator value, availability, period, or other aggregation input changes; or
- a model-eligible event's category, date, severity, or enforcement outcome changes in a way consumed by the ESG aggregation rules.

`reported` events, rejected candidates, duplicate-only collection results, and metadata changes that do not alter model inputs do not trigger recalculation. Validated mode must fail explicitly when a required aggregate ESG score is unavailable; sample defaults are allowed only in explicitly labeled `sample` or `fallback` mode.

`failed_sources` exposes partial collection failures. If the last validated snapshot remains usable, the response may keep it with `data_status: fallback` and a clear warning.

## Ownership and review checklist

- Data A (`review`): remediation artifacts exist, but the role log still records unavailable governance data and cross-role implementation dependencies.
- Data B (`pending`): confirm scoring-relevant recalculation triggers, result/version handling, and validated-mode missing-score behavior.
- Backend (`pending`): confirm provider/cache/error behavior, locks, scheduler/manual service reuse, and state persistence implementability.
- Frontend (`pending`): confirm polling behavior, timestamps, loading/error/fallback labels, manual refresh, and status consumption.
- Integration: verify the same quote snapshot drives both market cards and portfolio valuation.
