# Project Progress

## 1. Current Status

- Project phase: Pre-Development Review
- Overall status: `in_progress`
- Last updated: 2026-07-21
- Current integration checkpoint: `CHECKPOINT-01`
- Data mode: `sample`
- Root progress owner: Team Lead

> 루트 `PROGRESS.md`는 프로젝트 전체 요약 문서이며 팀 리드만 수정한다.  
> 팀원별 상세 작업 기록은 각 역할의 `progress/*.md`에 작성한다.

---

## 2. Role Progress Files

| Role | Progress File | Editor |
|---|---|---|
| Data A | `progress/DATA-A.md` | Data A 담당자 |
| Data B | `progress/DATA-B.md` | Data B 담당자 |
| Backend | `progress/BACKEND.md` | Backend 담당자 |
| Frontend | `progress/FRONTEND.md` | Frontend 담당자 |
| Integration | `progress/INTEGRATION.md` | Team Lead 또는 통합 담당자 |

팀원은 다른 역할의 진행 파일과 루트 `PROGRESS.md`를 직접 수정하지 않는다.

---

## 3. Allowed Status Values

아래 상태값만 사용한다.

- `todo`
- `in_progress`
- `blocked`
- `review`
- `done`

| Status | Meaning |
|---|---|
| `todo` | 아직 시작하지 않음 |
| `in_progress` | 담당자가 현재 작업 중 |
| `blocked` | 외부 작업이나 결정이 필요해 진행 불가 |
| `review` | 산출물은 있으나 다른 역할의 검토 필요 |
| `done` | 완료 조건과 검증을 모두 통과 |

---

## 4. Overall Task Status

### Common Setup

| Task ID | Task | Owner | Status | Output | Next Action |
|---|---|---|---|---|---|
| COMMON-01 | Repository Setup | Team Lead | `done` | 루트 문서·환경 파일 | 유지 |
| COMMON-02 | Shared Schema Definition | Team Lead | `review` | 데이터·API 스키마 | 역할별 검토 |
| COMMON-03 | Sample Data Preparation | Backend | `review` | 샘플 CSV·JSON | 역할별 검토 |

### Data A

| Task ID | Task | Status | Dependency |
|---|---|---|---|
| DATA-A-01 | ESG Indicator Definition | `todo` | COMMON-02 승인 |
| DATA-A-02 | Official Report Collection | `todo` | DATA-A-01 |
| DATA-A-03 | ESG Value Review | `todo` | DATA-A-02 |
| DATA-A-04 | Event Dataset | `todo` | DATA-A-02 |
| DATA-A-05 | Final Data Quality Review | `todo` | DATA-A-03, DATA-A-04 |

### Data B

| Task ID | Task | Status | Dependency |
|---|---|---|---|
| DATA-B-01 | Price Data Validation | `todo` | COMMON-02 승인 |
| DATA-B-02 | Downside Risk Functions | `todo` | DATA-B-01 |
| DATA-B-03 | Optimization Engine | `todo` | DATA-B-02, COMMON-03 승인 |
| DATA-B-04 | Event Reaction Function | `todo` | DATA-B-01, COMMON-03 승인 |
| DATA-B-05 | Real Data Integration | `todo` | DATA-A-05, DATA-B-03, DATA-B-04 |
| DATA-B-06 | Sensitivity Check | `todo` | DATA-B-05 |

### Backend

| Task ID | Task | Status | Dependency |
|---|---|---|---|
| BE-01 | FastAPI Skeleton | `todo` | COMMON-01 |
| BE-02 | Data Loader and Validation | `todo` | COMMON-02·03 승인 |
| BE-03 | Mock API | `todo` | BE-01, BE-02 |
| BE-04 | Real Data Integration | `todo` | DATA-A-05, BE-02 |
| BE-05 | Model Integration | `todo` | DATA-B-05, BE-03 |
| BE-06 | Fallback and Contract Tests | `todo` | BE-04, BE-05 |

### Frontend

| Task ID | Task | Status | Dependency |
|---|---|---|---|
| FE-01 | Stitch UI Drafts | `todo` | COMMON-02 승인 |
| FE-02 | Frontend Skeleton | `todo` | FE-01 |
| FE-03 | Mock Data Integration | `todo` | COMMON-03 승인, FE-02 |
| FE-04 | Real API Integration | `todo` | BE-03, FE-03 |
| FE-05 | Issues and Event Analysis | `todo` | DATA-B-04, BE-03 |
| FE-06 | Mobile and State Testing | `todo` | FE-04, FE-05 |

### Integration

| Task ID | Task | Status | Dependency |
|---|---|---|---|
| INT-01 | End-to-End Test | `todo` | DATA-B-05, BE-05, FE-04 |
| INT-02 | Data and Model Review | `todo` | DATA-A-05, DATA-B-06 |
| INT-03 | Demo Preparation | `todo` | INT-01, INT-02 |

---

## 5. Current Checkpoint

### CHECKPOINT-01 — Initial Parallel-Work Readiness

완료된 항목:

- [x] `README.md`
- [x] `AGENTS.md`
- [x] `ROADMAP.md`
- [x] `PROGRESS.md`
- [x] `.gitignore`
- [x] `.env.example`
- [x] Task ID와 역할 정의
- [x] 공통 enum 정의
- [x] ESG 데이터 스키마
- [x] 사건 데이터 스키마
- [x] 가격 데이터 스키마
- [x] 최적화 API 요청 스키마
- [x] 최적화 API 응답 스키마
- [x] API 요청·응답 예시
- [x] 샘플 ESG CSV
- [x] 샘플 사건 CSV
- [x] 샘플 가격 CSV
- [x] 샘플 최적화 결과 JSON
- [x] 자동 형식 검증

남은 항목:

- [ ] Data A 검토
- [ ] Data B 검토
- [ ] Backend 검토
- [ ] Frontend 검토
- [ ] 수정 요청 반영
- [ ] COMMON-02 `done`
- [ ] COMMON-03 `done`
- [ ] 역할별 진행 파일 생성
- [ ] 병렬 작업 시작

### Checkpoint Pass Condition

다음 조건을 모두 만족하면 `CHECKPOINT-01`을 통과한다.

1. 네 역할이 COMMON-02와 COMMON-03을 승인한다.
2. 샘플 파일이 담당 작업에 필요한 정보를 포함한다.
3. 스키마·샘플 간 열과 필드가 일치한다.
4. 수정 요청이 모두 해결된다.
5. 네 역할이 다른 담당자의 실제 산출물을 기다리지 않고 작업을 시작할 수 있다.

---

## 6. COMMON-02 Review

### Review Targets

```text
schemas/data/data-enums.yaml
schemas/data/esg-indicators.schema.json
schemas/data/events.schema.json
schemas/data/stock-prices.schema.json

schemas/api/portfolio-optimize-request.schema.json
schemas/api/portfolio-optimize-response.schema.json

schemas/api/examples/portfolio-optimize-request.example.json
schemas/api/examples/portfolio-optimize-response.example.json
```

### Review Checklist

| Reviewer | Review Focus | Result | Notes |
|---|---|---|---|
| Data A | 실제 ESG·사건 데이터를 입력할 수 있는가 | `pending` | |
| Data B | 위험·최적화 계산에 필요한 필드가 있는가 | `pending` | |
| Backend | 스키마 검증과 API 구현이 가능한가 | `pending` | |
| Frontend | 응답 JSON만으로 화면 구현이 가능한가 | `pending` | |

허용 결과:

- `approved`
- `changes_requested`

### Approval Condition

COMMON-02는 다음 조건에서만 `done`으로 변경한다.

- 네 역할 모두 `approved`
- 데이터 enum과 스키마 허용값 일치
- API 예시가 요청·응답 스키마 통과
- 수정 요청이 모두 해결됨
- `ROADMAP.md`와 이 문서의 상태가 일치함

---

## 7. COMMON-03 Review

### Review Targets

```text
data/sample/esg_indicators.sample.csv
data/sample/events.sample.csv
data/sample/stock_prices.sample.csv
data/sample/optimization-result.sample.json
data/sample/sample-validation-report.json
```

### Current Validation Results

- ESG CSV 헤더와 ESG 스키마 필수 필드: `passed`
- 사건 CSV 헤더와 사건 스키마 필수 필드: `passed`
- 가격 CSV 헤더와 가격 스키마 필수 필드: `passed`
- 최적화 결과 JSON과 API 응답 스키마: `passed`

### Role Review Checklist

| Reviewer | Review Focus | Result | Notes |
|---|---|---|---|
| Data A | 샘플 ESG·사건 데이터를 실제 수집 형식으로 사용할 수 있는가 | `pending` | |
| Data B | 샘플 ESG·사건·가격 데이터로 계산 함수를 만들 수 있는가 | `pending` | |
| Backend | 샘플 파일을 로드하고 검증할 수 있는가 | `pending` | |
| Frontend | 최적화 결과 JSON으로 핵심 화면을 만들 수 있는가 | `pending` | |

COMMON-03은 네 역할의 검토가 끝난 뒤 `done`으로 변경한다.

---

## 8. Active Blockers

| Blocker ID | Related Task | Description | Owner | Required Action | Status |
|---|---|---|---|---|---|
| - | - | 현재 등록된 차단 요소 없음 | - | - | - |

---

## 9. Immediate Next Actions

팀 회의에서 아래 순서로 진행한다.

1. COMMON-02 산출물을 역할별로 검토한다.
2. COMMON-03 샘플 파일을 역할별로 열어본다.
3. 누락 필드나 이해하기 어려운 필드를 기록한다.
4. 각 역할이 `approved` 또는 `changes_requested`를 선택한다.
5. 수정 요청이 있으면 Team Lead가 공통 스키마를 수정한다.
6. 네 역할 모두 승인하면 COMMON-02와 COMMON-03을 `done`으로 변경한다.
7. 역할별 진행 파일을 생성한다.
8. 다음 작업을 동시에 `in_progress`로 변경한다.

병렬 시작 작업:

```text
DATA-A-01 — ESG Indicator Definition
DATA-B-01 — Price Data Validation
BE-01     — FastAPI Skeleton
FE-01     — Stitch UI Drafts
```

---

## 10. Team Lead Update Rules

팀 리드는 다음 시점에 이 파일을 갱신한다.

- PR이 `main`에 병합된 후
- COMMON 작업 승인 후
- 통합 체크포인트 통과 후
- 프로젝트 전체 차단 요소 발생 시
- Day 1 종료 시
- Day 2 종료 시
- 최종 데모 준비 완료 시

팀원의 상세 작업 로그를 이 파일에 복사하지 않는다. 루트 문서에는 상태·산출물·차단 요소·다음 통합 작업만 기록한다.

---

## 11. Final Completion Summary

프로젝트 종료 시 아래 내용을 작성한다.

- 완료된 Must 기능
- 제외된 Should 기능
- 최종 데이터 상태
- 실제 사용한 ESG 지표
- 최종 모델 설정
- 추천 비중 제약
- 테스트 결과
- 알려진 제한사항
- 데모 입력값
- 데모 결과
- 폴백 경로
- 최종 발표 자료 위치
