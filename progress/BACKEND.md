# Backend Progress Log

## Task Status

| Task ID | Task | Status | Output | Blocker |
|---|---|---|---|---|
| BE-01 | FastAPI Skeleton | `done` | `src/backend/app/main.py` 등 | COMMON-01 완료 |
| BE-02 | Data Loader and Validation | `done` | `src/backend/app/utils/csv_validator.py` | COMMON-02, COMMON-03 승인 |
| BE-03 | Mock API | `done` | `src/backend/app/routes/` 내 Mocking | BE-01, BE-02 완료 |
| BE-04 | Real Data Integration | `done` | `data/reviewed/` 디렉토리 연동 완료 | DATA-A-05, BE-02 완료 |
| BE-05 | Model Integration | `done` | `src/backend/app/routes/` 내 실제 계산 모듈 연동 | DATA-B-05, BE-03 완료 |
| BE-06 | Fallback and Contract Tests | `done` | `test_portfolio.py` 수정 및 예외 폴백 로직 검증 | BE-04, BE-05 완료 |

## Active Blockers

| Blocker ID | Related Task | Description | Owner | Required Action | Status |
|---|---|---|---|---|---|
| - | - | 현재 없음 | - | - | - |

## Work Log

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



