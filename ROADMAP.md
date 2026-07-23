# Project Roadmap

## Project Goal
삼성전자와 SK하이닉스의 ESG 관리위험과 가격 하방위험을 함께 분석하고, 장중 시장 가격과 매일 갱신되는 공시·뉴스·ESG 이슈를 반영하여 두 종목 안에서 상대적으로 덜 취약한 추천 보유 비중과 실시간 자산 상태를 보여주는 4일 모바일 대시보드 MVP 완성.

## MVP Completion Criteria
- **데이터 검증**: 삼성전자와 SK하이닉스 ESG·주가 데이터가 자동 스키마·출처 검증을 통과.
- **모델 구현**: Historical CVaR 95% 및 ESG 관리위험, 턴오버 페널티를 결합한 20%~80% 비중 제약조건의 1% 그리드서치 최적화 엔진 구현.
- **백엔드 구축**: FastAPI 기반의 포트폴리오 계산, 최적화, 이슈 조회 API 제공 및 적절한 에러/폴백 처리.
- **프론트엔드 구축**: 모바일 390px 뷰포트에 최적화된 대시보드 화면 및 입력 폼, 로딩/오류/폴백/샘플 데이터 상태 처리 구현.
- **통합 검증**: 입력 변경에 따른 추천 비중의 실시간 재계산 및 과거 사건 주가 영향 분석 화면 완성.
- **시장 가격 갱신**: 홈에서 코스피·코스닥·삼성전자·SK하이닉스의 현재값, 전일 대비, 등락률과 조회 시각을 장중 10~30초 간격으로 표시.
- **실시간 자산 평가**: 삼성전자·SK하이닉스 현재가를 종목별 평가액, 총 자산 평가액, 평가손익과 현재 비중에 즉시 반영.
- **일일·수동 이슈 동기화**: 공시·뉴스·ESG 이슈를 하루 한 번 자동 동기화하고 사용자가 요청하면 추가 동기화하며, 자동 검증 통과 사건 또는 상태 변경 후 ESG 위험과 추천 비중을 재계산.
- **동기화 안정성**: 중복 실행 방지, 갱신 상태와 기준 시각 표시, 외부 API 실패 시 마지막 정상 데이터 폴백 검증.

## Team Roles
- **Data A**: ESG 지표 정의, 공식 보고서 수집, ESG 값 검증, 일일 공시·뉴스 수집 규칙, 사건 후보 분류·중복 판정, 공식 출처와 상태 확인 (`esg_indicators.csv`, `events.csv`, `sources.csv` 담당)
- **Data B**: 가격 데이터 검증, 수익률 계산, Historical CVaR, MDD, 하방편차, ESG 위험 집계, 자동 검증 통과 사건·상태 변경 후 위험 재계산, 턴오버 페널티 최적화 엔진, 과거 사건 영향 분석 담당
- **Backend**: FastAPI 프로젝트 뼈대, 시장 가격 서비스·캐시, 일일 스케줄러, 사용자 수동 동기화, 동시 실행 잠금, 데이터 로더·검증기, 모델 통합, 에러·폴백, OpenAPI 문서화 담당
- **Frontend**: Stitch UI 시안 통합, 홈 시장 현황, 실시간 총 자산 평가, 이슈 새로고침·동기화 상태, API 연동, 로딩·오류·빈·샘플·폴백 상태, 모바일 우선 레이아웃 담당

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

## Day 3-4 Realtime & Daily Sync Tasks

- [x] COMMON-RT-01: Realtime and Daily Sync Requirements Definition (팀 리드)
- [ ] COMMON-RT-02: Market, Portfolio Summary and Sync API Contract Review (팀 리드, 전 역할 승인 필요)
- [x] COMMON-RT-03: Human Review Removal and Automated Validation Contract Migration (팀 리드)
- [ ] DATA-A-RT-01: Daily Disclosure and News Source·Classification·Deduplication Rules
- [ ] DATA-A-RT-02: Candidate Data Quality and Event Status Validation
- [ ] DATA-B-RT-01: ESG Recalculation After Approved Event or Status Change
- [ ] DATA-B-RT-02: Optimization Recalculation and Explanation Integration
- [x] BE-RT-00: ESG Schema Validator and Sample Contract Compatibility Recovery
- [ ] BE-RT-01: KOSPI·KOSDAQ·Samsung·SK hynix Market Quote Service and Cache
- [ ] BE-RT-02: Realtime Portfolio Valuation and Current Weight API
- [ ] BE-RT-03: Daily Issue Scheduler, Manual Sync, Lock and Status API
- [ ] BE-RT-04: Last-Known-Good Market and Issue Fallback
- [ ] FE-RT-01: Home Market Overview and 10~30 Second Refresh
- [ ] FE-RT-02: Realtime Total Asset Value·P/L·Current Weight
- [ ] FE-RT-03: Issue Manual Refresh and Sync Status UI
- [x] FE-RT-04: Stitch Static Tailwind CSS Build
- [ ] INT-RT-01: Market·Portfolio·Daily Sync End-to-End Test

`COMMON-RT-02` 계약과 검증 예시는 `schemas/api/README.md`, `schemas/api/*summary*.schema.json`, `schemas/api/market-quotes-response.schema.json`, `schemas/api/sync-*.schema.json`, `schemas/api/examples/`에 작성되었다. 계약 테스트는 통과했지만 Data A는 `review`, Data B·Backend·Frontend는 `pending`이므로 전 역할 승인 전까지 `review`를 유지한다.

## Integration Checkpoints
- **CHECKPOINT-01 (Day 1 시작)**: Initial Parallel-Work Readiness (공통 스키마 및 샘플 데이터 합의) - *완료*
- **CHECKPOINT-02 (Day 1 종료)**: Mock-Based End-to-End Verification (Mock API 기반 프론트-백 연동 완료) - *완료*
- **CHECKPOINT-03 (Day 2 중간)**: Real Data & Model Integration (실제 데이터 및 최적화 엔진 백엔드 통합 완료) - *완료*
- **CHECKPOINT-04 (Day 2 종료)**: Final Production QA & Demo Ready (E2E 테스트, 예외/폴백 처리 완료 및 최종 데모 검증 완료) - *진행 중*
- **CHECKPOINT-05 (Day 3-4 실시간·동기화 확장)**: Market Quotes & Daily Issue Sync Ready (시장 가격, 실시간 자산 평가, 일일·수동 이슈 동기화, 재계산과 폴백 검증) - *계약 검토 / 구현 대기*

## Priority

### Must
- 삼성전자 및 SK하이닉스 대상 ESG 지표(E, S, G 항목별 정량/정성 점수) 수집 및 자동 검증.
- Historical CVaR 95% 계산 로직 및 20%~80% 제약조건의 1% 그리드서치 최적화 모델.
- 모바일(390px) 화면에서 포트폴리오 입력, 추천 비중 비교 및 추천 사유 제시.
- API 요청/응답 형식의 스키마 정합성 보장.
- 홈에서 코스피·코스닥·삼성전자·SK하이닉스 시장 데이터를 장중 10~30초 간격으로 갱신.
- 삼성전자·SK하이닉스 현재가 기반 종목별 평가액, 총 자산 평가액, 평가손익과 현재 비중 갱신.
- 공시·뉴스·ESG 이슈 하루 1회 자동 동기화와 사용자 수동 동기화.
- 자동 검증 통과 사건 또는 사건 상태 변경 후 ESG 위험과 추천 비중 재계산.
- 동기화 중복 방지, 기준 시각·상태 표시와 마지막 정상 데이터 폴백.

### Should
- ESG 등급이나 점수 산정 시 business_scope가 consolidated인 경우 scope_mismatch 경고 노출.
- 과거 주요 반도체 산업 사건(이슈) 발생 전후 1, 3, 5일 수익률 분석 기능.
- 모바일 UI에서 로딩 상태 및 API 실패 시 폴백(샘플 데이터 모드 전환) 안내.

### Drop First
- 2개 초과 다종목 포트폴리오 확장.
- Black-Litterman 등 고도화된 최적화 기법 적용.
- 로그인 및 회원가입 기능.
- 틱 단위 초고빈도 시세 스트리밍.
- 검증 규칙 없이 뉴스 원문을 최종 ESG 점수에 직접 반영하는 기능.

## Current Blockers

- `COMMON-RT-02`: Data A의 보완 검토와 Data B, Backend, Frontend의 명시적 계약 승인이 필요하다.
- Data B의 동적 ESG·최적화 변경이 아직 현재 브랜치에 동기화되지 않아 재계산 통합은 대기 중이다.
- 코스피·코스닥·삼성전자·SK하이닉스 시장 데이터와 공시·뉴스에 사용할 외부 소스, 호출 제한과 실패 정책을 확정해야 한다.

## Final Demo Flow
1. **투자 성향/우선순위 설정**: 사용자가 ESG 위험 가중치, 가격 하방위험 가중치 등을 조정하거나 선택.
2. **보유 정보 입력**: 삼성전자와 SK하이닉스의 현재 보유 수량과 평단가를 입력.
3. **시장·자산 현황 확인**: 코스피·코스닥·삼성전자·SK하이닉스 현재값과 조회 시각, 실시간 총 자산 평가액·평가손익·현재 비중 확인.
4. **현재 상태 진단**: 현재 보유 비중, 포트폴리오 통합 ESG 위험도, 가격 하방위험(CVaR) 수준 확인.
5. **추천 비중 비교**: 최적화 엔진에 의해 제안된 추천 비중(20%~80% 범위 내)과 현재 비중을 그래프 및 수치로 비교.
6. **위험 감소율 및 사유**: 추천 비중으로 변경 시 예상되는 위험 감소 효과 및 상세 정성적 추천 사유 조회.
7. **이슈 동기화와 과거 사건 분석**: `새로운 이슈 확인`을 실행하고 신규·변경 건수와 갱신 시각을 확인한 뒤 과거 사건 전후 주가 흐름을 조회.
8. **재계산 확인**: 자동 검증 통과 사건 또는 상태 변경이 있으면 ESG 위험과 추천 비중이 다시 계산되는 흐름 검증.
9. **보유 정보 수정**: 입력값을 수정하여 진단 결과가 재계산되는 흐름 검증.
10. **폴백 확인**: 가격·이슈 외부 API 실패 시 마지막 정상 데이터와 지연·폴백 상태가 표시되는지 확인.
