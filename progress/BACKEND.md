# Backend Progress Log

## Task Status

| Task ID | Task | Status | Output | Blocker |
|---|---|---|---|---|
| BE-01 | FastAPI Skeleton | `done` | `src/backend/app/main.py` 등 | COMMON-01 완료 |
| BE-02 | Data Loader and Validation | `done` | `src/backend/app/utils/csv_validator.py` | COMMON-02, COMMON-03 승인 |
| BE-03 | Mock API | `done` | `src/backend/app/routes/` 내 Mocking | BE-01, BE-02 완료 |
| BE-04 | Real Data Integration | `done` | `data/processed/` 자동 검증 스냅샷 연동 완료 | DATA-A-05, BE-02 완료 |
| BE-05 | Model Integration | `done` | `src/backend/app/routes/` 내 실제 계산 모듈 연동 | DATA-B-05, BE-03 완료 |
| BE-06 | Fallback and Contract Tests | `done` | `test_portfolio.py` 수정 및 예외 폴백 로직 검증 | BE-04, BE-05 완료 |
| BE-RT-00 | ESG Schema Validator and Sample Contract Compatibility Recovery | `done` | processed/sample ESG·event 계약, nullable 캐스팅, 회귀 테스트 | 없음 |
| BE-RT-01 | KOSPI·KOSDAQ·Samsung·SK hynix Market Quote Service and Cache | `review` | 내부 provider/adapter, TTL 캐시, timeout, mock 단위 테스트 | `COMMON-RT-02` 승인 전 공개 API 계약 확정 금지 |
| BE-RT-03 | Daily Issue Scheduler, Manual Sync, Lock and Status API | `in_progress` | 공통 coordinator, SQLite 일일 선점, 서울시간 scheduler, lifespan 제어 | 실제 수집 workflow·공개 API는 `COMMON-RT-02` 승인 대기 |
| BE-RT-03A | Open DART Adapter and Candidate Normalization | `review` | DART provider, runtime raw·rejected 보존, candidate 정규화·Data A 검증, mock 테스트 | Data A 교차 검토와 실제 키 smoke test 필요 |
| BE-RT-03B | Atomic Data A Snapshot Publisher | `review` | versioned staging 검증, active pointer 원자 교체, repository LKG 연동 | 통합 교차 검토 필요 |
| BE-RT-03C | Coordinator Publisher and Recalculation Workflow | `review` | 수집→검증→발행→선택적 재계산 내부 workflow | production normalizer 연결 필요 |
| BE-RT-03D | Side-Effect-Free Data B Recalculation Adapter | `review` | snapshot-bound ESG·최적화 재계산과 SQLite 결과 재사용 | Data B·통합 교차 검토 필요 |
| BE-RT-04 | Last-Known-Good Market and Issue Fallback | `review` | SQLite 시장 LKG 저장·KIS 장애 fallback | 실제 KIS smoke test와 공개 상태 표시는 승인 대기 |

## Active Blockers

| Blocker ID | Related Task | Description | Owner | Required Action | Status |
|---|---|---|---|---|---|
| - | - | 현재 없음 | - | - | - |

## Work Log

### 2026-07-25 — BE-RT-03B/C/D: Latest Main Reintegration Complete

- **Role**: Backend
- **Owner**: Backend
- **Task IDs**: `BE-RT-03B`, `BE-RT-03C`, `BE-RT-03D`
- **Status**: `review`
- **Completed**:
  - 오래된 feature 브랜치를 직접 병합하지 않고 최신 `main` 위에 원자적 Data A snapshot publisher, 내부 issue workflow, Data B 재계산 경계를 기능 단위로 재이식했다.
  - 최신 Data A 비교가능성 정책을 보존하고 E02·E04·E05·S04·S05·G02·G03이 기업 간 최적화 점수에서 제외되는 현재 계약과 재계산 경계를 정렬했다.
  - runtime repository가 활성 immutable snapshot을 우선 사용하고 pointer가 없을 때 Git 추적 processed bootstrap을 사용하는 LKG 경계를 복구했다.
  - snapshot version·발행 시각·모델 버전·입력 hash에 결합된 재계산 결과를 SQLite에 결정적으로 저장하고 동일 입력을 재사용하도록 했다.
  - `optimize_portfolio()`의 기본 실행에서 `data/processed/optimization_grid_results.csv`를 덮어쓰는 부수효과를 제거했다. 오프라인 배치는 `grid_results_output`을 명시한 경우에만 결과를 기록한다.
  - 배치 파이프라인과 민감도 분석을 `validated` 데이터 상태 및 명시적 ESG aggregate 입력 계약으로 정렬했다.
  - 기존 `IssueSyncCoordinator`가 상세 workflow 결과를 보존하면서 legacy 성공 상태 반환도 계속 지원하도록 호환성을 유지했다.
- **Created files**:
  - `src/backend/app/services/issue_snapshot_publisher.py`
  - `src/backend/app/services/issue_sync_workflow.py`
  - `src/backend/app/services/data_b_recalculation.py`
  - `src/backend/tests/test_issue_snapshot_publisher.py`
  - `src/backend/tests/test_issue_sync_workflow.py`
  - `src/backend/tests/test_data_b_recalculation.py`
- **Modified files**:
  - `src/backend/app/core/runtime.py`
  - `src/backend/app/repositories/esg_repository.py`
  - `src/backend/app/repositories/event_repository.py`
  - `src/backend/app/repositories/runtime_state_repository.py`
  - `src/backend/app/services/sync_coordinator.py`
  - `src/modeling/esg.py`
  - `src/modeling/optimizer.py`
  - `src/modeling/run_pipeline.py`
  - `src/modeling/sensitivity.py`
  - 관련 Backend/Data B 테스트
  - `progress/BACKEND.md`
- **Validation commands**:
  - `.venv\Scripts\python.exe scripts\validate_data_a.py`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_optimizer.py tests/test_esg.py src/backend/tests/test_issue_snapshot_publisher.py src/backend/tests/test_issue_sync_workflow.py src/backend/tests/test_data_b_recalculation.py src/backend/tests/test_runtime_state_repository.py src/backend/tests/test_sync_coordinator.py --disable-warnings`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests src/backend/tests --disable-warnings`
  - `.venv\Scripts\python.exe -m compileall -q src/backend/app src/modeling`
  - `git diff --check`
- **Validation results**:
  - Data A bundle PASS: candidate 9, source 15, event-source 7, event 6, ESG 72.
  - 집중 테스트 최초 1건은 구 E02 포함 예상값 때문에 실패했으며 최신 비교가능성 기준값으로 교정 후 `31 passed`.
  - 전체 회귀 `179 passed, 1 warning`.
  - optimizer 테스트 전후 `optimization_grid_results.csv` SHA-256 동일.
  - Python compile 및 whitespace 검사 통과.
- **Remaining**:
  - DART/news 후보를 완전한 Data A bundle로 만드는 production normalizer를 `build_internal_issue_sync_workflow()`에 주입한다.
  - 실제 coordinator 기본 workflow 전환, 공개 `/sync/issues`·`/sync/status`, 600초 쿨다운은 BE-RT-03 후속 범위로 유지한다.
  - Data B와 Integration이 snapshot-bound 재계산 출력 계약을 교차 검토해야 한다.
- **Blockers**: 없음
- **Next recommended task**: production normalizer를 구현·주입한 뒤 scheduler/manual 경로가 동일 workflow를 실행하는 통합 테스트를 추가한다.

### 2026-07-25 — BE-RT-03B/C/D: Latest Main Reintegration Start

- **Role**: Backend
- **Owner**: Backend
- **Task IDs**: `BE-RT-03B`, `BE-RT-03C`, `BE-RT-03D`
- **Status**: `in_progress`
- **Goal**:
  - 최신 `main`의 Data A 72행·출처 15건·사건 6건과 Data B 재계산 산출물을 기준으로 원자적 snapshot publisher와 공통 issue workflow를 재이식한다.
  - validated 런타임 최적화가 `data/processed/`를 덮어쓰지 않도록 side-effect-free callable 계약을 복구한다.
  - snapshot version에 결합된 재계산 결과만 저장·재사용하고 실패 시 기존 정상 snapshot과 계산 결과를 보존한다.
- **Allowed files**:
  - `src/modeling/optimizer.py`, `src/modeling/run_pipeline.py`, 관련 Data B 테스트
  - `src/backend/app/services/issue_snapshot_publisher.py`
  - `src/backend/app/services/issue_sync_workflow.py`
  - `src/backend/app/services/data_b_recalculation.py`
  - Backend repository/runtime 조립 및 관련 테스트
  - `progress/BACKEND.md`
- **Assumptions**:
  - 기존 feature 브랜치는 최신 `main`보다 뒤처져 있으므로 커밋 전체 병합 대신 기능 단위로 재이식한다.
  - 공유 스키마와 계산 공식은 변경하지 않는다.
  - 공개 `/sync/*` API와 외부 뉴스 수집은 이번 작업 범위에 포함하지 않는다.
- **Validation plan**:
  - side-effect-free optimizer 집중 테스트
  - publisher/workflow/recalculation/runtime 저장소 집중 테스트
  - 전체 `tests` 및 `src/backend/tests` 회귀 테스트
  - Python compile 및 `git diff --check`
- **Blockers**: 없음
- **Next task**: 기존 구현을 최신 `main`과 비교해 필요한 변경만 재이식

### 2026-07-22 18:01 — BE-RT-03A: Implementation Complete, Cross-Review Required

- **Role**: Backend
- **Owner**: Backend
- **Task ID**: `BE-RT-03A`
- **Status**: `review`
- **Completed**:
  - 삼성전자(`00126380`)·SK하이닉스(`00164779`) 대상 Open DART `list.json` provider를 구현했다.
  - timeout·network·HTTP·DART 상태 코드를 분류하고, timeout과 `020/800/900`만 지수 backoff로 재시도하도록 제한했다.
  - `013`을 정상 빈 결과로 처리하고 인증·입력 오류는 재시도하지 않도록 했다.
  - 예외 문자열과 코드에 API 키, 요청 URL, 외부 응답 메시지를 포함하지 않았다.
  - 성공 응답을 `data/runtime/issues/raw/dart/`에 먼저 원자적으로 저장한 뒤 candidate 정규화를 수행하도록 했다.
  - candidate를 기존 `event-candidates.schema.json` 형식으로 변환하고 접수번호·회사·URL·content hash·dedup key를 결정론적으로 생성·검증했다.
  - 신규 공시는 `pending`으로 유지하여 사건·ESG 점수에 자동 반영하지 않고, malformed·중복 후보는 `rejected` CSV로 보존했다.
  - 기존 Data A candidate/source 검증에 14자리 DART 접수번호와 viewer URL `rcpNo` 일치 검사를 연결했다.
- **Created files**:
  - `src/backend/app/services/dart_disclosures.py`
  - `src/backend/tests/test_dart_disclosures.py`
- **Modified files**:
  - `.env.example`
  - `.gitignore`
  - `src/backend/app/core/config.py`
  - `src/backend/app/utils/csv_validator.py`
  - `progress/BACKEND.md`
- **Validation commands**:
  - `.venv\\Scripts\\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_dart_disclosures.py src/backend/tests/test_issue_pipeline_contracts.py src/backend/tests/test_csv_validator.py`
  - `.venv\\Scripts\\python.exe -m pytest -p no:cacheprovider -q tests src/backend/tests --ignore=src/backend/tests/test_portfolio.py --ignore=src/backend/tests/test_ui_routes.py`
  - `.venv\\Scripts\\python.exe -m compileall -q src/backend/app`
  - `git diff --check`
- **Validation results**:
  - DART adapter·Data A 계약 집중 테스트: `28 passed`.
  - UI route 수집 테스트를 제외한 Backend·모델 전체 회귀: `86 passed`.
  - Python compile 및 whitespace 검사 통과.
  - 전체 suite는 최신 `main`에 `src/frontend/static/` 디렉터리가 없어 `test_portfolio.py`, `test_ui_routes.py` import 단계에서 중단됨. 이번 변경과 무관한 기준선 문제로 확인했다.
- **Remaining**:
  - Data A가 rejected 후보의 중복 보존 정책과 강화된 DART source 검사를 교차 검토해야 한다.
  - 실제 API 키 smoke test는 키·응답 원문을 출력하지 않고 회사별 수집 건수와 검증 결과만 확인해야 한다.
  - atomic snapshot publisher와 coordinator workflow 주입은 후속 작업으로 유지한다.
- **Blockers**:
  - 전체 회귀 실행을 위해 최신 `main`의 `src/frontend/static/` 기준선 복구가 필요하다.
- **Next task**: Data A 교차 검토 후 atomic publisher 브랜치에서 staging bundle 검증과 활성 snapshot 교체를 구현한다.

### 2026-07-22 17:55 — BE-RT-03A: Open DART Adapter and Candidate Normalization

- **Role**: Backend
- **Owner**: Backend
- **Task ID**: `BE-RT-03A`
- **Status**: `in_progress`
- **Scope**:
  - 삼성전자·SK하이닉스 Open DART 공시 조회 adapter
  - timeout·재시도·호출 오류 분류와 비밀정보 비노출
  - 외부 응답의 runtime raw 선저장
  - `event-candidates.schema.json` 기반 pending/rejected 후보 정규화와 Data A 검증 연결
- **Assumptions**:
  - DART 수집 후보는 공식 공시라는 이유만으로 기존 사건에 자동 연결하지 않고 `pending`으로 유지한다.
  - malformed 후보는 점수 경로로 보내지 않고 `rejected` 상태와 기계 판정 사유를 보존한다.
  - atomic snapshot publisher, coordinator 실제 workflow 주입, scheduler 활성화와 공개 `/sync/*` API는 이번 작업에서 제외한다.
- **Validation plan**:
  - provider mock 단위 테스트
  - candidate schema·URL·접수번호·dedup 검증 테스트
  - 기존 Data A 및 Backend 회귀 테스트
- **Next task**: provider와 raw/candidate 변환 구현 후 검증 결과 기록.

### 2026-07-22 — BE-RT-03: Project Environment Loading

- **Role**: Backend
- **Owner**: Backend
- **Task ID**: `BE-RT-03`
- **Status**: `in_progress`
- **Assumptions**:
  - 실제 비밀값은 로컬 `.env`에만 보관하고 테스트·로그·Git 출력에 노출하지 않는다.
  - 운영체제 또는 배포 Secret Manager가 주입한 환경변수는 `.env` 값보다 우선한다.
- **Completed**:
  - 프로젝트 루트 `.env`를 Backend 설정 import 시 자동으로 로드하도록 연결했다.
  - KIS·DART·뉴스·Gemini 키를 내부 설정으로 노출하되 실제 값은 출력하지 않았다.
  - 운영체제·배포 환경변수가 `.env`보다 우선하도록 `override=False`를 적용했다.
  - 상대 SQLite 경로를 shell 현재 위치가 아닌 프로젝트 루트 기준으로 정규화했다.
  - `.env` 파일은 읽기 대상일 뿐 수정하거나 Git 추적하지 않았다.
- **Allowed files**:
  - `src/backend/app/core/config.py`
  - `src/backend/requirements.txt`
  - `src/backend/tests/test_config_environment.py`
  - `progress/BACKEND.md`
- **Do not modify**:
  - `.env`
  - 공유 API·데이터 스키마
  - 다른 역할의 진행 로그
- **Created files**:
  - `src/backend/tests/test_config_environment.py`
- **Modified files**:
  - `src/backend/app/core/config.py`
  - `src/backend/requirements.txt`
  - `progress/BACKEND.md`
- **Validation commands**:
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_config_environment.py src/backend/tests/test_kis_market_data.py src/backend/tests/test_market_quotes.py`
  - 실제 값을 출력하지 않는 KIS·DART·Gemini 설정 smoke test
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q`
- **Validation results**:
  - 환경 로딩·runtime 경로·KIS 관련 테스트 `25 passed`.
  - KIS·DART·Gemini 설정이 모두 비어 있지 않음을 값 노출 없이 확인했다.
  - `NEWS_API_KEY`는 비어 있으나 뉴스 provider가 아직 미선정이므로 현재 실행의 blocker로 처리하지 않는다.
  - 전체 회귀 `92 passed`, 기존 Starlette deprecation warning 1개.
- **Remaining**:
  - DART와 Gemini 키는 설정에 연결됐지만 실제 provider·설명 서비스 호출은 아직 구현하지 않았다.
  - `BE-RT-03` 전체 작업은 실제 수집 workflow와 공개 계약 승인이 남아 `in_progress`를 유지한다.
- **Blockers**: 없음
- **Next task**: DART 수집 adapter와 mock 계약 테스트 구현

### 2026-07-22 — BE-RT-03: Internal Sync Coordinator and Daily Scheduler

- **Role**: Backend
- **Owner**: Backend
- **Task ID**: `BE-RT-03`
- **Status**: `in_progress`
- **Completed**:
  - manual·scheduled 실행이 동일한 `IssueSyncCoordinator`와 SQLite 단일 lock을 사용하도록 구현했다.
  - 기존 active 작업이 있으면 새 workflow를 실행하지 않고 기존 `sync_id`와 상태를 반환한다.
  - workflow stage heartbeat와 success·partial_success·failed terminal 기록을 연결했다.
  - 수집 workflow 미구성 시 `ISSUE_SYNC_WORKFLOW_NOT_CONFIGURED` 실패로 기록하여 거짓 성공을 방지했다.
  - 서울 시간 기준 일일 scheduler와 SQLite 날짜별 atomic claim을 구현해 다중 프로세스 중복 실행을 방지했다.
  - scheduler는 기본 비활성화하고 `ENABLE_ISSUE_SCHEDULER=true`일 때만 FastAPI lifespan에서 시작·종료한다.
  - 공개 `/sync/issues`, `/sync/status`, 기존 `/data/refresh` 동작과 공유 스키마는 변경하지 않았다.
- **Created files**:
  - `src/backend/app/services/sync_coordinator.py`
  - `src/backend/app/services/issue_scheduler.py`
  - `src/backend/tests/test_sync_coordinator.py`
  - `src/backend/tests/test_issue_scheduler.py`
- **Modified files**:
  - `.env.example`
  - `README.md`
  - `src/backend/app/core/config.py`
  - `src/backend/app/core/runtime.py`
  - `src/backend/app/main.py`
  - `src/backend/app/repositories/runtime_state_repository.py`
  - `src/backend/tests/test_portfolio.py`
  - `src/backend/tests/test_runtime_state_repository.py`
  - `progress/BACKEND.md`
- **Validation commands**:
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_runtime_state_repository.py src/backend/tests/test_sync_coordinator.py src/backend/tests/test_issue_scheduler.py`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_runtime_state_repository.py src/backend/tests/test_sync_coordinator.py src/backend/tests/test_issue_scheduler.py src/backend/tests/test_portfolio.py -k "runtime or sync or scheduler or startup or health"`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q`
  - `git diff --check`
- **Validation results**:
  - coordinator·scheduler·runtime 테스트 `13 passed`.
  - lifespan 연동 포함 관련 회귀 `17 passed`, `13 deselected`, 기존 warning 1개.
  - 전체 테스트 `89 passed`, 기존 Starlette deprecation warning 1개 유지.
  - 전체 테스트 시간 `27분 24초`; 지연은 기존 포트폴리오 계산 구간에서 발생했고 신규 관련 테스트는 `2.44초`에 통과.
  - whitespace 오류 없음.
- **Remaining**:
  - Data A 실제 수집·자동 검증·원자적 발행 workflow 구현 및 coordinator 주입.
  - Data B 재계산 workflow 연결.
  - `COMMON-RT-02` 승인 후 수동 실행·상태 공개 API 연결.
- **Blockers**: 실제 수집 workflow와 전 역할 공개 계약 승인 필요
- **Next task**: 전체 회귀 검증 후 내부 구현을 `review`로 유지

### 2026-07-22 — BE-RT-03/04: SQLite Runtime State and Durable Lock

- **Role**: Backend
- **Owner**: Backend
- **Task IDs**: `BE-RT-03`, `BE-RT-04`
- **Status**: `in_progress` / `review`
- **Completed**:
  - SQLite WAL 기반 runtime 저장소를 추가했다.
  - KIS 성공 시 KOSPI·KOSDAQ·삼성전자·SK하이닉스 마지막 정상 가격과 원천 시각을 upsert한다.
  - KIS 실패 시 네 항목 모두 SQLite last-known-good를 우선 사용하고, 저장값이 없는 주식만 검증 종가 fallback을 사용한다.
  - 단일 `issues` sync lock을 SQLite 트랜잭션으로 획득하고 다른 프로세스·저장소 인스턴스의 중복 실행을 거부한다.
  - owner token 검증, queued→running, heartbeat, terminal 완료와 lock 해제를 구현했다.
  - 서버 재시작 시 queued/running 작업을 `SERVER_RESTART_INTERRUPTED` 실패로 종료하고 lock을 해제하는 lifespan 복구 hook을 구현했다.
  - 공개 `/sync/*`와 `/market/quotes` 라우트 및 공유 스키마는 변경하지 않았다.
- **Created files**:
  - `src/backend/app/core/runtime.py`
  - `src/backend/app/repositories/runtime_state_repository.py`
  - `src/backend/tests/test_runtime_state_repository.py`
- **Modified files**:
  - `.env.example`
  - `README.md`
  - `src/backend/app/core/config.py`
  - `src/backend/app/main.py`
  - `src/backend/app/services/kis_market_data.py`
  - `src/backend/app/services/market_quotes.py`
  - `src/backend/app/utils/realtime_price.py`
  - `src/backend/tests/test_market_quotes.py`
  - `src/backend/tests/test_portfolio.py`
  - `progress/BACKEND.md`
- **Validation commands**:
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_runtime_state_repository.py`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_market_quotes.py src/backend/tests/test_runtime_state_repository.py src/backend/tests/test_kis_market_data.py`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_runtime_state_repository.py src/backend/tests/test_market_quotes.py src/backend/tests/test_kis_market_data.py src/backend/tests/test_portfolio.py -k "runtime or market or kis or health"`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q`
  - `git diff --check`
- **Validation results**:
  - runtime 저장소 단위 테스트 `6 passed`.
  - KIS·시장·runtime 관련 테스트 `21 passed`.
  - startup recovery 포함 관련 회귀 `22 passed`, `14 deselected`.
  - 전체 테스트 `81 passed`, 기존 Starlette deprecation warning 1개 유지.
  - whitespace 오류 없음. 실제 `data/runtime/` 파일 미생성 확인.
- **Remaining**:
  - 실제 scheduler와 수집·검증·원자적 발행 service 연결.
  - `COMMON-RT-02` 승인 후 수동 sync 및 상태 공개 API 연결.
  - 실제 KIS 키 smoke test와 last-known-good 공개 상태 표시.
- **Blockers**: 공개 계약 승인과 실제 KIS 키 필요
- **Next task**: 전체 회귀 테스트 후 내부 sync coordinator 구현 또는 계약 승인 대기

### 2026-07-22 — BE-RT-01: KIS Provider Confirmed and Adapter Implemented

- **Role**: Backend
- **Owner**: Backend
- **Task ID**: `BE-RT-01`
- **Status**: `review`
- **Decision**:
  - 팀 리드가 MVP 주 시장 provider를 한국투자증권 KIS REST API로 확정했다.
  - yfinance는 운영·보조 provider로 사용하지 않는다.
- **Completed**:
  - KIS OAuth 접근토큰 발급과 만료 전 재사용을 구현했다.
  - 삼성전자·SK하이닉스는 공식 주식현재가 endpoint와 TR ID로 매핑했다.
  - KOSPI(`0001`)·KOSDAQ(`1001`)은 공식 국내업종 현재지수 endpoint와 TR ID로 매핑했다.
  - 모든 KIS 요청에 서비스 timeout을 전달하고 KIS 오류·누락·0 이하 가격을 명시적 실패로 처리했다.
  - KIS 키가 모두 있을 때만 provider를 활성화하고, 키가 없으면 외부 호출 없는 provider와 기존 로컬 fallback을 유지한다.
  - 실제 키나 외부 호출 없이 검증하는 mock HTTP 테스트를 추가했다.
- **Created files**:
  - `src/backend/app/services/kis_market_data.py`
  - `src/backend/tests/test_kis_market_data.py`
- **Modified files**:
  - `.env.example`
  - `README.md`
  - `IDEA_ALIGNMENT_REPORT.md`
  - `src/backend/app/core/config.py`
  - `src/backend/app/utils/realtime_price.py`
  - `progress/BACKEND.md`
- **Validation commands**:
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_kis_market_data.py src/backend/tests/test_market_quotes.py`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q`
  - `git diff --check`
- **Validation results**:
  - KIS adapter와 시장 서비스 관련 테스트 `13 passed`.
  - 전체 테스트 `72 passed`, 기존 Starlette deprecation warning 1개 유지.
- **Remaining**:
  - 실제 KIS 키를 이용한 네 종목 smoke test.
  - SQLite last-known-good와 영속 sync lock 구현.
  - `COMMON-RT-02` 승인 후 공개 `/market/quotes` 통합.
- **Blockers**: 실제 KIS smoke test에는 팀 소유 KIS App Key·Secret이 필요함
- **Next task**: 전체 회귀 테스트 후 SQLite runtime state 내부 계층 구현

### 2026-07-22 — BE-RT-01: yfinance Excluded from MVP

- **Role**: Backend
- **Owner**: Backend
- **Task ID**: `BE-RT-01`
- **Status**: `review`
- **Decision**:
  - 팀 리드 지시에 따라 yfinance를 MVP 의존성과 운영 호출 경로에서 제외했다.
  - 승인된 국내 시장 provider가 연결되기 전까지 외부 provider 호출은 비활성화한다.
- **Completed**:
  - yfinance adapter와 import를 제거했다.
  - `requirements.txt`에서 yfinance 의존성을 제거했다.
  - provider별 심볼 매핑을 서비스에서 제거하고 provider adapter가 종목 매핑을 소유할 수 있게 경계를 정리했다.
  - 기본 provider를 외부 호출 없는 명시적 unavailable provider로 교체했다.
  - 삼성전자·SK하이닉스 기존 호출부는 검증 가격 저장소 fallback으로 동작하며, KOSPI·KOSDAQ은 승인 provider 전까지 값을 생성하지 않는다.
- **Modified files**:
  - `src/backend/requirements.txt`
  - `src/backend/app/services/market_quotes.py`
  - `src/backend/app/utils/realtime_price.py`
  - `src/backend/tests/test_market_quotes.py`
  - `IDEA_ALIGNMENT_REPORT.md`
  - `progress/BACKEND.md`
- **Validation commands**:
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_market_quotes.py`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q`
  - `rg -n -i "yfinance|YFinanceProvider|yf\\." src/backend/app src/backend/tests src/backend/requirements.txt -g "!*.pyc"`
  - `git diff --check`
- **Validation results**:
  - 시장 가격 서비스 테스트 `7 passed`.
  - 전체 테스트 `66 passed`, 기존 Starlette deprecation warning 1개 유지.
  - 활성 소스·테스트·의존성에서 yfinance 참조 없음. 과거 진행 로그는 이력 보존.
- **Remaining**: 승인된 KIS adapter 구현 및 실제 키 smoke test
- **Blockers**: `COMMON-RT-02` provider 및 공개 계약 승인 대기
- **Next task**: mock·로컬 fallback 회귀 검증 후 `review` 유지

### 2026-07-22 — BE-RT-01: Internal Market Quote Provider and Cache

- **Role**: Backend
- **Owner**: Backend
- **Task ID**: `BE-RT-01`
- **Status**: `review`
- **Assumptions**:
  - `COMMON-RT-02` 전 역할 승인 전에는 공개 요청·응답 모델과 `/market/quotes` 계약을 구현하지 않는다.
  - 이번 작업은 내부 provider/adapter, TTL 캐시, timeout, 로컬 가격 fallback 및 mock 기반 단위 테스트로 한정한다.
- **Completed**:
  - KOSPI·KOSDAQ·삼성전자·SK하이닉스 provider 심볼을 내부 계층에 매핑했다.
  - 승인된 외부 provider를 주입하고 timeout을 전달할 수 있는 내부 경계를 구현했다.
  - monotonic clock 기반 TTL 캐시와 테스트용 clock/provider 주입 구조를 구현했다.
  - 외부 provider 실패 시 삼성전자·SK하이닉스만 기존 검증 가격 저장소의 최신 종가를 사용하도록 제한했다.
  - 출처 없는 고정가격 fallback을 제거하고, provider와 로컬 가격이 모두 없으면 명시적 내부 예외를 발생시킨다.
  - 기존 API 회귀 테스트를 외부망과 분리하는 mock quote fixture를 추가했다.
- **Created files**:
  - `src/backend/app/services/__init__.py`
  - `src/backend/app/services/market_quotes.py`
  - `src/backend/tests/test_market_quotes.py`
- **Modified files**:
  - `.env.example`
  - `src/backend/app/core/config.py`
  - `src/backend/app/utils/realtime_price.py`
  - `src/backend/tests/test_portfolio.py`
  - `progress/BACKEND.md`
- **Validation commands**:
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_market_quotes.py src/backend/tests/test_portfolio.py`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_market_quotes.py`
  - `.venv\Scripts\python.exe -m pytest --collect-only -q -p no:cacheprovider`
  - `git diff --check`
- **Validation results**:
  - 시장 가격 서비스 단위 테스트 7개 통과.
  - 전체 회귀 테스트 65개 통과 후 provider adapter 경계 테스트도 별도 통과. 당시 총 66개 테스트 수집 확인.
  - whitespace 오류 없음. 줄바꿈 형식 안내만 확인.
- **Remaining**:
  - 공개 `/market/quotes` 요청·응답 계약과 fallback 표시는 구현하지 않았다.
  - `COMMON-RT-02` 승인 후 공개 API 통합 및 계약 테스트가 필요하다.
- **Blockers**: 공개 API 통합은 `COMMON-RT-02` 전 역할 승인 대기
- **Next task**: `COMMON-RT-02` 승인 후 `BE-RT-01` 공개 통합 검토 또는 승인 전 `BE-RT-03` 내부 scheduler/lock 기반 구조 착수

### 2026-07-21 13:20 — Common Schema & Sample Approval & BE-01 Start

- **Role**: Backend
- **Status**: `in_progress`
- **Completed**:
  - `COMMON-02` (Shared Schema Definition) 검토 완료 및 백엔드 담당자 관점 승인 (Approved).
  - `COMMON-03` (Sample Data Preparation) 검토 완료 및 백엔드 담당자 관점 승인 (Approved).
  - 백엔드 개발 병렬 시작에 따라 `BE-01` (FastAPI Skeleton) 작업 착수.
- **Created files**: None
- **Modified files**:
  - `progress/BACKEND.md`
- **Next task**: FastAPI Skeleton 설정 및 Jinja2, StaticFiles 마운트.

### 2026-07-21 14:05 — BE-01 & BE-03 Complete & BE-02 Start

- **Role**: Backend
- **Status**: `in_progress`
- **Completed**:
  - `BE-01`: FastAPI 프로젝트 뼈대 구성 완료. StaticFiles 마운트 및 Jinja2Templates 절대 경로 세팅 완료.
  - `BE-03`: 개발 B(프론트엔드)가 전달한 HTMX 및 Form 전송 연동 규격에 맞춰 HTML 조각(`components/risk_result.html`)을 렌더링하여 반환하는 Mock API 완비.
  - API 라우터 구조 설계 및 분리 구현 완료 (`health.py`, `portfolio.py`, `issues.py`, `risk.py`, `data.py`).
  - 테스트 모듈 `tests/test_portfolio.py`를 작성하여 `pytest` 검증 100% 통과 성공.
- **Created files**:
  - `src/backend/app/core/templates.py`
  - `src/backend/app/core/config.py`
  - `src/backend/app/routes/health.py`
  - `src/backend/app/routes/portfolio.py`
  - `src/backend/app/routes/issues.py`
  - `src/backend/app/routes/risk.py`
  - `src/backend/app/routes/data.py`
  - `src/backend/tests/test_portfolio.py`
- **Modified files**:
  - `src/backend/app/main.py`
  - `src/backend/requirements.txt`
  - `progress/BACKEND.md`
- **Next task**: `BE-02` (Data Loader and Validation) CSV 파서 및 스키마 검증기 구현.

### 2026-07-21 14:16 — BE-02, BE-04, BE-05, BE-06 Implementation & Tests Passed

- **Role**: Backend
- **Status**: `done` (백엔드 전 태스크 완료)
- **Completed**:
  - `BE-02`: CSV 검증기 및 로더 모듈(`csv_validator.py` 및 리포지토리 모듈) 완성 검증 및 로직 통과.
  - `BE-04`: `data/reviewed` 경로에 실데이터(또는 검증된 데이터) 탑재 및 로더 연동 완료.
  - `BE-05`: `portfolio.py` 및 `issues.py` 라우터에 실제 ESG 리스크 집계, 하방위험(CVaR) 계산, 포트폴리오 최적화(그리드서치), 그리고 과거 사건 반응 분석 모듈 통합 연동 완료.
  - `BE-06`: 데이터 로드 오류 및 모델 예외 처리 시 sample 데이터 폴백 로직 추가, 유동적 데이터 모드 대응을 위해 `test_portfolio.py` 단언문 수정 완료 및 전체 백엔드/모델링 테스트 통과(100%).
- **Created files**: None
- **Modified files**:
  - `src/backend/app/routes/portfolio.py`
  - `src/backend/app/routes/issues.py`
  - `src/backend/tests/test_portfolio.py`
  - `progress/BACKEND.md`
- **Validation commands**:
  - `.venv\Scripts\python -m pytest src/backend`
  - `.venv\Scripts\python -m pytest tests/`
- **Validation results**:
  - 백엔드 7개 테스트 케이스 모두 통과 (100% Pass)
  - 모델링 13개 테스트 케이스 모두 통과 (100% Pass)
- **Next task**: 프론트엔드 연동 및 최종 E2E 통합 테스트 검토 지원

### 2026-07-21 14:28 — Real-time External Stock Price Integration (yfinance)

- **Role**: Backend
- **Status**: `done`
- **Completed**:
  - `requirements.txt`에 `yfinance` 패키지 등록 및 가상환경 설치 완료.
  - `realtime_price.py` 유틸리티를 작성하여 삼성전자(`005930.KS`)와 SK하이닉스(`000660.KS`)의 라이브 주가를 yfinance로 실시간 조회하고, 네트워크 장애 시 로컬 CSV의 최신 종가로 복구되도록 구현 완료.
  - `portfolio.py` 및 `risk.py` 수정: 최적화 및 하방위험 연산 호출 전, 로컬 3개년 시계열 `price_df` (long format) 끝부분에 오늘 날짜의 실시간 주가 정보를 동적으로 concat(병합)하여 실시간 포트폴리오 처방이 반영되도록 통합함.
  - `test_portfolio.py`에 유틸리티 및 실시간 전송 테스트 케이스 2종을 보완하여 API 테스트 12개 항목 전체 정상 통과 완료.
- **Created files**:
  - `src/backend/app/utils/realtime_price.py`
- **Modified files**:
  - `src/backend/requirements.txt`
  - `src/backend/app/routes/portfolio.py`
  - `src/backend/app/routes/risk.py`
  - `src/backend/tests/test_portfolio.py`
  - `progress/BACKEND.md`
- **Validation commands**:
  - `.venv\Scripts\python -m pytest src/backend`
- **Validation results**:
  - 백엔드 12개 API 테스트 케이스 전체 정상 통과 (100% Pass)
- **Next task**: 프론트엔드 연동 및 최종 E2E 통합 테스트 검토 지원
### 2026-07-21 15:37 — Service Name Rename (Chip Buddy / 칩버디)

- **Role**: Backend
- **Status**: `done`
- **Completed**:
  - `Chip Buddy` 및 `칩버디`로 서비스명 반영 계획 수립 및 유저 승인 완료.
  - 백엔드, 프론트엔드, 각종 안내 문서 및 프로젝트 설정 전반의 서비스명 일괄 업데이트 완료.
- **Created files**: None
- **Modified files**:
  - `src/backend/app/main.py`
  - `src/backend/tests/test_portfolio.py`
  - `src/frontend/templates/index.html`
  - `README.md`
  - `AGENTS.md`
  - `개발 A GUIDELINE.md`
  - `데이터 B GUIDELINE.md`
  - `skills/semiconductor-project-coordinator/SKILL.md`
  - `progress/BACKEND.md`
- **Validation commands**:
  - `.venv\Scripts\python -m pytest src/backend`
- **Validation results**:
  - 12개 API 및 렌더링 테스트 케이스 전원 통과 (100% Pass)
- **Next task**: 프론트엔드 연동 및 최종 E2E 통합 테스트 검토 지원

### 2026-07-21 15:43 — Backend-based E2E Integration Test Verification & Feature Mapping

- **Role**: Backend
- **Status**: `done`
- **Completed**:
  - `pytest`를 통한 모델링 및 백엔드 API 모듈 전체 통합 테스트(총 25개 테스트 케이스)를 기동하여 100% Pass 검증을 확인했습니다 (E2E 통합 테스트 검증 백엔드 지원 완료).
  - 현재 백엔드 서버 소스 코드를 전수조사하여 칩버디(Chip Buddy) 서비스가 제공하는 모든 세부 기능 명세를 누락 없이 정리 및 체계화 완료했습니다.
- **Created files**: None
- **Modified files**:
  - `progress/BACKEND.md`
- **Validation commands**:
  - `.venv\Scripts\python -m pytest`
- **Validation results**:
  - 전체 25개 테스트(백엔드 API 12개 + 모델링 13개) 100% Pass 성공
- **Next task**: 최종 데모 시연 준비 및 프론트엔드 E2E 결합 지원

### 2026-07-21 17:20 — Rebalancing Profile & Purchase Reason Implementation

- **Role**: Backend
- **Status**: `done`
- **Completed**:
  - 기획안 '투자 분석 및 포트폴리오 조정 기준 설정' 구현 완료.
  - 암호화 쿠키 기반 세션(`SessionMiddleware`) 도입을 통해 사용자 설정 상태 유지.
  - `PurchaseReason`, `KnowledgeStage`, `RebalancingProfile`, `TurnoverLevel` 데이터 모델 추가 (`src/backend/app/core/schemas.py`).
  - 마법사 3단계 렌더링 라우터 추가 (`/diagnosis`, `/rebalancing-profile`, `/settings-result`).
  - `optimizer.py` 내 가중치 프로필 매핑 적용 (하방위험: 0.7, ESG: 0.3 고정 및 사용자 프로필별 `turnover_weight` 유동 적용).
  - Jinja2 매크로 순환 호출(RecursionError) 방지를 위한 인라인 테이블 렌더링 도입 (`risk_result.html`).
  - 전체 pytest 25개 테스트 케이스 100% 통과 완료.
- **Created files**:
  - `src/backend/app/core/schemas.py`
  - `src/frontend/templates/diagnosis.html`
  - `src/frontend/templates/rebalancing_profile.html`
  - `src/frontend/templates/settings_result.html`
- **Modified files**:
  - `src/backend/app/main.py`
  - `src/backend/app/core/config.py`
  - `src/backend/app/routes/portfolio.py`
  - `src/modeling/optimizer.py`
  - `src/frontend/templates/components/risk_result.html`
  - `src/frontend/templates/index.html`
  - `src/backend/requirements.txt`
  - `progress/BACKEND.md`
- **Validation commands**:
  - `.venv\Scripts\python -m pytest`
- **Validation results**:
  - 25 passed, 1 warning (100% Pass)
- **Next task**: 최종 데모 기동 수동 검증 및 프론트엔드 스타일 다듬기 지원

### 2026-07-21 17:48 — E2E Step 1: Issues Route Stabilization & Dynamic Binding

- **Role**: Backend
- **Status**: `done`
- **Completed**:
  - 이슈 분석 화면(`/issues`) 내의 `official_source_url` 및 `news_url` 키 매핑 오류 해결.
  - `test_portfolio.py` 내에 `/issues` HTML 페이지 렌더링 및 동적 과거 사례 반응 출력("주가 회복 소요 기간") 확인 테스트 케이스 `test_issues_page_rendering` 추가.
  - pytest 실행 검증 결과 총 26개 테스트 케이스 100% 통과 달성. 과거 유사 사례 주가 수익률 및 회복일(events.py 연산값)이 Jinja2 테이블에 동적 바인딩 성공함 확인.
- **Created files**: None
- **Modified files**:
  - `src/backend/app/routes/issues.py`
  - `src/backend/tests/test_portfolio.py`
  - `progress/BACKEND.md`
- **Validation commands**:
  - `.venv\Scripts\python -m pytest`
- **Validation results**:
  - 26 passed, 1 warning (100% Pass)
- **Next task**: E2E 2단계 (대시보드 종합 건강 점수 및 3색 위험 신호등 구현) 착수

### 2026-07-21 21:37 — BE-RT-00: ESG Schema Contract Recovery

- **Role**: Backend
- **Owner**: Backend
- **Task ID**: `BE-RT-00`
- **Status**: `done`
- **Completed**:
  - JSON Schema의 `type: [number, null]` nullable union을 CSV 숫자로 캐스팅하도록 검증기 보완.
  - sample ESG·event CSV를 최신 필수 열과 타입에 맞게 동기화.
  - reviewed ESG 72행, reviewed 사건 5건, sample ESG 2행, sample 사건 2행의 동일 검증기 통과 확인.
  - ESG repository와 `/risk/esg` 회귀 테스트 복구.
- **Created files**:
  - `src/backend/tests/test_csv_validator.py`
- **Modified files**:
  - `src/backend/app/utils/csv_validator.py`
  - `data/sample/esg_indicators.sample.csv`
  - `data/sample/events.sample.csv`
  - `data/sample/sample-validation-report.json`
  - `progress/BACKEND.md`
- **Validation commands**:
  - reviewed/sample ESG·event 직접 `validate_csv_file` 검증
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_csv_validator.py src/backend/tests/test_portfolio.py -k "csv_validator or esg_repository or event_repository or risk_esg"`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests src/backend/tests`
- **Validation results**:
  - 직접 검증 4종 모두 통과.
  - 관련 회귀 테스트 6 passed.
  - 전체 테스트 29 passed, 1 warning.
- **Remaining**:
  - `COMMON-RT-02` 시장·포트폴리오·동기화 API 계약 검토.
- **Blockers**: 없음
- **Next task**: `COMMON-RT-02` 계약 검토 후 `BE-RT-01` 시장 가격 서비스 구현.

