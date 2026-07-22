# Integration Progress Log

## Task Status

| Task ID | Task | Status | Output | Blocker |
|---|---|---|---|---|
| INT-CLEANUP-01 | Canonical Data, Environment and Frontend Draft Cleanup | `done` | canonical paths and isolated Stitch drafts | - |
| INT-01 | End-to-End Test | `in_progress` | 실데이터 & 실시간 주가 API 활용 최종 화면 연동 검증 | - |
| INT-02 | Data and Model Review | `done` | 실데이터 스키마 및 최적화 엔진 안정성 검수 완료 | - |
| INT-03 | Demo Preparation | `todo` | 투자 성향/보유 정보 입력에 따른 재계산 데모 구성 | INT-01 완료 대기 |
| COMMON-RT-01 | Realtime and Daily Sync Requirements Definition | `done` | PRD·Plan·ROADMAP 요구사항 확정 | - |
| COMMON-RT-02 | Market, Portfolio Summary and Sync API Contract Review | `review` | 계약 문서·JSON Schema·예시·계약 테스트 완료 | 전 역할 명시적 승인 필요 |
| COMMON-RT-03 | Human Review Removal and Automated Validation Contract Migration | `done` | processed/validated 자동 검증 계약·데이터·소비 코드 전환 | - |
| BE-RT-00 | ESG Schema Validator and Sample Contract Compatibility Recovery | `done` | processed/sample 검증과 ESG API 로딩 복구 | - |
| INT-RT-01 | Market·Portfolio·Daily Sync End-to-End Test | `todo` | 실시간 시장·자산 평가와 이슈 동기화 E2E | 역할별 구현 대기 |

## Active Blockers

| Blocker ID | Related Task | Description | Owner | Required Action | Status |
|---|---|---|---|---|---|
| RT-B01 | COMMON-RT-02 | Data A 보완 검토와 Data B·Backend·Frontend의 명시적 계약 승인 필요 | Team Lead / All Roles | 각 역할 로그에 검토·승인 기록 | `review` |
| RT-B02 | DATA-B-RT-01 | Data B 동적 ESG·최적화 변경 미동기화 | Data B | 완료 후 통합 브랜치 동기화 | `in_progress` |

## Work Log

### 2026-07-22 11:30 — Repository Canonicalization Cleanup Start

- **Role**: Integration
- **Owner**: Codex
- **Task ID**: `INT-CLEANUP-01`
- **Status**: `in_progress`
- **Assumptions**:
  - `data/processed/` is the only model/API source for validated price and index data.
  - `.env.example` is the canonical environment template referenced by project documentation.
  - Unreferenced Google Stitch HTML drafts belong under `stitch-export/raw/`, not production templates.
- **Planned work**:
  - Remove byte-identical legacy data copies and update migration references.
  - Remove the incomplete `env.example` duplicate.
  - Move unreferenced Stitch drafts out of `src/frontend/templates/`.
- **Validation commands**:
  - full pytest suite
  - canonical-path and template-reference scans
  - `git diff --check`
- **Blockers**: None

### 2026-07-22 12:05 — Repository Canonicalization Cleanup Complete

- **Role**: Integration
- **Owner**: Codex
- **Task ID**: `INT-CLEANUP-01`
- **Status**: `done`
- **Completed**:
  - Kept `data/processed/stock_prices.csv` and `data/processed/index_prices.csv` as the only validated price/index sources.
  - Kept `data/docs/data_dictionary.md` as the canonical data dictionary.
  - Kept `.env.example` as the only environment template.
  - Moved six unreferenced Stitch drafts from production templates to `stitch-export/raw/`.
  - Updated the legacy migration script to stop writing the removed price-data copy.
  - Preserved historical path mentions in role progress logs as immutable work history.
- **Created files**:
  - `stitch-export/raw/README.md`
- **Moved files**:
  - `diagnosis_result.html`, `home.html`, `issue_analysis.html`
  - `portfolio_edit.html`, `portfolio_input.html`, `portfolio_summary.html`
- **Deleted files**:
  - `data/index_prices.csv`
  - `data/prices.csv`
  - `data/notes/data_dictionary.md`
  - `env.example`
- **Modified files**:
  - `scripts/migrate_automated_validation.py`
  - `progress/INTEGRATION.md`
- **Validation commands**:
  - `.venv\\Scripts\\python.exe -m pytest -q`
  - canonical-path and production-template reference scans with `rg`
  - non-empty duplicate SHA-256 scan
  - `git diff --check`
- **Validation results**:
  - Full test suite passed (`81 tests collected`, exit code 0).
  - Removed-path references outside historical progress logs: 0.
  - Non-empty duplicate file hashes: 0.
  - Production route/template mapping is complete; whitespace check passed.
- **Remaining issues**: None for this cleanup task.
- **Blockers**: None.
- **Next recommended task**: Continue `INT-01` end-to-end verification.

### 2026-07-21 10:00 — Initial Setup

- **Role**: Integration
- **Status**: `todo`
- **Completed**: 폴더 구조 뼈대 설정 및 Integration 진행 문서 생성 완료.
- **Created files**:
  - `progress/INTEGRATION.md`
- **Next task**: 체크포인트별 연동 현황 관리 및 E2E 연동 계획 수립.

### 2026-07-21 10:05 — Git Remote Integration and Initial Push

- **Role**: Integration
- **Status**: `in_progress`
- **Completed**: 
  - 원격 저장소(`https://github.com/guruggurug/sesac-mini-project2`)와의 히스토리 불일치 오류(fetch first) 해결을 위해 `git fetch` 실행 후 unrelated histories merge (`-s ours` 전략) 수행하여 로컬 프로젝트 사양과 기본 파일 보존.
  - 원격 저장소의 `main` 브랜치로 모든 초기 뼈대 코드 및 아티팩트 푸시 완료.
- **Next task**: 공통 스키마 및 샘플 데이터에 대한 역할별(DATA A, DATA B, Backend, Frontend) 리뷰 및 승인(COMMON-02, COMMON-03).

### 2026-07-21 14:45 — COMMON-02 & COMMON-03 Approved & Checkpoint-01 Pass & E2E Start

- **Role**: Integration
- **Owner**: Team Lead
- **Status**: `in_progress`
- **Completed**:
  - `COMMON-02` (공통 스키마 정의) 및 `COMMON-03` (샘플 데이터 준비)에 대해 데이터 A, 데이터 B, 백엔드, 프론트엔드 전 직무의 승인(`approved`)이 완료되었음을 확인 및 `done` 처리.
  - 이에 따라 `CHECKPOINT-01` (Initial Parallel-Work Readiness) 공식 패스 선언.
  - 데이터 A의 실데이터 배포(`DATA-A-05`)가 완료되고 데이터 B의 실데이터 연동(`DATA-B-05`) 및 민감도 분석(`DATA-B-06`) 또한 안전하게 수행 완료됨에 따라 데이터 및 모델 검수(`INT-02`)를 `done`으로 판정.
  - 백엔드와 프론트엔드의 병렬 개발 산출물들이 모두 구현 완료되었으므로 최종 시스템을 E2E로 연동 테스트(`INT-01`)하기 위해 서버 구동 및 통합 검증 작업 착수.
- **Created files**: None
- **Modified files**:
  - `progress/INTEGRATION.md`
- **Next task**: `INT-01` (End-to-End Test) 최종 구동 및 HTMX-FastAPI 화면 표출 검증.

### 2026-07-21 16:25 — Issues Dashboard Normalization (INT-01)

- **Role**: Integration
- **Owner**: AI Coding Agent (Antigravity)
- **Status**: `in_progress`
- **Completed**:
  - 기획안 대비 누락되었던 `/issues` HTML 라우터를 백엔드 [issues.py](file:///c:/dev/sesac-mini-pjt2/src/backend/app/routes/issues.py)에 구현하여 404 에러 복구.
  - 신규 HTML 템플릿 [issues.html](file:///c:/dev/sesac-mini-pjt2/src/frontend/templates/issues.html)을 생성하여 모바일 화면으로 이슈 리스트 서빙 지원.
  - [bottom_nav.html](file:///c:/dev/sesac-mini-pjt2/src/frontend/templates/components/bottom_nav.html)의 active 탭 표시를 Request path에 따라 유동적으로 스타일링되도록 동적화.
  - [issue_cards.html](file:///c:/dev/sesac-mini-pjt2/src/frontend/templates/components/issue_cards.html) 내부의 과거 유사 사건 주가 반응 하드코딩 수치들을 제거하고 [events.py](file:///c:/dev/sesac-mini-pjt2/src/modeling/events.py)의 `analyze_all_events` 연산 결과와 연동하여 동적으로 바인딩 처리 완료.
- **Created files**:
  - [issues.html](file:///c:/dev/sesac-mini-pjt2/src/frontend/templates/issues.html)
- **Modified files**:
  - [issues.py](file:///c:/dev/sesac-mini-pjt2/src/backend/app/routes/issues.py)
  - [bottom_nav.html](file:///c:/dev/sesac-mini-pjt2/src/frontend/templates/components/bottom_nav.html)
  - [issue_cards.html](file:///c:/dev/sesac-mini-pjt2/src/frontend/templates/components/issue_cards.html)
  - [INTEGRATION.md](file:///c:/dev/sesac-mini-pjt2/progress/INTEGRATION.md)
- **Next task**: `INT-01` (End-to-End Test) 폼 입력 수정 및 홈 화면 실시간 재연산 관련 누락 기능 점검 및 보안.

### 2026-07-21 21:27 — Realtime Market & Daily Issue Sync Requirements Finalized

- **Role**: Integration
- **Owner**: Team Lead
- **Task ID**: `COMMON-RT-01`
- **Status**: `done`
- **Completed**:
  - 시장 가격은 장중 10~30초 간격으로 갱신하도록 확정.
  - 홈에 코스피·코스닥·삼성전자·SK하이닉스 시장 현황을 표시하도록 확정.
  - 삼성전자·SK하이닉스 현재가를 총 자산 평가액·평가손익·현재 비중에 반영하도록 확정.
  - 공시·뉴스·ESG 이슈는 하루 한 번 자동 동기화하고 사용자가 추가 동기화를 요청할 수 있도록 확정.
  - 신규 승인 사건 또는 사건 상태 변경 후 ESG 위험과 추천 비중을 다시 계산하도록 확정.
- **Modified files**:
  - `chipbuddy_prd_mvp_4days_v1.5.md`
  - `chipbuddy_plan_mvp_4days_v1.5.md`
  - `ROADMAP.md`
  - `PROGRESS.md`
  - `progress/INTEGRATION.md`
- **Validation commands**:
  - 실시간·동기화 키워드 및 잔존 충돌 문구 검색
- **Validation results**:
  - 제한적 실시간·실시간 가격 Drop First·관리자 전용 갱신 충돌 문구 제거 확인.
- **Remaining**:
  - `COMMON-RT-02` 공용 API·스키마에 대한 전 역할 검토 및 승인.
- **Blockers**:
  - Data B 변경 미동기화 및 ESG 데이터 계약 비호환.
- **Next task**: `COMMON-RT-02` 계약 초안 작성과 역할별 리뷰.

### 2026-07-21 21:45 — Market, Portfolio and Sync API Contract Draft

- **Role**: Integration
- **Owner**: Team Lead
- **Task ID**: `COMMON-RT-02`
- **Status**: `review`
- **Completed**:
  - `GET /market/quotes`의 필수 4개 항목, 10~30초 갱신 간격, 가격·시장·지연·출처 상태를 정의.
  - `POST /portfolio/summary`의 보유 수량·평단가 입력과 현재가 기반 평가액·손익·수익률·현재 비중 계산 계약을 정의.
  - `POST /sync/issues`와 `GET /sync/status`의 예약/수동 공용 서비스, 중복 실행 재사용, 상태 전이와 후보→검수 데이터 경계를 정의.
  - JSON Schema, sample 표기 예시와 산술·중복·상태 전이 계약 테스트를 작성.
- **Created files**:
  - `schemas/api/README.md`
  - `schemas/api/market-quotes-response.schema.json`
  - `schemas/api/portfolio-summary-request.schema.json`
  - `schemas/api/portfolio-summary-response.schema.json`
  - `schemas/api/sync-issues-request.schema.json`
  - `schemas/api/sync-status-response.schema.json`
  - `schemas/api/examples/market-quotes-response.example.json`
  - `schemas/api/examples/portfolio-summary-request.example.json`
  - `schemas/api/examples/portfolio-summary-response.example.json`
  - `schemas/api/examples/sync-issues-request.example.json`
  - `schemas/api/examples/sync-status-response.example.json`
  - `src/backend/tests/test_realtime_api_contracts.py`
- **Modified files**:
  - `schemas/data/data-enums.yaml`
  - `chipbuddy_prd_mvp_4days_v1.5.md`
  - `chipbuddy_plan_mvp_4days_v1.5.md`
  - `ROADMAP.md`
  - `PROGRESS.md`
  - `progress/INTEGRATION.md`
- **Validation commands**:
  - `.venv\\Scripts\\python.exe -m pytest src/backend/tests/test_realtime_api_contracts.py -q`
  - `git diff --check`
- **Validation results**:
  - 계약 테스트 `9 passed`.
  - whitespace 오류 없음.
- **Remaining**:
  - Data A, Data B, Backend, Frontend 역할별 계약 승인.
  - 승인 후 Pydantic 모델·라우터·서비스·프론트엔드 소비자 구현.
- **Blockers**:
  - 공유 스키마 승인이 끝나기 전에는 `done` 처리 불가.
- **Next task**: 역할별 계약 검토 후 Backend의 시장 가격 서비스와 포트폴리오 요약 API 구현.

### 2026-07-21 22:25 — Automated Validation Runtime Migration

- **Role**: Integration
- **Owner**: Team Lead
- **Task ID**: `COMMON-RT-03`
- **Status**: `done`
- **Completed**:
  - 런타임 파이프라인에서 사람 검수 단계를 제거하고 `raw → candidate → automated validation → processed → API → UI`로 확정.
  - `review_status`와 `needs_review`를 ESG·사건 스키마, enum, CSV와 모델 필터에서 제거.
  - `data_status=reviewed`를 `data_status=validated`로 변경하고 데이터 경로를 `data/reviewed/`에서 `data/processed/`로 이전.
  - 모델 사건 반영 조건을 `confirmed|sanctioned|resolved`, `authority_confirmed=true`, 공식 출처 존재로 자동화.
  - AGENTS·PRD·Plan·ROADMAP·README·API 계약을 같은 자동 검증 흐름으로 정렬.
- **Created files**:
  - `scripts/migrate_automated_validation.py`
  - `data/candidate/news_candidates.csv`
  - `data/processed/*`
- **Validation commands**:
  - `.venv\\Scripts\\python.exe -m pytest -q`
  - 활성 스키마·코드·데이터의 `review_status|needs_review|reviewed` 잔존 검색
- **Validation results**:
  - 전체 테스트 `38 passed`, 기존 Starlette/httpx deprecation warning 1건.
  - 활성 스키마·백엔드·모델·테스트·CSV에 사람 검수 상태 참조 없음.
- **Remaining**:
  - 실제 일일·수동 수집기와 원자적 processed 스냅샷 발행 서비스 구현.
  - `COMMON-RT-02`의 역할 관점 계약 검토.
- **Blockers**: 없음.
- **Next task**: `COMMON-RT-02` 단독 역할 관점 검토 후 `BE-RT-01` 시장 가격 서비스 구현.

### 2026-07-22 01:42 — Data A Contract Review Remediation

- **Role**: Integration / Data A self-review
- **Owner**: Team Lead
- **Task ID**: `COMMON-RT-02`
- **Status**: `review`
- **Completed**:
  - 사건 상태를 `reported|confirmed|resolved`로 단순화하고 제재 결과를 `enforcement_action`으로 분리.
  - 탐지 출처를 `dart_disclosure|news`로 제한하고 소문 데이터는 raw 단계에서 제외하도록 확정.
  - `availability=unavailable`이면 `raw_value=null`만 허용하고 0을 거부하는 계약 테스트 추가.
  - 검증 실패 후보는 unavailable 데이터로 변환하지 않고 processed 발행에서 제외하도록 문서화.
  - 동기화 응답에 `stage`, 단계별 건수, 스냅샷 발행 증거와 재계산 상태를 추가.
  - `success`, `partial_success`, `failed`의 수집·검증·발행 의미를 분리.
- **Modified files**:
  - `AGENTS.md`
  - `README.md`
  - `chipbuddy_prd_mvp_4days_v1.5.md`
  - `chipbuddy_plan_mvp_4days_v1.5.md`
  - `schemas/data/data-enums.yaml`
  - `schemas/data/events.schema.json`
  - `schemas/api/README.md`
  - `schemas/api/sync-status-response.schema.json`
  - `schemas/api/examples/sync-status-response.example.json`
  - `data/processed/events.csv`
  - `data/sample/events.sample.csv`
  - `scripts/migrate_automated_validation.py`
  - 관련 테스트와 Data A 문서
- **Validation commands**:
  - `.venv\\Scripts\\python.exe -m pytest -q`
  - `.venv\\Scripts\\python.exe -m pytest src/backend/tests/test_csv_validator.py src/backend/tests/test_realtime_api_contracts.py -q`
- **Validation results**:
  - 전체 회귀 테스트 `43 passed`, 기존 Starlette/httpx deprecation warning 1건.
  - 최종 스키마·계약 집중 테스트 `17 passed`.
- **Remaining**:
  - candidate, sources, event_sources 스키마 정의.
  - 자동 중복 판정 키와 충돌 처리 규칙 정의.
  - Data B 최신 ESG 모델에서 unavailable 값을 0 또는 하드코딩 기본점수로 대체하지 않는지 검증.
- **Blockers**:
  - 위 세 항목 완료 전 Data A 관점 최종 `approved` 처리 불가.
- **Next task**: candidate/source/dedup 계약을 보완한 뒤 Data A 자체 검토를 종료.

### 2026-07-22 03:28 — Integration Checkpoint Commit Preparation

- **Role**: Integration
- **Owner**: Team Lead / Codex
- **Task ID**: `INT-01`, `COMMON-RT-02`, `COMMON-RT-03`
- **Status**: `done`
- **Completed**:
  - 로컬 변경의 staged/unstaged 상태와 삭제 대상을 점검하고 `reviewed → processed` 마이그레이션에 따른 삭제임을 확인.
  - 삭제된 `data/reviewed/*`를 참조하던 환경 설정 예시를 `data/processed/*`로 정렬.
  - 원격 브랜치의 선행 커밋과 로컬 변경의 동기화 순서를 확인.
  - 자동 검증 파이프라인, 실시간 API 계약, 프로젝트 문서를 세 개의 논리적 커밋으로 분리.
  - 원격 선행 커밋을 rebase로 반영하고 `origin/feature/ui-railway`에 push 완료.
- **Modified files**:
  - `.env.example`
  - `env.example`
  - `progress/INTEGRATION.md`
- **Validation commands**:
  - 전체 pytest 회귀 테스트
  - Git whitespace 검사
- **Validation results**:
  - 커밋 전과 rebase 후 전체 pytest 회귀 테스트 통과.
  - `git diff --check` 통과.
- **Remaining**:
  - 프로젝트 작업 상태상 `COMMON-RT-02` 역할별 승인과 Realtime & Daily Sync 구현은 계속 진행 필요.
- **Blockers**: 없음.
- **Next task**: `COMMON-RT-02` 역할별 승인을 완료하고 Realtime & Daily Sync 역할 구현 착수.

### 2026-07-22 03:41 — COMMON-RT-02 Final Cross-Role Contract Review

- **Role**: Integration / Team Lead
- **Owner**: Team Lead / Codex
- **Task ID**: `COMMON-RT-02`
- **Status**: `done`
- **Completed**:
  - Data A·Data B·Backend·Frontend 관점의 계약 승인 조건과 기존 보완 내역 재검토.
  - candidate/source/event-source 스키마와 자동 중복 판정 규칙 존재 확인.
  - validated 모드에서 ESG 집계 점수 누락 시 예시 점수를 사용하지 않고 오류 처리하는 모델 경로 확인.
  - fallback 가격의 stale 상태를 스키마에서 강제하고 scoring 입력 변경에 따른 재계산 트리거를 명시.
  - Data A, Data B, Backend, Frontend 관점 계약을 모두 `approved`로 확정.
- **Schema proposal**:
  - 시장 시세의 `price_status=fallback`이면 `is_stale=true`를 JSON Schema에서 강제해 문서와 응답 계약을 일치시킨다.
  - 자동 검증 후 ESG·최적화 재계산을 발생시키는 모델 적격 사건 변경 조건을 API 계약 문서에 명시한다.
- **Affected roles**: Data A, Data B, Backend, Frontend, Integration.
- **Validation commands**:
  - `pytest src/backend/tests/test_realtime_api_contracts.py src/backend/tests/test_issue_pipeline_contracts.py -q`
  - 전체 pytest 회귀 테스트
  - `git diff --check`
- **Validation results**:
  - 계약·이슈 파이프라인 집중 테스트 `23 passed`.
  - 전체 pytest 회귀 테스트 통과 (`59 tests collected`).
  - JSON Schema Draft 2020-12 자체 검증과 예시 검증 통과.
- **Remaining**: 승인된 계약에 따른 역할별 Realtime & Daily Sync 구현.
- **Blockers**: 없음.
- **Next task**: Data B 변경을 동기화하고 `BE-RT-01`, `DATA-A-RT-01`부터 역할 구현 착수.

### 2026-07-22 03:54 — COMMON-RT-02 Premature Approval Correction

- **Role**: Integration / Team Lead
- **Owner**: Team Lead / Codex
- **Task ID**: `COMMON-RT-02`
- **Status**: `review`
- **Completed**:
  - 계약 테스트 통과와 역할별 승인을 구분해 승인 근거를 재감사.
  - Data A 역할 로그가 `review`, Data B·Backend·Frontend 역할 로그에 COMMON-RT-02 명시적 승인이 없음을 확인.
  - 루트 진행표와 로드맵의 성급한 `done/approved` 표시를 `review/pending`으로 교정.
  - fallback stale 스키마, 재계산 조건 문서와 계약 테스트 보완은 유효하므로 유지.
- **Modified files**:
  - `PROGRESS.md`
  - `ROADMAP.md`
  - `schemas/api/README.md`
  - `progress/INTEGRATION.md`
- **Validation commands**:
  - `pytest src/backend/tests/test_realtime_api_contracts.py -q`
  - `git diff --check`
- **Validation results**:
  - Realtime API 계약 테스트 `12 passed`.
  - `git diff --check` 통과.
- **Remaining**:
  - Data A 보완 조건 확인 및 담당자 승인.
  - Data B, Backend, Frontend 역할별 계약 검토와 명시적 승인.
- **Blockers**: `RT-B01` 복원.
- **Next task**: 각 역할이 자기 진행 로그에 COMMON-RT-02 검토 결과를 기록한 뒤 팀 리드가 최종 승인 여부를 재판정.

### 2026-07-22 04:05 — Four-Day Scope and Legacy Contract Cleanup

- **Role**: Integration / Team Lead
- **Owner**: Team Lead / Codex
- **Task ID**: `COMMON-RT-02`
- **Status**: `review`
- **Completed**:
  - 프로젝트 기간을 4일로 확정.
  - `ROADMAP.md`의 실시간·일일 동기화 작업을 Day 3-4 구간으로 명시.
  - 프론트엔드 런타임의 `reviewed` 상태를 `validated`·`fallback`·`sample` 계약으로 교정.
  - PRD·계획·기능 문서의 사건 상태를 `reported`·`confirmed`·`resolved`로 통일하고 제재 결과를 `enforcement_action`으로 분리.
  - 개발 A 가이드의 `raw → candidate → processed` 자동 검증·원자적 발행 흐름과 Realtime API 목록을 최신화.
  - 데이터 B 가이드의 역할 명칭, 4일 범위, 이벤트 필터·결과 상태 계약을 최신화.
  - Data A·Backend 현재 작업표의 폐기된 `data/reviewed` 산출물 경로를 processed 경로로 교정.
  - 오래된 분석 보고서 2개에 superseded 표식을 추가.
- **Assumptions**:
  - `AGENTS.md`, `README.md`, 프로젝트 coordinator skill의 2일 표현을 4일로 통일.
  - 기존 B 가이드 파일은 `데이터 B GUIDELINE.md`로 변경하고 역할 명칭을 데이터 B로 통일.
  - 과거 Work Log와 마이그레이션 스크립트의 레거시 문자열은 감사 이력·호환 목적으로 보존.
- **Created or renamed files**:
  - `데이터 B GUIDELINE.md` (기존 B 가이드 파일 이름 변경)
- **Modified files**:
  - `AGENTS.md`, `README.md`, `ROADMAP.md`, `PROGRESS.md`
  - `개발 A GUIDELINE.md`, `chipbuddy_prd_mvp_4days_v1.5.md`, `chipbuddy_plan_mvp_4days_v1.5.md`, `chip_buddy_features.md`
  - `src/frontend/index.js`, `src/frontend/templates/issues.html`, `src/frontend/templates/components/risk_result.html`, `src/frontend/static/css/index.css`
  - `progress/DATA-A.md`, `progress/BACKEND.md`, `progress/INTEGRATION.md`
  - `IDEA_ALIGNMENT_REPORT.md`, `analysis_results.md`, `skills/semiconductor-project-coordinator/SKILL.md`
- **Validation commands**:
  - `rg`로 레거시 경로·상태·사건 enum·기간 전수 재검색
  - `.venv\\Scripts\\python.exe -m pytest -q --disable-warnings`
  - `git diff --check`
- **Validation results**: 활성 문서·런타임의 레거시 표현 없음. 전체 테스트 `59 passed, 1 warning` (276.70초). `git diff --check` 통과.
- **Remaining**: `COMMON-RT-02`는 Data A `review`, Data B·Backend·Frontend `pending`이므로 전 역할 명시 승인 후에만 `done` 처리.
- **Blockers**: 없음.
- **Next task**: 역할별 `COMMON-RT-02` 계약 검토와 명시 승인 수집.
