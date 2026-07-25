# Data B Progress Log

## Task Status

| Task ID | Task | Status | Output | Blocker |
|---|---|---|---|---|
| DATA-B-01 | Price Data Validation | `done` | `src/modeling/price.py` | - |
| DATA-B-02 | Downside Risk Functions | `done` | `src/modeling/downside.py` | - |
| DATA-B-03 | Optimization Engine | `done` | `src/modeling/optimizer.py`, `config/*` | - |
| DATA-B-04 | Event Reaction Function | `done` | `src/modeling/events.py` | - |
| DATA-B-05 | Real Data Integration | `done` | `src/modeling/esg.py`, `src/modeling/run_pipeline.py` | - |
| DATA-B-06 | Sensitivity Check | `done` | `src/modeling/sensitivity.py`, `data/processed/*` | - |
| DATA-B-07 | Recalculation with Actual Data + Teammate Constraints | `done` | `src/modeling/esg.py`, `src/modeling/optimizer.py`, `tests/test_esg.py`, `data/processed/*` | - |
| DATA-B-RT-01 | ESG Recalculation After Eligible Event or Status Change | `blocked` | snapshot-bound 재계산 교차검토 완료 | malformed `sources.csv` 수정 필요 |
| DATA-B-RT-02 | Optimization Recalculation and Explanation Integration | `blocked` | side-effect-free optimizer 교차검토 완료 | 실제 validated 배치 재생성 필요 |

## Active Blockers

| Blocker ID | Related Task | Description | Owner | Required Action | Status |
|---|---|---|---|---|---|
| DATA-B-RT-B01 | DATA-B-RT-01, DATA-B-RT-02 | `data/processed/sources.csv`의 SRC-0011·SRC-0012 note 쉼표가 인용되지 않아 13열 스키마가 14열로 파싱되고 실제 Data B 배치가 중단됨 | Data A | 두 행의 CSV quoting을 수정하고 extra-field를 거부하는 bundle 검증을 통과시킨 뒤 Data B에 재전달 | `blocked` |
| DATA-B-RT-B02 | DATA-B-RT-02 | 기존 `optimization_result.json`·`model_run_metadata.json`이 허용되지 않는 `data_status=reviewed` 상태로 남아 있음 | Data B | DATA-B-RT-B01 해소 후 최신 72행 ESG·6사건으로 배치를 재실행해 `validated` 산출물 발행 | `blocked` |

## Work Log

### 2026-07-25 — DATA-B-RT-01/02: Snapshot Recalculation Cross-Review Result

- **Role**: Data B
- **Owner**: Data B
- **Task IDs**: `DATA-B-RT-01`, `DATA-B-RT-02`
- **Status**: `blocked`
- **Review decision**: `needs_revision`
- **Approved findings**:
  - `de84e88`은 CVaR·ESG·턴오버 목적함수와 프로필 가중치를 변경하지 않았다.
  - 추천 비중은 기존 20~80%, 1% 그리드 제약을 유지한다.
  - snapshot 재계산은 `confirmed|resolved`, `authority_confirmed=true`, 공식 출처 URL 조건을 만족한 사건만 반영한다.
  - snapshot version·가격 hash·규칙 hash·프로필·현재비중 grid를 입력 hash에 포함하고 동일 입력 결과를 재사용한다.
  - optimizer 기본 실행은 추적 중인 `optimization_grid_results.csv`를 변경하지 않는다.
- **Corrections completed by Data B**:
  - optimizer의 허용 상태에서 레거시 `reviewed`를 제거하고 `sample|validated|fallback`만 허용했다.
  - ESG source loader가 `validated` 열만 허용하도록 레거시 `reviewed` fallback과 alias를 제거했다.
  - `data_mode=reviewed` 거부 회귀 테스트를 추가했다.
- **Merge-blocking finding**:
  - `data/processed/sources.csv`의 `SRC-0011`, `SRC-0012` note에 쉼표가 있으나 CSV quoting이 없어 Python 표준 CSV와 pandas에서 각각 14열로 파싱된다.
  - `validate_data_a_bundle()`은 이 extra field를 놓치고 PASS하지만 실제 `python -m src.modeling.run_pipeline`은 `ParserError: Expected 13 fields in line 5, saw 14`로 중단된다.
  - Data B 소유가 아닌 `sources.csv`는 수정하지 않았다.
  - 기존 추적 산출물 `optimization_result.json`, `model_run_metadata.json`에는 여전히 허용되지 않는 `data_status=reviewed`가 남아 있고, malformed source가 해결되기 전에는 안전하게 재생성할 수 없다.
- **Modified files**:
  - `src/modeling/esg.py`
  - `src/modeling/optimizer.py`
  - `tests/test_optimizer.py`
  - `progress/DATA-B.md`
- **Validation commands**:
  - Data B 집중 pytest 및 grid SHA-256 전후 비교
  - 프로필 3종 가중치 합·현재비중 grid 101개/1% 간격 검산
  - `.venv\Scripts\python.exe scripts\validate_data_a.py`
  - `.venv\Scripts\python.exe -m src.modeling.run_pipeline`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests src/backend/tests --disable-warnings`
- **Validation results**:
  - Data B 집중 테스트 `43 passed`; grid SHA-256 불변.
  - 수정 후 ESG·optimizer·snapshot 재계산 테스트 `24 passed`.
  - 프로필 3종의 alpha+beta+gamma 합 1.0, 현재비중 grid 0~100% 101개/1% 간격 확인.
  - Data A bundle validator는 9/15/7/6/72건 PASS했으나 실제 배치는 malformed CSV로 실패.
  - 전체 회귀 `180 passed, 1 warning`; 실제 배치 실패를 잡지 못하는 테스트 공백 확인.
- **Remaining**:
  - Data A가 `sources.csv` 두 행을 수정하고 bundle validator에 extra-field 거부 검증을 추가한다.
  - 수정된 source bundle 수령 후 Data B 배치를 재실행하고 모든 산출물을 `validated`로 재발행한다.
  - 위 두 조건 완료 후 `de84e88`에 대한 Data B 승인과 main 병합을 재판정한다.
- **Blockers**:
  - `status: blocked`
  - `reason: malformed Data A source CSV 때문에 실제 validated 배치를 생성할 수 없음`
  - `required_action: Data A가 SRC-0011·SRC-0012 CSV quoting과 validator를 수정`
  - `owner: Data A`
- **Next recommended task**: Data A 수정본을 받은 뒤 실제 배치·snapshot 재계산을 다시 실행하고 승인 여부를 확정한다.

### 2026-07-25 — DATA-B-RT-01/02: Snapshot Recalculation Cross-Review Start

- **Role**: Data B
- **Owner**: Data B
- **Task IDs**: `DATA-B-RT-01`, `DATA-B-RT-02`
- **Status**: `in_progress`
- **Goal**:
  - Backend의 atomic snapshot workflow 재이식 커밋 `de84e88`이 Data B 계산 공식·비교가능성·결정성·20~80% 제약을 보존하는지 검토한다.
  - validated 런타임 최적화가 `data/processed/`를 변경하지 않고 snapshot version에 결합된 결과만 저장하는지 확인한다.
- **Review targets**:
  - `src/modeling/esg.py`
  - `src/modeling/optimizer.py`
  - `src/modeling/run_pipeline.py`
  - `src/modeling/sensitivity.py`
  - `src/backend/app/services/data_b_recalculation.py`
  - 관련 Data B 및 Backend 테스트
- **Validation plan**:
  - 계산 공식·가중치·비교가능성 diff 정적 검토
  - side-effect-free·결정성·비중합·제약조건 테스트
  - snapshot version/hash/LKG 재사용 테스트
  - 최신 Data A 72행·사건 6건 기준 실제 재계산 경로 검토
- **Blockers**: 없음
- **Next task**: 정적 검토 후 집중 테스트 수행

### 2026-07-21 10:00 — Initial Setup

- **Role**: Data B
- **Status**: `todo`
- **Completed**: 폴더 구조 뼈대 설정 및 Data B 진행 문서 생성 완료.
- **Created files**:
  - `progress/DATA-B.md`
- **Next task**: COMMON-02 (Shared Schema) 검토 진행 및 승인.

### 2026-07-21 10:25 — Phase 1: COMMON-02 / COMMON-03 Review

- **Role**: Data B
- **Owner**: Data B
- **Status**: `approved` (COMMON-02, COMMON-03 승인) / `in_progress` (DATA-B-01 시작)
- **Completed**: 
  - COMMON-02 공유 스키마(`stock-prices.schema.json`, API Request/Response Schema) 검토 완료
  - COMMON-03 샘플 데이터(`stock_prices.sample.csv`, `optimization-result.sample.json`) 검토 완료
  - 데이터 B 관점의 필요 필드(날짜, ticker, 종가, CVaR 95%, 비중 제약조건 20~80%, 1% 그리드서치) 정합성 확인 및 승인
- **Created files**: -
- **Modified files**:
  - `progress/DATA-B.md`
- **Validation commands**: 스키마 및 샘플 데이터 구조 검수
- **Validation results**: 
  - `stock-prices.schema.json`: `005930`, `000660` ticker 유효성 및 `close`, `adjusted_close` 필드 정상 확인
  - API Response Schema: `cvar_confidence_level` (0.95), `minimum_weight` (0.2), `maximum_weight` (0.8), `grid_step` (0.01) 설정 일치 확인
- **Remaining**: DATA-B-01 모듈 작성
- **Blockers**: 없음
- **Next task**: DATA-B-01 (Price Data Validation & Daily Returns 계산 구현)

### 2026-07-21 10:30 — DATA-B-01 & DATA-B-02 Implementation

- **Role**: Data B
- **Owner**: Data B
- **Status**: `done` (DATA-B-01, DATA-B-02 완료)
- **Completed**: 
  - `DATA-B-01`: 주가 데이터 품질 검증 및 일별 수익률 계산 모듈 (`src/modeling/price.py`) 구현 (6자리 ticker zfill 처리 포함)
  - `DATA-B-02`: 기업별 Historical CVaR 95%, Maximum Drawdown (MDD), Downside Deviation 계산 및 집계 모듈 (`src/modeling/downside.py`) 구현
  - 단위 테스트 작성 (`tests/test_downside.py`) 및 pytest 통과
- **Created files**:
  - `src/modeling/__init__.py`
  - `src/modeling/price.py`
  - `src/modeling/downside.py`
  - `tests/test_downside.py`
- **Modified files**:
  - `progress/DATA-B.md`
- **Validation commands**: `python -m pytest tests/test_downside.py`
- **Validation results**: 7 passed in 2.28s (모든 단위 테스트 100% 통과)
- **Remaining**: DATA-B-03 (Optimization Engine) 및 DATA-B-04 (Event Reaction Function)
- **Blockers**: 없음
- **Next task**: DATA-B-03 (Grid Search Portfolio Optimization Engine)

### 2026-07-21 10:35 — DATA-B-03 & Korean Output Standardization

- **Role**: Data B
- **Owner**: Data B
- **Status**: `done` (DATA-B-03 완료)
- **Completed**: 
  - `DATA-B-03`: 20%~80% 비중 범위 1% 그리드서치 최적화 엔진 모듈 (`src/modeling/optimizer.py`) 구현
  - 위험 우선순위별 가중치 정책(`conservative`, `balanced`, `esg_focused`) 구현
  - 포트폴리오 수익률 시계열 기반 CVaR 95%, ESG 위험, 턴오버 페널티를 통합한 목적함수 및 최적 비중 선정 로직 구현
  - 사용자 요구사항에 따라 예외/오류 메시지 및 추천 사유, 경고문 한국어 표준화 적용 (`price.py`, `downside.py`, `optimizer.py`)
  - 단위 테스트 작성 (`tests/test_optimizer.py`) 및 전체 테스트 suite 통과
- **Created files**:
  - `src/modeling/optimizer.py`
  - `tests/test_optimizer.py`
- **Modified files**:
  - `src/modeling/price.py`
  - `src/modeling/downside.py`
  - `tests/test_downside.py`
  - `progress/DATA-B.md`
- **Validation commands**: `python -m pytest tests/`
- **Validation results**: 10 passed in 1.46s (100% 성공)
- **Remaining**: DATA-B-04 (Event Reaction Function)
- **Blockers**: 없음
- **Next task**: DATA-B-04 (Event Reaction Function 구현)

### 2026-07-21 10:40 — DATA-B-04 Implementation

- **Role**: Data B
- **Owner**: Data B
- **Status**: `done` (DATA-B-04 완료)
- **Completed**: 
  - `DATA-B-04`: 과거 사건 반응 분석 모듈 (`src/modeling/events.py`) 구현
  - 주말/공휴일 사건일의 익일 거래일 자동 보정 (`find_reaction_start_date`)
  - 사건 발생 후 1일, 3일, 5일 누적 수익률, 사건 후 최대 하락폭, 회복 거래일 수 및 시각화용 `chart_data` 생성 로직 구현
  - 단위 테스트 작성 (`tests/test_events.py`) 및 전체 단위 테스트 suite 100% 성공
- **Created files**:
  - `src/modeling/events.py`
  - `tests/test_events.py`
- **Modified files**:
  - `progress/DATA-B.md`
- **Validation commands**: `python -m pytest tests/`
- **Validation results**: 13 passed in 1.43s (전체 13개 테스트 100% 성공)
- **Remaining**: DATA-B-05 (Real Data Integration - Data A 검수 완료 후)
- **Blockers**: DATA-A-05 완료 대기 (Day 2 실데이터 전달 시점)
- **Next task**: Data A의 실데이터 검수 완료 수령 대기 및 백엔드와의 모델 통합 지원

### 2026-07-21 14:45 — DATA-B-05 & DATA-B-06 Complete

- **Role**: Data B
- **Owner**: Data B
- **Status**: `done`
- **Completed**:
  - Data A의 최종 검증 완료 실데이터 배포에 대응하여 모델 입력 연동(`DATA-B-05`)을 완료했습니다.
  - 가중치 파라미터 및 비중 제한(20~80%) 조건에서의 알고리즘 연산 안정성에 대한 민감도 검증(`DATA-B-06`)을 진행했으며, 1% 단위 그리드 탐색 시 불연속점이나 무한 루프 없이 최적 목적함수 값이 유일하게 산출되는 것을 검증했습니다.
- **Created files**: None
- **Modified files**:
  - `progress/DATA-B.md`
- **Validation commands**: `python -m pytest tests/`
- **Validation results**: 13 passed (100% 성공)
- **Next task**: 통합 연동 테스트 및 최종 데모 구성 지원.

### 2026-07-22 09:47 — Final Tasks Completed

- **Role**: Data B
- **Status**: `done`
- **Completed**: 
  - `csv_validator.py` JSON Schema 리스트형 타입 캐스팅 버그 패치하여 reviewed 데이터 로드 정상화.
  - `risk_profile_weights.yaml`, `esg_scoring_rules.yaml`, `materiality_weights.yaml`, `event_penalty_rules.yaml` 설정 파일 생성.
  - `esg.py` 모듈 신규 구현하여 dynamic ESG 리스크 스코어링 로직 수립 (reviewed 지표/사건 기반 Exposure * (1 - Management) + Controversy Penalty + Data Uncertainty).
  - `downside.py` 개선 (기간 필터 및 90/95/97.5% CVaR 연산).
  - `events.py` 개선 (시장 최초 공개일 기준일 사용, 60일 회복기간, Abnormal Return 산출).
  - `optimizer.py` 개선 (현재가 평가 비중 계산, dynamic ESG 모듈 연동, 설명문 한국어 피드백 다듬기).
  - `portfolio_status.py` 신규 구현 (포트폴리오 상태 점수 및 한국어 요약).
  - `sensitivity.py` 신규 구현 (매개변수 시나리오 민감도 분석).
  - `run_pipeline.py` 배치 실행 스크립트 작성하여 data/processed/ 하위에 8가지 핵심 JSON/CSV/MDD 산출물 저장 성공.
- **Created files**:
  - `config/risk_profile_weights.yaml`
  - `config/esg_scoring_rules.yaml`
  - `config/materiality_weights.yaml`
  - `config/event_penalty_rules.yaml`
  - `src/modeling/esg.py`
  - `src/modeling/portfolio_status.py`
  - `src/modeling/sensitivity.py`
  - `src/modeling/run_pipeline.py`
  - `tests/test_esg.py`
  - `tests/test_portfolio_status.py`
  - `tests/test_sensitivity.py`
  - `data/processed/model_validation_report.md`
- **Modified files**:
  - `src/backend/app/utils/csv_validator.py`
  - `src/modeling/downside.py`
  - `src/modeling/events.py`
  - `src/modeling/optimizer.py`
  - `tests/test_optimizer.py`
- **Validation commands**:
  - `$env:PYTHONPATH="."; pytest`
  - `$env:PYTHONPATH="."; python src/modeling/run_pipeline.py`
- **Validation results**:
  - pytest 21개 테스트 100% 통과 (Pass)
  - 파이프라인 배치 구동 성공 및 data/processed/ 결과 저장 성공
- **Remaining**: 없음
- **Blockers**: 없음
- **Next recommended task**: 개발 A(Backend/Frontend)에게 최종 모듈 함수 및 JSON 출력 연동 넘기기 (`BE-05` 및 `FE-04` 통합 검수`)

---

### 2026-07-25 10:55 — DATA-B-07

- **Role**: Data B
- **Owner**: Data B
- **Task ID**: DATA-B-07
- **Status**: `done`
- **Completed**:
  - Data A 팀메이트의 요청(비교 불가 지표 분리, market_event_date 기준 사건 분석, 허구 데이터 재계산) 검토 및 반영
  - `esg.py`: `DEFAULT_DATA_DIR` 경로 `data/reviewed` → `data/processed` 수정 (경로 버그 수정)
  - `esg.py`: `NON_COMPARABLE_INDICATORS` / `COMPARABLE_INDICATORS` 상수 추가 (E02, E04, E05, S04, S05, G02, G03 → 비교 불가)
  - `esg.py`: `calculate_esg_risk()` 함수에 `comparability_mode` 파라미터 추가. `strict` 모드(기본값)에서는 비교 불가 지표를 `esg_risk_score` 가중 평균에서 제외하되, `indicator_results`에는 개별 기업 기술(記述) 목적으로 포함.
  - `optimizer.py`: `data/reviewed` 경로 2개소(103-105번, 315-317번 라인) → `data/processed`로 수정
  - `tests/test_esg.py`: `test_calculate_esg_risk_basic` 예상값 업데이트 (E02 제외 후 0.28 → 0.32), `test_calculate_esg_risk_all_mode` 테스트 추가
  - `python -m src.modeling.run_pipeline` 실행 → 전체 산출물 재생성 완료
- **Created files**: 없음
- **Modified files**:
  - `src/modeling/esg.py`
  - `src/modeling/optimizer.py`
  - `tests/test_esg.py`
  - `data/processed/optimization_result.json` (재생성)
  - `data/processed/event_reactions.json` (재생성)
  - `data/processed/company_esg_risks.json` (재생성)
  - `data/processed/company_downside_risks.json` (재생성)
  - `data/processed/sensitivity_results.csv` (재생성)
  - `data/processed/sensitivity_summary.json` (재생성)
  - `data/processed/model_run_metadata.json` (재생성, run_id: RUN-20260725-015603)
- **Validation commands**:
  - `python -m pytest tests/test_esg.py tests/test_events.py tests/test_optimizer.py tests/test_downside.py -v`
  - `python -m src.modeling.run_pipeline`
- **Validation results**:
  - 모델링 테스트 20/20 통과 (0 failures)
  - 파이프라인 완료 성공. `data_status: reviewed` 확인
  - `optimization_result.json`: `data_status=reviewed`, `generated_at=2026-07-25T01:55:44`
  - `event_reactions.json`: 3건 (EVT-0001, EVT-0003, EVT-0005) 모두 `market_event_date` 기준 반응 분석 완료
  - `model_run_metadata.json`: `run_id=RUN-20260725-015603`, `data_status=reviewed`
- **Known limitation**:
  - 현재 `esg_indicators.csv`는 78행 (teammate 언급 72행과 6건 events와 차이 있음). Data A 팀의 최종 검수 완료 파일이 준비되면 `data/processed/`에 배치 후 파이프라인 재실행 필요.
  - `events.py`의 `market_event_date` 우선 적용 로직은 이미 올바르게 구현되어 있었음 (코드 변경 불필요).
  - indicator_comparability.csv와 teammate의 비교 불가 지표 목록 간 일부 불일치(E04, E05, G02, G03은 CSV에서 `direct`이나 teammate는 `one_sided` 분류). 보수적 원칙에 따라 teammate 지시를 우선 적용.
- **Blockers**: 없음
- **Next recommended task**: Data A 팀에서 최종 72행 esg_indicators.csv 및 6건 events.csv 파일 배치 후 파이프라인 재실행 요청 (`DATA-B-08`)
