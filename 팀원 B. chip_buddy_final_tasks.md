# 데이터 B 칩버디 최종 기능 완성 작업 가이드

## 0. 문서 목적

이 문서는 데이터 B 담당자가 현재 작성된 모델링 코드와 데이터 A의 검수 데이터를 바탕으로 **칩버디의 최종 기능을 실제 계산 결과로 완성하기 위해 수행해야 하는 작업**을 정리한 실행 가이드다.

데이터 B의 최종 책임은 다음과 같다.

> 검증된 가격·ESG·사건 데이터를 재현 가능한 Python 함수로 계산하여 기업별 위험점수, 포트폴리오 상태, 추천 비중, 사건 전후 주가 반응을 생성하고 개발 A가 API에서 바로 호출할 수 있는 형태로 전달한다.

---

# 1. 현재 구현 상태

## 1.1 이미 구현된 기능

현재 모델링 코드에는 다음 기능이 구현되어 있다.

### 가격 데이터

- 필수 종목 코드 `005930`, `000660` 확인
- 날짜·종목별 중복 검사
- 가격 숫자형·양수 검사
- 수정주가 우선 사용
- 공통 거래일 기준 피벗
- 일별 수익률 계산

관련 파일:

```text
price.py
```

### 하방위험

- Historical CVaR
- 최대 낙폭
- 하방편차
- 기업별 하방위험 결과 생성

관련 파일:

```text
downside.py
```

### 포트폴리오 최적화

- 삼성전자 20~80% 범위
- 1% 단위 그리드서치
- 포트폴리오 CVaR 계산
- ESG 비중가중 위험
- 턴오버 페널티
- 현재·추천 위험 비교
- 추천 이유 문장 생성
- 결과 JSON 구조 생성

관련 파일:

```text
optimizer.py
```

### 사건 반응 분석

- 사건일 또는 이후 첫 거래일 탐색
- 사건 후 1일·3일·5일 누적수익률
- 사건 후 최대 하락폭
- 회복 기간
- 차트용 누적수익률 배열 생성
- 여러 사건 일괄 분석

관련 파일:

```text
events.py
```

---

## 1.2 아직 해결되지 않은 핵심 문제

현재 상태에서는 칩버디의 최종 기능이 완성됐다고 볼 수 없다.

### 가장 큰 문제

`optimizer.py`의 ESG 입력은 실제 지표 계산 결과가 없으면 다음 고정값을 사용한다.

```python
{
    "005930": 0.42,
    "000660": 0.55,
}
```

따라서 가격 위험은 실제 데이터로 계산되더라도 ESG 위험과 추천 비중은 샘플값에 의존할 수 있다.

### 추가 문제

- 12개 ESG 지표 계산 모듈이 없음
- `Exposure × (1 - Management)` 계산이 없음
- 사건 페널티 계산이 없음
- 데이터 불확실성 계산이 없음
- 중요도 가중합이 없음
- 기업별 `data_confidence`가 코드에 고정됨
- 사용자 현재 비중을 평단가 기준으로 계산함
- 현재 비중 목적함수 계산에서 턴오버 항이 누락될 가능성이 있음
- 위험 우선순위 이름과 PRD 이름이 일치하지 않음
- 사건 분석에서 `reported` 사건을 자동 제외하지 않음
- 사건 기준일이 시장 최초 공개일인지 검증하지 않음
- 사건 반응에 시장·반도체 지수 벤치마크가 반영되지 않음
- 1년·3년·5년 및 CVaR 90%·95%·97.5% 민감도 분석이 없음
- 테스트 코드와 최종 검증 보고서가 없음

---

# 2. 데이터 B 최종 산출물

데이터 B는 최종적으로 다음 파일과 함수를 제공해야 한다.

## 2.1 필수 Python 모듈

```text
src/modeling/
├── price.py
├── downside.py
├── esg.py
├── events.py
├── optimizer.py
├── portfolio_status.py
├── sensitivity.py
└── __init__.py
```

## 2.2 필수 설정 파일

```text
config/
├── esg_scoring_rules.yaml
├── materiality_weights.yaml
├── event_penalty_rules.yaml
└── risk_profile_weights.yaml
```

## 2.3 필수 결과 파일

```text
data/processed/
├── company_esg_risks.json
├── company_downside_risks.json
├── event_reactions.json
├── optimization_result.json
├── sensitivity_results.csv
├── model_run_metadata.json
└── model_validation_report.md
```

## 2.4 개발 A에게 전달할 핵심 함수

```python
calculate_esg_risk(indicators, events, rules)
calculate_historical_cvar(returns, confidence_level=0.95)
calculate_company_downside_risks(returns_df, prices_df)
calculate_event_reactions(events_df, prices_df, index_df=None)
optimize_portfolio(
    holdings,
    current_prices,
    price_data,
    esg_result,
    risk_priority,
    turnover_weight,
)
calculate_portfolio_status(optimization_result)
run_sensitivity_analysis(...)
```

---

# 3. 작업 1 — 현재 코드의 안전성 수정

## 3.1 현재 비중 계산 방식을 현재가 기준으로 수정

현재 `optimizer.py`는 다음 방식으로 보유금액을 계산한다.

```text
보유 수량 × 평균 매수가
```

하지만 실제 현재 비중은 다음 방식이어야 한다.

```text
보유 수량 × 현재가
```

평균 매수가는 평가손익 계산에 사용하고, 현재 비중 계산에는 사용하지 않는다.

### 수정 후 입력 예

```python
holdings = [
    {
        "ticker": "005930",
        "quantity": 70,
        "average_price": 70000,
        "current_price": 82000,
    },
    {
        "ticker": "000660",
        "quantity": 30,
        "average_price": 180000,
        "current_price": 210000,
    },
]
```

### 완료 기준

- 동일 수량이라도 현재가가 달라지면 현재 비중이 달라져야 한다.
- 평균 매수가를 바꿔도 현재 비중은 변하지 않아야 한다.
- 평균 매수가는 평가손익에만 영향을 줘야 한다.

---

## 3.2 한 종목만 보유한 경우 처리

서비스 요구사항은 한 종목만 입력해도 작동해야 한다.

현재 비중이 100:0이어도 최적화 후보는 20~80% 제약을 적용할 수 있다.

### 확인할 사례

```text
삼성전자만 보유
SK하이닉스만 보유
두 종목 모두 보유
두 종목 모두 0주
```

### 완료 기준

- 한 종목만 보유해도 오류 없이 결과를 반환한다.
- 두 종목 모두 0주이면 명확한 오류를 반환한다.
- 현재 비중이 제약 범위 밖이어도 추천 비중은 20~80% 안에서 계산된다.

---

## 3.3 목적함수 가중치 검증

최적화 식은 다음과 같다.

```text
Total Risk
= α × Normalized CVaR
+ β × Portfolio ESG Risk
+ γ × Turnover
```

입력된 `α`, `β`, `γ`에 대해 다음을 검사한다.

```text
각 값은 0 이상
합계는 1 또는 사전에 정한 정책값
NaN 금지
```

직접 가중치를 입력하는 경우 현재 코드처럼 `downside_weight`, `esg_weight`, `turnover_weight`를 그대로 사용할 수 있지만, 합계 검증을 추가해야 한다.

### 완료 기준

잘못된 가중치 입력은 조용히 계산하지 않고 `ValueError`를 반환한다.

---

## 3.4 위험 우선순위 이름 통일

PRD 기준 이름:

```text
loss_minimization
balanced
esg_focused
```

현재 코드에는 다음 이름이 섞여 있다.

```text
conservative
balanced
esg_focused
strategy_preserving
balanced_adjustment
risk_priority_adjustment
```

### 해야 할 일

외부 API 입력값은 PRD 이름으로 통일하고, 내부 변환 함수 하나만 둔다.

```python
def resolve_risk_profile(risk_priority: str) -> dict:
    ...
```

### 권장 기본값

```yaml
loss_minimization:
  alpha: 0.72
  beta: 0.18
  gamma: 0.10

balanced:
  alpha: 0.63
  beta: 0.27
  gamma: 0.10

esg_focused:
  alpha: 0.45
  beta: 0.45
  gamma: 0.10
```

가중치 정책은 코드에 중복 작성하지 말고 설정 파일 하나에서 불러온다.

---

# 4. 작업 2 — ESG 고정값 제거

이 작업이 데이터 B의 최우선 과제다.

## 4.1 새 `esg.py` 작성

다음 계산 흐름을 구현한다.

```text
검수 완료 ESG 지표
→ 사용 가능 행 필터
→ 방향 통일
→ 지표별 정규화
→ Exposure 계산
→ Management 계산
→ Residual Risk 계산
→ 사건 페널티 계산
→ 데이터 불확실성 계산
→ Issue Risk 계산
→ 중요도 가중합
→ 기업별 ESG Risk
```

---

## 4.2 입력 필터 규칙

다음 행만 사용한다.

```text
review_status == approved
availability == available
```

다음은 점수 계산에서 제외한다.

```text
review_status == needs_review
review_status == rejected
availability == unavailable
```

단, `unavailable`은 완전히 무시하지 말고 데이터 완전성과 불확실성 계산에는 반영한다.

---

## 4.3 위험 방향 통일

지표별 방향은 다음 두 가지다.

```text
higher_is_worse
higher_is_better
```

모든 정규화 결과는 다음 의미로 통일한다.

```text
0 = 낮은 위험
1 = 높은 위험
```

예:

```text
온실가스 배출집약도: 값이 높을수록 위험
재활용률: 값이 낮을수록 위험
```

---

## 4.4 두 기업만으로 Min-Max 정규화 금지

삼성전자와 SK하이닉스 두 값만 사용한 Min-Max 정규화는 금지한다.

잘못된 예:

```python
(x - min(two_companies)) / (max(two_companies) - min(two_companies))
```

권장 우선순위:

1. 기업의 3개년 또는 5개년 자체 추세
2. 기업 공개 목표 대비 거리
3. 법정 기준 또는 산업 기준
4. 사전에 정의한 절대 구간
5. 비교 불가 시 정성 수준과 낮은 신뢰도 표시

---

## 4.5 Exposure와 Management 계산

### Exposure

기업이 해당 위험에 얼마나 노출되는지 0~1로 계산한다.

가능한 기준:

- 배출집약도
- 물 사용집약도
- 사고 발생 빈도
- 산업 특성상 기본 노출도
- 공식 사건 이력

### Management

기업이 위험을 얼마나 관리하는지 0~1로 계산한다.

가능한 기준:

- 목표 달성률
- 최근 3개년 개선 추세
- 재활용률·재이용률
- 감사·실사 범위
- 제3자 검증
- 관리체계 존재 여부

계산식:

```text
Residual Risk = Exposure × (1 - Management)
```

### 중요한 원칙

정량 데이터가 부족하면 임의의 정밀 숫자를 만들지 않는다.

예:

```text
low / medium / high
improving / stable / worsening
target_met / off_track
```

를 규칙으로 변환하되, 변환 기준을 설정 파일에 공개한다.

---

## 4.6 사건 페널티 계산

다음 식을 구현한다.

```text
Controversy Penalty
= Severity
× Recency
× Responsibility
× Persistence
× Evidence Confidence
```

### 상태별 처리

```text
rumor       → 0
reported    → 점수 반영 금지, 경고 전용
confirmed   → 반영
sanctioned  → 강한 반영
resolved    → 시간 감쇠 적용
```

### 사건과 ESG 지표 연결

예:

```text
산업안전 사건 → S01
화학물질 사건 → E04 또는 E05
정보보호 사건 → S04
공정거래 사건 → G03
```

하나의 사건을 전체 ESG 점수에 중복 가산하지 않는다.

---

## 4.7 데이터 불확실성 계산

다음 요소를 이용해 0~1 범위의 불확실성을 계산한다.

```text
scope_mismatch
기준연도 불일치
단위·산식 불일치
제3자 검증 부재
출처 신뢰도
정량값 부재
결측 지표 비율
```

예시 설정:

```yaml
scope_mismatch_penalty: 0.08
period_mismatch_1y_penalty: 0.03
period_mismatch_2y_penalty: 0.05
no_assurance_penalty: 0.03
non_official_source_penalty: 0.05
missing_quantitative_value_penalty: 0.07
```

정확한 수치는 팀에서 합의하고 설정 파일에 기록한다.

---

## 4.8 중요도 가중합

최종 기업 ESG 위험:

```text
ESG Risk
= Σ(Materiality Weight × Issue Risk)
```

필수 조건:

- 사용된 지표 가중치 합계 확인
- unavailable 지표 처리 방식 명시
- 특정 지표 하나가 전체 점수를 과도하게 지배하지 않는지 검사
- 환경·사회·지배구조별 중간점수 제공

### 출력 구조 예

```json
{
  "company_id": "005930",
  "esg_risk_score": 0.41,
  "environment_risk": 0.38,
  "social_risk": 0.47,
  "governance_risk": 0.35,
  "data_confidence": "medium",
  "data_completeness": 0.83,
  "scope_mismatch": true,
  "indicator_results": [
    {
      "indicator_id": "E01",
      "exposure": 0.62,
      "management": 0.71,
      "residual_risk": 0.18,
      "controversy_penalty": 0.00,
      "data_uncertainty": 0.03,
      "issue_risk": 0.21,
      "materiality_weight": 0.10
    }
  ]
}
```

---

## 4.9 `load_esg_scores()` 제거 또는 제한

현재 `load_esg_scores()`의 고정 기본값은 최종 서비스에서 제거한다.

권장 동작:

```text
실제 ESG 계산 결과 있음
→ 사용

실제 결과 없음
→ sample 모드에서만 샘플 사용

reviewed 모드인데 실제 결과 없음
→ 오류 또는 unavailable 반환
```

절대로 reviewed 상태에서 `0.42`, `0.55`를 조용히 사용하지 않는다.

---

# 5. 작업 3 — 가격 하방위험 완성

## 5.1 분석기간 선택 기능

다음 기간을 지원한다.

```text
1년
3년
5년
```

함수 예:

```python
filter_price_period(prices_df, years=3)
```

결과에 반드시 다음을 포함한다.

```text
price_period_start
price_period_end
number_of_observations
```

---

## 5.2 CVaR 신뢰수준 지원

다음 신뢰수준을 테스트할 수 있어야 한다.

```text
90%
95%
97.5%
```

기본값은 95%다.

---

## 5.3 포트폴리오 CVaR 정규화 개선

현재 후보군의 최대 CVaR로 나누는 방식은 실행 가능한 MVP 방식이지만 다음 내용을 문서화해야 한다.

```text
Normalized CVaR = Candidate CVaR / Max Candidate CVaR
```

추가 권장:

- 최소·최대가 같을 때 처리
- 정규화 기준을 결과 메타데이터에 기록
- 기업 위험 카드와 포트폴리오 위험의 스케일을 구분

---

## 5.4 하방위험 결과 구조 확장

기업별 출력:

```json
{
  "ticker": "005930",
  "cvar": 0.0312,
  "max_drawdown": 0.284,
  "downside_deviation": 0.014,
  "analysis_period": "3y",
  "confidence_level": 0.95,
  "data_status": "reviewed"
}
```

---

# 6. 작업 4 — 사건 반응 분석 완성

## 6.1 승인 상태 필터 강화

현재 코드는 `review_status == approved`만 필터한다.

추가로 다음 규칙을 적용한다.

### 모델 및 과거 흐름 분석 가능

```text
confirmed
sanctioned
resolved
```

### 경고 화면만 가능

```text
reported
```

### 제외

```text
rumor
rejected
```

---

## 6.2 시장 최초 공개일 사용

주가 반응 기준일은 실제 사고 발생일이 아니라 시장이 사건을 알 수 있었던 날짜를 우선한다.

우선순위:

```text
official_disclosure_date
authority_announcement_date
first_public_report_date
sanction_date
```

`occurrence_date`만 있는 사건은 경고를 표시하거나 별도 검토 대상으로 둔다.

---

## 6.3 회복 기간 계산 창 확장

현재 기본 분석 창은 10거래일이다.

회복 기간이 10일보다 길면 `None`이 반환될 수 있다.

권장:

```text
수익률 차트 기본 창: 10거래일
회복 기간 탐색 창: 최대 60거래일
```

두 창을 분리한다.

---

## 6.4 최대 낙폭 정의 명확화

현재 사건 반응의 `max_drawdown`은 사건 기준 가격 대비 최저 누적수익률이다.

일반적인 MDD는 구간 내 고점 대비 저점 하락률이다.

둘을 구분한다.

```text
event_relative_min_return
window_max_drawdown
```

화면에서 무엇을 사용할지 개발팀과 합의한다.

---

## 6.5 벤치마크 초과수익률 추가

가능하면 `index_prices.csv`를 사용한다.

계산:

```text
Abnormal Return
= Stock Cumulative Return
- Benchmark Cumulative Return
```

출력:

```text
abnormal_return_1d
abnormal_return_3d
abnormal_return_5d
benchmark_name
```

벤치마크가 없으면 값은 `unavailable`로 표시한다.

---

## 6.6 사건 결과 저장

출력 파일:

```text
data/processed/event_reactions.json
```

각 사건에 다음을 포함한다.

```text
event_id
company_id
event_date
reaction_start_date
return_1d
return_3d
return_5d
event_relative_min_return
window_max_drawdown
recovery_days
chart_data
benchmark_returns
abnormal_returns
status
source_url
analysis_version
```

---

# 7. 작업 5 — 포트폴리오 최적화 완성

## 7.1 실제 ESG 결과 연결

최적화 입력은 기업별 계산된 ESG 결과만 사용한다.

```python
esg_scores = {
    "005930": samsung_esg_result["esg_risk_score"],
    "000660": sk_esg_result["esg_risk_score"],
}
```

고정 기본값 사용 금지.

---

## 7.2 현재 포트폴리오 위험 계산 수정

현재 포트폴리오가 그리드에 정확히 존재하지 않더라도 목적함수를 직접 계산한다.

```text
Current Total Risk
= α × Current Normalized CVaR
+ β × Current ESG Risk
+ γ × 0
```

현재 비중과 현재 비중의 차이는 0이므로 턴오버는 0이다.

현재 위험을 근처 1% 후보값으로 대신하지 않는다.

---

## 7.3 후보 결과 상세 저장

각 후보 비중별로 다음을 저장할 수 있게 한다.

```text
w_samsung
w_skhynix
raw_cvar
normalized_cvar
portfolio_esg_risk
turnover
total_objective
```

최종 API에서는 전체 후보를 반환할 필요가 없지만, 검증용 CSV로 저장한다.

```text
optimization_grid_results.csv
```

---

## 7.4 동률 및 근접 최적 처리

목적함수 값 차이가 매우 작은 후보가 여러 개일 수 있다.

권장 규칙:

1. 최소 목적함수 후보 집합 생성
2. 허용오차 안의 후보 중 현재 비중과 가장 가까운 후보 선택
3. 근접 최적 구간 계산

예:

```text
최적 추천: 삼성전자 54%
근접 최적 구간: 51~57%
```

---

## 7.5 추천 신뢰수준 계산

추천 신뢰수준은 주가 예측 확률이 아니다.

다음 요소를 결합한다.

```text
데이터 완전성
출처 신뢰성
기간 일치성
scope mismatch
민감도 안정성
사건 편중도
```

출력:

```text
high
medium
low
```

함께 이유를 반환한다.

---

## 7.6 기업별 `data_confidence` 고정값 제거

현재 코드에서 삼성전자는 `high`, SK하이닉스는 `medium`으로 고정되어 있다.

다음 값에서 계산해야 한다.

```text
사용 가능 지표 비율
제3자 검증 비율
공식 출처 비율
scope mismatch 비율
연도 일치율
```

---

## 7.7 설명문 사실성 개선

현재 설명문에는 실제 계산하지 않은 내용이 포함될 수 있다.

예:

```text
3개년 시계열 주가 종속성을 반영했다
사건 반응과 회복력을 종합 반영했다
```

실제 목적함수에 사건 반응이 직접 들어가지 않는다면 이런 문장을 사용하면 안 된다.

### 해야 할 일

설명문은 실제 사용된 입력과 결과에서만 생성한다.

예:

```text
삼성전자의 정규화 CVaR가 더 낮아 추천 비중이 증가했습니다.
SK하이닉스의 ESG 관리위험이 상대적으로 높게 계산되었습니다.
현재 비중에서 과도하게 멀어지지 않도록 턴오버 페널티를 적용했습니다.
```

---

# 8. 작업 6 — 포트폴리오 상태 점수와 홈 요약

현재 구현 분석에서 홈의 종합 상태 점수와 신호등이 누락되어 있다.

데이터 B는 상태 점수 계산 함수를 제공해야 한다.

## 8.1 권장 계산

최적화 결과의 현재 종합 위험이 0~1이면:

```text
Portfolio Status Score
= round((1 - Current Total Risk) × 100)
```

단, 이 계산식은 팀에서 공식 승인하고 문서화해야 한다.

## 8.2 신호등

```text
70~100 → green
40~69  → yellow
0~39   → red
```

## 8.3 출력 예

```json
{
  "portfolio_status_score": 58,
  "signal": "yellow",
  "label": "비중 조정 검토 필요",
  "summary": [
    "현재 포트폴리오는 SK하이닉스 비중이 상대적으로 높습니다.",
    "가격 하방위험과 ESG 관리위험을 함께 반영했습니다.",
    "추천 비중 적용 시 종합 위험이 감소합니다."
  ]
}
```

설명은 규칙 기반으로 생성하고, 매수·매도 명령으로 표현하지 않는다.

---

# 9. 작업 7 — 민감도 분석

최종 기능 검증을 위해 반드시 수행한다.

## 9.1 분석기간

```text
1년
3년
5년
```

## 9.2 CVaR 신뢰수준

```text
90%
95%
97.5%
```

## 9.3 가중치

```text
loss_minimization
balanced
esg_focused
```

## 9.4 턴오버

최소 3개 수준:

```text
low
default
high
```

## 9.5 사건 영향

```text
전체 사건 사용
가장 심각한 사건 제거
사건 페널티 제거
```

## 9.6 확인 항목

- 추천 비중이 과도하게 뒤집히는가
- 특정 사건 하나가 결과를 지배하는가
- ESG 제거 시 변화가 설명 가능한가
- 기간 변경 시 결과가 얼마나 달라지는가
- 추천 안정 구간이 지나치게 좁지 않은가

## 9.7 산출물

```text
sensitivity_results.csv
sensitivity_summary.json
```

---

# 10. 작업 8 — 테스트 작성

## 10.1 가격 테스트

```text
필수 열 누락
종목 누락
중복 날짜
음수 가격
문자열 가격
공통 거래일 없음
정상 데이터
```

## 10.2 하방위험 테스트

```text
CVaR 계산값 검증
신뢰수준 경계값
빈 수익률
MDD 단조 증가 가격
MDD 급락 가격
하방편차
```

## 10.3 ESG 테스트

```text
higher_is_worse
higher_is_better
unavailable 처리
reported 사건 제외
sanctioned 사건 강화
resolved 감쇠
scope_mismatch 불확실성
가중치 합계
```

## 10.4 최적화 테스트

```text
추천 비중 합계 1
각 비중 0.20~0.80
1% 단위
동일 입력 동일 결과
한 종목만 보유
현재가 기준 현재 비중
샘플 ESG 자동 사용 금지
```

## 10.5 사건 테스트

```text
주말 사건일
휴일 사건일
가격 범위 밖 사건
reported 제외
5거래일 미만 데이터
60일 이내 회복
미회복
```

## 10.6 테스트 파일

```text
tests/
├── test_price.py
├── test_downside.py
├── test_esg.py
├── test_events.py
├── test_optimizer.py
├── test_portfolio_status.py
└── test_sensitivity.py
```

---

# 11. 작업 9 — 실행 이력과 재현성

모든 결과에 다음 메타데이터를 저장한다.

```text
run_id
model_version
input_data_version
input_file_hash
price_period_start
price_period_end
number_of_price_observations
cvar_confidence
alpha
beta
gamma
min_weight
max_weight
grid_step
used_indicator_ids
excluded_indicator_ids
used_event_ids
generated_at
data_status
```

## `data_status` 규칙

```text
sample
reviewed
fallback
partial
```

실제 ESG 데이터가 불완전하면 `reviewed`가 아니라 `partial`을 고려한다.

---

# 12. 작업 10 — 개발 A와의 인터페이스 확정

## 12.1 최적화 입력

```json
{
  "holdings": [
    {
      "ticker": "005930",
      "quantity": 70,
      "average_price": 70000,
      "current_price": 82000
    },
    {
      "ticker": "000660",
      "quantity": 30,
      "average_price": 180000,
      "current_price": 210000
    }
  ],
  "risk_priority": "balanced",
  "turnover_weight": 0.10,
  "price_period_years": 3,
  "cvar_confidence": 0.95
}
```

## 12.2 최적화 출력

```json
{
  "current_weights": {
    "005930": 0.48,
    "000660": 0.52
  },
  "recommended_weights": {
    "005930": 0.56,
    "000660": 0.44
  },
  "current_total_risk": 0.54,
  "optimized_total_risk": 0.48,
  "risk_reduction_rate": 0.111,
  "current_cvar": 0.032,
  "optimized_cvar": 0.029,
  "current_esg_risk": 0.49,
  "optimized_esg_risk": 0.46,
  "turnover": 0.16,
  "portfolio_status": {
    "score": 46,
    "signal": "yellow"
  },
  "company_risks": {},
  "recommendation_confidence": "medium",
  "near_optimal_range": {
    "samsung_min": 0.53,
    "samsung_max": 0.59
  },
  "explanation": [],
  "warnings": [],
  "model_metadata": {}
}
```

## 12.3 사건 출력

```json
{
  "events": [
    {
      "event_id": "EVT-0001",
      "company_id": "005930",
      "event_date": "2024-05-29",
      "reaction_start_date": "2024-05-29",
      "return_1d": -0.018,
      "return_3d": -0.042,
      "return_5d": -0.029,
      "event_relative_min_return": -0.061,
      "window_max_drawdown": -0.048,
      "recovery_days": 13,
      "abnormal_return_5d": -0.021,
      "chart_data": []
    }
  ]
}
```

---

# 13. 작업 우선순위

## 최우선 — 하드코딩 제거

1. `esg.py` 구현
2. 실제 ESG 원천 데이터 연결
3. 고정 ESG 기본값 제거
4. 기업별 고정 `data_confidence` 제거
5. 설명문에서 계산하지 않은 주장 제거

## 두 번째 — 계산 정확성

6. 현재 비중을 현재가 기준으로 수정
7. 현재 포트폴리오 목적함수 직접 계산
8. 위험 프로필 이름과 가중치 통일
9. 사건 상태 필터 강화
10. 시장 최초 공개일 사용

## 세 번째 — 최종 기능

11. 포트폴리오 상태 점수와 신호등
12. 사건 결과 동적 저장
13. 근접 최적 구간
14. 추천 신뢰수준
15. 1·3·5년 및 CVaR 민감도 분석

## 네 번째 — 통합·검증

16. pytest
17. 실행 메타데이터
18. 결과 JSON 스키마 고정
19. 개발 A API 연결
20. 샘플·reviewed·fallback 상태 테스트

---

# 14. 권장 실행 일정

## 1단계 — 오전

```text
현재 코드 수정
현재가 기준 비중 계산
가중치 검증
프로필 이름 통일
```

## 2단계 — 오전 후반

```text
esg.py 구조 작성
정규화 규칙
불확실성 계산
사건 페널티 계산
중요도 가중합
```

## 3단계 — 오후 초반

```text
실제 ESG CSV 연결
고정 ESG 점수 제거
최적화 재실행
회사별 위험 결과 생성
```

## 4단계 — 오후 중반

```text
사건 상태 필터
시장 공개일 기준 분석
회복기간 확장
event_reactions.json 생성
```

## 5단계 — 오후 후반

```text
포트폴리오 상태 점수
민감도 분석
테스트
개발 A 전달용 함수·JSON 확정
```

---

# 15. 데이터 A에게 요청할 항목

데이터 B는 데이터 A에게 다음을 명확히 요청해야 한다.

```text
최종 12개 indicator_id
각 지표의 risk_direction
각 지표의 단위와 산식
3개년 값 또는 목표값
scope_mismatch
availability
data_confidence
review_status
사건별 linked_indicator_id
사건별 시장 최초 공개일
사건별 status
사건별 severity 근거
resolved_date
```

데이터가 아직 없으면 임의값을 만들지 말고 다음과 같이 처리한다.

```text
availability = unavailable
data_status = partial
recommendation_confidence = low
```

---

# 16. 완료 기준

데이터 B 작업은 다음 조건을 모두 만족해야 완료다.

## ESG

- 고정 ESG 점수 `0.42`, `0.55`를 reviewed 모드에서 사용하지 않는다.
- ESG 점수가 실제 원천 지표와 사건에서 계산된다.
- `Residual Risk`, `Issue Risk`, 중요도 가중합 결과가 저장된다.
- unavailable과 scope mismatch가 신뢰도에 반영된다.
- 지표별 중간 계산을 추적할 수 있다.

## 가격 위험

- 실제 가격으로 CVaR·MDD·하방편차가 계산된다.
- 1년·3년·5년 기간을 테스트할 수 있다.
- CVaR 90%·95%·97.5%를 테스트할 수 있다.

## 최적화

- 현재 비중은 현재가 기준이다.
- 추천 비중 합계는 항상 100%다.
- 각 비중은 20~80%다.
- 동일 입력은 동일 결과를 반환한다.
- 현재·추천 CVaR, ESG 위험, 턴오버를 구분해 반환한다.
- 추천 안정 구간과 신뢰수준을 반환한다.

## 사건

- reported와 rumor는 위험점수에 들어가지 않는다.
- 시장 최초 공개일 기준으로 주가 반응을 계산한다.
- 1일·3일·5일 수익률과 회복 기간이 실제 데이터로 생성된다.
- 화면용 하드코딩 숫자를 완전히 제거할 수 있는 JSON을 제공한다.

## 전달

- 개발 A가 노트북 없이 함수만 호출할 수 있다.
- 입력과 출력 스키마가 문서화돼 있다.
- pytest가 통과한다.
- 모델 실행 메타데이터가 저장된다.
- 샘플 결과와 실제 결과가 명확히 구분된다.

---

# 17. 데이터 B에게 그대로 전달할 최종 지시

> 현재 가격 검증, CVaR·MDD·하방편차, 1% 그리드서치, 사건 후 수익률 함수는 구현되어 있습니다. 하지만 ESG 위험이 아직 고정값에 의존하므로 최우선으로 `esg.py`를 구현해 실제 12개 지표와 공식 사건에서 `Exposure × (1-Management) + Controversy + Uncertainty`를 계산해 주세요. reviewed 모드에서는 샘플 ESG 기본값을 절대 사용하지 않도록 수정하고, 현재 비중은 평단가가 아니라 현재가로 계산해 주세요. 사건 분석은 approved 여부뿐 아니라 confirmed·sanctioned·resolved 상태만 계산 대상으로 하고 시장 최초 공개일을 기준일로 사용해 주세요. 이후 포트폴리오 상태 점수, 추천 신뢰수준, 근접 최적 구간, 1·3·5년 및 CVaR 민감도 분석과 pytest를 완료한 뒤 개발 A가 바로 호출할 수 있는 함수와 JSON 결과를 전달해 주세요.

---

# 18. 핵심 요약

```text
현재 구현됨:
가격 검증
수익률
CVaR
MDD
하방편차
그리드서치
턴오버
기본 사건 반응

반드시 추가:
실제 ESG 계산
사건 페널티
데이터 불확실성
현재가 기준 비중
민감도 분석
상태 점수
추천 신뢰도
테스트
API용 결과
```

데이터 B의 최종 성공 기준은 단순히 추천 비중 숫자를 출력하는 것이 아니다.

> 화면에 표시되는 ESG 위험, 하방위험, 추천 비중, 사건 수익률이 모두 실제 검수 데이터와 재현 가능한 Python 계산에서 생성되고, 어떤 입력과 규칙으로 계산됐는지 다시 확인할 수 있어야 한다.
