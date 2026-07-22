# Data B Progress Log

## Task Status

| Task ID | Task | Status | Output | Blocker |
|---|---|---|---|---|
| DATA-B-01 | Price Data Validation | `done` | src/modeling/price.py | - |
| DATA-B-02 | Downside Risk Functions | `done` | src/modeling/downside.py | - |
| DATA-B-03 | Optimization Engine | `done` | src/modeling/optimizer.py, config/* | - |
| DATA-B-04 | Event Reaction Function | `done` | src/modeling/events.py | - |
| DATA-B-05 | Real Data Integration | `done` | src/modeling/esg.py, run_pipeline.py | - |
| DATA-B-06 | Sensitivity Check | `done` | src/modeling/sensitivity.py, data/processed/* | - |

## Active Blockers

| Blocker ID | Related Task | Description | Owner | Required Action | Status |
|---|---|---|---|---|---|
| - | - | 현재 없음 | - | - | - |

## Work Log

### 2026-07-21 10:00 — Initial Setup

- **Role**: Data B
- **Status**: `todo`
- **Completed**: 폴더 구조 뼈대 설정 및 Data B 진행 문서 생성 완료.
- **Created files**:
  - `progress/DATA-B.md`
- **Next task**: COMMON-02 (Shared Schema) 검토 진행 및 승인.

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
- **Next recommended task**: 개발 A(Backend/Frontend)에게 최종 모듈 함수 및 JSON 출력 연동 넘기기 (`BE-05` 및 `FE-04` 통합 검수)
