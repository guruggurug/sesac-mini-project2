# 개발 A 작업 가이드라인

## 1. 역할 한눈에 보기

개발 A의 역할은 **데이터 A가 만든 검증된 데이터와 데이터 B가 만든 계산 함수를 웹서비스에서 사용할 수 있도록 백엔드 API로 연결하는 것**이다.

```text
데이터 A → 검증된 ESG·사건 CSV
데이터 B → 위험 계산·최적화 함수
개발 A → 데이터와 모델을 연결하는 백엔드 API
개발 B → API 결과를 보여주는 프론트엔드 화면
```

개발 A는 ESG 점수를 직접 판단하거나, 최적화 공식을 새로 만드는 역할이 아니다.

### 개발 A가 하는 일

- FastAPI 백엔드 프로젝트 구조 정리
- 요청·응답 스키마 정의
- 샘플 CSV와 더미 응답으로 API 선개발
- CSV 로더와 데이터 검증기 구현
- 데이터 A의 실제 CSV 연결
- 데이터 B의 Python 함수 연결
- 오류 처리와 fallback 구현
- 개발 B가 사용할 API 응답 예시 제공
- 통합 테스트와 README 작성

### 개발 A가 하지 않는 일

- ESG 원문 자료 수집 및 사실 검증
- 사건의 중요도 판단
- CVaR 수식 설계
- 최적화 가중치 임의 수정
- 추천 비중 임의 변경
- 프론트엔드 화면 구현
- 미확정 뉴스의 자동 승인

---

# 2. 최종 목표

개발 A의 최종 목표는 아래 흐름이 끊기지 않도록 만드는 것이다.

```text
사용자가 보유 수량과 평균 매수가 입력
→ 백엔드가 현재 비중 계산
→ ESG 데이터와 주가 데이터 로드
→ 데이터 B의 위험 계산 함수 호출
→ 20~80% 범위에서 추천 비중 계산
→ 현재 위험과 추천 위험 비교
→ JSON 응답 반환
→ 개발 B 화면에 표시
```

개발 A의 성공 기준은 외부 API를 많이 붙이는 것이 아니다.

> 샘플 데이터로 전체 API가 먼저 동작하고, 이후 실제 CSV와 모델 함수를 코드 구조를 크게 바꾸지 않고 교체할 수 있으면 성공이다.

---

# 3. 작업 순서

```text
프로젝트 구조 확인
→ 백엔드 실행 환경 설정
→ /health 구현
→ 요청·응답 스키마 확정
→ 샘플 데이터 준비
→ 더미 API 구현
→ CSV 로더·검증기 구현
→ 실제 데이터 연결
→ 실제 모델 함수 연결
→ 오류·fallback 처리
→ 프론트엔드 연결
→ 전체 통합 테스트
```

---

# 4. 권장 폴더 구조

저장소의 기존 구조를 우선 사용하되, 백엔드 폴더가 `src/backend`라면 다음처럼 정리한다.

```text
src/
└── backend/
    ├── app/
    │   ├── main.py
    │   ├── routes/
    │   │   ├── health.py
    │   │   ├── portfolio.py
    │   │   ├── risk.py
    │   │   ├── optimization.py
    │   │   ├── issues.py
    │   │   └── data.py
    │   ├── schemas/
    │   │   ├── portfolio.py
    │   │   ├── risk.py
    │   │   ├── optimization.py
    │   │   └── issue.py
    │   ├── repositories/
    │   │   ├── price_repository.py
    │   │   ├── esg_repository.py
    │   │   └── event_repository.py
    │   ├── services/
    │   │   ├── portfolio_service.py
    │   │   ├── risk_service.py
    │   │   └── optimization_service.py
    │   ├── model_bridge/
    │   │   ├── downside_adapter.py
    │   │   ├── esg_adapter.py
    │   │   ├── event_adapter.py
    │   │   └── optimization_adapter.py
    │   ├── core/
    │   │   ├── config.py
    │   │   ├── exceptions.py
    │   │   └── constants.py
    │   └── utils/
    │       ├── csv_validator.py
    │       └── response_builder.py
    ├── data/
    │   ├── sample/
    │   ├── raw/
    │   ├── candidate/
    │   └── processed/
    ├── tests/
    │   ├── test_health.py
    │   ├── test_portfolio.py
    │   ├── test_risk.py
    │   └── test_optimization.py
    ├── requirements.txt
    ├── .env.example
    └── README.md
```

기존 파일이 이미 있다면 새로 전부 만들지 말고 역할에 맞게 정리한다.

---

# 5. 개발 환경 설정

## 5.1 Python 버전

README에 Python 3.11 이상이라고 되어 있으므로 Python 3.11 계열을 사용한다.

프로젝트 최상위 폴더에서:

```powershell
pyenv local 3.11.9
python --version
```

정상 출력 예:

```text
Python 3.11.9
```

## 5.2 가상환경

프로젝트 최상위 폴더에 `.venv`를 만든 경우 그대로 사용한다.

```powershell
.venv\Scripts\Activate.ps1
python -c "import sys; print(sys.executable)"
```

## 5.3 패키지 설치

`requirements.txt`가 `src/backend`에 있다면 프로젝트 최상위 폴더에서 다음처럼 실행한다.

```powershell
python -m pip install --upgrade pip
pip install -r src\backend\requirements.txt
```

## 5.4 절대 커밋하지 않을 파일

```text
.venv/
.env
__pycache__/
.pytest_cache/
*.pyc
```

`.gitignore`에 포함되어 있는지 확인한다.

---

# 6. 1단계: 기존 코드 상태 파악

개발을 시작하기 전에 다음을 먼저 확인한다.

```text
현재 백엔드 실행 파일
현재 API 목록
현재 데이터 파일 위치
현재 모델 코드 위치
requirements.txt
README 실행 명령
환경변수 파일
테스트 코드 존재 여부
```

PowerShell 예시:

```powershell
Get-ChildItem
Get-ChildItem src\backend
Get-ChildItem src\backend -Recurse -Depth 2
```

## 완료 기준

- 백엔드 진입 파일 위치를 설명할 수 있다.
- 서버 실행 명령을 안다.
- 데이터 파일 위치를 안다.
- 모델 함수가 어디에 있는지 안다.
- 현재 오류가 있다면 재현할 수 있다.

---

# 7. 2단계: 서버 기본 실행과 `/health`

먼저 어떤 데이터나 모델이 없어도 서버가 실행되어야 한다.

## 예시

`app/main.py`

```python
from fastapi import FastAPI

app = FastAPI(
    title="Chip Buddy API",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
```

실행 예시:

```powershell
cd src\backend
uvicorn app.main:app --reload
```

확인 주소:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

## 완료 기준

- 서버가 오류 없이 실행된다.
- `/health`가 HTTP 200을 반환한다.
- `/docs`에서 Swagger UI가 열린다.

---

# 8. 3단계: API 목록 고정

4일 MVP 기준 최소 API는 다음과 같다.

| 기능 | 메서드 | 경로 |
|---|---|---|
| 서버 상태 | GET | `/health` |
| 현재 포트폴리오 계산 | POST | `/portfolio/calculate` |
| ESG 위험 조회 | POST | `/risk/esg` |
| 하방위험 조회 | POST | `/risk/downside` |
| 추천 비중 계산 | POST | `/portfolio/optimize` |
| 현재 이슈 조회 | GET | `/issues/current` |
| 과거 사건 조회 | GET | `/issues/historical` |
| 시장 가격 조회 | GET | `/market/quotes` |
| 실시간 포트폴리오 평가 | POST | `/portfolio/summary` |
| 이슈 수동 동기화 | POST | `/sync/issues` |
| 이슈 동기화 상태 | GET | `/sync/status` |
| 레거시 데이터 갱신 호환 경로 | POST | `/data/refresh` |

Realtime API는 `schemas/api/README.md`와 JSON Schema 승인을 기준으로 구현한다. `/data/refresh`는 `BE-RT-03` 구현 전까지 HTTP 501을 반환하고, 구현 후에도 `/sync/issues`와 동일한 내부 동기화 서비스를 재사용해야 한다.

---

# 9. 4단계: 요청·응답 스키마 확정

실제 계산 로직보다 먼저 개발 A·개발 B·데이터 B가 공통으로 사용할 JSON 구조를 고정한다.

## 9.1 포트폴리오 입력 요청

```json
{
  "holdings": [
    {
      "ticker": "005930",
      "quantity": 70,
      "average_price": 70000
    },
    {
      "ticker": "000660",
      "quantity": 30,
      "average_price": 180000
    }
  ],
  "risk_priority": "balanced"
}
```

허용 종목:

```text
005930: 삼성전자
000660: SK하이닉스
```

허용 위험 우선순위 예:

```text
loss_minimization
balanced
esg_focus
```

## 9.2 최적화 응답

```json
{
  "current_weights": {
    "005930": 0.7,
    "000660": 0.3
  },
  "recommended_weights": {
    "005930": 0.54,
    "000660": 0.46
  },
  "current_total_risk": 0.58,
  "optimized_total_risk": 0.49,
  "risk_reduction_rate": 0.155,
  "company_risks": {
    "005930": {
      "esg_risk": 0.42,
      "downside_risk": 0.38,
      "total_risk": 0.40
    },
    "000660": {
      "esg_risk": 0.55,
      "downside_risk": 0.47,
      "total_risk": 0.51
    }
  },
  "explanation": [
    "현재 삼성전자 비중이 위험 기준에서 높습니다.",
    "두 기업의 ESG 위험과 가격 하방위험을 함께 반영했습니다."
  ],
  "data_status": "sample",
  "warning": null
}
```

## 9.3 이슈 응답

```json
{
  "events": [
    {
      "event_id": "EVT001",
      "company_name": "SK하이닉스",
      "event_category": "occupational_safety",
      "event_date": "2024-03-15",
      "status": "confirmed",
      "summary": "반도체 사업장 안전사고",
      "official_source_url": "https://example.com",
      "return_1d": -0.018,
      "return_3d": -0.042,
      "return_5d": -0.029,
      "max_drawdown": -0.061,
      "recovery_days": 13
    }
  ],
  "data_status": "sample"
}
```

## 완료 기준

- 개발 B가 필요한 필드를 확인했다.
- 데이터 B가 함수 출력 형식을 확인했다.
- 잘못된 요청은 422를 반환한다.
- 모든 비율은 0~1 또는 퍼센트 중 하나로 통일했다.

---

# 10. 5단계: 샘플 데이터 준비

실제 데이터 A 결과가 없어도 API 개발을 진행한다.

## `data/sample/esg_scores_sample.csv`

```csv
company_id,esg_risk_score,data_confidence,data_status
005930,0.40,high,sample
000660,0.55,medium,sample
```

## `data/sample/events_sample.csv`

```csv
event_id,company_id,company_name,event_category,event_date,status,severity,summary
SAMPLE001,005930,삼성전자,occupational_safety,2024-03-15,confirmed,3,샘플 안전사고
SAMPLE002,000660,SK하이닉스,environmental_violation,2024-05-10,confirmed,4,샘플 환경사건
```

## 주의

샘플 데이터는 실제 데이터처럼 보이면 안 된다.

모든 응답에 다음을 포함한다.

```json
{
  "data_status": "sample"
}
```

---

# 11. 6단계: 더미 API 먼저 구현

데이터 B의 모델 함수가 아직 없어도 응답 형식부터 완성한다.

예시:

```python
from typing import Any


def mock_optimize() -> dict[str, Any]:
    return {
        "current_weights": {"005930": 0.7, "000660": 0.3},
        "recommended_weights": {"005930": 0.54, "000660": 0.46},
        "current_total_risk": 0.58,
        "optimized_total_risk": 0.49,
        "risk_reduction_rate": 0.155,
        "company_risks": {
            "005930": {
                "esg_risk": 0.42,
                "downside_risk": 0.38,
                "total_risk": 0.40,
            },
            "000660": {
                "esg_risk": 0.55,
                "downside_risk": 0.47,
                "total_risk": 0.51,
            },
        },
        "explanation": [
            "현재 삼성전자 비중이 위험 기준에서 높습니다.",
            "ESG 위험과 가격 하방위험을 함께 반영했습니다.",
        ],
        "data_status": "sample",
        "warning": "샘플 계산 결과입니다.",
    }
```

## 완료 기준

개발 B가 실제 API 없이도 다음 화면을 만들 수 있다.

- 현재 비중
- 추천 비중
- 위험 감소율
- 기업별 ESG 위험
- 기업별 하방위험
- 현재 이슈
- 과거 사건

---

# 12. 7단계: CSV 로더와 검증기 구현

개발 A는 데이터의 학술적 의미가 아니라 **시스템에서 안전하게 읽히는지** 검증한다.

## 12.1 ESG CSV 검사

필수 검사:

```text
필수 열 존재
company_id 허용값
중복 행
숫자 변환 가능 여부
availability 허용값
status 허용값
빈 파일 여부
scope_mismatch 존재 여부
```

## 12.2 사건 CSV 검사

```text
event_id 중복
날짜 형식 YYYY-MM-DD
company_id 허용값
status 허용값
공식 URL 존재 여부
자동 검증된 confirmed 또는 resolved 필터 가능 여부
```

## 12.3 주가 CSV 검사

```text
날짜 열 존재
날짜 중복 없음
날짜 오름차순
가격 결측 여부
두 종목 공통 거래일 존재
가격 숫자 변환 가능
```

## 검증 실패 시

서버를 강제로 종료시키기보다 명확한 예외를 반환한다.

예:

```json
{
  "detail": {
    "code": "INVALID_ESG_SCHEMA",
    "message": "esg_indicators.csv에 필수 열 indicator_id가 없습니다."
  }
}
```

---

# 13. 8단계: 저장 영역 구분

데이터 상태에 따라 폴더를 구분한다.

```text
data/raw/
외부 API나 뉴스 검색으로 가져온 원본

data/candidate/
원본을 정규화한 자동 검증 대상 후보

data/processed/
스키마·공식 출처·상태·근거·중복 검증을 통과해 원자적으로 발행된 데이터

data/sample/
개발·데모용 샘플 데이터
```

권장 파일:

```text
data/candidate/news_candidates.csv
data/processed/esg_indicators.csv
data/processed/events.csv
data/processed/stock_prices.csv
data/processed/risk_results.json
data/processed/optimization_results.json
```

## 중요한 규칙

```text
raw·candidate 데이터 → 모델에 직접 사용 금지
reported 사건 → 점수 반영 금지
confirmed 또는 resolved 사건 → 자동 스키마·공식 출처 검증 통과 시 모델 반영 가능
sanctioned → 사건 상태가 아니라 enforcement_action 값
```

---

# 14. 9단계: 데이터 A의 실제 파일 연결

데이터 A가 실제 CSV를 전달하면 샘플 파일을 대체한다.

```text
data/sample/esg_scores_sample.csv
→ data/processed/esg_indicators.csv

data/sample/events_sample.csv
→ data/processed/events.csv
```

## 연결 전에 확인

```text
필수 열이 있는가
파일이 비어 있지 않은가
자동 검증을 통과한 validated 데이터만 포함되는가
reported 사건이 분리되는가
삼성전자 DS와 전사 범위가 표시되는가
결측값을 임의로 채우지 않았는가
```

## 응답 상태 변경

```text
data_status = sample
→ data_status = validated
```

---

# 15. 10단계: 데이터 B 모델 함수 연결

데이터 B에게 노트북이 아니라 **호출 가능한 Python 함수**를 요청한다.

필요 함수 예:

```python
calculate_downside_risk(price_df)
calculate_esg_risk(esg_df)
calculate_event_reaction(price_df, events_df)
optimize_portfolio(
    returns,
    esg_scores,
    current_weights,
    risk_profile,
)
```

## 어댑터 구조

데이터 B 함수 이름이나 출력 형식이 바뀌어도 API 전체가 흔들리지 않도록 어댑터를 둔다.

```text
API route
→ service
→ model adapter
→ 데이터 B 함수
→ 응답 스키마 변환
```

예:

```python
from typing import Any


def run_portfolio_optimization(
    returns: Any,
    esg_scores: dict[str, float],
    current_weights: dict[str, float],
    risk_profile: str,
) -> dict[str, Any]:
    result = optimize_portfolio(
        returns=returns,
        esg_scores=esg_scores,
        current_weights=current_weights,
        risk_profile=risk_profile,
    )

    return {
        "recommended_weights": result["weights"],
        "current_total_risk": result["current_risk"],
        "optimized_total_risk": result["optimized_risk"],
        "risk_reduction_rate": result["risk_reduction_rate"],
    }
```

## 완료 기준

- 같은 입력은 같은 결과를 반환한다.
- 추천 비중 합계가 1이다.
- 각 종목 비중은 0.2~0.8이다.
- 모델 오류가 발생해도 서버 전체가 종료되지 않는다.

---

# 16. 11단계: 포트폴리오 계산 로직

사용자 입력에서 현재 비중을 계산한다.

## 계산 기준

```text
평가금액 = 보유 수량 × 현재 가격
현재 비중 = 종목 평가금액 ÷ 전체 평가금액
```

평균 매수가는 수익률·손익 표시에는 사용할 수 있지만, 현재 비중은 현재 가격을 기준으로 계산한다.

## 예외 처리

```text
두 종목 수량이 모두 0
현재 가격이 없음
수량이 음수
평균 매수가가 음수
허용되지 않은 ticker
```

이 경우 400 또는 422 오류를 명확히 반환한다.

---

# 17. 12단계: 오류와 fallback 처리

다음 상황을 반드시 고려한다.

```text
ESG 파일 없음
사건 파일 없음
주가 파일 없음
CSV 열 이름 불일치
가격 데이터 기간 부족
데이터 B 함수 오류
외부 API 호출 실패
```

권장 흐름:

```text
최신 processed 데이터 사용 시도
→ 실패
→ 마지막 정상 processed 스냅샷 사용
→ 실패
→ sample 데이터 사용
→ 응답에 상태와 경고 포함
```

응답 예:

```json
{
  "data_status": "fallback",
  "warning": "최신 데이터 로드에 실패해 마지막 정상 결과를 사용했습니다."
}
```

상태 값 권장:

```text
sample
validated
fallback
```

`unavailable`은 응답 전체의 `data_status`가 아니라 개별 값의 `availability`에만 사용한다.

---

# 18. 13단계: 개발 B와 연결

개발 B에게 아래를 전달한다.

```text
백엔드 실행 주소
Swagger 문서 주소
API별 요청 예시
API별 응답 예시
오류 응답 예시
data_status 의미
CORS 설정 여부
```

## 화면과 API 연결표

| 화면 | API |
|---|---|
| 포트폴리오 입력 | `POST /portfolio/calculate` |
| ESG 위험 카드 | `POST /risk/esg` |
| 하방위험 카드 | `POST /risk/downside` |
| 추천 비중 | `POST /portfolio/optimize` |
| 현재 이슈 | `GET /issues/current` |
| 과거 사건 | `GET /issues/historical` |

## CORS 예시

프론트엔드 개발 서버가 다른 포트를 사용한다면 FastAPI에 CORS를 설정한다.

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

개발 환경에서만 허용하고, 배포 시에는 실제 도메인만 등록한다.

---

# 19. 14단계: 테스트

## 19.1 필수 테스트

### 서버

```text
/health가 200 반환
/docs 접속 가능
```

### 포트폴리오

```text
정상 보유 수량 입력
한 종목만 보유
두 종목 모두 0
음수 수량
잘못된 ticker
```

### 데이터

```text
CSV 정상
필수 열 누락
빈 파일
중복 행
잘못된 날짜
숫자 열 문자열
```

### 최적화

```text
추천 비중 합계 100%
각 종목 20~80%
같은 입력에서 같은 결과
현재 위험과 추천 위험 비교 가능
```

### 사건

```text
reported 사건은 점수 반영 제외
confirmed 사건은 조회 가능
confirmed/resolved 사건은 자동 검증 통과 시 조회·모델 반영 가능하고 sanctioned는 enforcement_action으로만 노출
중복 사건 제외
```

## 19.2 pytest 실행 예시

백엔드 폴더에서:

```powershell
pytest
```

상세 출력:

```powershell
pytest -v
```

---

# 20. 외부 API 연결은 마지막

정적 데이터와 실제 모델 연결이 완료되기 전에는 외부 API를 먼저 붙이지 않는다.

권장 우선순위:

```text
1. 정적 CSV로 전체 기능 동작
2. 데이터 A 실제 CSV 연결
3. 데이터 B 실제 모델 연결
4. 프론트엔드 통합
5. 시간이 남으면 외부 갱신 API
```

외부 갱신 후보:

```text
OpenDART 공시 목록
주가 최신 데이터
뉴스 후보 검색
```

## `/data/refresh`의 역할

```text
외부 데이터 수집
→ raw 또는 candidate 폴더 저장
→ 스키마·공식 출처·상태·근거·중복 자동 검증
→ 검증 전체 통과 시 processed 스냅샷 원자적 발행
→ 검증 실패 후보는 rejected로 유지하고 기존 processed 스냅샷 보존
```

외부 데이터가 곧바로 모델 입력을 덮어쓰면 안 된다.

---

# 21. README에 반드시 적을 내용

```text
필요 Python 버전
가상환경 생성·활성화 방법
패키지 설치 명령
환경변수 설정 방법
백엔드 실행 명령
테스트 실행 명령
데이터 파일 위치
API 문서 주소
샘플 데이터 여부
오류 발생 시 확인 방법
```

예시:

```powershell
pyenv local 3.11.9
.venv\Scripts\Activate.ps1
pip install -r src\backend\requirements.txt
cd src\backend
uvicorn app.main:app --reload
```

---

# 22. 개발 A 하루 일정

## 오전 09:00~10:00 — 환경과 구조 확인

```text
기존 코드 파악
Python·venv 확인
패키지 설치
서버 실행
/health 구현
```

## 오전 10:00~11:30 — 스키마와 샘플 데이터

```text
Pydantic 요청·응답 모델
샘플 ESG·사건·가격 파일
API 응답 예시
```

## 오전 11:30~12:30 — 더미 API

```text
/issues/current
/issues/historical
/portfolio/calculate
/risk/esg
/risk/downside
/portfolio/optimize
```

## 오후 13:30~15:00 — 로더와 검증

```text
CSV 로더
필수 열 검사
데이터 타입 검사
상태값 검사
오류 응답
```

## 오후 15:00~16:00 — 실제 데이터 연결

```text
데이터 A CSV 연결
sample → validated 전환
reported 사건 필터
```

## 오후 16:00~17:00 — 실제 모델 연결

```text
데이터 B 함수 연결
어댑터 작성
응답 형식 변환
오류 처리
```

## 오후 17:00 이후 — 통합

```text
개발 B API 연결
CORS
전체 사용자 흐름 테스트
README 정리
시간이 남으면 /data/refresh
```

---

# 23. 개발 A 체크리스트

## 환경

- [ ] Python 3.11.x가 적용되어 있다.
- [ ] `.venv`가 활성화된다.
- [ ] `requirements.txt` 설치가 성공한다.
- [ ] `.env`가 Git에 포함되지 않는다.

## 서버

- [ ] `/health`가 200을 반환한다.
- [ ] `/docs`가 열린다.
- [ ] 백엔드 실행 명령이 README에 있다.

## 데이터

- [ ] 샘플 데이터로 먼저 동작한다.
- [ ] raw·candidate·processed 데이터가 분리된다.
- [ ] CSV 필수 열을 검증한다.
- [ ] reported 사건을 모델에서 제외한다.
- [ ] 결측값을 임의로 채우지 않는다.

## 모델

- [ ] 데이터 B 함수를 Python 함수로 호출한다.
- [ ] 추천 비중 합계가 1이다.
- [ ] 각 비중이 0.2~0.8이다.
- [ ] 같은 입력은 같은 결과를 낸다.
- [ ] 모델 오류가 서버 전체를 종료시키지 않는다.

## API

- [ ] 요청과 응답 스키마가 고정되어 있다.
- [ ] 개발 B에게 응답 예시를 전달했다.
- [ ] sample·validated·fallback 상태가 구분된다.
- [ ] 오류 메시지가 구체적이다.

## 통합

- [ ] 프론트엔드에서 API 호출이 성공한다.
- [ ] 포트폴리오 수정 후 재계산된다.
- [ ] 로딩·오류·데이터 부족 상태가 표시된다.
- [ ] 전체 데모 흐름이 끊기지 않는다.

---

# 24. 조장이 개발 A에게 확인할 질문

```text
서버가 실행돼?
/health가 200을 반환해?
샘플 데이터만으로 모든 API가 응답해?
데이터 A 파일이 없어도 서버가 죽지 않아?
실제 CSV로 교체할 때 코드를 많이 수정해야 해?
reported 사건이 모델 입력에 들어가지 않아?
데이터 B 함수는 어디에서 호출해?
모델 함수가 실패하면 어떤 응답을 반환해?
추천 비중 합계가 100%인지 검사해?
개발 B에게 요청·응답 예시를 전달했어?
README만 보고 새 환경에서 실행할 수 있어?
```

---

# 25. 최종 완료 조건

개발 A 작업은 아래 조건을 모두 충족하면 완료다.

```text
1. 새 환경에서 패키지 설치와 서버 실행이 가능하다.
2. /health와 Swagger 문서가 정상 동작한다.
3. 샘플 데이터로 전체 API가 응답한다.
4. 데이터 A의 실제 CSV를 연결할 수 있다.
5. 데이터 B의 계산 함수를 API에서 호출할 수 있다.
6. 추천 비중 합계와 20~80% 제약을 검증한다.
7. reported 사건은 모델에 반영하지 않는다.
8. 오류 시 fallback과 경고를 반환한다.
9. 개발 B가 API를 연결해 전체 화면을 시연할 수 있다.
10. README만 보고 다른 팀원이 실행할 수 있다.
```

---

# 26. 역할 최종 정리

```text
데이터 A
검증된 ESG·사건 데이터를 만든다.

데이터 B
위험과 추천 비중을 계산한다.

개발 A
데이터와 계산 함수를 API로 연결한다.

개발 B
사용자가 입력하고 결과를 이해할 수 있는 화면을 만든다.
```

개발 A가 가장 우선해야 할 것은 외부 API 자동화가 아니라 다음 한 문장이다.

> 샘플 데이터로 전체 백엔드 흐름을 먼저 완성하고, 실제 데이터와 모델을 안전하게 교체할 수 있는 구조를 만든다.
