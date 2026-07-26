# Data A Progress Log

## Task Status

| Task ID | Task | Status | Output | Blocker |
|---|---|---|---|---|
| DATA-A-01 | ESG Indicator Definition | `done` | `data/processed/esg_indicators.csv`, `data/notes/data_dictionary.md` | 없음 |
| DATA-A-02 | Official Report Collection | `done` | `data/raw/reports/README.md`, `data/processed/sources.csv` | 없음 |
| DATA-A-03 | ESG Value Review | `done` | `data/processed/esg_indicators.csv` (72행: available 54, unavailable 18) | 없음 |
| DATA-A-04 | Event Dataset | `done` | `data/processed/events.csv` (공식 확인 confirmed 사건 3건) | 없음 |
| DATA-A-05 | Final Data Quality Review | `done` | `validate_data_a_bundle()` 및 계약 테스트 통과 | 없음 |
| DATA-A-RT-01 | Daily Disclosure and News Source·Classification·Deduplication Rules | `review` | DART 원문 ZIP/XML 본문 수집·안전 추출·본문 기반 경고 분류 및 실 API smoke 완료 | Backend/Data B 교차 검토와 production 뉴스 provider 승인 필요 |
| DATA-A-RT-02 | Candidate Data Quality and Event Status Validation | `review` | candidate 분류·중복·출처 SHA-256·상태·원자적 발행 통합 검증 | Backend/Data B 교차 검토 필요 |
| DATA-A-RT-FINAL-02 | final audit remediation (S02/S05 split, event deduplication gate, EVT-0001 date, scripts restore) | `review` | scripts/validate_data_a.py, data/processed/*, data/docs/*, etc. | 없음 |
| DATA-A-06 | ESG Indicator Re-validation (원문 재대조, 전임 산출물 전면 폐기) | `done` | `data/processed/esg_indicators.csv`(64행), `data/processed/sources.csv`(10건), `data/docs/data_quality_report.md`, `data/docs/indicator_comparability.csv`, `data/docs/data_dictionary.md` | 없음 — `validate_data_a_bundle()` 전체 통과(main 최신 검증 로직 기준으로 재확인) |
| DATA-A-07 | EDA 수행 및 데이터분석 정의서 작성 (모델링 A 역할 요구사항) | `done` | `notebooks/eda_analysis.ipynb`, `notebooks/charts/*.png`, 지침 폴더 `데이터분석 정의서.docx`("2. EDA 명세서" 섹션) | Modeling B 결과 교차검수·최종 발표 준비는 후속 작업으로 남음 |
| DATA-A-08 | G02/SK G01·G03 DART 조사 | `review` | `data/processed/esg_indicators.csv`(68행, SK G01·G03 4행 추가), `data/processed/sources.csv`(SRC-0015/0016) | G02(양사)만 Open DART API 키 발급 대기, G01/G03은 완료 |

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

### 2026-07-25 (계속) — `data_a_human_review_checklist.md` 1절 갱신 (RT-B01 관련)

- **Role**: Data A
- **Owner**: Data A
- **Status**: `review`
- **Completed**:
  - `data/docs/data_a_human_review_checklist.md` 1절(G01~G03 공식자료 검토)이 옛 72/78행 구조("양사 G01~G03 전부 unavailable 18행, 2022~2024") 기준으로 작성돼 있어 새 64행 실측 구조와 맞지 않는 것을 발견해 갱신
  - 삼성전자 G01(2행, SEC-2025 p.6/SEC-2026 p.6)·G03(1행, SEC-2024 p.57 + PIPC 의결서)은 원문 근거가 확인된 것으로 표기하고 체크리스트 항목을 `승인`으로 판정
  - SK하이닉스 G01·G03, 양사 G02는 "임시 unavailable 행"이 아니라 "행 자체가 없는 미확보 상태(사유 명시)"로 정정, 수정 필요 사항에 DART 조사 필요성을 남김
  - 2절(비전공자용 사용자 문구 검토)은 ESG 데이터 구조와 무관해 손대지 않음(Frontend/Backend 카피 검토 영역)
- **Modified files**:
  - `data/docs/data_a_human_review_checklist.md`
  - `progress/DATA-A.md`
- **Validation commands**: 없음(문서 갱신, 데이터 파일 변경 아님 — 스키마 검증 대상 아님)
- **Remaining**:
  - `COMMON-RT-02`가 `done`이 되려면 Data B·Backend·Frontend가 각자 로그에 승인 기록을 남겨야 함(RT-B01)
  - G02/SK G01·G03 DART 조사는 여전히 미착수(팀 결정 대기)
- **Blockers**: 없음
- **Next task**: 커밋/PR 여부는 사용자 확인 후 진행

### 2026-07-25 (계속) — DATA-A-07: EDA 수행 및 데이터분석 정의서 작성

- **Role**: Data A (모델링 A 역할 기준)
- **Owner**: Data A
- **Status**: `done`
- **배경**: `[2] semiconductor_navigation_2day_4person_execution_plan_v2.md`(지침 폴더) 기준 "모델링 A" 책임에 EDA 수행·EDA 노트북/차트·데이터분석 정의서 작성이 명시돼 있으나, 이전까지의 ESG 원문 재검증 작업(DATA-A-06)은 이 요구사항을 충족하지 못했음을 확인하고 착수
- **Completed**:
  - `notebooks/eda_analysis.ipynb` 작성 및 실행(Anaconda Python 사용 — `.venv`는 이 PC의 애플리케이션 제어 정책이 pandas DLL을 차단해 사용 불가)
  - 가격 데이터(`stock_prices.csv`, `index_prices.csv`): 크기·기간·결측·중복 확인(0건), 종가·수익률 기초통계, 수익률 히스토그램+VaR95%/CVaR95%, 누적수익률(SOX 비교), 최대낙폭(MDD), 두 종목 상관관계(0.688), 최근 1년 vs 전체(~3년) CVaR 비교
  - ESG 데이터(`esg_indicators.csv`): 카테고리(E/S/G)·`data_confidence`·`risk_direction`·`scope_mismatch` 분포, `scope_mismatch=true`(21행, 전부 삼성) 및 `data_confidence=low`(2행) 목록 추출
  - matplotlib 기본 폰트가 한글 글리프를 지원하지 않아 차트 텍스트가 깨지는 문제를 발견해 `Malgun Gothic`으로 폰트 설정 수정 후 전체 재실행
  - 차트 5종을 `notebooks/charts/*.png`로 저장(발표자료·정의서 재사용용)
  - 지침 폴더 `데이터분석 정의서.docx`의 "2. EDA 명세서" 섹션(목표/데이터정의/데이터획득방법/EDA과정/EDA결론/KPI확정 6개 셀)을 실제 분석 결과로 채움. "3. 모델링 명세서"는 Modeling B 영역이라 손대지 않음. python-docx로 편집 후 원본 백업 보존, XML well-formed 여부 및 pandoc 렌더링으로 결과 확인
- **Created files**:
  - `notebooks/eda_analysis.ipynb`
  - `notebooks/charts/01_return_histogram.png` 등 5개
- **Modified files**:
  - `C:/Users/tiger/OneDrive/Desktop/지침/데이터분석 정의서.docx` (리포지토리 밖 파일)
  - `progress/DATA-A.md`
- **Validation commands**:
  - `anaconda3/python.exe -m jupyter nbconvert --to notebook --execute --inplace notebooks/eda_analysis.ipynb`
  - `python -c "import xml.etree.ElementTree as ET; ET.parse(...)"`(docx 내부 XML 4종 well-formed 확인)
- **Validation results**: 노트북 전체 셀 오류 없이 실행 완료, 차트 5종 생성, docx XML 구조 이상 없음
- **Remaining**:
  - Modeling B(Data B) 계산 결과와 EDA 결론(특히 CVaR 기준기간 1년 vs 3년) 교차검수 — Data B 재계산 이후 가능
  - 최종 발표/제출 준비
- **Blockers**: 없음
- **Next task**: 커밋/PR 후 사용자 확인, 이후 Modeling B 재계산 대기

### 2026-07-25 (계속) — DATA-A-08: SK하이닉스 G03(준법/제재 현황) 원문 확보

- **Role**: Data A
- **Owner**: Data A
- **Status**: `review`
- **Completed**:
  - DART 사업보고서(2025.03.19 제출, rcpNo=20250319000665) 뷰어에서 "XI. 그 밖에 투자자 보호를 위하여 필요한 사항 > 3. 제재 등과 관련된 사항" 섹션 위치를 확인했으나, 가상 스크롤(virtualized) 목차 트리를 자동화 도구로 탐색하는 데 반복 실패해 사용자가 직접 DART에서 원문을 열람해 표 전체를 전달함
  - 원문 기준 SK하이닉스 G03을 연도별 3행(2022=6건, 2023=3건, 2024=2건)으로 `esg_indicators.csv`에 추가. 각 행에 제재기관·금액·근거법령을 note에 요약 기록
  - `sources.csv`에 `SRC-0015`(SK하이닉스 사업보고서, `validation_method=dart_receipt`, `external_id=20250319000665`) 등록. 사용자가 DART에서 PDF를 다운로드해 `data/raw/reports/`에 저장, SHA-256 재계산 후 등록
  - SK G01(사외이사 비율)도 KRX KIND 기업지배구조보고서(2025-05-30 제출, acptno=20250530000841) 원문에서 "총 9명 이사 중 사외이사 5명(55.6%)" 확인(WebFetch로 원문 인용 확보) — 단, 사용자가 받은 raw 파일이 0바이트라 아직 `esg_indicators.csv`/`sources.csv`에는 미반영, 재다운로드 대기
  - `data/docs/indicator_comparability.csv`, `data_dictionary.md`, `data_quality_report.md`, `data_a_human_review_checklist.md`를 G03 확보 반영해 갱신(G03: 삼성 PIPC 단일 제재 vs SK 전 규제기관 제재로 정의 상이 확인, `not_comparable`로 분류)
- **Created files**: 없음
- **Modified files**:
  - `data/processed/esg_indicators.csv` (67행)
  - `data/processed/sources.csv` (11건)
  - `data/raw/reports/skhynix_business_report_2025_rcp20250319000665.pdf` (사용자 다운로드)
  - `data/docs/indicator_comparability.csv`, `data_dictionary.md`, `data_quality_report.md`, `data_a_human_review_checklist.md`
  - `src/backend/tests/test_csv_validator.py`, `src/backend/tests/test_issue_pipeline_contracts.py` (esg 64→67, sources 10→11)
  - `progress/DATA-A.md`
- **Validation commands**:
  - `validate_data_a_bundle()` 직접 호출
  - `.venv/Scripts/python.exe -m pytest src/backend/tests/test_csv_validator.py src/backend/tests/test_issue_pipeline_contracts.py -q`
- **Validation results**: `validate_data_a_bundle()` PASS(esg 67, sources 11), pytest 23 passed
- **Remaining**:
  - SK G01: raw 파일 재다운로드 필요(현재 0바이트) — 받으면 esg_indicators.csv 1행 + sources.csv 1건 추가
  - G02(양사): Open DART API 키 발급 대기
- **Blockers**: 위 2건
- **Next task**: SK G01 파일 재확보, 이후 G02 API 키 발급 시 정정공시 건수 집계

### 2026-07-25 (계속) — DATA-A-08 완료: SK하이닉스 G01(사외이사 비율) 확보, 이 데이터셋 최초의 direct 지표

- **Role**: Data A
- **Owner**: Data A
- **Status**: `done`
- **Completed**:
  - 사용자가 KRX KIND 기업지배구조보고서(2025.05.30 제출, acptno=20250530000841) 원문 PDF를 재다운로드(65페이지, 이전 0바이트 문제 해소)해 전달
  - p.4 "독립적 이사회 구성"에서 "총 9명의 이사(사내이사 2명, 기타비상무이사 2명, 사외이사 5명)... 사외이사의 비율을 과반수 이상(55.6%)" 확인 → `esg_indicators.csv`에 SK G01 2025년 1행 추가(raw_value=55.6, business_scope=consolidated)
  - `sources.csv`에 `SRC-0016` 등록(SHA-256 재계산 일치 확인). `kind.krx.co.kr`가 기존 `official_domains` 허용목록에 없어 `schemas/data/issue-pipeline-rules.json`에 `krx.co.kr` 추가(KRX는 한국거래소 공식 공시시스템으로, 기존 nssc.go.kr/moel.go.kr/pipc.go.kr와 동일 성격의 공식기관 도메인)
  - G01은 삼성·SK 산식이 완전히 동일(사외이사수/이사회총원)해 `indicator_comparability.csv`에서 `one_sided`→**`direct`**로 재분류. 이 프로젝트 ESG 데이터셋 전체에서 최초의 직접비교 가능 지표
  - `data/docs/data_quality_report.md`, `data_dictionary.md`, `data_a_human_review_checklist.md` 갱신(G01 확보 반영, 이제 미확보는 G02(양사)·S05(삼성)뿐). `data_dictionary.md`의 이벤트 raw artifact 관련 stale 경고문도 이번에 정리(이미 해소된 결함이었음)
- **Modified files**:
  - `data/processed/esg_indicators.csv` (68행)
  - `data/processed/sources.csv` (12건)
  - `data/raw/reports/skhynix_corporate_governance_report_2025_acpt20250530000841.pdf` (사용자 재다운로드)
  - `schemas/data/issue-pipeline-rules.json` (official_domains에 krx.co.kr 추가)
  - `data/docs/indicator_comparability.csv`, `data_dictionary.md`, `data_quality_report.md`, `data_a_human_review_checklist.md`
  - `src/backend/tests/test_csv_validator.py`, `src/backend/tests/test_issue_pipeline_contracts.py` (esg 67→68, sources 11→12)
  - `progress/DATA-A.md`
- **Validation commands**:
  - `validate_data_a_bundle()` 직접 호출
  - `.venv/Scripts/python.exe -m pytest src/backend/tests/test_csv_validator.py src/backend/tests/test_issue_pipeline_contracts.py -q`
  - `.venv/Scripts/python.exe -m pytest src/backend/tests -q`(pandas 미의존 부분)
- **Validation results**: `validate_data_a_bundle()` PASS(esg 68, sources 12), pytest 23 passed / 69 passed
- **Remaining**:
  - G02(양사): Open DART API 키 발급 대기(팀 결정)
- **Blockers**: G02만 남음(사용자 계정 생성 필요, Data A가 대신할 수 없음)
- **Next task**: 커밋/PR 여부 사용자 확인 후 진행. G02는 API 키 확보 시 재개

### 2026-07-25 (계속) — DATA-A-09: G03 최신 사업보고서로 전면 갱신, 중대재해 2건 신규 발견·추가, G02 API 없이 건수 확보

- **Role**: Data A
- **Owner**: Data A
- **Status**: `review`
- **배경**: 사용자가 SK/삼성 최신 사업보고서(2026년 3월 제출본)의 XI.3 제재현황 원문을 직접 열람해 전달. 기존 SK G03(2025.03.19본, 2022~2024 window)이 이미 오래됐고, 삼성 G03(PIPC 단일건만)은 사업보고서 전체를 본 게 아니었음을 확인해 전면 재작업.
- **Completed**:
  - **G03 전면 교체**: 양사 모두 2026년 3월 제출 사업보고서(2023~2025 window)로 통일
    - SK하이닉스: 당사 단독 기준 2023=3건/2024=2건/2025=3건 (수사·사법기관 해당없음). 기존 2022~2024 데이터(2025.03.19본)와 2023·2024년 숫자가 완전히 일치해 교차검증됨
    - 삼성전자: 당사+전세계 종속회사(Harman·삼성디스플레이·삼성메디슨·레인보우로보틱스·SEUZ/SEASA/SETK/SEM/SEVT/SEF/SEMAG 등) 합산 2023=7건/2024=7건/2025=16건. **비반도체 종속회사 포함 여부를 note에 명시**(지침의 "삼성=반도체 외 사업 포함, 주의 필요" 경고에 부합)
    - `sources.csv`: `SRC-0015`를 2026.03.17 제출본으로 교체, `SRC-0017`(삼성 사업보고서 2026.03.10) 신규 등록. 기존 2025.03.19본 raw 파일은 삭제
  - **중대재해 2건을 신규 이벤트로 추가**(사용자 승인, "1번 추가"):
    - `EVT-0006`: SK하이닉스, 2024-05-10 발생 업무상 질병 사망 1명(사외). 사업보고서(SRC-0015)만 근거, 언론보도 확인 안 됨. severity=5(사망 키워드), enforcement_action=no_action(명시된 정부조치 없음)
    - `EVT-0007`: 삼성전자(삼성디스플레이), 2025-12-23 아산2캠퍼스 협력사 직원 끼임사고 사망1+부상1. 사업보고서(SRC-0017)+뉴스(디지털데일리 등 사고 당일 다수 보도) 교차확인. 대전지방고용노동청 천안지청 부분작업중지명령(2025-12-23 발령, 2026-02-20 해제) 확인, enforcement_action=corrective_order, severity=5
    - `candidate_content_hash`/`canonicalize_url`/`calculate_event_severity`는 실제 `app.utils.issue_rules` 함수를 그대로 호출해 계산(수동 계산으로 인한 오류 방지)
    - `news_candidates.csv`에 `CND-0007`(EVT-0006용, dart_disclosure)·`CND-0008`(EVT-0007용, news) 추가, `event_sources.csv`에 두 이벤트의 공식 1차 출처 연결 추가
  - **뉴스 조사 중 SK하이닉스의 별개 사망 사건 발견**: 산재 승인 2025-03-05, 사망 2026-06-25(2026-06-26 다수 매체 보도, "중대재해 여부 조사 중"). 사업보고서 표의 2024-05-10 건과 날짜가 달라 별개 인물로 추정. 사용자가 "조사해서 추가" 결정 — DART 원문(수시공시) 링크를 사용자에게 요청, 확보 후 `EVT-0008`로 추가 예정
  - `data/docs/data_quality_report.md`, `data_dictionary.md`, `indicator_comparability.csv`, `data_a_human_review_checklist.md` 갱신(G03 신규 수치, 사건 5건으로 갱신, 비반도체 종속회사 주의사항 명시)
  - 테스트 3개(`test_bundle_rejects_semantic_duplicate_events`, `test_bundle_rejects_orphan_events`, 행수 단언)가 `lines[-1]`(마지막 줄)을 EVT-0005로 가정하고 있었는데 새 이벤트를 뒤에 추가하면서 깨짐 — `next(line for line in lines if line.startswith("EVT-0005,"))`로 위치에 의존하지 않도록 수정
- **Created files**:
  - `data/raw/reports/skhynix_business_report_2026_rcp20260317000635.pdf`, `samsung_business_report_2026_rcp20260310002820.pdf` (사용자 다운로드)
- **Modified files**:
  - `data/processed/esg_indicators.csv`(70행), `data/processed/sources.csv`(13건), `data/processed/events.csv`(5건), `data/candidate/news_candidates.csv`(8건), `data/processed/event_sources.csv`(6건)
  - `data/docs/data_quality_report.md`, `data_dictionary.md`, `indicator_comparability.csv`, `data_a_human_review_checklist.md`
  - `src/backend/tests/test_csv_validator.py`, `src/backend/tests/test_issue_pipeline_contracts.py`
  - `progress/DATA-A.md`
- **Validation commands**:
  - `validate_data_a_bundle()` 직접 호출
  - `.venv/Scripts/python.exe -m pytest src/backend/tests/test_csv_validator.py src/backend/tests/test_issue_pipeline_contracts.py -q`
  - `.venv/Scripts/python.exe -m pytest src/backend/tests -q`(pandas 미의존 부분)
- **Validation results**: `validate_data_a_bundle()` PASS(esg 70, sources 13, events 5, candidates 8), pytest 23 passed / 69 passed
- **Remaining**:
  - G02: 사용자가 API 없이 DART "정정보고서 검색"으로 건수 직접 확인(삼성 45건/SK 28건, 2023~2025). 근거 파일(캡처 또는 인쇄 PDF)만 받으면 반영 가능
  - EVT-0008: SK하이닉스 2026-06-25 사망 건, DART 수시공시 원문 링크 확보 대기
- **Blockers**: 위 2건(둘 다 사용자 확인/자료 제공 필요)
- **Next task**: G02 근거 파일 및 EVT-0008용 DART 링크 확보 후 마무리, 이후 커밋/PR

### 2026-07-25 (계속) — DATA-A-10: G02 양사 확보(API 불필요) 및 SK하이닉스 세 번째 중대재해(EVT-0008) 추가로 4단계 항목 전부 마무리

- **Role**: Data A
- **Owner**: Data A
- **Status**: `done`(커밋/PR 대기)
- **배경**: 사용자가 DART "정정보고서 검색" 화면 캡처(삼성 45건/SK 28건, 2023-01-01~2025-12-31)와 SK하이닉스의 세 번째 중대재해 발생 공시(2026.06.26 접수, rcpNo=20260626801398) 화면 캡처를 `data/raw/reports/`에 직접 저장 후 전달
- **Completed**:
  - **G02(정정공시 건수) 양사 확보**: `SRC-0019`로 등록(organization_name=전자공시시스템(DART), validation_method=`official_domain`, url=`https://dart.fss.or.kr/dsab001/main.do`). 개별 rcpNo 문서가 아닌 검색결과 화면이라 `dart_receipt` 대신 `official_domain` 적용 — `issue-pipeline-rules.json`의 `official_domains`에 `dart.fss.or.kr` 추가. `esg_indicators.csv`에 삼성(45건)·SK(28건) 각 1행 추가(연도별 세부내역 없이 3개년 누적치, `not_comparable`로 분류 — 계열사 규모 차이 때문에 단순 비교 금지 명시)
  - **EVT-0008 추가**: SK하이닉스, 산재보험법상 업무상 질병 승인(2025-03-05) 후 요양 중 사망(2026-06-25), 고용노동부 보고일자 2026-06-26. `SRC-0018`(dart_receipt, rcpNo=20260626801398)로 근거 등록. `EVT-0006`(사업보고서 XI.라 기재, 2024-05-10 사망)과는 발생일자가 달라 별개 인물로 판단 — 사업보고서 제출(2026.03.17) 이후 발생한 별건이라 해당 보고서에는 미기재. `enforcement_action=investigation`(고용노동부 현장조사·원인파악 진행 중, 공시 자체에 "중대재해 여부 미확정, 확정 시 정정공시 예정" 명시), severity=5(실제 함수 재계산 확인)
  - `CND-0009`(EVT-0008용 dart_disclosure 후보) 추가, `event_sources.csv`에 EVT-0008↔SRC-0018 연결 추가
  - **파일명 정리**: 사용자가 저장한 원본 파일명(`G02(정정보고서 45건,28건).pdf`, `SK하이닉스_중대재해발생_2026.06.26.pdf`)에 한글·쉼표가 포함돼 있어 CSV 파싱 사고 방지 및 기존 명명 규칙(영문 snake_case) 일치를 위해 각각 `dart_correction_report_search_g02_2023_2025.pdf`, `skhynix_fatality_disclosure_2026_rcp20260626801398.pdf`로 리네임(콘텐츠는 불변이라 SHA-256 동일)
  - **CSV 파싱 버그 발견·수정**: `SRC-0019`의 `document_title` 필드에 쉼표가 포함된 채 따옴표 없이 입력해 컬럼이 밀리는 사고 발생 → `validate_data_a_bundle()` 실행 중 `INVALID_SOURCE_DART_RECEIPT` 등 엉뚱한 오류로 감지, 해당 필드를 따옴표로 감싸 수정 후 재검증 통과
  - `data_quality_report.md`(12개 지표 전부 확보로 요약 갱신, G02 not_comparable 사유 추가, 남은 한계 8번 EVT-0008 반영), `data_dictionary.md`(총 72행=삼성32+SK40, G02 확보 반영, scope_mismatch 대상에 G02 추가), `indicator_comparability.csv`(G02 행 추가), `data_a_human_review_checklist.md`(G01~G03 전부 확보 11행, "수정 필요 사항" 없음으로 갱신) 업데이트
  - 테스트 카운트 갱신: esg 70→72, sources 13→15, events 5→6, candidates 8→9(validated 5→6), event_sources 6→7
- **Created files**:
  - `data/raw/reports/dart_correction_report_search_g02_2023_2025.pdf`, `skhynix_fatality_disclosure_2026_rcp20260626801398.pdf`(사용자 저장, 리네임)
- **Modified files**:
  - `data/processed/esg_indicators.csv`(72행), `data/processed/sources.csv`(15건), `data/processed/events.csv`(6건), `data/candidate/news_candidates.csv`(9건), `data/processed/event_sources.csv`(7건)
  - `schemas/data/issue-pipeline-rules.json`(official_domains에 dart.fss.or.kr 추가)
  - `data/docs/data_quality_report.md`, `data_dictionary.md`, `indicator_comparability.csv`, `data_a_human_review_checklist.md`
  - `src/backend/tests/test_csv_validator.py`, `src/backend/tests/test_issue_pipeline_contracts.py`
  - `progress/DATA-A.md`
- **Validation commands**:
  - `validate_data_a_bundle()` 직접 호출
  - `.venv/Scripts/python.exe -m pytest src/backend/tests/test_csv_validator.py src/backend/tests/test_issue_pipeline_contracts.py -q`
  - `.venv/Scripts/python.exe -m pytest src/backend/tests -q --ignore=...`(pandas 미의존 부분)
- **Validation results**: `validate_data_a_bundle()` PASS(esg 72, sources 15, events 6, candidates 9, event_sources 7), pytest 23 passed / 69 passed
- **Remaining**: 없음 — G01~G03 12개 지표 전부 양사 확보, 발견된 중대재해 3건(EVT-0006/0007/0008) 전부 반영 완료
- **Blockers**: 없음
- **Next task**: 이번 라운드 전체(G03 교체+EVT-0006/0007/0008+G02+문서 갱신)를 새 브랜치로 커밋·푸시하고 PR 링크 제공, 사용자 병합 대기

### 2026-07-26 05:44 — DATA-A-RT-01/02: Production Complete-Bundle Normalizer 착수

- **Role**: Data A
- **Owner**: Data A
- **Status**: `in_progress`
- **Goal**:
  - Open DART 수집 결과를 현재 정상 Data A 스냅샷과 병합해 완전한 candidate/source/event-source/event/ESG bundle로 만드는 운영용 normalizer 구현
  - 확정 근거가 부족한 후보는 모델 입력에 포함하지 않고 결정적 규칙으로 `reported`, `pending` 또는 `rejected` 상태 보존
  - 완성된 bundle이 `validate_data_a_bundle()`을 통과한 경우에만 원자적 발행 워크플로로 전달
- **Allowed files**:
  - `src/backend/app/services/`
  - `src/backend/app/core/runtime.py`
  - `src/backend/tests/`
  - `data/docs/issue_pipeline_contract.md`
  - `progress/DATA-A.md`
  - `ROADMAP.md`의 해당 Data A 체크박스
- **Do not modify**:
  - 공유 데이터/API 스키마
  - 기존 `data/processed/` 및 `data/candidate/` 기준 데이터
  - 다른 역할의 progress 파일과 루트 `PROGRESS.md`
- **Validation plan**:
  - production normalizer 단위 테스트
  - issue workflow·snapshot publisher·runtime wiring 회귀 테스트
  - `python scripts/validate_data_a.py`
  - 전체 backend/model 회귀 테스트 및 `git diff --check`
- **Shared rule proposal**:
  - `schemas/data/issue-pipeline-rules.json`에 `candidate_classification` 규칙을 추가하고 대응 스키마를 먼저 갱신한다.
  - 영향 역할은 Data A(규칙 소유), Backend(normalizer/runtime 소비), Data B(`confirmed|resolved` 사건 재계산 소비)다.
  - 코드 하드코딩 대신 버전 관리되는 JSON 규칙을 단일 원본으로 사용하며 기존 API·CSV 필드는 변경하지 않는다.
  - 구현·계약 테스트 후 Backend/Data B 교차 검토 전까지 상태를 `review`로 유지한다.
- **Blockers**: 없음
- **Next task**: complete-bundle normalizer와 DART 일일 collector adapter 구현

### 2026-07-26 05:58 — DATA-A-RT-01/02: Production Complete-Bundle Normalizer 구현 완료

- **Role**: Data A
- **Owner**: Data A
- **Status**: `review`
- **Completed**:
  - `DailyDartIssueCollector` 구현: 서울 날짜 기준 1일 lookback, 양사 독립 수집, 한 회사 실패 시 `partial_success`, 양사 실패 시 발행 중단
  - `DataAIssueBundleNormalizer` 구현: 활성 정상 bundle 복사, candidate 중복 제거, 승인 규칙 분류, source/event/event-source 생성, raw SHA-256 확인, 전체 bundle 검증
  - 자동 분류 규칙을 `issue-pipeline-rules.json`의 `candidate_classification`으로 이동하고 대응 JSON Schema를 먼저 갱신
  - 승인 규칙 미일치 일반 공시는 `rejected/no_approved_esg_event_rule_match`, 공식 확인 없는 뉴스는 `rejected/official_confirmation_required`로 보존
  - Open DART 접수번호·공식 URL·sanitized raw 응답 hash가 모두 유효한 후보만 `validated/confirmed` 사건으로 변환
  - 기존 후보·사건·출처는 결정적 키로 중복 처리하며 기존 활성 스냅샷과 checked-in processed 데이터는 직접 수정하지 않음
  - prepared bundle cleanup을 workflow 성공·실패 공통 `finally` 경로에 연결
  - `DART_API_KEY`가 있을 때만 production workflow를 coordinator에 연결하고, 키가 없으면 명시적 unavailable 유지
  - Windows 긴 경로에서도 raw evidence를 원자적으로 복사하도록 publisher staging 디렉터리 이름 단축
  - production normalizer → 전체 검증 → 원자적 발행 → Data B 재계산 통합 테스트 추가
- **Unexpected findings and fixes**:
  - 사건 스키마가 `EVT-` 뒤 정확히 4자리만 허용함을 테스트에서 확인하여 다음 순번 ID 생성으로 교정
  - 실제 raw 파일명이 긴 경우 pytest 임시 경로에서 publisher staging 경로가 Windows 한도를 넘는 문제를 확인하여 짧은 임시 staging ID로 교정
  - 코드 내 분류 키워드가 규칙 단일 원본 원칙과 충돌하는 점을 최종 검토에서 발견하여 JSON 규칙으로 이전
- **Created files**:
  - `src/backend/app/services/issue_bundle_normalizer.py`
  - `src/backend/tests/test_issue_bundle_normalizer.py`
- **Modified files**:
  - `schemas/data/issue-pipeline-rules.json`
  - `schemas/data/issue-pipeline-rules.schema.json`
  - `src/backend/app/core/runtime.py`
  - `src/backend/app/services/issue_sync_workflow.py`
  - `src/backend/app/services/issue_snapshot_publisher.py`
  - `src/backend/tests/test_runtime_wiring.py`
  - `data/docs/issue_pipeline_contract.md`
  - `README.md`
  - `ROADMAP.md`
  - `progress/DATA-A.md`
- **Validation commands**:
  - `.venv\Scripts\python.exe scripts\validate_data_a.py`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_issue_bundle_normalizer.py src/backend/tests/test_issue_pipeline_contracts.py --disable-warnings`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests src/backend/tests --disable-warnings`
  - `.venv\Scripts\python.exe -m compileall -q src/backend/app src/modeling`
  - `git diff --check`
- **Validation results**:
  - Data A bundle PASS: candidate 9, source 15, event-source 7, event 6, ESG 72
  - 신규 normalizer·규칙 계약 집중 테스트 `22 passed`
  - 전체 회귀 `237 passed, 1 warning`
  - `optimization_grid_results.csv` 테스트 전후 SHA-256 동일
  - Python compile 및 whitespace 검사 통과(CRLF 변환 안내만 존재)
- **Remaining**:
  - Backend와 Data B가 `candidate_classification` 규칙 및 `confirmed` 사건 재계산 입력을 교차 검토
  - 운영 배포 환경에서 실제 DART 키로 양사 1일 수집 smoke test 수행
  - 뉴스 collector는 후속 Backend 범위이며, 추가 시 동일 candidate/공식 확인 게이트를 사용
- **Blockers**:
  - 코드·자동 검증 blocker는 없음
  - 공유 규칙과 재계산 소비 경로의 역할 간 승인 전 `done` 처리 불가
- **Next task**: Backend/Data B 교차 리뷰 후 실제 DART smoke test와 수동 `/sync/issues` 런타임 E2E 검증

### 2026-07-26 — DATA-A-RT-01: DART Smoke Test 및 안전한 뉴스 Collector 기반 착수

- **Role**: Data A
- **Owner**: Data A
- **Status**: `in_progress`
- **Goal**:
  - 기존 production normalizer 기준선을 실제 DART 양사 수집으로 확인
  - 특정 뉴스 API를 아직 선택하지 않고도 사용할 수 있는 provider protocol, raw 저장, candidate 정규화·중복 제거 경계 구현
  - 뉴스만으로는 사건을 확정하거나 모델 재계산을 유발하지 않는 안전 게이트 검증
- **Allowed files**:
  - `src/backend/app/services/`
  - `src/backend/tests/`
  - `data/docs/issue_pipeline_contract.md`
  - `README.md`
  - `progress/DATA-A.md`
  - `ROADMAP.md`의 Data A 상태 노트
- **Do not modify**:
  - 기존 `data/processed/` 및 `data/candidate/` 기준 데이터
  - API/CSV 공유 스키마
  - 다른 역할 progress 및 루트 `PROGRESS.md`
- **Validation plan**:
  - 실제 DART 키 smoke test는 임시 디렉터리에서 실행하고 키·원문 응답을 출력하지 않음
  - 뉴스 raw→candidate 및 중복·오류 보존 단위 테스트
  - 뉴스 candidate→complete bundle 안전 게이트 통합 테스트
  - 전체 회귀, Data A bundle, compile, whitespace 검사
- **Blockers**: 실제 production 뉴스 제공자 선택은 후속 결정 사항이며 이번 작업의 provider-neutral 기반 구현을 막지 않음

### 2026-07-26 06:13 — DATA-A-RT-01: DART Production Smoke 및 뉴스 Collector 안전 기반 완료

- **Role**: Data A
- **Owner**: Data A
- **Status**: `review`
- **Completed**:
  - 키와 응답 본문을 출력하지 않고 임시 저장소만 사용하는 `scripts/smoke_dart_issue_collector.py` 추가
  - 실제 Open DART 양사 1일 smoke 성공: company batch 2개, 신규 공시 0건, raw artifact 2개 검증
  - 실제 Open DART 양사 7일 smoke 성공: candidate 102건, 모두 schema-valid `pending`, raw artifact 검증 통과
  - 102개 실제 후보를 production complete-bundle normalizer까지 실행해 전체 bundle 검증 통과
    - 기존 validated candidate 총계 6건 유지
    - 기존 rejected 3건 + 신규 일반 공시 rejected 102건 = 105건
    - 신규 사건 0건으로 오탐·모델 재계산 유발 없음 확인
  - provider-neutral `NewsProvider`, `NewsRawPage`, `NewsCollectionService` 계약 구현
  - 뉴스 응답을 정규화보다 먼저 raw에 원자 저장하고 이후 candidate CSV를 별도 저장
  - 기사 날짜·URL·host·canonical URL·content hash·batch 중복 검증 구현
  - provider가 요청과 다른 회사·검색어·기간을 반환하면 raw만 보존하고 candidate 생성을 중단
  - malformed 기사는 구체적 rejection reason과 함께 schema-valid candidate로 보존
  - 뉴스 candidate를 shared complete-bundle 입력으로 연결하는 `adapt_news_batch()` 추가
  - ESG 키워드가 일치하는 뉴스도 공식 근거 없이는 `official_confirmation_required`로 거절되고 사건·source·재계산을 생성하지 않는 통합 테스트 추가
- **Created files**:
  - `scripts/smoke_dart_issue_collector.py`
  - `src/backend/app/services/news_collection.py`
  - `src/backend/tests/test_news_collection.py`
- **Modified files**:
  - `src/backend/app/services/issue_bundle_normalizer.py`
  - `data/docs/issue_pipeline_contract.md`
  - `README.md`
  - `ROADMAP.md`
  - `progress/DATA-A.md`
- **Validation commands**:
  - `.venv\Scripts\python.exe scripts\smoke_dart_issue_collector.py --lookback-days 1`
  - `.venv\Scripts\python.exe scripts\smoke_dart_issue_collector.py --lookback-days 7`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_news_collection.py src/backend/tests/test_issue_bundle_normalizer.py src/backend/tests/test_issue_pipeline_contracts.py --disable-warnings`
  - `.venv\Scripts\python.exe scripts\validate_data_a.py`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests src/backend/tests --disable-warnings`
  - `.venv\Scripts\python.exe -m compileall -q src/backend/app src/modeling scripts\smoke_dart_issue_collector.py`
  - `git diff --check`
- **Validation results**:
  - 실제 DART API 연결·양사 raw 저장·candidate 정규화·complete bundle 검증 성공
  - 뉴스 collector 집중 테스트 `8 passed`
  - 뉴스·normalizer·공유 규칙 집중 테스트 `29 passed`(범위 fixture 교정 전 1건 탐지 후 수정)
  - Data A 기준 bundle PASS: candidate 9, source 15, event-source 7, event 6, ESG 72
  - 전체 회귀 `245 passed, 1 warning`
  - `optimization_grid_results.csv` 테스트 전후 SHA-256 동일
  - Python compile 및 whitespace 검사 통과(CRLF 변환 안내만 존재)
- **Remaining**:
  - Backend가 뉴스 collector adapter를 scheduler/manual workflow에 연결하는 방식 검토
  - Data B가 뉴스-only candidate가 재계산 입력에서 제외되는지 교차 승인
  - production 뉴스 제공자, 검색어, 호출 제한, 보존 가능 필드와 이용약관 승인
  - 제공자 승인 후 실제 API adapter 및 DART+뉴스 runtime E2E 추가
- **Blockers**:
  - provider-neutral 구현과 자동 검증 blocker는 없음
  - 실제 뉴스 호출은 제공자와 데이터 보존 정책 승인 전 연결하지 않음
- **Next task**: Backend/Data B 교차 리뷰 후 production 뉴스 provider 결정 및 adapter 구현

### 2026-07-26 06:24 — DATA-A-RT-01: DART 공시 원문 본문 수집 확장 착수

- **Role**: Data A
- **Owner**: Data A
- **Status**: `in_progress`
- **Reason**: 실제 DART 7일 후보 102건이 목록 제목·메타데이터만으로 모두 비사건 처리되어 본문 내 ESG 사건 누락 가능성을 확인
- **Official API contract**:
  - Open DART `GET /api/document.xml`
  - 입력: API 인증키, 14자리 접수번호
  - 출력: ZIP binary 원문 또는 오류 XML
- **Goal**:
  - 원문 ZIP을 candidate 변환 전에 raw에 저장하고 SHA-256 보존
  - ZIP path traversal·암호화·과도한 파일 수/압축 해제 크기를 차단
  - XML/HTML 본문을 텍스트로 변환하고 승인 분류 규칙 주변의 근거 구간만 candidate에 보존
  - 제목 일치 사건은 기존 confirmed 정책을 유지하되, 본문에서만 탐지한 사건은 `reported` 경고로 제한하여 Data B 재계산에서 제외
- **Do not modify**:
  - checked-in `data/processed/`와 `data/candidate/`
  - API/CSV 필드 계약
  - 다른 역할 progress 및 루트 `PROGRESS.md`
- **Validation plan**:
  - ZIP/XML 정상·오류·zip-slip·zip-bomb 단위 테스트
  - raw 저장 선행과 parser 실패 rejected 보존 테스트
  - body-only 사건이 reported이고 재계산 비대상인지 통합 테스트
  - 기존 공식 DART 접수번호 1건 실제 원문 smoke
  - 전체 회귀와 Data A bundle 불변 검증

### 2026-07-26 — DATA-A-RT-01: DART 공시 원문 본문 수집·분류 검증 완료

- **Role**: Data A
- **Owner**: Data A
- **Status**: `review`
- **Completed**:
  - Open DART `document.xml`에서 접수번호별 공식 원문 ZIP을 가져와 raw evidence로 먼저 보존하고 SHA-256을 기록하도록 구현.
  - ZIP을 파일시스템에 풀지 않고 XML/HTML/TXT 본문만 안전하게 추출하며 경로 탈출, 암호화 파일, 파일 수·압축 해제 크기·본문 길이 초과를 차단.
  - 제목용 `pattern`과 더 엄격한 본문용 `body_pattern`을 분리해 단순 지표명(`산업재해율`)이 사건으로 오인되지 않도록 보강.
  - 제목과 본문이 같은 ESG 사건 규칙에 일치하면 기존 `confirmed` 경로를 유지하고, 본문에서만 발견된 사건은 `reported`·비점수 경고로 제한.
  - 원문 미존재는 해당 candidate만 rejected로 보존하고, 인증·네트워크·호출 제한 등 시스템 오류는 회사 단위 발행을 중단해 last-known-good snapshot을 보호.
  - 실제 DART 접수번호 `20260626801398` 원문 smoke에서 ZIP 1,475 bytes, 본문 328자 추출, `OCCUPATIONAL_SAFETY` 분류 및 raw hash 검증 성공.
  - 최근 7일 운영 smoke에서 후보 102건의 공식 원문 ZIP 102개를 모두 저장·본문 추출했으며, 승인된 ESG 사건 본문 패턴 일치 0건과 신규 사건 0건을 확인.
- **Created files**:
  - `src/backend/tests/test_dart_documents.py`
- **Modified files**:
  - `src/backend/app/services/dart_disclosures.py`
  - `src/backend/app/services/issue_bundle_normalizer.py`
  - `src/backend/app/utils/issue_rules.py`
  - `schemas/data/issue-pipeline-rules.json`
  - `schemas/data/issue-pipeline-rules.schema.json`
  - `scripts/smoke_dart_issue_collector.py`
  - `data/docs/issue_pipeline_contract.md`
  - `README.md`
  - `ROADMAP.md`
  - `progress/DATA-A.md`
- **Validation commands**:
  - `.venv\Scripts\python.exe scripts\smoke_dart_issue_collector.py --document-receipt 20260626801398`
  - `.venv\Scripts\python.exe scripts\smoke_dart_issue_collector.py --lookback-days 7`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q src/backend/tests/test_dart_documents.py src/backend/tests/test_dart_disclosures.py src/backend/tests/test_issue_bundle_normalizer.py src/backend/tests/test_issue_pipeline_contracts.py --disable-warnings`
  - `.venv\Scripts\python.exe scripts\validate_data_a.py`
  - `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests src/backend/tests --disable-warnings`
  - `.venv\Scripts\python.exe -m compileall -q src/backend/app src/modeling scripts\smoke_dart_issue_collector.py`
  - `git diff --check`
- **Validation results**:
  - 실제 DART 원문 ZIP 저장·해시·본문 추출·분류 smoke 성공.
  - 최근 7일 DART: collected 102, document artifacts 102/102 valid, pending 0, rejected 102, added events 0.
  - 원문 수집·안전 추출·본문 분류 집중 테스트 포함 관련 테스트 `44 passed`.
  - Data A 기준 bundle PASS: candidate 9, source 15, event-source 7, event 6, ESG 72.
  - 전체 회귀 `256 passed, 1 warning`.
  - `optimization_grid_results.csv` 테스트 전후 SHA-256 동일.
  - Python compile 및 whitespace 검사 통과(CRLF 변환 안내만 존재).
- **Remaining**:
  - Backend/Data B가 `reported` 본문-only 경고의 API 노출과 점수 제외를 교차 검토.
  - production 뉴스 provider 선정·승인 후 동일 candidate/공식 확인 gate에 연결.
- **Blockers**:
  - 구현·자동 검증 blocker는 없음.
  - 공유 분류 규칙과 모델 소비 경로 교차 승인 전에는 `done` 처리 불가.
- **Next task**: Backend/Data B 교차 검토 후 DART+뉴스 runtime E2E를 수행하고 production 뉴스 provider를 결정.
