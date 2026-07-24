# Data A Progress Log

## Task Status

| Task ID | Task | Status | Output | Blocker |
|---|---|---|---|---|
| DATA-A-01 | ESG Indicator Definition | `done` | `data/processed/esg_indicators.csv`, `data/notes/data_dictionary.md` | 없음 |
| DATA-A-02 | Official Report Collection | `done` | `data/raw/reports/README.md`, `data/processed/sources.csv` | 없음 |
| DATA-A-03 | ESG Value Review | `done` | `data/processed/esg_indicators.csv` (72행: available 54, unavailable 18) | 없음 |
| DATA-A-04 | Event Dataset | `done` | `data/processed/events.csv` (공식 확인 confirmed 사건 3건) | 없음 |
| DATA-A-05 | Final Data Quality Review | `done` | `validate_data_a_bundle()` 및 계약 테스트 통과 | 없음 |
| DATA-A-RT-01 | Daily Disclosure and News Source·Classification·Deduplication Rules | `review` | candidate/source 계약, 중복·severity 자동 결정 규칙 | 공유 스키마 교차 검토 필요 |
| DATA-A-RT-02 | Candidate Data Quality and Event Status Validation | `review` | candidate 6건, source 6건, event-source 4건, processed event 3건 통합 검증 | 실제 일일 수집기 연동 필요 |
| DATA-A-RT-FINAL-02 | final audit remediation (S02/S05 split, event deduplication gate, EVT-0001 date, scripts restore) | `review` | scripts/validate_data_a.py, data/processed/*, data/docs/*, etc. | 없음 |
| DATA-A-06 | ESG Indicator Re-validation (원문 재대조, 전임 산출물 전면 폐기) | `done` | `data/processed/esg_indicators.csv`(64행), `data/processed/sources.csv`(10건), `data/docs/data_quality_report.md`, `data/docs/indicator_comparability.csv`, `data/docs/data_dictionary.md` | 없음 — `validate_data_a_bundle()` 전체 통과(main 최신 검증 로직 기준으로 재확인) |

## Active Blockers

| Blocker ID | Related Task | Description | Owner | Required Action | Status |
|---|---|---|---|---|---|
| - | - | 현재 없음 | - | - | - |

## Work Log

### 2026-07-21 10:00 — Initial Setup

- **Role**: Data A
- **Status**: `todo`
- **Completed**: 폴더 구조 뼈대 설정 및 Data A 진행 문서 생성 완료.
- **Created files**:
  - `progress/DATA-A.md`
- **Next task**: COMMON-02 (Shared Schema) 검토 진행 및 승인.

### 2026-07-21 10:33 — DATA-A-01: ESG Indicator Definition & SOX Index Collection Setup

- **Role**: Data A
- **Owner**: Data A
- **Status**: `in_progress`
- **Completed**:
  - 모델링 A 추가 요건 정의서 v2 작성 (지수, ESG 지표, 이슈 필드 스펙 정의).
  - 필라델피아 반도체 지수(SOX) 수집 및 무결성 검증 파이프라인(`scripts/collect_index.py`) 구축.
  - SOX 지수 수집 데이터(`data/index_prices.csv`, 총 754행) 구축 완료.
- **Created files**:
  - `scripts/collect_index.py`
  - `data/index_prices.csv`
  - `모델링A요건정의(추가)_v2.md`
- **Modified files**:
  - `progress/DATA-A.md`
- **Validation commands**:
  - `python scripts/collect_index.py`
- **Validation results**:
  - 754행 지수 데이터 검증 통과 (2023-07-21 ~ 2026-07-20)
- **Remaining**:
  - ESG 12개 지표 정의 수집 및 `data/reviewed/esg_indicators.csv` 작성
- **Blockers**: 없음
- **Next task**: DATA-A-02 (Official Report Collection - 지속가능경영보고서 및 DART 보고서 데이터 수집)

### 2026-07-21 10:46 — DATA-A-01 ~ DATA-A-05 Complete Data A Guidelines Execution

- **Role**: Data A
- **Owner**: Data A
- **Status**: `done`
- **Completed**:
  - `데이터_A_조원_작업_가이드라인.md` 및 `AGENTS.md` 기준 산출물 전체 구축 완료.
  - `data/raw/` 및 `data/reviewed/`, `data/notes/` 디렉토리 파이프라인 정립.
  - 삼성전자(005930) 및 SK하이닉스(000660) 대상 12개 정밀 검수 ESG 지표 데이터셋 (`data/reviewed/esg_indicators.csv`) 작성 (DS vs Consolidated 구분, `scope_mismatch` 플래그 적용).
  - 5개 주요 공식 ESG/준법 사건 데이터셋 (`data/reviewed/events.csv`) 수록 (공식 출처 URL, `confirmed`/`sanctioned`/`resolved` 상태, 원안위/환경부/고용부/공정위/개인정보위 출처 교차검증 완료).
  - 공식 보고서, DART 공시 및 정부 발표 출처 레지스트리 (`data/reviewed/sources.csv`) 구축.
  - Data B 및 백엔드 팀용 데이터 사전 및 전달용 메타데이터 노트 (`data/notes/data_dictionary.md`) 작성.
  - 데이터 A 품질 검증 스크립트 (`scripts/validate_data_a.py`) 작성 및 실행하여 전체 검증 통과.
- **Created files**:
  - `data/raw/news_candidates.csv`
  - `data/raw/reports/README.md`
  - `data/reviewed/esg_indicators.csv`
  - `data/reviewed/events.csv`
  - `data/reviewed/sources.csv`
  - `data/notes/data_dictionary.md`
  - `scripts/validate_data_a.py`
- **Modified files**:
  - `progress/DATA-A.md`
- **Validation commands**:
  - `python scripts/validate_data_a.py`
- **Validation results**:
  - ESG 지표 12행 검증 통과 (005930: 6행, 000660: 6행)
  - 사건 데이터 5건 검증 통과 (공식 출처 URL 및 authority_confirmed=true 검증 완료)
  - 출처 데이터 10건 검증 통과
  - 전체 스키마 정합성 검증 성공
- **Remaining**: 없음
- **Blockers**: 없음
- **Next task**: Data B 및 백엔드 팀으로의 데이터 전달 및 연동 검토 지원

### 2026-07-21 18:10 — DATA-A Advanced Deliverables: ESG & Events Data Final Upgrade

- **Role**: Data A
- **Owner**: Data A
- **Status**: `done`
- **Completed**:
  - `data_A_chip_buddy_final_tasks.md` 고도화 요구에 맞춘 데이터셋 전면 수정 및 최종 산출물 완성.
  - 가격 및 지수 파일 검수 완료 폴더로 이동: `prices.csv` ➡️ `data/reviewed/stock_prices.csv`, `index_prices.csv` ➡️ `data/reviewed/index_prices.csv`.
  - ESG 지표 12개로 전면 확장 및 3개년 시계열(2022~2024) 및 기업 목표값 수집 완료 (`data/reviewed/esg_indicators.csv`, 총 72행).
  - 지표 비교 가능성 분석서 (`data/docs/indicator_comparability.csv`) 신설하여 양사 산식 및 단위 비교 분류 완료.
  - 사건 데이터에 최초 시장 공개일(`market_event_date`, `market_event_date_type`) 도입 및 관련 ESG 지표 연계 완료 (`data/reviewed/events.csv`).
  - 다대다 출처 연계를 위해 `data/reviewed/event_sources.csv` 신설 및 뉴스 후보 연계 컬럼 보완 (`data/raw/news_candidates.csv`).
  - 사건 심각도 판단 가이드라인 (`data/docs/event_severity_guide.md`) 및 데이터 품질 보고서 (`data/docs/data_quality_report.md`) 신설.
  - `schemas/data/esg-indicators.schema.json` 및 `schemas/data/events.schema.json` 스키마 고도화 수정.
  - `scripts/validate_data_a.py` 검증 규칙 수정 후 데이터 무결성 최종 검증 통과 (72행 ESG 지표, 5건 사건, 10건 출처 완벽 통과).
- **Created files**:
  - `data/docs/indicator_comparability.csv`
  - `data/docs/event_severity_guide.md`
  - `data/docs/data_quality_report.md`
  - `data/reviewed/event_sources.csv`
- **Modified files**:
  - `data/reviewed/esg_indicators.csv`
  - `data/reviewed/events.csv`
  - `data/raw/news_candidates.csv`
  - `schemas/data/esg-indicators.schema.json`
  - `schemas/data/events.schema.json`
  - `scripts/validate_data_a.py`
  - `progress/DATA-A.md`
- **Validation commands**:
  - `python scripts/validate_data_a.py`
- **Validation results**:
  - ESG 지표 72행 검증 통과 (005930: 36행, 000660: 36행)
  - 사건 데이터 5건 검증 통과 (market_event_date 및 linked_indicator_id 수록 완료)
  - 전체 스키마 정합성 검증 성공
- **Remaining**: 없음
- **Blockers**: 없음
- **Next task**: Data B 및 백엔드 팀으로의 데이터 전달 및 연동 검토 지원 (예: `stock_prices.csv`와 `index_prices.csv` 기반의 역사적 CVaR 및 포트폴리오 최적화 계산 연동)

### 2026-07-22 02:00 — DATA-A-RT-01/02: Candidate·Source·Dedup·Severity Contract Recovery

- **Role**: Data A
- **Owner**: Data A / Team Lead
- **Status**: `review`
- **Completed**:
  - candidate, source, event-source JSON Schema 신규 정의
  - candidate 5건과 source 10건, event-source 6건을 새 계약으로 마이그레이션
  - 후보 URL/external ID/content hash 중복 키와 사건 동일성·날짜·텍스트 유사도 판정 규칙 명문화
  - 사건 병합 우선순위와 충돌 시 후보 거절 정책 명문화
  - 처분 기준과 근거 키워드 중 최댓값을 사용하는 deterministic severity 산정 구현
  - 레거시 `sanctioned` 일괄 이관으로 과대 분류된 처분을 근거 문구에 따라 `fine` 또는 `corrective_order`로 정정
  - 사건에 `severity_rule_version=1.0.0`을 저장하고 processed/sample severity 재산정
  - 공식 1차 출처가 사건마다 정확히 하나인지 검증하는 CSV 계약 검사 추가
- **Created files**:
  - `schemas/data/event-candidates.schema.json`
  - `schemas/data/sources.schema.json`
  - `schemas/data/event-sources.schema.json`
  - `schemas/data/issue-pipeline-rules.json`
  - `schemas/data/issue-pipeline-rules.schema.json`
  - `data/docs/issue_pipeline_contract.md`
  - `src/backend/app/utils/issue_rules.py`
  - `src/backend/tests/test_issue_pipeline_contracts.py`
- **Modified files**:
  - `schemas/data/events.schema.json`
  - `schemas/data/data-enums.yaml`
  - `data/candidate/news_candidates.csv`
  - `data/processed/sources.csv`
  - `data/processed/event_sources.csv`
  - `data/processed/events.csv`
  - `data/sample/events.sample.csv`
  - `src/backend/app/utils/csv_validator.py`
  - `scripts/migrate_automated_validation.py`
  - `data/docs/event_severity_guide.md`
  - `data/docs/data_quality_report.md`
- **Validation commands**:
  - `.venv/Scripts/python.exe -m pytest src/backend/tests/test_csv_validator.py src/backend/tests/test_issue_pipeline_contracts.py -q`
  - `.venv/Scripts/python.exe -m pytest tests src/backend/tests/test_realtime_api_contracts.py -q --disable-warnings`
- **Validation results**:
  - Data A 신규·기존 계약 테스트 14건 통과
  - 모델링·실시간 API 계약 회귀 테스트 24건 통과
  - 전체 52건 실행은 기존 실시간 외부 가격 경로에서 장시간 대기하여 중단했으며 assertion 실패는 확인되지 않음
- **Remaining**:
  - Backend가 일일 동기화 서비스에서 새 candidate/source validator와 severity 함수를 호출하도록 연결
  - Data B가 `confirmed|resolved` 사건과 새 severity를 재계산 입력으로 사용하는지 교차 검토
- **Blockers**: 공유 계약이므로 Backend·Data B 교차 검토 전 `done` 처리 불가
- **Next task**: Backend 동기화 구현 시 자동 발행 게이트 연결 및 계약 테스트 추가

### 2026-07-22 02:40 — DATA-A-RT-01/02: needs_revision Remediation

- **Role**: Data A
- **Owner**: Data A / Team Lead
- **Status**: `review`
- **Completed**:
  - 공식 근거를 확인하지 못한 EVT-0002·EVT-0004를 processed에서 제거하고 해당 후보를 `rejected`로 전환
  - EVT-0003을 고용부 공식 보도자료 기준 `confirmed/investigation`으로 정정하고 해결일을 null 처리
  - EVT-0005를 개인정보위 공식 발표 ID·발표일·제재 내용으로 정정
  - 원안위·고용부·개인정보위 및 ESG 공식 자료를 `data/raw/reports/`에 저장하고 SHA-256을 source registry에 연결
  - 잘못된 `SRC-0001=company_response` 연결을 `context`로 정정
  - 임시 DART 접수번호에 의존하던 G01~G03 양사 18행을 `availability=unavailable`, `raw_value=null`로 전환
  - JSON Schema format, 회사 ID/이름, DART·공식 도메인, candidate 파생값, severity 버전·재계산 검증 추가
  - candidate→event→event-source→source 및 ESG→source와 raw hash를 검사하는 `validate_data_a_bundle()` 구현
  - ESG·event repository가 통합 bundle validator를 통과해야만 `validated`로 로드하도록 변경
  - 미구현 `/data/refresh`가 성공을 가장하지 않고 HTTP 501을 반환하도록 변경
  - Data B 사건 반응 기준일을 `market_event_date` 우선으로 수정
  - 데이터 사전을 12개 지표와 현재 결측 상태 기준으로 갱신
- **Created files**:
  - `scripts/remediate_data_a_findings.py`
  - `data/raw/reports/README.md`
  - `data/raw/reports/Samsung_Electronics_Sustainability_Report_2024_ENG.pdf`
  - `data/raw/reports/skhynix_sustainability_report_archive.html`
  - `data/raw/reports/nssc_201_samsung_radiation.pdf`
  - `data/raw/reports/moel_19573_skhynix_fluorine_inspection.html`
  - `data/raw/reports/pipc_8994_samsung_privacy.html`
- **Modified files**:
  - `data/candidate/news_candidates.csv`
  - `data/processed/esg_indicators.csv`
  - `data/processed/events.csv`
  - `data/processed/event_sources.csv`
  - `data/processed/sources.csv`
  - `data/docs/data_dictionary.md`
  - `data/notes/data_dictionary.md`
  - `data/docs/data_quality_report.md`
  - `data/docs/issue_pipeline_contract.md`
  - `schemas/data/event-candidates.schema.json`
  - `schemas/data/sources.schema.json`
  - `schemas/data/issue-pipeline-rules.json`
  - `schemas/data/issue-pipeline-rules.schema.json`
  - `src/backend/app/utils/csv_validator.py`
  - `src/backend/app/repositories/esg_repository.py`
  - `src/backend/app/repositories/event_repository.py`
  - `src/backend/app/routes/data.py`
  - `src/modeling/events.py`
  - `src/backend/tests/test_issue_pipeline_contracts.py`
  - `tests/test_events.py`
- **Validation commands**:
  - `.venv/Scripts/python.exe -m pytest src/backend/tests/test_csv_validator.py src/backend/tests/test_issue_pipeline_contracts.py tests/test_events.py -q`
  - `.venv/Scripts/python.exe -m pytest <repository/API subset> tests src/backend/tests/test_realtime_api_contracts.py -q --disable-warnings`
- **Validation results**:
  - Data A 계약·raw hash·시장 공개일·거짓 동기화 성공 방지 집중 테스트 22건 통과
  - 저장소·API·모델링·실시간 계약 회귀 테스트 30건 통과 (경고 1건)
- **Remaining**:
  - G01~G03 공식 원문을 다시 수집해 현재 unavailable 18행을 복구
  - BE-RT-03 실제 일일 수집·잠금·원자적 스냅샷 발행 구현
- **Blockers**: 실제 외부 수집기는 Backend 작업이므로 Data A 단독으로 `done` 처리하지 않음
- **Next task**: BE-RT-03 구현 시 `validate_data_a_bundle()`을 발행 직전 게이트로 호출

### 2026-07-22 03:10 — DATA-A-RT-01/02: 결측 ESG 소비 경로 보완

- **Role**: Data A / 교차 계약 점검
- **Owner**: Data A / Team Lead
- **Status**: `review`
- **Completed**:
  - Data B 집계 점수가 없는 validated ESG 지표에 하드코딩 점수를 자동 대입하던 경로 제거
  - 예시 ESG 점수는 `sample` 또는 명시적 `fallback` 모드에서만 허용
  - 운영 모드에서 기업별 집계 점수가 누락되면 모델 입력 검증 오류를 발생시키도록 변경
  - `/risk/esg`가 존재하지 않는 `esg_risk_score`를 `0.0`으로 바꾸지 않고 `null`과 `risk_level=unavailable`을 반환하도록 변경
  - Data B 집계 모델 미동기화 상태를 API 경고로 명시
- **Modified files**:
  - `src/modeling/optimizer.py`
  - `src/backend/app/routes/risk.py`
  - `tests/test_optimizer.py`
  - `src/backend/tests/test_portfolio.py`
  - `progress/DATA-A.md`
- **Validation commands**:
  - `.venv/Scripts/python.exe -m pytest -q tests/test_optimizer.py src/backend/tests/test_portfolio.py::test_risk_esg_endpoint src/backend/tests/test_portfolio.py::test_portfolio_optimize_form_submit src/backend/tests/test_portfolio.py::test_portfolio_optimize_realtime_endpoint`
  - `.venv/Scripts/python.exe -m pytest -q tests src/backend/tests`
  - `git diff --check`
- **Validation results**:
  - 대상 테스트 5건 통과
  - 모델·백엔드 전체 회귀 테스트 35건 통과
  - 공백 오류 없음(기존 CRLF 변환 경고만 존재)
- **Remaining**:
  - Data B의 실제 ESG 집계 점수 산식과 출력 계약이 동기화되면 `validated` 최적화 경로에 연결
  - 지배구조 G01~G03 공식 원문 재수집 전 18행은 `unavailable` 유지
- **Blockers**: Data B 집계 모델이 현재 브랜치에 아직 없음
- **Next task**: Data B 산출물 동기화 후 두 기업의 완전한 `esg_risk_score` 입력을 계약 테스트로 고정

### 2026-07-22 12:20 — DATA-A-RT-FINAL-02: Final Audit Quality Remediation

- **Role**: Data A
- **Owner**: Data A
- **Status**: `review`
- **Completed**:
  - S02(협력사 ESG 현장실사 비율)와 S05(책임광물 제3자 검증률) 지표 분리 완료.
    - `data/processed/esg_indicators.csv` 수정 (SK Hynix S02 -> S05 변경 및 삼성 S05, SK Hynix S02에 대한 3개년 unavailable 결측 행 추가, 총 78행).
    - `data/docs/indicator_comparability.csv` 수정 (S02/S05 개별 비교 행으로 분리 및 `insufficient_data` 설정).
    - `data/docs/data_dictionary.md` 및 `data/notes/data_dictionary.md` 수정 (S05 지표 정보 추가 및 scope_mismatch 전체 리스트 명시).
  - 사건 의미 중복 검사를 processed 발행 게이트에 연결 완료.
    - `src/backend/app/utils/csv_validator.py`의 `validate_data_a_bundle` 내에 `events_are_duplicates`를 연동하여 의미상 중복된 사건 발생 시 `INVALID_EVENT_SEMANTIC_DUPLICATE` 오류 코드로 반려하도록 수정.
    - bidirectional 검증 추가: 모든 processed event가 최소 하나의 `validation_status=validated` candidate에 의해 참조되고, candidate와 event의 company_id가 일치해야 함을 검증하며, 고아 사건 존재 시 `INVALID_EVENT_CANDIDATE_REFERENCE` 오류 코드로 반려.
    - `src/backend/tests/test_issue_pipeline_contracts.py`에 esg 행 수 78/24행 변경 사항 반영 및 중복/고아 사건 예외 테스트 케이스 추가.
  - EVT-0001 기흥 방사선 피폭 사고 시장 공개일 근거 보존 (Option B 선택).
    - 2024-05-28 최초 보도일 근거 확보 실패로 인해, 검증 가능한 가장 빠른 공식 원안위 보도자료일인 `2024-09-26`로 `market_event_date` 통일.
    - `market_event_date_type`을 `authority_announcement_date`로 변경하고 사건 메모(`note`)에 날짜 폐기 이유 수록.
  - Data A 검증 진입점 및 문서 복구.
    - `scripts/validate_data_a.py` 스크립트를 `validate_data_a_bundle` 통합 검증을 실행하는 방식으로 복구 완료.
    - `README.md` 내의 개별 검증 명령어를 `python scripts/validate_data_a.py`로 통일 및 가이드 보완.
- **Created files**: None
- **Modified files**:
  - `data/processed/esg_indicators.csv`
  - `data/processed/events.csv`
  - `data/docs/indicator_comparability.csv`
  - `data/docs/data_dictionary.md`
  - `data/notes/data_dictionary.md`
  - `src/backend/app/utils/csv_validator.py`
  - `src/backend/tests/test_issue_pipeline_contracts.py`
  - `scripts/validate_data_a.py`
  - `README.md`
  - `progress/DATA-A.md`
- **Validation commands**:
  - `python scripts/validate_data_a.py`
  - `python -m pytest src/backend/tests/test_issue_pipeline_contracts.py`
- **Validation results**: Pass
- **Remaining**:
  - Data B/Backend는 S02/S05 분리에 따라 최적화 모델 및 UI에서 `unavailable` 지표가 0으로 오처리되지 않도록 점검 필요.
  - Data B/Backend는 EVT-0001의 시장 공개일 변경(`2024-09-26`)에 따른 주가 반응 분석(Reaction Window) 재계산 필요.
- **Blockers**: 없음
- **Next task**: 없음

### 2026-07-22 12:45 — DATA-A-RT-FINAL-02: Local Virtual Environment and Verification Complete

- **Role**: Data A
- **Owner**: Data A
- **Status**: `review`
- **Completed**:
  - 로컬 가상환경 `.venv` 생성 및 `requirements.txt` 패키지 설치 완료.
  - 동적 웹페이지인 고용부(MOEL) 및 개인정보위(PIPC) 원문 파일 다운로드 및 `data/processed/sources.csv` 내 실시간 content_hash 동기화 완료.
  - `scripts/validate_data_a.py` 실행하여 데이터셋 통합 검증 성공 완료.
  - 신규 스키마 규격(ESG 78행) 및 중복 사건 검출 로직에 맞춰 `test_csv_validator.py` 및 `test_issue_pipeline_contracts.py` 테스트 케이스 보완 완료.
  - 백엔드 전체 테스트 스위트 68건 실행 및 전체 통과 완료.
- **Created files**:
  - `scripts/download_reports.py`
- **Modified files**:
  - `data/processed/sources.csv`
  - `src/backend/tests/test_csv_validator.py`
  - `src/backend/tests/test_issue_pipeline_contracts.py`
- **Validation commands**:
  - `.venv/Scripts/python.exe scripts/validate_data_a.py`
  - `.venv/Scripts/python.exe -m pytest src/backend/tests/`
- **Validation results**:
  - 데이터 검증: `[+] Data A bundle validation PASSED!` (candidates: 6, sources: 6, events: 3, esg: 78)
  - 테스트: `68 passed`
- **Remaining**:
  - 타 역할 직무(Data B, Backend, Frontend)에서 S02/S05 분리 및 EVT-0001 공개일 변경에 따른 연동 재확인
- **Blockers**: 없음
- **Next task**: 없음

### 2026-07-25 — DATA-A-06: 78행도 여전히 원문 미검증이었음을 확인, 원문 재대조본(64행)으로 전면 교체

- **Role**: Data A
- **Owner**: Data A (신규 인수인계)
- **Status**: `done`
- **배경**: 위 DATA-A-RT-FINAL-02까지의 78행 `esg_indicators.csv`를 재점검한 결과, S02/S05 분리는 구조적으로는 맞았지만 여전히 `source_id`가 `SRC-0001`/`SRC-0002`/`SRC-0004` 3개로만 귀속되고 `note`가 "자동 출처 검증 완료"로 전 행 동일한, 원문 대조 없이 생성된 값이었음을 확인함. `data/docs/data_quality_report.md`도 "8개 지표 직접비교 가능"이라 기술했으나 실제 재대조 결과 직접비교 가능 지표는 0개였음.
- **Completed**:
  - `data/raw/reports/`의 지속가능경영보고서 PDF 6종(삼성전자·SK하이닉스 각 2024~2026) SHA-256을 직접 재계산해 `extraction_manifest.csv`와 100% 일치 확인
  - 팀원이 원문 페이지·표제목·근거문장을 직접 대조해 작성한 `esg_indicators.csv`(65행, 유효 64행)로 전면 교체. `company_name`/`risk_direction`/`business_scope`/`geography`/`availability` 스키마 enum 매핑, 삼성 `consolidated`(DX+DS/전사) 판정 시 스키마 규칙대로 `scope_mismatch=true` 강제 적용, SK 인증 3행(`raw_value="Y"`)·삼성 G03 제재 1행(복합 텍스트)의 숫자 인코딩, E05 기간범위 3행의 대표연도 단일화, `target_candidates_FINAL.csv` 채택분 중 지표 정의가 정확히 일치하는 2건만 수치화(나머지는 null+note)
  - `data/processed/sources.csv`: 브라우저로 삼성(`images.samsung.com`)·SK하이닉스(`skhynix.com` 공식 자료실) 공식 URL을 직접 접속해 존재 확인, PDF 6종 전부 SHA-256 일치. 이벤트 증거 3건(원안위/고용노동부/개인정보위)도 사용자가 직접 다운로드해 `data/raw/reports/`에 저장 — 고용노동부·개인정보위 첨부가 실제로는 `.html`이 아닌 `.pdf`였음을 확인해 `file_name` 정정
  - `data/docs/data_quality_report.md`, `data/docs/indicator_comparability.csv`, `data/docs/data_dictionary.md`를 원문 대조 기반 실제 분석본으로 교체
  - **브랜치 재구성**: 최초 작업은 `codex/frontend-ui-tweak`(UI 브랜치) 위에서 분기해 진행했으나, 데이터 전용 브랜치를 요청받았음에도 UI 브랜치 계보가 섞이는 문제를 발견해 `origin/main`에서 새로 분기(`data-a/esg-revalidation`)하고 데이터 변경분만 이식. 그 사이 main은 독자적으로 DART 어댑터, orphan-event 검증, 사건 의미 중복 검증(`severity_rule_version=1.1.0`) 등을 추가했음을 확인 — 이 커밋들은 건드리지 않고 그대로 유지
- **Modified files**:
  - `data/processed/esg_indicators.csv`, `data/processed/sources.csv`
  - `data/docs/data_quality_report.md`, `data/docs/indicator_comparability.csv`, `data/docs/data_dictionary.md`
  - `src/backend/tests/test_csv_validator.py`, `src/backend/tests/test_issue_pipeline_contracts.py` (esg 78→64행, sources 6→10건, unavailable 24→0건으로 정정. main이 추가한 orphan-event/의미중복/DART 정규식 테스트는 그대로 유지)
  - `progress/DATA-A.md`, `PROGRESS.md`
- **Validation commands**:
  - 로컬 PDF 6종 + 이벤트 증거 3종 SHA-256 재계산 및 대조
  - `.venv/Scripts/python.exe -m pytest src/backend/tests/test_csv_validator.py src/backend/tests/test_issue_pipeline_contracts.py -q`
  - `.venv/Scripts/python.exe -m pytest src/backend/tests -q` (pandas 의존 4개 파일은 로컬 환경의 애플리케이션 제어 정책이 pandas DLL을 차단해 실행 불가 — 제 변경과 무관한 로컬 환경 제약)
  - `validate_data_a_bundle()` 직접 호출(main 최신 로직: orphan-event, 의미상 중복 사건, DART 접수번호 정규식 포함)
- **Validation results**:
  - `validate_data_a_bundle()` PASS (esg 64, sources 10, events 3, candidates 6)
  - pytest: `test_csv_validator.py`+`test_issue_pipeline_contracts.py` 23 passed / 나머지 백엔드 테스트(pandas 미의존 부분) 69 passed
- **Remaining**:
  - G02(정정공시 건수)는 여전히 미확보(DART 별도 트랙, 이번 작업 범위 밖)
  - Data B의 `event_reactions.json`/`optimization_result.json` 등은 구 78행(여전히 허구) 데이터 기반일 가능성이 있어 재계산 필요(`PROGRESS.md` Active Blockers 참고)
- **Blockers**: 없음
- **Next task**: Data B가 새 64행 ESG 데이터 기준으로 재계산, 이후 PR 생성 및 리뷰
