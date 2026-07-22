# 칩버디 (Chip Buddy) PRD

## 0. 문서 정보

- 문서명: 칩버디 (Chip Buddy) Product Requirements Document
- 버전: v1.5 Python · Railway · Antigravity Architecture Update
- 프로젝트 기간: 4일
- 대상 플랫폼: 모바일 웹 대시보드
- 지원 종목: 삼성전자, SK하이닉스
- 주요 사용자: 주식 및 반도체 배경지식이 거의 없는 초보 투자자
- 구현 전략: Python 기반 FastAPI 웹앱을 Railway에 배포하고, Google Stitch로 UI를 설계하며, Antigravity와 Gemini를 개발·수집·분석·검증 오케스트레이션 엔진으로 활용한다. 시장 가격은 장중 10~30초 간격으로 갱신하고, 공시·뉴스·ESG 이슈는 하루 한 번 자동 동기화하며 사용자가 요청하면 추가 동기화한다.

---

# 1. 제품 정의

## 1.1 제품 한 줄 정의

> 국내 공식자료를 바탕으로 삼성전자 반도체 사업과 SK하이닉스의 ESG 관리위험·가격 하방위험을 구분해 분석하고, 데이터 신뢰도와 과도한 비중 변경을 함께 고려해 두 종목 안에서 상대적으로 덜 취약한 비중을 추천하는 모바일 포트폴리오 최적화 서비스

## 1.2 핵심 가치

- 현재 포트폴리오 상태를 숫자와 신호로 요약
- 기업별 ESG 리스크 정량화
- 기업별 하락 리스크 정량화
- 위험 기반 최적 포트폴리오 자동 계산
- 현재 비중과 추천 비중 비교
- 추천 비중 적용 시 예상 위험 변화 설명
- 현재 이슈와 과거 흐름의 별도 분석
- 코스피·코스닥·삼성전자·SK하이닉스 시장 현황의 장중 갱신
- 실시간 현재가를 반영한 총 자산 평가액·평가손익·현재 비중
- 일일 자동 동기화와 사용자 수동 동기화를 통한 최신 이슈 확인

## 1.3 제품 목표

1. 사용자가 자신의 현재 포트폴리오 비중을 정확히 이해한다.
2. 사용자가 삼성전자와 SK하이닉스의 ESG·하락 리스크 차이를 이해한다.
3. 시스템이 위험 기반 적정 비중을 자동 산출한다.
4. 사용자가 현재 비중과 추천 비중의 차이와 이유를 이해한다.
5. 추천 결과가 수익률 보장이나 매매 명령으로 오해되지 않도록 한다.
6. 사용자가 홈에서 시장과 보유자산의 최신 상태를 확인할 수 있도록 한다.
7. 매일 갱신되는 공시·뉴스·ESG 이슈와 사용자 요청 동기화를 통해 최신 위험 정보를 제공한다.

## 1.4 비목표

- 미래 수익률 최대화
- 목표주가 제시
- 실제 매수·매도 주문
- 증권 계좌 연동
- 현금·ETF·타 산업 자산을 포함한 자산배분
- 전체 국내 종목 지원
- 반도체 산업 지도
- 홈의 현재 핵심 이슈 요약
- 홈의 과거 유사 사례 요약
- 포트폴리오 가치 영향 점수
- 가장 영향을 받는 종목 표시
- 단기 주가와 장기 가치 영향 분리
- 가치 영향 경로
- 다음 확인 행동

---

# 2. 변경 사항

## 2.1 국내 기업 비교 범위 정합성 추가

- 삼성전자는 가능한 경우 DS부문 또는 삼성반도체 사업부 데이터를 우선 사용한다.
- 사업부 데이터가 없을 때만 삼성전자 연결 전체 데이터를 사용한다.
- 전체 수치를 사용하면 `scope_mismatch = true`와 비교 한계를 표시한다.
- SK하이닉스와의 비교 기준연도, 지역, 단위, 검증 여부를 함께 저장한다.

## 2.2 ESG 점수 구조 변경

기존의 단순 E·S·G 고정가중합을 폐기하고 다음 구조를 사용한다.

```text
Residual Risk = Exposure × (1 - Management)
Issue Risk = Residual Risk + Confirmed Controversy Penalty + Data Uncertainty
ESG Risk = Σ(Materiality Weight × Issue Risk)
```

- 사건·논란은 독립 10% 항목이 아니라 해당 E·S·G 이슈에 덧붙이는 오버레이로 처리한다.
- 미확정 뉴스는 점수에 넣지 않고 경고 상태로만 표시한다.
- 결측치를 임의 평균값으로 대체하지 않는다.

## 2.3 가격 하방위험 및 최적화 변경

- 공분산 기반 하방위험을 Historical CVaR 중심으로 변경한다.
- 최적화 목적함수에 현재 비중과의 차이를 줄이는 턴오버 페널티를 추가한다.
- 외부 반도체 사업위험과 ESG 관리위험을 별도 변수로 관리하며 MVP 최적화에는 혼합하지 않는다.

## 2.4 데이터·출처 원칙 강화

- OpenDART 전자공시를 공식 확인 근거로 우선하고 뉴스는 사건 탐지에 사용한다.
- 외부 ESG 등급은 참고자료로만 사용하며 원점수를 흉내 내거나 무단 재가공하지 않는다.
- 모든 위험 카드에 기준연도, 사업범위, 출처, 데이터 신뢰도를 표시한다.


## 2.5 Python·Railway·Antigravity 기술 구조 추가

- Streamlit 단일 앱 전제는 사용하지 않는다.
- 사용자 화면과 API는 Python `FastAPI + Jinja2 + HTMX`로 구현한다.
- 인터랙티브 차트는 Plotly를 사용한다.
- 애플리케이션, 데이터베이스, 정기 수집 작업은 Railway에 배포한다.
- Railway는 화면 프레임워크가 아니라 배포·운영 플랫폼으로 정의한다.
- Antigravity는 코드 작성, 데이터 수집, 테스트, 브라우저 검증과 에이전트 작업 오케스트레이션을 담당한다.
- Gemini는 논문·공시·뉴스를 구조화하고 설명문 초안을 생성하되, 최종 위험점수와 추천 비중은 재현 가능한 Python 계산 함수가 결정한다.

## 2.6 North Star 반영

최종 목표는 단순 데모가 아니라 다음 흐름을 갖는 지능형 투자 의사결정 플랫폼이다.

```text
공시·뉴스·가격 데이터 수집
→ 기업·사업범위·사건 상태 검증
→ ESG 관리위험 및 Historical CVaR 계산
→ 포트폴리오 최적화
→ 초보자용 설명 생성
→ Railway에서 웹 리포트와 API 제공
→ Antigravity가 수집·분석·테스트 작업을 지속적으로 오케스트레이션
```

# 3. 사용자 문제

- 현재 보유 비중이 적절한지 판단하기 어렵다.
- 두 기업의 손실 위험을 비교하기 어렵다.
- ESG 리스크를 투자 비중에 반영하는 방법을 모른다.
- 포트폴리오 비중을 어떤 기준으로 조정해야 하는지 모른다.
- 추천 비중이 제시되어도 계산 근거를 이해하기 어렵다.
- 동일 산업의 두 종목만 보유한 집중 위험을 인지하기 어렵다.

---

# 4. 제품 범위

## 4.1 Must Have

- 3문항 투자 이해도 진단
- 위험 우선순위 선택
- 삼성전자·SK하이닉스 포트폴리오 입력
- 종목별 현재 비중 자동 계산
- 포트폴리오 상태 점수와 신호등
- AI 포트폴리오 요약
- 종목별 상태 점수
- 기업별 ESG 리스크 점수
- 기업별 하락 리스크 점수
- 종합 리스크 점수
- 포트폴리오 최적화 계산
- 추천 비중 자동 산출
- 현재 비중과 추천 비중 비교
- 현재·추천 포트폴리오 위험 비교
- 예상 위험 감소율
- 추천 근거 설명
- 추천 결과 한계 및 산업 집중 경고
- 현재 이슈 상세
- 과거 유사 사례 1~3건
- 과거 사건 수익률 차트 및 타임라인
- 포트폴리오 수정 후 최적화 재계산
- 출처 및 면책 문구
- 코스피·코스닥·삼성전자·SK하이닉스 장중 시장 현황
- 삼성전자·SK하이닉스 실시간 현재가 기반 총 자산 평가액·평가손익·현재 비중
- 공시·뉴스·ESG 이슈 하루 1회 자동 동기화
- 사용자가 요청하는 이슈 수동 동기화
- 마지막 갱신 시각, 다음 자동 갱신 시각, 갱신·실패·폴백 상태 표시
- 자동 검증 통과 사건 또는 사건 상태 변경 시 ESG 위험과 추천 비중 재계산

## 4.2 Should Have

- 샘플 포트폴리오 불러오기
- 최적화 가중치 설명 바텀시트
- ESG·하락 리스크 세부 구성 보기
- 서버 세션 또는 SQLite 기반 임시 저장
- 최적화 재계산 버튼
- 추천 결과 생성 시각 표시

## 4.3 Out of Scope

- 반도체 산업 지도
- 독립 기업 비교 화면
- 독립 투자 학습 화면
- 홈의 현재 핵심 이슈
- 홈의 과거 유사 사례
- 사용자의 직접 목표 비중 입력
- 자동 매수·매도 수량 산출
- 실제 주문
- 기대수익률 예측
- 고도화된 블랙리터만·효율적 프런티어 시각화
- 전 종목 검색
- 계좌 연동
- 틱 단위 초고빈도 시세 스트리밍
- 검증 규칙 없이 뉴스 원문을 최종 ESG 점수에 직접 반영하는 기능
- 알림

---

# 5. 정보 구조

## 5.1 하단 내비게이션

1. 홈
2. 포트폴리오 최적화
3. 이슈 분석
4. 내 포트폴리오

## 5.2 페이지 구조

```text
투자 진단
→ 포트폴리오 입력
→ 홈
→ 포트폴리오 최적화
→ 이슈 분석
→ 내 포트폴리오 수정
```

보조 UI:

- 상태 점수 상세 바텀시트
- 최적화 근거 바텀시트

---

# 6. 기능 요구사항

## 6.1 투자 이해도 진단

### 입력

3개 단일 선택 문항

### 문항

1. 매수 이유
2. 10% 하락 시 행동
3. 포트폴리오에서 가장 중요하게 보는 요소

### 출력

- `knowledge_stage`
- `risk_priority`
- `downside_weight`
- `esg_weight`

### 가중치 기본값

| risk_priority | downside_weight | esg_weight |
|---|---:|---:|
| loss_minimization | 0.8 | 0.2 |
| balanced | 0.7 | 0.3 |
| esg_focused | 0.5 | 0.5 |

### 수용 기준

- 1분 이내 완료 가능해야 한다.
- 한 화면에 한 문항만 표시한다.
- 사용자가 선택한 위험 우선순위가 최적화 계산에 반영되어야 한다.

---

## 6.2 포트폴리오 입력

### 필드

| 필드 | 필수 | 설명 |
|---|---:|---|
| stock_name | Y | 삼성전자 또는 SK하이닉스 |
| quantity | Y | 보유 수량 |
| average_price | Y | 평균 매수가 |
| purchase_reason | Y | 매수 이유 |

### 계산

```text
market_value = quantity × current_price
current_weight = market_value / total_market_value
```

### 수용 기준

- 입력 즉시 현재 비중을 계산한다.
- 한 종목만 입력해도 저장 가능하다.
- 샘플 포트폴리오를 한 번에 불러올 수 있다.

---

## 6.3 포트폴리오 상태

### 출력

- `portfolio_status_score`: 0~100
- `signal`: green / yellow / red
- `score_change`
- `summary`

### 임계값

| 점수 | 신호 | 의미 |
|---:|---|---|
| 70~100 | 초록불 | 상대적으로 안정적 |
| 40~69 | 노란불 | 비중 조정 검토 필요 |
| 0~39 | 빨간불 | 위험 집중 점검 필요 |

### 표시 예시

```text
58점 · 노란불 · 비중 조정 검토 필요
```

### 수용 기준

- 숫자·색상·텍스트를 함께 표시한다.
- 매수·매도 신호로 표현하지 않는다.
- 상태 점수의 산출 기준을 바텀시트에서 확인할 수 있다.

---

## 6.4 홈 화면

### 목적

사용자가 현재 상태와 최적화 필요 여부를 5초 안에 확인한다.

### 구성

1. 코스피·코스닥·삼성전자·SK하이닉스 시장 현황
2. 실시간 총 자산 평가액·평가손익·현재 비중
3. 포트폴리오 상태 점수와 신호
4. AI 포트폴리오 요약
5. 종목별 상태 카드
6. 최적화 미리보기
7. 포트폴리오 최적화 화면 CTA

### 최적화 미리보기 필드

- 현재 비중
- 추천 비중
- 현재 종합 위험
- 추천 포트폴리오 예상 위험
- 예상 위험 감소율

### 홈에서 제외

- 현재 핵심 이슈 요약
- 과거 유사 사례 요약
- 포트폴리오 가치 영향 점수
- 가장 영향을 받는 종목
- 단기·장기 영향 분리
- 가치 영향 경로
- 다음 확인 행동

### 수용 기준

- 사용자는 5초 이내 상태 점수와 신호를 확인할 수 있다.
- 사용자는 15초 이내 현재 비중과 추천 비중을 비교할 수 있다.
- 홈에서 이슈 콘텐츠가 노출되지 않아야 한다.
- 홈 진입 시 코스피·코스닥·삼성전자·SK하이닉스의 현재값, 전일 대비, 등락률과 조회 시각을 표시한다.
- 시장 가격은 장중 10~30초 간격으로 다시 조회하며 페이지 전체를 새로 불러오지 않는다.
- 실시간 가격 조회 실패 시 마지막 정상값과 지연 상태를 표시하고 임의 값이나 0으로 대체하지 않는다.
- 총 자산 평가액, 평가손익과 현재 비중은 삼성전자·SK하이닉스의 동일 조회 시각 현재가로 다시 계산한다.

---

## 6.5 ESG 리스크 분석

### 필수 지표

환경 5개, 사회 4개, 지배구조 3개의 총 12개 핵심 지표를 사용한다.

- 환경: 온실가스·공정가스, 수자원, 유해화학물질, 폐기물
- 사회: 산업안전, 핵심인력·노사, 공급망 인권, 제품품질·정보보호
- 지배구조: 이사회·감사, 공시·내부통제, 준법·공정거래·수출통제

### 계산

```text
ResidualRisk(k) = Exposure(k) × (1 - Management(k))
IssueRisk(k) = ResidualRisk(k) + ControversyPenalty(k) + DataUncertainty(k)
ESGRisk = Σ(MaterialityWeight(k) × IssueRisk(k))
```

사건 점수는 심각도, 최신성, 기업 책임, 지속성, 근거 신뢰도를 곱해 산정한다. 소문성 기록은 raw 단계에서 제외하고, `Reported`는 경고만 표시한다. `Confirmed`와 `Resolved` 사건 중 자동 스키마·공식 출처 검증을 통과한 사건만 정량 반영하며 제재 결과는 별도 `enforcement_action`에 저장한다.

### 출력

- 기업별 ESG 관리위험
- 지표별 위험수준: 낮음 / 보통 / 높음
- 추세: 개선 / 유지 / 악화
- 데이터 신뢰도: 높음 / 중간 / 낮음
- 기준연도, 사업범위, 지역, 제3자 검증 여부, 출처
- `scope_mismatch`

### 수용 기준

- 삼성전자 DS 데이터가 있으면 연결 전체 수치보다 우선한다.
- 결측값은 `unavailable`로 표시한다.
- 미확정 뉴스는 점수에 넣지 않는다.
- 단순히 두 기업만으로 Min-Max 정규화하지 않는다.

## 6.6 하락 리스크 분석

### 입력 데이터

- 일별 또는 주별 수익률 시계열
- 분석기간 1년·3년·5년 중 선택 또는 고정
- CVaR 신뢰수준 기본 95%
- 최대 낙폭과 하방편차는 보조 설명 지표로 사용

### 계산

```text
Historical CVaR 95%
= 손실이 가장 큰 하위 5% 구간의 평균 손실
```

포트폴리오별 Historical CVaR를 계산한 뒤 0~1 범위로 정규화한다.

### 출력

- 기업별 Historical CVaR
- 최대 낙폭
- 하방편차
- 분석기간과 기준일
- 데이터 사용 가능 여부

### 수용 기준

- 가격 위험과 ESG 위험을 별도 카드로 표시한다.
- 기간과 신뢰수준을 표시한다.
- 데이터가 없으면 임의 추정하지 않고 `unavailable`을 표시한다.

## 6.7 포트폴리오 최적화

### 목적

Historical CVaR, ESG 관리위험, 현재 비중과의 차이를 함께 고려해 두 종목 안에서 상대적으로 덜 취약한 추천 비중을 계산한다.

### 목적함수

```text
Minimize
α × Normalized Historical CVaR95(portfolio)
+ β × Σ(weight_i × ESG Risk_i)
+ γ × Σ|weight_i - current_weight_i|
```

- `α`: 가격 하방위험 가중치
- `β`: ESG 관리위험 가중치
- `γ`: 과도한 비중 변경을 막는 턴오버 가중치

### 제약조건

```text
w_samsung + w_skhynix = 1
0.20 ≤ each weight ≤ 0.80
공매도 금지
```

### 구현 방식

삼성전자 비중 20~80%를 1% 단위로 순회하는 그리드 서치를 사용한다.

### 추가 출력

- 추천 비중
- 현재·추천 CVaR
- 현재·추천 ESG 가중위험
- 턴오버 크기
- 종합 목적함수 변화
- 데이터 신뢰도 기반 추천 신뢰수준
- 산업 집중 경고

### 수용 기준

- 동일 입력에 동일 결과를 반환한다.
- 최근 1년·3년·5년, CVaR 90%·95%·97.5%의 민감도 결과를 테스트할 수 있다.
- 추천 신뢰수준을 주가 예측 확률로 표현하지 않는다.
- 비중 합계 100%, 종목별 20~80% 제약을 준수한다.

## 6.8 최적화 결과 화면

### 상단

- 현재 비중
- 추천 비중
- 예상 위험 감소율

### 비교 시각화

- 현재 비중 수평 바
- 추천 비중 수평 바
- 현재·추천 종합 위험 비교

### 기업별 위험 카드

- ESG 리스크
- 하락 리스크
- 종합 위험

### 추천 근거

최대 3개 문장으로 요약한다.

### 필수 안내

```text
추천 비중은 ESG와 하락 위험을 기준으로 계산한 참고값입니다.
기대수익률과 거래 비용은 반영하지 않습니다.
두 종목 모두 반도체 산업에 속하므로 산업 집중 위험은 유지됩니다.
```

---

## 6.9 이슈 분석

### 탭

- 현재 이슈
- 과거 흐름

### 현재 이슈 필드

- 이슈명
- 유형
- 사실 상태
- 게시일
- 출처
- 관련 기업
- 쉬운 요약
- 미확정 정보
- ESG 관련 여부

### 과거 흐름 필드

- 유사 사건 1~3건
- 1일·3일·5일 수익률
- 최대 하락폭
- 회복 기간
- 간단한 차트
- 현재와 과거의 차이

### 수용 기준

- 이슈 콘텐츠는 홈이 아닌 이슈 분석 화면에서만 제공한다.
- 과거 사례가 미래 성과를 보장하지 않는다는 문구를 표시한다.
- 공시·뉴스·ESG 이슈는 매일 지정된 시각에 한 번 자동 동기화한다.
- 사용자는 이슈 분석 화면의 `새로운 이슈 확인` 기능으로 추가 동기화를 요청할 수 있다.
- 수동 동기화는 동시 중복 실행을 방지하고 기존 실행의 상태를 반환해야 한다.
- 신규 이슈가 없을 때도 기준 시각과 함께 정상 완료 메시지를 표시한다.
- 동기화 실패 시 기존 validated 데이터와 마지막 정상 결과를 유지한다.
- 자동 검증 통과 사건이나 사건 상태 변경이 있으면 ESG 위험과 최적화 결과를 다시 계산한다.
- 마지막 성공 시각, 다음 자동 갱신 예정 시각, 신규·변경 건수와 실패 소스를 표시한다.

---

## 6.10 내 포트폴리오 수정

### 수정 가능 필드

- 보유 수량
- 평균 매수가
- 매수 이유

### 저장 후 동작

- 현재 비중 재계산
- 포트폴리오 상태 재계산
- 최적화 결과 재계산

### 수용 기준

- 저장 전후 값을 명확히 구분한다.
- 직접 목표 비중 입력 UI는 제공하지 않는다.
- 실제 주문 기능은 제공하지 않는다.

---

# 7. 데이터 요구사항

## 7.1 사용자

| 필드 | 타입 | 설명 |
|---|---|---|
| knowledge_stage | enum | 가격 추종형, 정보 탐색형, 가치 판단 입문형 |
| risk_priority | enum | loss_minimization, balanced, esg_focused |
| downside_weight | float | 하락 리스크 가중치 |
| esg_weight | float | ESG 리스크 가중치 |

## 7.2 포트폴리오

| 필드 | 타입 | 설명 |
|---|---|---|
| ticker | string | 종목 코드 |
| stock_name | string | 종목명 |
| quantity | number | 보유 수량 |
| average_price | number | 평균 매수가 |
| current_price | number | 현재가 |
| market_value | number | 평가금액 |
| current_weight | float | 현재 비중 |

## 7.3 기업 위험

| 필드 | 타입 | 설명 |
|---|---|---|
| esg_environment | float | 환경 리스크 |
| esg_social | float | 사회 리스크 |
| esg_governance | float | 지배구조 리스크 |
| esg_controversy | float | 논란 리스크 |
| esg_risk_score | float | 종합 ESG 리스크 |
| max_drawdown_score | float | 최대 낙폭 점수 |
| downside_deviation_score | float | 하방편차 점수 |
| negative_frequency_score | float | 음의 수익률 빈도 점수 |
| cvar_score | float | CVaR 점수 |
| downside_risk_score | float | 종합 하락 리스크 |

## 7.4 최적화 결과

| 필드 | 타입 | 설명 |
|---|---|---|
| recommended_samsung_weight | float | 삼성전자 추천 비중 |
| recommended_skhynix_weight | float | SK하이닉스 추천 비중 |
| current_total_risk | float | 현재 종합 위험 |
| optimized_total_risk | float | 추천 비중 종합 위험 |
| risk_reduction_rate | float | 예상 위험 감소율 |
| generated_at | datetime | 계산 시각 |
| explanation | text | 추천 근거 |

## 7.5 시장 가격

| 필드 | 타입 | 설명 |
|---|---|---|
| instrument_id | string | KOSPI, KOSDAQ, 005930, 000660 |
| instrument_type | enum | index 또는 equity |
| current_value | number | 현재 지수 또는 주가 |
| previous_close | number | 전일 종가 |
| change | number | 전일 대비 변화량 |
| change_rate | float | 전일 대비 등락률 |
| market_status | enum | open, closed, delayed, unavailable |
| as_of | datetime | 가격 기준 시각 |
| data_status | enum | validated, sample, fallback |

## 7.6 동기화 상태

| 필드 | 타입 | 설명 |
|---|---|---|
| sync_id | string | 동기화 실행 식별자 |
| sync_type | enum | scheduled 또는 manual |
| status | enum | queued, running, success, partial_success, failed |
| stage | enum | queued, collecting, normalizing, validating, publishing, recalculating, completed |
| started_at | datetime | 시작 시각 |
| completed_at | datetime 또는 null | 완료 시각 |
| last_success_at | datetime 또는 null | 마지막 성공 시각 |
| next_scheduled_at | datetime | 다음 자동 갱신 예정 시각 |
| collected_items | integer | 전자공시·뉴스 수집 건수 |
| candidate_items | integer | 정규화된 후보 건수 |
| validated_items | integer | 자동 검증 통과 건수 |
| rejected_items | integer | 자동 검증 탈락 건수 |
| published_items | integer | processed 스냅샷 발행 건수 |
| new_items | integer | 신규 이슈 수 |
| updated_items | integer | 상태 변경 이슈 수 |
| snapshot_updated | boolean | 새 processed 스냅샷 발행 여부 |
| published_snapshot_version | string 또는 null | 발행된 스냅샷 버전 |
| published_at | datetime 또는 null | 발행 시각 |
| recalculation_triggered | boolean | ESG·최적화 재계산 요청 여부 |
| recalculation_status | enum | not_requested, queued, running, success, failed |
| recalculated_at | datetime 또는 null | 재계산 종료 시각 |
| failure_stage | enum 또는 null | 실패한 파이프라인 단계 |
| failed_sources | array | 실패한 외부 소스 |
| data_status | enum | validated, sample, fallback |

`success`는 수집과 모든 후보의 자동 검증이 끝나고, 유효한 변경이 있으면 processed 스냅샷 발행까지 성공한 상태다. 신규 데이터가 없으면 `snapshot_updated=false`인 정상 성공이다. 일부 소스만 실패했지만 나머지 후보 검증과 안전한 발행이 완료되면 `partial_success`, 사용 가능한 결과가 없거나 원자적 발행이 실패하면 `failed`다.

---

# 8. Python 애플리케이션·API·배포 구조

## 8.1 MVP 애플리케이션 구조

```text
브라우저
→ FastAPI 라우터
→ Jinja2 템플릿 + HTMX 상호작용
→ Python 위험·최적화 서비스
→ SQLite/Parquet 및 사전 수집 데이터
→ Plotly 차트
```

- 프론트엔드와 분석 엔진은 모두 Python 프로젝트 안에서 관리한다.
- HTML 템플릿은 Stitch 설계 결과를 기준으로 구성한다.
- HTMX는 전체 페이지를 다시 불러오지 않고 입력·최적화 결과 영역만 갱신한다.
- MVP 저장소는 SQLite와 Parquet를 사용하고, 운영 단계에서는 Railway PostgreSQL로 전환한다.

## 8.2 최소 API

```text
GET  /health
GET  /market/quotes
POST /portfolio/summary
POST /portfolio/calculate
POST /risk/esg
POST /risk/downside
POST /portfolio/optimize
GET  /issues/current
GET  /issues/historical
POST /sync/issues
GET  /sync/status
```

`POST /sync/issues`는 사용자의 `새로운 이슈 확인` 요청과 일일 예약 작업이 같은 동기화 서비스를 사용하도록 한다. 요청은 동시 실행 잠금, 최소 재요청 간격과 `sync_id`를 사용해 중복 수집을 막는다. 원본은 raw 또는 candidate 저장소에 기록하고 스키마·공식 출처·사건 상태·근거·중복 검사를 통과한 결과를 사람 검수 없이 processed 스냅샷에 원자적으로 반영한다.

## 8.3 Python 서비스 인터페이스

```python
def collect_disclosures(company_id: str): ...
def collect_news(company_id: str): ...
def calculate_esg_risk(indicators, events): ...
def calculate_historical_cvar(returns, confidence_level=0.95): ...
def optimize_portfolio(current_weights, returns, esg_risks, downside_weight, esg_weight, turnover_weight): ...
```

## 8.4 Railway 배포 구조

```text
Railway Web Service
- FastAPI + Jinja2 + HTMX 애플리케이션

Railway Database
- MVP: SQLite 또는 파일 데이터
- 목표: PostgreSQL

Railway Scheduled Job
- 공시·가격·뉴스 갱신 스크립트

Railway Environment Variables
- OpenDART 키
- Gemini 키
- 뉴스 데이터 키
- 관리자 토큰
```

Railway는 서비스를 실행하고 배포하는 운영 환경이며, 화면을 만드는 프레임워크는 아니다.

## 8.5 Antigravity·Gemini 역할

### Antigravity

- 데이터 수집기와 분석 모듈 코드 작성·수정
- 테스트 실행 및 실패 원인 분석
- 브라우저에서 주요 사용자 흐름 검증
- 공시 수집, 뉴스 분류, 데이터 품질 검사 에이전트 오케스트레이션
- 배포 전 산출물과 검증 결과 관리

### Gemini

- 논문 방법론을 Python 요구사항과 코드 초안으로 변환
- 한국어 공시·뉴스에서 사건 필드 추출
- 사건 유형과 공식 확인 상태 분류 보조
- 초보 투자자용 설명문 초안 생성

### 금지 원칙

- Gemini가 임의로 ESG 점수나 추천 비중을 결정하지 않는다.
- 미확정 뉴스만으로 위험점수를 올리지 않는다.
- 모든 최종 숫자는 테스트 가능한 Python 함수에서 생성한다.

# 9. 비기능 요구사항

## 성능

- Railway 배포 환경에서 주요 화면 초기 로딩 3초 이내
- 포트폴리오 수정 후 최적화 재계산 2초 이내
- 외부 데이터 갱신과 사용자 요청 계산을 분리해 수집 지연이 화면을 막지 않도록 한다
- 시장 가격은 장중 10~30초 간격으로 갱신하고 각 값에 `as_of`를 표시한다.
- 수동 이슈 동기화 요청은 즉시 `queued` 또는 `running` 상태와 `sync_id`를 반환한다.

## 안정성

- Railway `/health` 엔드포인트로 서비스 상태를 확인한다
- 라이브 데이터 실패 시 마지막 정상 데이터 또는 샘플 데이터 사용
- 동일 입력에 동일 결과 반환
- 누락 데이터는 임의 추정하지 않고 샘플 또는 unavailable로 표시
- 동일 동기화의 중복 실행을 금지하고 기존 작업 상태를 반환한다.
- 외부 가격 API 실패 시 마지막 정상 가격을 사용하되 `delayed` 또는 `fallback`으로 표시한다.
- 동기화 실패는 기존 validated 데이터와 마지막 정상 스냅샷을 덮어쓰지 않는다.

## 접근성

- 색상만으로 위험을 표현하지 않는다.
- 모든 점수에 텍스트 레이블을 병기한다.
- 모바일 터치 영역은 최소 44px 이상으로 한다.

## 법적·윤리적 요구사항

- 추천 비중을 매수·매도 명령으로 표현하지 않는다.
- 투자 참고 및 교육 목적임을 명시한다.
- ESG·하락 리스크 데이터 기준일과 출처를 표시한다.
- 과거 데이터가 미래 성과를 보장하지 않음을 명시한다.

---

# 10. 4일 개발 우선순위

## Day 1 — Python 웹앱 기반과 데이터 범위

- 삼성전자 DS와 SK하이닉스 비교 범위 확정
- 12개 ESG 핵심 지표 샘플 데이터 작성
- 기준연도·단위·사업범위·출처 메타데이터 연결
- FastAPI 프로젝트, Jinja2 템플릿, HTMX 기본 구조 생성
- Stitch 설계를 모바일 템플릿에 매핑
- 투자 진단 및 포트폴리오 입력 구현

## Day 2 — Python 분석 엔진과 데이터 수집

- Exposure–Management–Controversy–Uncertainty 계산 구현
- 사건 상태 규칙 구현
- 데이터 신뢰도 계산
- 가격 수익률과 Historical CVaR 계산
- OpenDART·가격·뉴스 수집기 인터페이스와 Pydantic 스키마 구현

## Day 3 — 최적화·인터랙티브 리포트·Railway

- 턴오버 페널티 포함 1% 그리드서치 구현
- 현재/추천 비중과 위험 비교
- ESG·가격 하방위험 별도 카드
- Plotly 기반 비중·위험 차트 구현
- 이슈 분석 및 규칙 기반 추천 문장 구현
- 코스피·코스닥·삼성전자·SK하이닉스 시장 가격 서비스와 캐시 구현
- 실시간 현재가 기반 총 자산 평가액·평가손익·현재 비중 구현
- Railway Web Service 배포 및 환경변수 설정

## Day 4 — Antigravity 검증·예약 갱신·데모

- 사업부/연결전체 범위 혼용 점검
- 기간·CVaR 신뢰수준·가중치 민감도 분석
- 합계 100%, 20~80% 제약, 재현성 테스트
- 공식 출처·기준연도·데이터 신뢰도·면책 표시
- Antigravity로 pytest와 브라우저 사용자 흐름 검증
- 공시·뉴스·ESG 이슈 하루 1회 예약 동기화 검증
- 사용자 수동 이슈 동기화, 동시 실행 잠금과 상태 조회 검증
- 자동 검증 통과 사건 또는 상태 변경 후 ESG 위험·추천 비중 재계산 검증
- 가격 및 이슈 외부 API 실패 시 마지막 정상 데이터 폴백 검증

# 11. 출시 기준

MVP는 다음 조건을 모두 충족해야 한다.

- 3문항 진단 완료
- 포트폴리오 입력 및 비중 계산
- 기업별 ESG 리스크 표시
- 기업별 하락 리스크 표시
- 추천 비중 자동 산출
- 추천 비중 합계 100%
- 현재·추천 위험 비교
- 추천 근거와 한계 표시
- 홈에서 현재 이슈와 과거 사례가 제거됨
- 이슈 분석 화면에서 현재·과거 이슈 확인 가능
- 포트폴리오 수정 후 최적화 재계산
- 전체 데모 흐름 오류 없음
- 홈에서 코스피·코스닥·삼성전자·SK하이닉스 시장 현황과 기준 시각 확인
- 실시간 현재가 변경 시 총 자산 평가액·평가손익·현재 비중 갱신
- 이슈 하루 1회 자동 동기화와 사용자 수동 동기화 동작
- 자동 검증 통과 사건 또는 사건 상태 변경 후 ESG 위험·추천 비중 재계산
- 가격·이슈 외부 API 실패 시 마지막 정상 데이터와 폴백 상태 표시

---

# 12. 최종 제품 원칙

1. 홈은 상태와 최적화 필요 여부에 집중한다.
2. 현재 이슈와 과거 사례는 이슈 분석 화면에서만 제공한다.
3. ESG와 하락 리스크를 별도로 계산하고 함께 반영한다.
4. 추천 비중은 위험 기반 참고값이지 수익률 보장이 아니다.
5. 최적화 계산 기준과 제약조건을 숨기지 않는다.
6. 두 종목만으로는 산업 분산이 불가능하다는 점을 명시한다.
7. 4일 MVP에서는 재현 가능하고 설명 가능한 단순 최적화를 우선한다.


# 13. v1.5 변경 이력

- 삼성전자 DS 우선 비교와 `scope_mismatch` 추가
- 12개 반도체 특화 ESG 지표 및 데이터 신뢰도 도입
- 고정 E·S·G 가중합 폐기, 노출–관리–사건–불확실성 구조 도입
- 공분산 중심 최적화를 Historical CVaR + ESG + 턴오버 페널티로 변경
- 미확정 뉴스 점수 반영 금지, 공식자료 우선순위 명시
- 민감도 분석과 추천 신뢰수준 정의 추가
- Python FastAPI + Jinja2 + HTMX 기반 웹 구조 확정
- Railway 배포, 환경변수, 데이터 갱신 작업 구조 추가
- Antigravity와 Gemini의 역할 및 책임 경계 추가
- North Star인 실시간 대응형 지능형 투자 의사결정 플랫폼 확장 경로 추가
