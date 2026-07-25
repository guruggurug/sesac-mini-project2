# Integration Progress Log

## Task Status

| Task ID | Task | Status | Output | Blocker |
|---|---|---|---|---|
| INT-UI-01 | Intended Frontend UI Route Canonicalization | `done` | six approved UI templates wired to FastAPI | - |
| INT-CLEANUP-01 | Canonical Data and Environment Cleanup | `done` | canonical data/config paths; frontend UI ownership restored | - |
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

### 2026-07-25 — INT-DEPLOY-01 Reproducible Frontend Build Start

- **Role**: Integration
- **Owner**: Codex
- **Task ID**: `INT-DEPLOY-01`
- **Status**: `in_progress`
- **Goal**:
  - Node.js 24 LTS에서 Tailwind CSS를 재현 가능하게 빌드한다.
  - 운영 이미지는 Python/FastAPI 런타임만 포함하는 다단계 Docker 배포 구조를 제공한다.
- **Expected outputs**:
  - `Dockerfile`
  - `.dockerignore`
  - `.nvmrc`
  - Node/npm 엔진 계약과 실제 실행·배포 문서
- **Validation plan**:
  - Dockerfile·ignore·package 계약 정적 검증
  - Docker CLI 사용 가능 시 image build 및 `/health` smoke test
  - 전체 Python 회귀 테스트
  - `git diff --check`
- **Blockers**: 없음.

### 2026-07-25 — INT-DEPLOY-01 Reproducible Frontend Build Complete

- **Role**: Integration
- **Owner**: Codex
- **Task ID**: `INT-DEPLOY-01`
- **Status**: `review`
- **Completed**:
  - EOL인 Node.js 20 대신 공식 최신 LTS 계열인 Node.js 24와 npm 11을 프로젝트 계약으로 고정했다.
  - Node 24 Alpine CSS 빌드 단계와 Python 3.11 non-root 런타임 단계로 구성된 다단계 `Dockerfile`을 추가했다.
  - `.env`, 로컬 DB, runtime·raw·private 데이터, Node/Python 개발 의존성을 Docker context에서 제외했다.
  - 프로젝트 로컬 portable Node.js `v24.18.0`과 npm `11.16.0`을 공식 SHA256으로 검증해 `.tools/`에 준비했다.
  - `npm ci`와 Tailwind CSS 빌드를 실제 실행해 생성 CSS를 최신 템플릿과 동기화했다.
  - Windows 실행 정책을 전역 변경하지 않고 portable 또는 시스템 Node를 선택하는 `scripts/build_frontend.ps1`을 추가했다.
  - README의 존재하지 않는 별도 프론트엔드 개발 서버 안내를 실제 FastAPI/Jinja/Tailwind 구조로 교정했다.
- **Created files**:
  - `Dockerfile`
  - `.dockerignore`
  - `.nvmrc`
  - `scripts/build_frontend.ps1`
  - `src/backend/tests/test_deployment_config.py`
- **Modified files**:
  - `.gitignore`
  - `package.json`
  - `package-lock.json`
  - `README.md`
  - `src/frontend/static/css/index.css`
- **Validation commands**:
  - 공식 Node archive SHA256 검증
  - `npm ci`
  - `npm run css:build`
  - `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_frontend.ps1`
  - `.venv\Scripts\python.exe -m pytest -vv src/backend/tests/test_deployment_config.py src/backend/tests/test_ui_routes.py`
  - `git diff --check`
- **Validation results**:
  - Node `v24.18.0`, npm `11.16.0`, SHA256 일치.
  - 잠금 파일 기반 `77 packages` 설치와 Tailwind 빌드 성공.
  - 배포 계약·생성 CSS·UI 라우트 테스트 `27 passed, 1 warning`.
  - 직전 기능 전체 회귀 테스트 `188 passed, 1 warning`.
  - whitespace 오류 없음. 기존 CRLF 변환 안내만 확인.
- **Remaining**:
  - 현재 PC에 Docker CLI가 없어 실제 image build와 컨테이너 `/health` smoke test는 배포 환경에서 수행해야 한다.
  - Browserslist DB 업데이트 알림은 기능·빌드 실패가 아니며 별도 의존성 유지보수 범위다.
- **Blockers**: 없음.
- **Next recommended task**: Docker 사용 가능한 CI/배포 환경에서 image smoke test 후 3단계 시장 시세 API 연결을 진행한다.

### 2026-07-25 — INT-01 Phase 1 Frontend Optimization Binding Start

- **Role**: Integration
- **Owner**: Codex
- **Task ID**: `INT-01`
- **Status**: `in_progress`
- **Goal**:
  - 포트폴리오 입력 폼을 기존 `/portfolio/optimize` 계산 경로에 실제로 제출한다.
  - 진단 화면의 고정 샘플 추천값을 모델 응답의 현재·추천 비중, CVaR, ESG 위험, 설명, 경고로 교체한다.
  - 계산 전에는 결과를 꾸며내지 않고 명시적 빈 상태를 표시한다.
- **Allowed files**:
  - `src/frontend/templates/portfolio_input.html`
  - `src/frontend/templates/diagnosis_result.html`
  - `src/backend/app/routes/portfolio.py`
  - `src/backend/tests/test_portfolio.py`
  - `src/backend/tests/test_ui_routes.py`
  - `progress/INTEGRATION.md`
- **Validation plan**:
  - `.venv\Scripts\python.exe -m pytest -q src/backend/tests/test_ui_routes.py src/backend/tests/test_portfolio.py`
  - `.venv\Scripts\python.exe -m pytest -q`
  - `npm run css:build`
  - `git diff --check`
- **Blockers**: 없음.

### 2026-07-25 — INT-01 Phase 1 Frontend Optimization Binding Complete

- **Role**: Integration
- **Owner**: Codex
- **Task ID**: `INT-01`
- **Status**: `review`
- **Completed**:
  - 포트폴리오 입력 화면의 가짜 완료 alert를 제거하고 기존 `/portfolio/optimize` 폼 제출을 로딩 상태와 연결했다.
  - 투자 성향 선택값을 `conservative`·`balanced`·`esg_focused` 요청값으로 연결했다.
  - 진단 결과의 고정 비중·CVaR·ESG 등급·추천 문구를 모델 응답 기반 값으로 교체했다.
  - 계산 전 GET 화면에는 고정 결과 대신 명시적 빈 상태를 표시한다.
  - 계산 결과의 실제 `sample`·`validated`·`fallback` 상태를 화면에 보존한다.
- **Modified files**:
  - `src/frontend/templates/portfolio_input.html`
  - `src/frontend/templates/diagnosis_result.html`
  - `src/backend/app/routes/portfolio.py`
  - `src/backend/tests/test_portfolio.py`
  - `src/backend/tests/test_ui_routes.py`
- **Validation commands**:
  - `.venv\Scripts\python.exe -m pytest -q src/backend/tests/test_ui_routes.py src/backend/tests/test_portfolio.py`
  - `.venv\Scripts\python.exe -m pytest -q`
  - 390×844 인앱 브라우저 입력→최적화 결과 제출
  - `git diff --check`
- **Validation results**:
  - 동적 결과·빈 상태·실제 폼 제출 집중 테스트 `3 passed`.
  - 전체 회귀 테스트 `184 passed, 1 warning`.
  - 390px 화면에서 현재·추천 비중, CVaR, ESG 위험, 설명이 실제 모델 결과로 렌더링됐고 가로 overflow와 콘솔 오류가 없었다.
  - Node/npm 실행 파일이 현재 셸에 없어 `npm run css:build`는 실행하지 못했다. 새로 추가한 상태 표현은 기존 생성 CSS와 inline style만 사용한다.
- **Remaining**:
  - 포트폴리오 요약·홈·실시간 시세·이슈·동기화 화면 연결.
- **Blockers**: 없음.
- **Next recommended task**: 승인된 포트폴리오 요약 계약으로 JSON API와 `portfolio_summary.html`을 연결한다.

### 2026-07-25 — INT-01 Phase 2 Portfolio Summary Binding Start

- **Role**: Integration
- **Owner**: Codex
- **Task ID**: `INT-01`, `FE-RT-02`
- **Status**: `in_progress`
- **Goal**:
  - 승인된 포트폴리오 요약 스키마에 맞는 백엔드 응답을 제공한다.
  - 요약 화면의 고정 평가금액·손익·현재 비중을 응답 데이터로 교체한다.
- **Assumptions**:
  - 팀 리드의 단계별 구현 지시에 따라 `COMMON-RT-02` 문서의 현재 `review` 계약을 변경 없이 구현한다.
  - 이번 작업은 역할별 계약 승인 상태를 대신하지 않으며 `COMMON-RT-02` 상태는 그대로 유지한다.
- **Blockers**: 없음.

### 2026-07-25 — INT-01 Phase 2 Portfolio Summary Binding Complete

- **Role**: Integration
- **Owner**: Codex
- **Task ID**: `INT-01`, `FE-RT-02`
- **Status**: `review`
- **Completed**:
  - 승인된 계약과 동일한 `POST /portfolio/summary` 요청·응답 Pydantic 모델을 추가했다.
  - 현재가 기준 평가금액, 매입금액, 평가손익, 수익률, 종목 비중을 백엔드에서 결정적으로 계산한다.
  - KIS 설정 시 승인 provider를 사용하고, 미설정·실패 시 검증 종가 또는 마지막 정상 가격을 `fallback`으로 명시한다.
  - 가격 기준 시각은 사용 시세 중 가장 오래된 시각이며 모든 공개 시각을 Asia/Seoul `+09:00`으로 반환한다.
  - 최적화 입력의 수량·평균단가를 세션에 저장하고 포트폴리오 요약 화면이 동일 보유정보로 API를 호출한다.
  - 요약 화면의 고정 평가액·수익률·수량·비중을 제거하고 loading·empty·error·fallback 상태를 추가했다.
- **Created files**:
  - `src/backend/app/services/portfolio_summary.py`
  - `src/backend/tests/test_portfolio_summary.py`
- **Modified files**:
  - `src/backend/app/core/runtime.py`
  - `src/backend/app/core/schemas.py`
  - `src/backend/app/routes/portfolio.py`
  - `src/backend/app/routes/ui.py`
  - `src/backend/tests/test_portfolio.py`
  - `src/backend/tests/test_ui_routes.py`
  - `src/frontend/templates/portfolio_summary.html`
- **Validation commands**:
  - `.venv\Scripts\python.exe -m pytest -vv src/backend/tests/test_portfolio_summary.py`
  - `.venv\Scripts\python.exe -m pytest -q`
  - 실제 기본 runtime으로 `POST /portfolio/summary` smoke test
  - `git diff --check`
- **Validation results**:
  - 요약 API 계산·fallback·중복 입력·JSON Schema 검증 `3 passed`.
  - 전체 회귀 테스트 `188 passed, 1 warning`.
  - 기본 runtime smoke test `200 OK`; KIS 키 없는 환경에서 `price_status=fallback`, `data_status=fallback`을 명시했다.
  - whitespace 오류 없음. 기존 CRLF 변환 안내만 확인했다.
- **Remaining**:
  - 390px 요약 화면 브라우저 검증은 최종 E2E 단계에서 수행한다.
  - 시장 전체 공개 API와 장중 폴링, 홈 화면 연결은 3단계 범위다.
- **Blockers**: 없음.
- **Next recommended task**: `GET /market/quotes`와 홈 화면의 장중 폴링·fallback 표시를 연결한다.

### 2026-07-22 12:50 — Intended Frontend UI Route Canonicalization Start

- **Role**: Integration
- **Owner**: Codex
- **Task ID**: `INT-UI-01`
- **Status**: `in_progress`
- **Finding**:
  - The intended six-template frontend existed only in a disconnected Flask draft.
  - FastAPI localhost routes rendered a separately generated Jinja UI set instead.
- **Scope**:
  - Wire the intended six designs to FastAPI route paths.
  - Preserve calculation and JSON API behavior.
  - Remove the unintended production UI templates and their exclusive assets.
  - Add route-level regression tests that prevent the unintended UI from returning.
- **Blockers**: None

### 2026-07-22 17:30 — Intended Frontend UI Route Canonicalization Complete

- **Role**: Integration / Frontend
- **Owner**: Codex
- **Task ID**: `INT-UI-01`
- **Status**: `done`
- **Completed**:
  - Declared the six team-designed templates as the only canonical localhost UI screens.
  - Connected canonical and compatibility URLs to those templates through the FastAPI UI router.
  - Removed the disconnected legacy FastAPI templates, template fragments, and their exclusive static assets.
  - Replaced direct `/templates/*.html` links with application routes and made portfolio input submit to the existing optimization endpoint.
  - Added explicit sample/fallback labels and stable screen markers to prevent sample presentation values from appearing validated.
  - Repaired the truncated portfolio-input script and Material Symbols font loading.
- **Created files**:
  - `src/backend/app/routes/ui.py`
  - `src/backend/tests/test_ui_routes.py`
- **Modified files**:
  - `src/backend/app/main.py`
  - `src/backend/app/routes/issues.py`
  - `src/backend/app/routes/portfolio.py`
  - `src/backend/tests/test_portfolio.py`
  - the six canonical files under `src/frontend/templates/`
- **Removed files**: legacy `diagnosis`, `index`, `issues`, `rebalancing_profile`, `settings_result`, old component fragments, and their exclusive `index.js`/`index.css` assets.
- **Validation commands**:
  - `pytest tests/test_ui_routes.py tests/test_portfolio.py -q`
  - `pytest -q`
  - In-app browser checks at 390 x 844 for all six canonical routes.
- **Validation results**:
  - Targeted UI and portfolio regression tests: `30 passed`.
  - Full backend suite: `80 passed, 1 dependency deprecation warning`.
  - All six routes rendered the expected `data-ui-screen`; no browser JavaScript errors remained.
- **Remaining**: Replace the approved design's sample presentation values with complete API bindings in a separate frontend integration task.
- **Blockers**: None.
- **Next task**: Bind remaining approved-template sample fields to backend response data without changing the canonical designs.

### 2026-07-22 12:25 — Frontend UI Ownership Correction

- **Role**: Integration
- **Owner**: Codex
- **Task ID**: `INT-CLEANUP-01`
- **Status**: `done`
- **Correction**:
  - The six files previously classified as raw Stitch drafts are active frontend UI assets.
  - Restored all six files to `src/frontend/templates/` without content changes.
  - Removed the incorrect `stitch-export/raw/README.md` classification notice.
  - Data and environment canonicalization remains unchanged.
- **Validation commands**:
  - `.venv\\Scripts\\python.exe -m pytest -q`
  - frontend file location and hash verification
  - `git diff --check`
- **Blockers**: None

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

### 2026-07-22 11:23 — COMMON-RT-02 Automated Contract Remediation and Human Review Split

- **Role**: Integration / Team Lead
- **Owner**: Team Lead / Codex
- **Task ID**: `COMMON-RT-02`, `DATA-A-RT-01`, `DATA-A-RT-02`
- **Status**: `review`
- **Completed**:
  - 코스피·코스닥 단위를 `points`, 주식 가격 단위를 `KRW`로 분리했다.
  - 장중에만 10~30초 폴링하고 장 마감 시 자동 폴링을 중지하는 계약을 추가했다.
  - 수동 이슈 동기화에 600초 서버 쿨다운, `429`, `Retry-After`, 재시도 가능 시각 계약을 추가했다.
  - `success`, `partial_success`, `failed`와 실패 출처·실패 단계·재계산 실패의 모순 상태를 스키마로 차단했다.
  - 재계산 실패 시 이전 정상 결과를 `fallback`으로 유지하는 계약을 추가했다.
  - 3일·Jaccard 0.65 사건 중복 기준을 MVP 정책으로 확정했다.
  - `사망 없음` 등 명시적 부정 문구가 severity 5점을 만들지 않도록 규칙 버전 1.1.0과 테스트를 추가했다.
  - Data A 사람 검토 범위를 G01~G03 unavailable 18행과 비전공자용 사용자 문구로 한정한 체크리스트를 작성했다.
- **Created files**:
  - `schemas/api/sync-error-response.schema.json`
  - `schemas/api/examples/sync-error-response.example.json`
  - `data/docs/data_a_human_review_checklist.md`
- **Modified files**:
  - `schemas/api/README.md`
  - `schemas/api/market-quotes-response.schema.json`
  - `schemas/api/sync-status-response.schema.json`
  - `schemas/api/examples/market-quotes-response.example.json`
  - `schemas/api/examples/sync-status-response.example.json`
  - `schemas/data/issue-pipeline-rules.json`
  - `schemas/data/issue-pipeline-rules.schema.json`
  - `schemas/data/events.schema.json`
  - `src/backend/app/utils/issue_rules.py`
  - `src/backend/tests/test_realtime_api_contracts.py`
  - `src/backend/tests/test_issue_pipeline_contracts.py`
  - `data/processed/events.csv`
  - `data/sample/events.sample.csv`
  - `data/docs/issue_pipeline_contract.md`
  - `data/docs/data_quality_report.md`
  - `ROADMAP.md`, `PROGRESS.md`, `progress/INTEGRATION.md`
- **Validation commands**:
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_realtime_api_contracts.py src/backend/tests/test_issue_pipeline_contracts.py src/backend/tests/test_csv_validator.py`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q`
  - `git diff --check`
- **Validation results**:
  - 계약·Data A 집중 테스트 `40 passed`.
  - 전체 회귀 테스트 `92 passed, 1 warning` (387.23초).
  - whitespace 오류 없음. 기존 CRLF 변환 안내만 확인.
- **Remaining**:
  - Data A가 사람 검토 체크리스트를 완료하고 역할 로그에 승인 또는 수정 필요를 기록한다.
  - Data B·Backend·Frontend가 수정된 계약을 각 역할 로그에서 명시적으로 승인한다.
  - Backend가 공개 Realtime API와 실제 10분 쿨다운을 구현한다.
- **Blockers**: 역할별 승인과 Backend 공개 API 구현 대기.
- **Next task**: Data A 체크리스트 전달과 역할별 계약 승인 수집.
## 2026-07-25 — INT-MARKET-03 started

- **Role**: Integration
- **Task ID**: INT-MARKET-03
- **Status**: in_progress
- **Goal**: Implement the approved `GET /market/quotes` contract and replace fixed home-market values with API-driven loading, error, fallback, and market-hours polling states.
- **Assumptions**:
  - KIS is the live provider when credentials are configured.
  - KOSPI/KOSDAQ must return `503` when neither a provider quote nor a persisted last-known-good quote exists; the UI must not invent index values.
  - Polling is enabled only during Korean exchange weekday hours (09:00–15:30 Asia/Seoul); exchange holidays remain a documented MVP limitation.
- **Allowed files**:
  - `src/backend/app/core/`
  - `src/backend/app/routes/`
  - `src/backend/app/services/`
  - `src/backend/tests/`
  - `src/frontend/templates/home.html`
  - `.env.example`
  - `progress/INTEGRATION.md`

## 2026-07-25 — INT-MARKET-03 completed

- **Role**: Integration
- **Task ID**: INT-MARKET-03
- **Status**: done
- **Work completed**:
  - Added public `GET /market/quotes` with the approved four-instrument response contract.
  - Added KIS previous-close parsing and persisted previous-close/source metadata in last-known-good SQLite snapshots.
  - Added Korean market-hours polling control, explicit live/cached/fallback states, and 503 handling when index data is unavailable.
  - Replaced all fixed home-market and portfolio figures with API-driven loading, fallback, error, retry, and disclaimer states.
  - Verified the home at a 390px viewport with no horizontal overflow and no legacy fixed index value.
- **Created files**:
  - `src/backend/app/routes/market.py`
  - `src/backend/app/services/market_dashboard.py`
  - `src/backend/tests/test_market_dashboard.py`
- **Modified files**:
  - `.env.example`
  - `src/backend/app/core/config.py`
  - `src/backend/app/core/runtime.py`
  - `src/backend/app/core/schemas.py`
  - `src/backend/app/main.py`
  - `src/backend/app/repositories/runtime_state_repository.py`
  - `src/backend/app/services/kis_market_data.py`
  - `src/backend/app/services/market_quotes.py`
  - `src/backend/tests/test_kis_market_data.py`
  - `src/backend/tests/test_portfolio.py`
  - `src/frontend/templates/home.html`
  - `src/frontend/static/css/index.css`
- **Validation commands**:
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_portfolio.py::test_get_diagnosis_page src/backend/tests/test_market_dashboard.py`
  - `powershell -ExecutionPolicy Bypass -File scripts/build_frontend.ps1`
  - `git diff --check`
- **Validation results**:
  - Full suite reached `197 passed, 1 failed`; the only failure was an obsolete home-copy assertion removed by this task.
  - The corrected home assertion plus market endpoint/service tests passed: `7 passed, 1 warning`.
  - Earlier market, contract, runtime persistence, and UI focused run passed: `69 passed, 1 warning`.
  - Frontend production CSS build passed.
  - Browser verification passed at 390px; KIS-unconfigured mode returned the expected 503 and the UI displayed a data-unavailable state without invented values.
  - `git diff --check` reported no whitespace errors; only existing Windows line-ending notices.
- **Remaining issues**:
  - Exchange holidays are not yet represented; weekday 09:00–15:30 KST is the MVP market-hours rule.
  - Live production values require `KIS_APP_KEY` and `KIS_APP_SECRET`.
  - The next approved implementation step is the issue-analysis UI/API integration.
- **Blockers**: None for this task.
- **Next recommended task**: Implement the issue-analysis screen against the approved issues snapshot/status contracts.

## 2026-07-25 — INT-ISSUES-04 started

- **Role**: Integration
- **Task ID**: INT-ISSUES-04
- **Status**: in_progress
- **Goal**: Replace fixed issue-analysis content with the existing validated current-event and historical-reaction APIs.
- **Dependencies confirmed**:
  - `GET /issues/current` returns validated/sample/fallback event records with official source metadata.
  - `GET /issues/historical` applies the model-eligibility gate and returns deterministic 1/3/5-day reaction metrics and chart points.
- **Scope**:
  - API-driven company tabs, loading, error, empty, sample/fallback, source-link, and historical-analysis states.
  - No manual synchronization controls in this task; those remain in the next sync-status stage.

## 2026-07-25 — INT-ISSUES-04 completed

- **Role**: Integration
- **Task ID**: INT-ISSUES-04
- **Status**: done
- **Work completed**:
  - Connected the issue-analysis screen to `GET /issues/current` and `GET /issues/historical`.
  - Removed fixed event narratives, fixed stock prices, fixed return metrics, and placeholder SVG paths.
  - Added company filtering, verified source links, event status/severity text, deterministic 1/3/5-day reaction metrics, and data-driven SVG charts.
  - Added loading, API error/retry, empty, sample, fallback, warning, source-unavailable, and insufficient-chart-data states.
  - Escaped event text and restricted source links to HTTP(S).
- **Modified files**:
  - `src/frontend/templates/issue_analysis.html`
  - `src/frontend/static/css/index.css`
  - `src/backend/tests/test_portfolio.py`
  - `progress/INTEGRATION.md`
- **Validation commands**:
  - `powershell -ExecutionPolicy Bypass -File scripts/build_frontend.ps1`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_portfolio.py::test_issues_endpoints src/backend/tests/test_portfolio.py::test_issues_page_rendering src/backend/tests/test_ui_routes.py`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests/test_events.py src/backend/tests/test_issue_pipeline_contracts.py`
  - `git diff --check`
- **Validation results**:
  - Frontend production CSS build passed.
  - Issue endpoint and UI route tests passed: `25 passed, 1 warning`.
  - Event modeling and issue-pipeline contract tests passed: `21 passed`.
  - Browser verification loaded three current and three historical records for each company, displayed official source links, switched tabs correctly, removed the old fixed price, and showed no horizontal overflow at the mobile viewport.
  - `git diff --check` reported no whitespace errors; only existing Windows line-ending notices.
- **Remaining issues**:
  - Manual issue refresh and sync-status feedback are intentionally deferred to the next stage.
  - Event category and enforcement values currently display contract enum values; localized labels are a polish task.
- **Blockers**: None for this task.
- **Next recommended task**: Implement `POST /sync/issues` and `GET /sync/status` UI integration with active-run reuse, cooldown, progress, and last-known-good states.

## 2026-07-25 — INT-SYNC-05 started

- **Role**: Integration
- **Task ID**: INT-SYNC-05
- **Status**: in_progress
- **Goal**: Implement the approved manual issue-sync and status contracts with durable state, active-run reuse, idempotency, cooldown, polling, and fallback UI.
- **Assumptions**:
  - The endpoint must not report a successful refresh while the external collector/normalizer is unconfigured.
  - A failed refresh keeps the last validated issue snapshot visible and reports the failure explicitly.
  - Scheduler and manual refresh continue to share the same SQLite lock and coordinator.

## 2026-07-25 — INT-SYNC-05 completed

- **Role**: Integration
- **Task ID**: INT-SYNC-05
- **Status**: done
- **Work completed**:
  - Added `POST /sync/issues` and `GET /sync/status` using the approved request, status, and cooldown contracts.
  - Split durable queue creation from background execution so a new manual request returns `202` immediately.
  - Added contract-format sync IDs, active-run reuse, `client_request_id` idempotency, persisted workflow metadata, latest/specific status lookup, and restart-safe terminal state.
  - Added a server-enforced 600-second manual cooldown with `Retry-After` and the approved 429 response.
  - Added issue-screen refresh, stage polling, terminal counts, last-run time, failure/fallback messaging, and a live cooldown countdown.
  - Kept scheduler and manual execution behind the same durable SQLite lock.
- **Created files**:
  - `src/backend/app/routes/sync.py`
  - `src/backend/app/services/sync_status.py`
  - `src/backend/tests/test_sync_api.py`
- **Modified files**:
  - `src/backend/app/core/runtime.py`
  - `src/backend/app/core/schemas.py`
  - `src/backend/app/main.py`
  - `src/backend/app/repositories/runtime_state_repository.py`
  - `src/backend/app/services/sync_coordinator.py`
  - `src/backend/tests/test_portfolio.py`
  - `src/frontend/templates/issue_analysis.html`
  - `src/frontend/static/css/index.css`
  - `progress/INTEGRATION.md`
- **Validation commands**:
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_sync_api.py src/backend/tests/test_runtime_state_repository.py src/backend/tests/test_issue_scheduler.py src/backend/tests/test_realtime_api_contracts.py src/backend/tests/test_portfolio.py::test_issues_page_rendering src/backend/tests/test_ui_routes.py`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_sync_coordinator.py src/backend/tests/test_issue_sync_workflow.py`
  - `powershell -ExecutionPolicy Bypass -File scripts/build_frontend.ps1`
  - `git diff --check`
- **Validation results**:
  - Sync API, persistence, scheduler, contract, and UI tests passed: `58 passed, 1 warning`.
  - Coordinator and complete workflow regression tests passed: `18 passed`.
  - Frontend production CSS build passed.
  - Browser verification passed through first-run state, manual request, explicit unconfigured-collector failure, retained validated issue cards, and live cooldown countdown without mobile horizontal overflow.
  - `git diff --check` reported no whitespace errors; only existing Windows line-ending notices.
- **Remaining issues**:
  - A successful production refresh still requires an approved collector and complete-bundle normalizer to replace `UnavailableIssueSyncWorkflow`.
  - Live market success paths still require KIS credentials.
- **Blockers**:
  - Production sync success is blocked by missing external issue collector/normalizer configuration; failure and last-known-good behavior are complete and verified.
- **Next recommended task**: Run consolidated E2E/accessibility/deployment validation, using stubs for success paths and documenting the two production credential/provider dependencies.

## 2026-07-25 — INT-E2E-06 started

- **Role**: Integration
- **Task ID**: INT-E2E-06
- **Status**: in_progress
- **Goal**: Consolidate realtime market, portfolio valuation, issue analysis, and manual sync into one success-path E2E test, then verify default fallback behavior, mobile accessibility, frontend build, and deployability.
- **Known production dependencies**:
  - KIS credentials for live market success.
  - Approved issue collector and normalizer for live sync success.

## 2026-07-25 — INT-E2E-06 review

- **Role**: Integration
- **Task ID**: INT-E2E-06
- **Status**: review
- **Work completed**:
  - Added a consolidated success-path E2E test covering the home market API, portfolio valuation, issue/current history APIs, and manual sync queued-to-success transition.
  - Verified default no-provider behavior, empty portfolio summary, and empty diagnosis state without fixed demo values.
  - Audited six primary screens at the mobile viewport for horizontal overflow, Korean document language, one H1, duplicate IDs, image alternatives, and accessible interactive names.
  - Rebuilt production CSS, checked Node/npm runtime versions, verified `/health`, deployment files, and the complete test suite.
  - Updated README public API, sync behavior, and final validation commands.
- **Created files**:
  - `src/backend/tests/test_realtime_e2e.py`
- **Modified files**:
  - `README.md`
  - `progress/INTEGRATION.md`
- **Validation commands**:
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_realtime_e2e.py`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_deployment_config.py src/backend/tests/test_realtime_e2e.py src/backend/tests/test_ui_routes.py`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q`
  - `powershell -ExecutionPolicy Bypass -File scripts/build_frontend.ps1`
  - `Invoke-WebRequest http://127.0.0.1:8010/health`
  - `git diff --check`
- **Validation results**:
  - Consolidated realtime success E2E passed: `1 passed`.
  - Deployment, E2E, and UI route bundle passed: `28 passed, 1 warning`.
  - Full repository suite passed: `204 passed, 1 warning` in 286.27 seconds.
  - Node `v24.18.0`, npm `11.16.0`, frontend build, and health endpoint passed.
  - Six-screen accessibility/mobile audit found no horizontal overflow, missing accessible names, missing image alternatives, or duplicate IDs.
  - `git diff --check` found no whitespace errors; existing Windows line-ending notices only.
- **Remaining issues**:
  - Docker CLI is not installed in the current environment, so the image could not be built locally.
  - Live KIS verification requires deployment credentials.
  - Live successful issue refresh requires an approved collector/normalizer.
  - Root roadmap/progress tasks remain unchanged because production-provider verification and cross-role contract approval are still outstanding.
- **Blockers**:
  - Docker image execution and live-provider success paths require external environment setup.
- **Next recommended task**:
  - Configure KIS and the issue collection workflow in a deployment environment, build the Docker image, run the final live smoke test, and then let the team lead mark `INT-01`/`INT-RT-01` complete.

## 2026-07-25 — INT-KIS-07 review

- **Role**: Integration
- **Task ID**: INT-KIS-07
- **Status**: review
- **Work completed**:
  - Confirmed the project loads the KIS virtual-trading base URL from `.env` without exposing credentials.
  - Started a fresh backend instance on port 8020 after ports 8000 and 8010 were found to be owned by earlier task sessions.
  - Verified live KIS responses for KOSPI, KOSDAQ, Samsung Electronics, and SK hynix through `GET /market/quotes`.
  - Confirmed the service safely uses last-known-good values while KIS rejects rapid OAuth token reissuance, then returns to validated KIS data after the cooldown.
- **Modified files**:
  - `progress/INTEGRATION.md`
- **Validation commands**:
  - `.venv\Scripts\python.exe -c "<load runtime configuration and provider>"`
  - `.venv\Scripts\python.exe -c "<fetch all four KIS instruments>"`
  - `curl.exe http://127.0.0.1:8020/health`
  - `curl.exe http://127.0.0.1:8020/market/quotes`
  - Browser smoke test: `http://127.0.0.1:8020/home`
- **Validation results**:
  - `/health` returned HTTP 200.
  - All four instruments returned `source=kis`, `is_stale=false`, and the response returned `data_status=validated` with no warnings.
  - Because validation ran on Saturday after market hours, the API correctly returned `market_status=closed`, `price_status=cached`, and disabled polling.
  - The home UI rendered all four KIS market cards, the closed-market label, the quote timestamp, and the investment disclaimer with no browser console errors.
- **Remaining issues**:
  - Earlier task sessions still own ports 8000 and 8010 and cannot be terminated from the current execution session.
  - The frontend should target port 8020 for this validation instance, or the externally managed port-8000 backend must be restarted by its owning terminal.
- **Blockers**:
  - None for KIS virtual-trading connectivity.
- **Next recommended task**:
  - Point the frontend API base URL at the validated backend instance, run one browser smoke test, and then complete deployment-provider review.

## 2026-07-25 — INT-DEPLOY-08 review

- **Role**: Integration
- **Task ID**: INT-DEPLOY-08
- **Status**: review
- **Work completed**:
  - Reviewed the cumulative realtime market, portfolio valuation, issue sync, frontend, and deployment changes as one release candidate.
  - Confirmed `.env`, runtime databases, backend logs, virtual environments, portable tools, and `node_modules` are excluded from Git and the Docker build context.
  - Rebuilt the production Tailwind CSS asset.
  - Updated the Docker health check to follow the deployment platform's `PORT` environment variable.
  - Re-ran the complete repository regression suite before commit preparation.
- **Modified files**:
  - `Dockerfile`
  - `src/backend/tests/test_deployment_config.py`
  - `src/frontend/static/css/index.css`
  - `progress/INTEGRATION.md`
- **Validation commands**:
  - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build_frontend.ps1`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q`
  - `git diff --check`
  - `docker --version`
- **Validation results**:
  - Frontend production CSS build passed.
  - Full repository suite passed: `206 passed, 1 warning` in 217.93 seconds.
  - `git diff --check` reported no whitespace errors; existing Windows line-ending notices only.
  - Secret and runtime artifacts are ignored and are not part of the commit candidate.
- **Remaining issues**:
  - Docker CLI is not installed in the current environment, so the image itself could not be built or run locally.
  - A live successful issue refresh still requires an approved collector and normalizer.
  - Cross-role contract approval and final roadmap completion remain team-lead actions.
- **Blockers**:
  - No blocker for creating the release-candidate commit.
  - Container runtime smoke testing remains blocked until Docker is available.
- **Next recommended task**:
  - Push the commit to the remote, build the container in CI or a Docker-enabled environment, configure deployment secrets and persistent runtime storage, then run `/health` and `/market/quotes` production smoke tests.

## 2026-07-25 — INT-DEPLOY-HOTFIX-09 started

- **Role**: Integration
- **Task ID**: INT-DEPLOY-HOTFIX-09
- **Status**: in_progress
- **Goal**: Restore production styling by preventing Railway's HTTPS pages from rendering the local Tailwind asset with an insecure HTTP URL.
- **Observed production failure**:
  - `GET /home` rendered the stylesheet as `http://sesac-mini-project2-production.up.railway.app/static/css/index.css`.
  - Browsers block that URL as mixed content because the page itself is HTTPS.
- **Allowed files**:
  - `src/frontend/templates/`
  - `src/backend/tests/test_ui_routes.py`
  - `Dockerfile`
  - `Procfile`
  - `src/backend/tests/test_deployment_config.py`
  - `progress/INTEGRATION.md`
- **Validation plan**:
  - UI route and deployment configuration tests.
  - Full repository regression suite.
  - Production CSS build.
  - Browser smoke test using forwarded HTTPS headers locally, followed by a production smoke test after redeployment.

## 2026-07-25 — INT-DEPLOY-HOTFIX-09 review

- **Role**: Integration
- **Task ID**: INT-DEPLOY-HOTFIX-09
- **Status**: review
- **Work completed**:
  - Replaced generated absolute Tailwind stylesheet URLs with same-origin `/static/css/index.css` URLs on every production UI template.
  - Configured Docker and Procfile Uvicorn commands to trust Railway's forwarded scheme headers.
  - Added deployment configuration and UI-route regression checks, including the production home screen.
- **Modified files**:
  - `Dockerfile`
  - `Procfile`
  - `src/frontend/templates/diagnosis_result.html`
  - `src/frontend/templates/home.html`
  - `src/frontend/templates/issue_analysis.html`
  - `src/frontend/templates/login.html`
  - `src/frontend/templates/portfolio_edit.html`
  - `src/frontend/templates/portfolio_input.html`
  - `src/frontend/templates/portfolio_summary.html`
  - `src/frontend/templates/setting.html`
  - `src/frontend/static/css/index.css`
  - `src/backend/tests/test_deployment_config.py`
  - `src/backend/tests/test_ui_routes.py`
  - `progress/INTEGRATION.md`
- **Validation commands**:
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_deployment_config.py src/backend/tests/test_ui_routes.py`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q`
  - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build_frontend.ps1`
  - `git diff --check`
  - Browser smoke test: `http://127.0.0.1:8030/home`
- **Validation results**:
  - Deployment and UI regression bundle passed: `30 passed, 1 warning`.
  - Full repository suite passed: `207 passed, 1 warning` in 619.66 seconds.
  - Production Tailwind build passed.
  - Local browser loaded `/static/css/index.css`, applied the expected body styles, and reported no console errors.
  - `git diff --check` reported no whitespace errors; existing Windows line-ending notices only.
- **Remaining**:
  - Push the hotfix to `main`, wait for Railway redeployment, and confirm the production stylesheet resolves over HTTPS.
- **Blockers**: None.
- **Next recommended task**: Run the live `/home`, `/health`, and static asset smoke test after Railway finishes deploying the hotfix.

## 2026-07-25 — INT-DEPLOY-HOTFIX-09 blocked

- **Role**: Integration
- **Task ID**: INT-DEPLOY-HOTFIX-09
- **Status**: blocked
- **Reason**: Repository rules require a pull request for `main`, and GitHub web access is unavailable from the current execution environment.
- **Required action**: Open and merge the `feature/railway-https-styles` pull request into `main`, then allow Railway to redeploy.
- **Owner**: Team lead or repository maintainer.
- **Prepared commit**: `1c35244 fix(deploy): serve styles over HTTPS behind Railway`
- **Remote branch**: `origin/feature/railway-https-styles`
- **Post-merge validation**:
  - Confirm `/home` references `https://sesac-mini-project2-production.up.railway.app/static/css/index.css`.
  - Confirm the stylesheet loads and the mobile dashboard layout is restored.

## 2026-07-25 — INT-DEPLOY-RAILPACK-10 started

- **Role**: Integration
- **Task ID**: INT-DEPLOY-RAILPACK-10
- **Status**: in_progress
- **Goal**: Make new Railway services build the repository's verified multi-stage Dockerfile instead of failing during Railpack auto-detection.
- **Observed failure**:
  - A newly created Railway service reports `railpack process exited with an error`.
  - The repository already has a root `Dockerfile`, but no config-as-code file explicitly selects the Dockerfile builder.
- **Assumption**:
  - The service is connected to the repository root and the failure summary accurately identifies Railpack as the selected builder.
- **Allowed files**:
  - `railway.json`
  - `src/backend/tests/test_deployment_config.py`
  - `progress/INTEGRATION.md`
- **Validation plan**:
  - Parse and assert the Railway config contract.
  - Run deployment configuration and UI route tests.
  - Run the full repository regression suite if focused validation passes.

## 2026-07-25 — INT-DEPLOY-RAILPACK-10 review

- **Role**: Integration
- **Task ID**: INT-DEPLOY-RAILPACK-10
- **Status**: review
- **Work completed**:
  - Added Railway config-as-code that explicitly selects the repository `Dockerfile` builder.
  - Added `/health` deployment healthcheck, a 300-second startup timeout, and bounded restart settings.
  - Added a regression test for the Railway build and healthcheck contract.
- **Created files**:
  - `railway.json`
- **Modified files**:
  - `src/backend/tests/test_deployment_config.py`
  - `progress/INTEGRATION.md`
- **Validation commands**:
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_deployment_config.py src/backend/tests/test_ui_routes.py`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q`
  - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build_frontend.ps1`
  - `git diff --check`
- **Validation results**:
  - Deployment and UI route bundle passed: `31 passed, 1 warning`.
  - Full repository suite passed: `209 passed, 1 warning` in 797.93 seconds.
  - Production Tailwind build passed.
  - `git diff --check` reported no whitespace errors; existing Windows line-ending notices only.
- **Remaining**:
  - Merge this deployment configuration into `main`.
  - In Railway, leave Root Directory empty, remove Build/Start command overrides, and redeploy the latest `main`.
  - Confirm the build log uses the Dockerfile instead of Railpack.
- **Blockers**:
  - Docker CLI is not installed locally, so the container image cannot be built in this environment.
  - If Dockerfile mode still fails, the full build log above the final Railpack summary is required to identify the next cause.
- **Next recommended task**: Deploy the merged config in the user's Railway project and verify `/health`, `/login`, and `/static/css/index.css`.

## 2026-07-26 — INT-FE-API-11 started

- **Role**: Integration
- **Task ID**: INT-FE-API-11
- **Status**: in_progress
- **Goal**: Restore the missing API-driven home, portfolio, diagnosis, issue-analysis, and sync UI behavior, then remove the production market quote timeout.
- **Production evidence**:
  - `GET /health` returns `200`.
  - `GET /issues/current` returns `200` with event data.
  - `GET /market/quotes` exceeds a 20-second client timeout.
  - The deployed home template contains fixed market and portfolio values and no API request.
- **Recovery source**:
  - Unreachable Git commit `1b1b1b4b462789011b2f962a702f7c54ecc8a17c` contains the previously validated API-integrated templates and tests.
- **Allowed files**:
  - `src/frontend/templates/`
  - `src/frontend/static/css/index.css`
  - `src/backend/app/services/`
  - `src/backend/tests/`
  - `progress/INTEGRATION.md`
- **Validation plan**:
  - Restore only the relevant Git-recoverable templates, preserving later HTTPS and deployment fixes.
  - Add focused UI/API and timeout regression tests.
  - Rebuild Tailwind CSS and run browser checks at the mobile viewport.
  - Run the full repository test suite before commit preparation.

## 2026-07-26 — INT-FE-API-11 review

- **Role**: Integration
- **Task ID**: INT-FE-API-11
- **Status**: review
- **Work completed**:
  - Restored API-driven home, portfolio input/result, diagnosis, and issue-analysis templates while preserving same-origin HTTPS static asset paths.
  - Replaced production hard-coded dashboard values with `/market/quotes`, `/portfolio/*`, and `/issues/*` API consumers and explicit loading, error, empty, sample, fallback, and source states.
  - Added a 15-second browser timeout and user-facing fallback message for market quotes.
  - Made the four independent market quote requests concurrent and added a short KIS token-failure cooldown so one upstream failure does not repeatedly consume the full timeout.
  - Rebuilt the production Tailwind stylesheet.
- **Modified files**:
  - `src/frontend/templates/home.html`
  - `src/frontend/templates/issue_analysis.html`
  - `src/frontend/templates/portfolio_input.html`
  - `src/frontend/templates/portfolio_summary.html`
  - `src/frontend/templates/diagnosis_result.html`
  - `src/frontend/static/css/index.css`
  - `src/backend/app/services/market_dashboard.py`
  - `src/backend/app/services/kis_market_data.py`
  - `src/backend/tests/test_market_dashboard.py`
  - `src/backend/tests/test_kis_market_data.py`
  - `src/backend/tests/test_portfolio.py`
  - `src/backend/tests/test_realtime_e2e.py`
  - `src/backend/tests/test_ui_routes.py`
  - `progress/INTEGRATION.md`
- **Validation commands**:
  - `.venv\Scripts\python.exe -m pytest src/backend/tests/test_market_dashboard.py src/backend/tests/test_kis_market_data.py src/backend/tests/test_portfolio.py src/backend/tests/test_ui_routes.py src/backend/tests/test_realtime_e2e.py`
  - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build_frontend.ps1`
  - `.venv\Scripts\python.exe -m pytest`
  - Local Uvicorn request to `GET /market/quotes`
  - `git diff --check`
- **Validation results**:
  - Focused integration bundle passed: `63 passed, 1 warning`.
  - Full repository suite passed: `215 passed, 1 warning` in 463.98 seconds.
  - Production Tailwind build passed.
  - Local `/market/quotes` returned `200` with four ordered fallback quotes in 12.67 seconds.
  - `git diff --check` reported no whitespace errors; existing Windows line-ending notices only.
- **Remaining**:
  - Merge the feature branch into `main` so Railway can auto-deploy it.
  - Verify `/home`, `/market/quotes`, `/issues`, and the portfolio calculation flow on the new Railway deployment.
- **Blockers**:
  - Automated in-app browser inspection was interrupted by a browser runtime crash; route rendering, API contracts, loading/error states, and mobile CSS are covered by the passing test/build bundle, but the final deployed visual check remains.
- **Next recommended task**: Merge and monitor the Railway deployment, then perform a mobile visual smoke test against `https://chip-buddy.up.railway.app/`.

## 2026-07-26 — INT-BE-AUDIT-12 review

- **Role**: Integration
- **Task ID**: INT-BE-AUDIT-12
- **Status**: review
- **Goal**: Reassess backend completion before expanding frontend debugging.
- **Evidence reviewed**:
  - `ROADMAP.md`, root `PROGRESS.md`, and Backend/Integration role logs.
  - FastAPI runtime wiring, public routes, market/portfolio services, issue workflow, scheduler, and backend tests.
- **Findings**:
  - Initial backend tasks `BE-01` through `BE-06` are implemented, but realtime tasks `BE-RT-01` through `BE-RT-04` remain `review` or `in_progress`.
  - Production runtime wires `/sync/issues` and the daily scheduler to `UnavailableIssueSyncWorkflow`; a manual or scheduled sync therefore cannot collect and publish real issues.
  - `/data/refresh` intentionally returns `501 ISSUE_SYNC_NOT_IMPLEMENTED`.
  - The scheduler is disabled unless `ENABLE_ISSUE_SCHEDULER=true`.
  - Realtime E2E tests inject successful fake quote and sync services, so they verify API contracts but do not verify production runtime wiring.
  - The session signing secret is hard-coded and CORS is configured as wildcard plus credentials.
  - The deployed market endpoint still reflects the old sequential implementation and took 23.85 seconds; deployment of commit `376fec8` remains unverified.
- **Validated backend capabilities**:
  - Health, validated/sample repositories, CVaR/optimization, issue query/analysis, market quote contracts, portfolio summary, SQLite locks/LKG storage, and atomic snapshot components have automated coverage.
  - Full repository regression suite passed before this audit: `215 passed, 1 warning`.
- **Blocking dependency**:
  - A production issue workflow requires a complete-bundle normalizer/classifier owned by Data A. The repository currently contains DART raw/candidate collection, but no production normalizer that turns candidates into an automatically verified complete Data A bundle.
- **Required action**:
  - Team lead must confirm whether backend completion means DART-only candidate collection with warnings, or the full DART+news automated classification and publication flow defined by the roadmap.
- **Next recommended task**: Implement production runtime wiring and runtime-level E2E tests after the issue collection scope is confirmed; independently harden session/CORS configuration and deployment readiness.

## 2026-07-26 — INT-KIS-STABILITY-13 started

- **Role**: Integration
- **Task ID**: INT-KIS-STABILITY-13
- **Status**: in_progress
- **Goal**: Diagnose production KIS quote instability without exposing credentials or changing shared API contracts.
- **Observed evidence**:
  - Production `GET /market/quotes` returned `200` but took 23.85 seconds.
  - The deployed `/home` still served the previous frontend/runtime version when measured.
- **Validation plan**:
  - Inspect token caching, retry, rate limiting, timeout, quote concurrency, and last-known-good behavior.
  - Compare direct provider timing with local service and production endpoint timing using bounded requests.
  - Separate upstream KIS failures from stale deployment and application orchestration problems.

## 2026-07-26 — INT-KIS-STABILITY-13 in progress

- **Role**: Integration
- **Task ID**: INT-KIS-STABILITY-13
- **Status**: in_progress
- **Findings**:
  - A clean local cold request using the configured KIS credentials returned `200` in 24.13 seconds.
  - An immediately following request still did not complete within 10 seconds.
  - Production returned `200` in 23.85 seconds, so the latency is reproducible outside the browser.
  - The configured values are a 5-second per-operation timeout, 15-second quote cache, 15-second UI refresh, and a one-second KIS request interval.
  - The `httpx` timeout is applied to individual network phases/operations rather than enforcing a strict end-to-end dashboard deadline.
  - Access tokens are cached only in process memory; Railway restart/redeploy causes token reissuance, while KIS documents token reuse and a one-minute reissuance limit.
  - Concurrent dashboard requests previously created duplicate per-instrument provider work; a single-flight guard now coalesces identical in-process lookups.
  - A synchronous request path still waits for KIS before returning, so single-flight prevents amplification but does not solve cold-start latency.
- **Modified files**:
  - `src/backend/app/services/market_quotes.py`
  - `src/backend/tests/test_market_quotes.py`
  - `progress/INTEGRATION.md`
- **Validation commands**:
  - `.venv\Scripts\python.exe -m pytest -q src/backend/tests/test_market_quotes.py src/backend/tests/test_market_dashboard.py src/backend/tests/test_kis_market_data.py`
  - Local Uvicorn cold/warm `GET /market/quotes` probes with bounded curl timeouts.
- **Validation results**:
  - Focused KIS/market regression bundle passed: `26 passed, 1 warning`.
  - Eight concurrent identical lookups are covered and produce one provider request.
  - Cold/warm timing remains outside the UI latency budget.
- **Required architecture change**:
  - Move KIS refresh off the public request path.
  - Return a cached or SQLite last-known-good four-instrument snapshot immediately.
  - Refresh the snapshot in one background worker with single-flight, a strict refresh deadline, backoff, and observable sanitized failure codes.
  - Persist runtime state on a Railway volume so last-known-good data survives deployment replacement.
- **Remaining**:
  - Implement and test the background market snapshot refresher.
  - Add readiness/degraded-state visibility without exposing credentials.
  - Verify latency under cold start, overlapping requests, provider timeout, and Railway restart.
- **Blockers**:
  - A Railway persistent volume must be mounted for durable last-known-good state; code alone cannot make an ephemeral filesystem survive redeployment.
- **Next recommended task**: Implement stale-while-revalidate market snapshots before further frontend polling work.

## 2026-07-26 — INT-KIS-STABILITY-13 review

- **Role**: Integration
- **Task ID**: INT-KIS-STABILITY-13
- **Status**: review
- **Work completed**:
  - Removed synchronous KIS network waits from public `/market/quotes` and `/portfolio/summary` requests.
  - Added immediate in-memory/SQLite last-known-good snapshot reads with explicit stale/fallback sources.
  - Added a single background market refresh worker with per-instrument single-flight, success interval, failure retry backoff, and sanitized failure logging.
  - Added Railway startup refresh while keeping local/test startup free from automatic external calls.
  - Deferred expensive historical-price validation unless a snapshot lacks a trustworthy previous close.
  - Removed historical-price loading from realtime portfolio valuation because quote provenance already determines validated/fallback state.
  - Documented the required Railway volume mount and runtime database path.
  - Fixed a fast-future callback lock re-entry deadlock found during live runtime validation.
- **Modified files**:
  - `.env.example`
  - `README.md`
  - `src/backend/app/core/config.py`
  - `src/backend/app/main.py`
  - `src/backend/app/routes/market.py`
  - `src/backend/app/routes/portfolio.py`
  - `src/backend/app/services/market_dashboard.py`
  - `src/backend/app/services/market_quotes.py`
  - `src/backend/app/services/portfolio_summary.py`
  - `src/backend/tests/test_market_dashboard.py`
  - `src/backend/tests/test_market_quotes.py`
  - `progress/INTEGRATION.md`
- **Validation commands**:
  - Focused KIS, market, portfolio, API contract, deployment, and realtime E2E pytest bundles.
  - Local Uvicorn cold snapshot, portfolio summary, and overlapping request probes.
  - `.venv\Scripts\python.exe -m pytest -q`
  - `git diff --check`
- **Validation results**:
  - Focused market/integration bundle passed: `55 passed, 1 warning`.
  - Final full repository suite passed: `222 passed, 1 warning` in 342.90 seconds.
  - Before the redesign, a clean KIS-backed cold request took 24.13 seconds and a following request exceeded 10 seconds.
  - After the redesign, `/market/quotes` returned the LKG snapshot in 0.691 seconds and repeated calls completed in 0.027, 0.008, and 0.007 seconds while refresh ran in the background.
  - `/portfolio/summary` returned in 0.016 seconds from the same snapshot.
  - `git diff --check` reported no whitespace errors; Windows line-ending notices only.
- **Remaining**:
  - Mount a Railway Volume at `/app/data/runtime`.
  - Set `RUNTIME_STATE_DB_PATH=/app/data/runtime/state.db`.
  - Set `RAILWAY_RUN_UID=0` because Railway mounts Volumes as root while the Docker image declares a non-root runtime user.
  - Deploy and verify cold start, background promotion from `fallback` to current KIS data, and snapshot survival after redeployment.
- **Blockers**:
  - Durable restart behavior cannot be verified until the Railway volume is mounted.
- **Next recommended task**: Deploy this branch, configure the Railway volume, and run production latency/state-transition smoke tests.
