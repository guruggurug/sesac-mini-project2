# Project Roadmap

## Project Goal
삼성전자와 SK하이닉스의 ESG 관리위험과 가격 하방위험을 함께 분석하여, 두 종목 안에서 상대적으로 덜 취약한 추천 보유 비중을 계산하고 모바일 대시보드로 보여주는 2일 MVP 프로젝트 완성.

## MVP Completion Criteria
- **데이터 검증**: 삼성전자와 SK하이닉스에 대해 검수 완료된 ESG 데이터 및 주가 데이터 검증 통과.
- **모델 구현**: Historical CVaR 95% 및 ESG 관리위험, 턴오버 페널티를 결합한 20%~80% 비중 제약조건의 1% 그리드서치 최적화 엔진 구현.
- **백엔드 구축**: FastAPI 기반의 포트폴리오 계산, 최적화, 이슈 조회 API 제공 및 적절한 에러/폴백 처리.
- **프론트엔드 구축**: 모바일 390px 뷰포트에 최적화된 대시보드 화면 및 입력 폼, 로딩/오류/폴백/샘플 데이터 상태 처리 구현.
- **통합 검증**: 입력 변경에 따른 추천 비중의 실시간 재계산 및 과거 사건 주가 영향 분석 화면 완성.

## Team Roles
- **Data A**: ESG 지표 정의, 공식 보고서 수집, ESG 값 검증, 사건 후보 검토 및 공식 출처 확인 (`esg_indicators.csv`, `events.csv`, `sources.csv` 담당)
- **Data B**: 가격 데이터 검증, 수익률 계산, Historical CVaR, MDD, 하방편차, ESG 위험 집계, 턴오버 페널티 최적화 엔진, 과거 사건 영향 분석 담당
- **Backend**: FastAPI 프로젝트 뼈대 구축, 데이터 로더 및 검증기, API 스키마, 레포지토리/서비스, 모델 함수 통합, 에러/폴백 처리, OpenAPI 문서화 담당
- **Frontend**: Stitch UI 시안 통합, 모바일 사용자 흐름, API 연동, 로딩/오류/빈/샘플/폴백 상태 UI, 반응형(모바일 우선) 레이아웃 담당

## Day 1 Tasks
- [x] COMMON-01: Repository Setup (팀 리드)
- [x] COMMON-02: Shared Schema Definition (팀 리드)
- [x] COMMON-03: Sample Data Preparation (Backend)
- [x] BE-01: FastAPI Skeleton
- [x] FE-01: Stitch UI Drafts
- [x] DATA-A-01: ESG Indicator Definition
- [x] DATA-A-02: Official Report Collection
- [x] DATA-B-01: Price Data Validation
- [x] DATA-B-02: Downside Risk Functions
- [x] BE-02: Data Loader and Validation
- [x] FE-02: Frontend Skeleton
- [x] FE-03: Mock Data Integration
- [x] BE-03: Mock API

## Day 2 Tasks
- [x] DATA-A-03: ESG Value Review
- [x] DATA-A-04: Event Dataset
- [x] DATA-B-03: Optimization Engine
- [x] DATA-B-04: Event Reaction Function
- [x] DATA-A-05: Final Data Quality Review
- [x] DATA-B-05: Real Data Integration
- [x] DATA-B-06: Sensitivity Check
- [x] BE-04: Real Data Integration
- [x] BE-05: Model Integration
- [x] BE-06: Fallback and Contract Tests
- [x] FE-04: Real API Integration
- [x] FE-05: Issues and Event Analysis
- [x] FE-06: Mobile and State Testing
- [ ] INT-01: End-to-End Test
- [x] INT-02: Data and Model Review
- [ ] INT-03: Demo Preparation

## Integration Checkpoints
- **CHECKPOINT-01 (Day 1 시작)**: Initial Parallel-Work Readiness (공통 스키마 및 샘플 데이터 합의) - *완료*
- **CHECKPOINT-02 (Day 1 종료)**: Mock-Based End-to-End Verification (Mock API 기반 프론트-백 연동 완료) - *완료*
- **CHECKPOINT-03 (Day 2 중간)**: Real Data & Model Integration (실제 데이터 및 최적화 엔진 백엔드 통합 완료) - *완료*
- **CHECKPOINT-04 (Day 2 종료)**: Final Production QA & Demo Ready (E2E 테스트, 예외/폴백 처리 완료 및 최종 데모 검증 완료) - *진행 중*

## Priority

### Must
- 삼성전자 및 SK하이닉스 대상의 ESG 지표(E, S, G 항목별 정량/정성 점수) 수집 및 검수.
- Historical CVaR 95% 계산 로직 및 20%~80% 제약조건의 1% 그리드서치 최적화 모델.
- 모바일(390px) 화면에서 포트폴리오 입력, 추천 비중 비교 및 추천 사유 제시.
- API 요청/응답 형식의 스키마 정합성 보장.

### Should
- ESG 등급이나 점수 산정 시 business_scope가 consolidated인 경우 scope_mismatch 경고 노출.
- 과거 주요 반도체 산업 사건(이슈) 발생 전후 1, 3, 5일 수익률 분석 기능.
- 모바일 UI에서 로딩 상태 및 API 실패 시 폴백(샘플 데이터 모드 전환) 안내.

### Drop First
- 2개 초과 다종목 포트폴리오 확장.
- Black-Litterman 등 고도화된 최적화 기법 적용.
- 실시간 주가 API 연동 (배치성/고정 시계열 데이터 사용 가능).
- 로그인 및 회원가입 기능.

## Current Blockers
- 현재 등록된 차단 요소 없음.

## Final Demo Flow
1. **투자 성향/우선순위 설정**: 사용자가 ESG 위험 가중치, 가격 하방위험 가중치 등을 조정하거나 선택.
2. **보유 정보 입력**: 삼성전자와 SK하이닉스의 현재 보유 수량과 평단가를 입력.
3. **현재 상태 진단**: 현재 보유 비중, 포트폴리오 통합 ESG 위험도, 가격 하방위험(CVaR) 수준 확인.
4. **추천 비중 비교**: 최적화 엔진에 의해 제안된 추천 비중(20%~80% 범위 내)과 현재 비중을 그래프 및 수치로 비교.
5. **위험 감소율 및 사유**: 추천 비중으로 변경 시 예상되는 위험 감소 효과 및 상세 정성적 추천 사유 조회.
6. **과거 사건 분석**: 반도체 산업의 역사적 사건(예: 규제, 제재 등) 전후의 두 종목 주가 흐름 및 반응 분석 제공.
7. **보유 정보 수정**: 입력값을 수정하여 실시간으로 진단 결과가 재계산되는 흐름 검증.
