# Project Progress

## 1. Current Status

- Project phase: Realtime Market & Daily Issue Sync Contract Review
- Overall status: `in_progress`
- Project duration: 4 days
- Last updated: 2026-07-22 04:15 KST
- Current integration checkpoint: `CHECKPOINT-05`
- Data mode: `validated` (Fallback: `sample`)
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
| COMMON-02 | Shared Schema Definition | Team Lead | `done` | 데이터·API 스키마 | 검토 완료 및 합의 |
| COMMON-03 | Sample Data Preparation | Backend | `done` | 샘플 CSV·JSON | 검토 완료 및 합의 |

### Data A

| Task ID | Task | Status | Dependency |
|---|---|---|---|
| DATA-A-01 | ESG Indicator Definition | `done` | COMMON-02 승인 |
| DATA-A-02 | Official Report Collection | `done` | DATA-A-01 |
| DATA-A-03 | ESG Value Review | `done` | DATA-A-02 |
| DATA-A-04 | Event Dataset | `done` | DATA-A-02 |
| DATA-A-05 | Final Data Quality Review | `done` | DATA-A-03, DATA-A-04 |

### Data B

| Task ID | Task | Status | Dependency |
|---|---|---|---|
| DATA-B-01 | Price Data Validation | `done` | COMMON-02 승인 |
| DATA-B-02 | Downside Risk Functions | `done` | DATA-B-01 |
| DATA-B-03 | Optimization Engine | `done` | DATA-B-02, COMMON-03 승인 |
| DATA-B-04 | Event Reaction Function | `done` | DATA-B-01, COMMON-03 승인 |
| DATA-B-05 | Real Data Integration | `done` | DATA-A-05, DATA-B-03, DATA-B-04 |
| DATA-B-06 | Sensitivity Check | `done` | DATA-B-05 |

### Backend

| Task ID | Task | Status | Dependency |
|---|---|---|---|
| BE-01 | FastAPI Skeleton | `done` | COMMON-01 |
| BE-02 | Data Loader and Validation | `done` | COMMON-02·03 승인 |
| BE-03 | Mock API | `done` | BE-01, BE-02 |
| BE-04 | Real Data Integration | `done` | DATA-A-05, BE-02 |
| BE-05 | Model Integration | `done` | DATA-B-05, BE-03 |
| BE-06 | Fallback and Contract Tests | `done` | BE-04, BE-05 |

### Frontend

| Task ID | Task | Status | Dependency |
|---|---|---|---|
| FE-01 | Stitch UI Drafts | `done` | COMMON-02 승인 |
| FE-02 | Frontend Skeleton | `done` | FE-01 |
| FE-03 | Mock Data Integration | `done` | COMMON-03 승인, FE-02 |
| FE-04 | Real API Integration | `done` | BE-03, FE-03 |
| FE-05 | Issues and Event Analysis | `done` | DATA-B-04, BE-03 |
| FE-06 | Mobile and State Testing | `done` | FE-04, FE-05 |

### Integration

| Task ID | Task | Status | Dependency |
|---|---|---|---|
| INT-01 | End-to-End Test | `in_progress` | DATA-B-05, BE-05, FE-04 |
| INT-02 | Data and Model Review | `done` | DATA-A-05, DATA-B-06 |
| INT-03 | Demo Preparation | `todo` | INT-01, INT-02 |

### Day 3-4 Realtime & Daily Sync

| Task ID | Task | Status | Dependency |
|---|---|---|---|
| COMMON-RT-01 | Realtime and Daily Sync Requirements Definition | `done` | Team Lead decision |
| COMMON-RT-02 | Market, Portfolio Summary and Sync API Contract Review | `review` | Data A review and Data B, Backend, Frontend explicit approval required |
| COMMON-RT-03 | Human Review Removal and Automated Validation Contract Migration | `done` | Team Lead realtime pipeline decision |
| BE-RT-00 | ESG Schema Validator and Sample Contract Compatibility Recovery | `done` | Updated ESG·event schemas |
| INT-RT-01 | Market·Portfolio·Daily Sync End-to-End Test | `todo` | COMMON-RT-02 and Realtime role implementations |

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
- [x] Data A 검토 및 승인 완료 (`approved`)
- [x] Data B 검토 및 승인 완료 (`approved`)
- [x] Backend 검토 및 승인 완료 (`approved`)
- [x] Frontend 검토 및 승인 완료 (`approved`)
- [x] COMMON-02 `done` 및 스키마 합의 완료
- [x] COMMON-03 `done` 및 샘플 데이터 합의 완료
- [x] 역할별 진행 파일 생성 및 병렬 작업 가동

남은 항목 없음 (체크포인트 1 통과 완료)

### CHECKPOINT-02 & CHECKPOINT-03 — Mock-Based E2E & Real Data/Model Integration

완료된 항목:

- [x] FastAPI 백엔드 뼈대 세팅 및 라우터 분리 (`BE-01`)
- [x] 데이터 로더 및 스키마 기반 유효성 검증기 완성 (`BE-02`)
- [x] HTMX 및 Jinja2 템플릿 기반 모바일 최적화 화면 UI 뼈대 작성 (`FE-02`)
- [x] 클라이언트 사이드 Mock 계산 시뮬레이션 및 API 통신 연결 (`FE-03`)
- [x] 데이터 A의 실제 검증 완료 ESG 및 역사적 사건 데이터 구축 완료 (`DATA-A-01~05`)
- [x] 데이터 B의 일별 가격 검증, CVaR 계산, 1% 그리드서치 최적화 모델 탑재 완료 (`DATA-B-01~04`)
- [x] 실제 데이터 검증 결과 로드 및 모델과의 API 통합 처리 완료 (`BE-04`, `BE-05`)
- [x] yfinance 기반 실시간 주가 동적 병합 및 데이터 결손 시 폴백 안전 장치 추가 (`BE-06`)

남은 항목 없음 (체크포인트 2, 3 통과 완료)

### CHECKPOINT-04 — Final Production QA & Demo Ready

완료된 항목:
- [x] 실데이터 연동 및 최적화 엔진 통합 구현
- [x] 390px 뷰포트 기반 모바일 UI 및 로딩/에러 피드백 상태 검증
- [x] 데이터 검증 및 최적화 모델 유닛 테스트 통과 (100% Pass)

남은 항목:
- [ ] 서버 실구동 E2E 통합 테스트 검증 (`INT-01`)
- [ ] 투자 성향/보유 정보 입력 변경에 따른 추천 비중 실시간 재계산 흐름 최종 데모 준비 (`INT-03`)

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
| Data A | 실제 ESG·사건 데이터를 입력할 수 있는가 | `approved` | 스키마 적합 확인 |
| Data B | 위험·최적화 계산에 필요한 필드가 있는가 | `approved` | 필요 연산 변수 포괄 확인 |
| Backend | 스키마 검증과 API 구현이 가능한가 | `approved` | Pydantic 및 JSON 검증 가능 |
| Frontend | 응답 JSON만으로 화면 구현이 가능한가 | `approved` | UI 표출 요구사항 부합 |

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
| Data A | 샘플 ESG·사건 데이터를 실제 수집 형식으로 사용할 수 있는가 | `approved` | 실데이터 입력 전환 용이 |
| Data B | 샘플 ESG·사건·가격 데이터로 계산 함수를 만들 수 있는가 | `approved` | 모델 연산 정상 동작 확인 |
| Backend | 샘플 파일을 로드하고 검증할 수 있는가 | `approved` | CSV 로더 연동 확인 |
| Frontend | 최적화 결과 JSON으로 핵심 화면을 만들 수 있는가 | `approved` | 렌더링 검증 완료 |

---

## 7.5 COMMON-RT-02 Contract Review

### Review Targets

```text
schemas/data/data-enums.yaml
schemas/api/README.md
schemas/api/market-quotes-response.schema.json
schemas/api/portfolio-summary-request.schema.json
schemas/api/portfolio-summary-response.schema.json
schemas/api/sync-issues-request.schema.json
schemas/api/sync-status-response.schema.json
schemas/api/examples/market-quotes-response.example.json
schemas/api/examples/portfolio-summary-request.example.json
schemas/api/examples/portfolio-summary-response.example.json
schemas/api/examples/sync-issues-request.example.json
schemas/api/examples/sync-status-response.example.json
```

### Current Validation Results

- JSON Schema Draft 2020-12 자체 검증: `passed`
- 시장 가격·포트폴리오·동기화 예시 계약 검증: `passed`
- 필수 4개 시장 항목 및 중복 종목 차단 검증: `passed`
- 포트폴리오 합계·비중 산술 정합성 검증: `passed`
- 동기화 상태별 시작·완료 시각 규칙 검증: `passed`
- 사람 검수 필드 제거, `processed/validated` 로딩과 자동 사건 필터 검증: `passed`
- 사건 상태·제재 결과 분리, ESG unavailable/null, 동기화 단계·발행 증거 계약: `passed`
- fallback 가격의 `is_stale=true` 강제와 재계산 트리거 계약: `passed`
- 계약·이슈 파이프라인 집중 테스트: `23 passed`
- 전체 회귀 테스트: `passed` (`59 tests collected`)

### Role Review Checklist

| Reviewer | Review Focus | Result | Notes |
|---|---|---|---|
| Data A | raw→candidate→자동 검증→processed 경계와 출처 보존 | `review` | 보완 산출물은 있으나 unavailable 18행, Backend 발행 게이트와 Data B 교차 검토가 남음 |
| Data B | 자동 검증 통과 이벤트 이후 ESG·추천 비중 재계산 트리거 | `pending` | 역할 로그에 COMMON-RT-02 검토·승인 기록 없음 |
| Backend | 가격 캐시·동기화 잠금·상태 전이·오류 구현 가능성 | `pending` | 역할 로그에 COMMON-RT-02 검토가 Remaining으로 기록됨 |
| Frontend | 폴링·기준 시각·지연/폴백·동기화 상태 표현 가능성 | `pending` | 역할 로그에 Realtime 계약 검토·승인 기록 없음 |

`COMMON-RT-02`는 계약 초안과 자동 검증은 통과했지만 역할별 명시적 승인이 완료되지 않아 `review` 상태다.

---

## 8. Active Blockers

| Blocker ID | Related Task | Description | Owner | Required Action | Status |
|---|---|---|---|---|---|
| RT-B01 | COMMON-RT-02 | Data A 보완 검토와 Data B·Backend·Frontend의 명시적 계약 승인이 필요 | Team Lead / All Roles | 역할별 로그에 검토 결과와 승인 기록 | `review` |
| RT-B02 | DATA-B-RT-01 | Data B 동적 ESG·최적화 변경이 현재 브랜치에 미동기화 | Data B | 작업 완료 후 통합 브랜치 동기화 | `in_progress` |

---

## 9. Immediate Next Actions

1. Data A, Data B, Backend, Frontend가 `COMMON-RT-02` 계약을 각 역할 로그에서 검토하고 명시적으로 승인한다.
2. Data A 잔여 데이터 조건과 Data B·Backend·Frontend 구현 관점의 계약 쟁점을 반영한다.
3. 기존 `INT-01`과 신규 `INT-RT-01`의 E2E 범위를 통합한다.

---

## 10. Team Lead Update Rules

팀 리드는 다음 시점에 이 파일을 갱신한다.

- PR이 `main`에 병합된 후
- COMMON 작업 승인 후
- 통합 체크포인트 통과 후
- 프로젝트 전체 차단 요소 발생 시
- Day 1 종료 시
- Day 2 종료 시
- Day 3 종료 시
- Day 4 종료 시
- 최종 데모 준비 완료 시

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
