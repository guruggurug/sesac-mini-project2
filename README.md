# 칩버디 (Chip Buddy)

삼성전자와 SK하이닉스의 **ESG 관리위험**과 **가격 하방위험**을 함께 분석하여, 두 종목 안에서 상대적으로 덜 취약한 추천 보유 비중을 계산하고 모바일 대시보드로 보여주는 2일 MVP 프로젝트입니다.

> 이 프로젝트는 주가 상승을 예측하거나 수익을 보장하는 서비스가 아닙니다.  
> 추천 비중은 삼성전자와 SK하이닉스 두 종목 안에서의 상대적 위험 배분이며, 반도체 산업 전체의 집중위험을 제거하지 않습니다.

---

## 1. 프로젝트 목표

사용자는 삼성전자와 SK하이닉스의 보유 수량과 평균 매수가를 입력하고 다음 결과를 확인할 수 있습니다.

- 현재 보유 비중
- 기업별 ESG 관리위험
- Historical CVaR 기반 가격 하방위험
- 현재 비중과 추천 비중 비교
- 예상 위험 감소율
- 추천 비중 산출 근거
- 과거 유사 사건 이후 1·3·5거래일 주가 흐름
- 데이터 출처와 신뢰도
- 샘플·검수 완료·폴백 데이터 상태

---

## 2. 분석 대상

| 기업 | 종목코드 | 비교 원칙 |
|---|---:|---|
| 삼성전자 | `005930` | DS부문 또는 반도체 사업 데이터 우선 |
| SK하이닉스 | `000660` | 반도체 사업 기준 |

삼성전자 DS부문 자료가 없어서 연결 전체 자료를 사용하면 반드시 다음과 같이 표시합니다.

```text
business_scope = consolidated
scope_mismatch = true
```

---

## 3. 핵심 분석 구조

```text
공식 ESG·사건 데이터
        +
주가 시계열 데이터
        ↓
ESG 관리위험 계산
가격 하방위험 계산
과거 사건 반응 계산
        ↓
20%~80% 제약의 1% 그리드서치
        ↓
현재 비중과 추천 비중 비교
        ↓
FastAPI
        ↓
모바일 대시보드
```

### 가격 하방위험

핵심 지표는 `Historical CVaR 95%`입니다.

보조지표로 다음을 사용할 수 있습니다.

- 최대 낙폭
- 하방편차
- 사건 이후 누적수익률
- 회복 기간

### 포트폴리오 최적화

기본 목적함수는 다음 요소를 결합합니다.

```text
총위험
= 가격 하방위험
+ ESG 관리위험
+ 현재 비중과의 차이에 대한 턴오버 페널티
```

기본 제약조건:

```text
삼성전자 비중 + SK하이닉스 비중 = 100%
각 종목 비중 = 20%~80%
탐색 간격 = 1%
```

모델 가중치는 코드에 직접 고정하지 않고 설정 파일에서 관리합니다.

---

## 4. MVP 범위

### Must Have

- 투자 위험 우선순위 선택
- 삼성전자·SK하이닉스 보유 정보 입력
- 현재 비중 계산
- ESG 위험 표시
- Historical CVaR 계산
- 추천 비중 계산
- 현재·추천 비중 비교
- 예상 위험 감소율 표시
- 샘플·검수·폴백 상태 표시
- 과거 사건 후 1·3·5거래일 반응 표시
- 출처 및 면책 문구 표시

### Should Have

- 최대 낙폭과 하방편차
- 추천 이유 자동 생성
- 현재 이슈와 과거 흐름 탭
- 포트폴리오 수정 후 재계산
- 데이터 신뢰도 표시

### 제외 범위

- 주가 방향 또는 기대수익률 예측
- 자동매매
- 삼성전자·SK하이닉스 외 종목
- 실시간 투자 추천
- 미확정 뉴스의 자동 점수 반영
- 고급 머신러닝
- Black–Litterman
- PCA 기반 ESG 점수
- 로그인 및 회원 관리
- 다종목 포트폴리오 최적화

---

## 5. 팀 역할

| 역할 | 핵심 책임 | 주요 산출물 |
|---|---|---|
| 데이터 A | ESG·사건 데이터 검수 | `esg_indicators.csv`, `events.csv`, `sources.csv` |
| 데이터 B | 위험 계산·최적화 | 위험 함수, 최적화 함수, 결과 JSON |
| 개발 A | 백엔드·API 통합 | FastAPI, 데이터 로더, OpenAPI |
| 개발 B | 화면·사용자 흐름 | Stitch UI, 프론트엔드, API 연결 |

### 데이터 A

- 공식 보고서와 공공기관 자료 수집
- ESG 지표 값·단위·연도·범위 확인
- 사건 후보의 공식 확인 여부 검수
- 검수 완료 CSV 작성

### 데이터 B

- 주가 검증과 수익률 계산
- Historical CVaR 계산
- ESG 위험 집계
- 턴오버 페널티
- 1% 그리드서치
- 사건 전후 수익률 분석

### 개발 A

- FastAPI 프로젝트 구성
- CSV·JSON 로더와 검증기
- 모델 함수 연결
- 샘플·검수·폴백 처리
- OpenAPI 문서화

### 개발 B

- Google Stitch 화면 초안 생성
- 모바일 페이지와 공통 컴포넌트 구현
- 더미 JSON 연결
- 실제 API 연결
- 로딩·오류·샘플·데이터 부족 상태 구현

---

## 6. 작업 시작 전 필수 확인

모든 팀원과 Antigravity 에이전트는 구현 전에 다음 순서로 문서를 확인해야 합니다.

```text
1. AGENTS.md
2. ROADMAP.md
3. PROGRESS.md
4. schemas 또는 명세 파일
5. 담당 작업 관련 문서
```

### 주요 문서

| 파일 | 역할 |
|---|---|
| `AGENTS.md` | 팀원과 AI 에이전트가 반드시 지켜야 하는 규칙 |
| `ROADMAP.md` | 2일 일정, 담당자, 우선순위, 완료 조건 |
| `PROGRESS.md` | 현재 작업 상태, 로그, 차단 요소 |
| `README.md` | 프로젝트 개요와 실행 안내 |
| `docs/product/PRD.md` | 사용자 요구사항과 기능 범위 |
| `schemas/` | 데이터와 API 형식 |
| `.env.example` | 필요한 환경변수 목록 |

`ROADMAP.md` 또는 `PROGRESS.md`가 없으면 기능 구현 전에 먼저 생성해야 합니다.

---

## 7. 권장 레포지토리 구조

```text
.
├── README.md
├── AGENTS.md
├── ROADMAP.md
├── PROGRESS.md
├── .gitignore
├── .env.example
│
├── docs/
│   ├── project/
│   ├── product/
│   ├── architecture/
│   ├── data/
│   ├── model/
│   ├── api/
│   ├── design/
│   ├── testing/
│   ├── presentation/
│   ├── decisions/
│   └── handoff/
│
├── schemas/
│   ├── data/
│   └── api/
│
├── data/
│   ├── dictionary/
│   ├── sample/
│   ├── raw/
│   ├── reviewed/
│   ├── processed/
│   └── snapshots/
│
├── src/
│   ├── modeling/
│   ├── backend/
│   ├── frontend/
│   └── shared/
│
├── prompts/
│   ├── antigravity/
│   ├── stitch/
│   ├── data-extraction/
│   └── event-classification/
│
├── stitch-export/
│   ├── raw/
│   ├── approved/
│   └── screenshots/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── e2e/
│   └── fixtures/
│
├── tools/
├── artifacts/
└── .github/
```

---

## 8. 데이터 디렉터리 규칙

```text
data/raw/
→ 외부에서 수집한 원본 및 후보 데이터

data/reviewed/
→ 사람이 검수하고 승인한 데이터

data/processed/
→ 모델 계산 결과

data/sample/
→ 병렬 개발과 데모를 위한 샘플 데이터
```

모델과 API는 `data/raw/`를 직접 읽으면 안 됩니다.

```text
raw
→ candidate
→ human review
→ reviewed
→ processed
→ API
→ UI
```

### 필수 검수 데이터

```text
data/reviewed/esg_indicators.csv
data/reviewed/events.csv
data/reviewed/sources.csv
data/reviewed/stock_prices.csv
```

### 필수 샘플 데이터

```text
data/sample/esg_indicators.sample.csv
data/sample/events.sample.csv
data/sample/stock_prices.sample.csv
data/sample/optimization-result.sample.json
```

샘플 데이터는 반드시 다음 상태를 포함해야 합니다.

```text
data_status = sample
```

---

## 9. 데이터 품질 원칙

### 결측값

- 결측값을 `0`으로 바꾸지 않습니다.
- 동종기업 평균으로 자동 대체하지 않습니다.
- `unavailable`로 유지합니다.
- 필요한 경우 데이터 신뢰도를 낮춥니다.
- 화면에는 `데이터 부족`으로 표시합니다.

### 사건 상태

허용 상태:

```text
rumor
reported
confirmed
sanctioned
resolved
```

모델 점수에 반영할 수 있는 상태:

```text
confirmed
sanctioned
검수된 resolved
```

`rumor`와 `reported`는 화면 경고로 표시할 수 있지만 ESG 점수에 반영하면 안 됩니다.

### 데이터 상태

```text
sample
reviewed
fallback
```

API와 화면은 현재 어떤 상태의 데이터를 사용 중인지 명확히 표시해야 합니다.

---

## 10. Google Antigravity 사용 규칙

Antigravity 작업 프롬프트에는 최소한 다음 항목이 포함되어야 합니다.

```text
Task ID
목표
수정 허용 파일
수정 금지 파일
입력
예상 출력
검증 명령
완료 조건
```

예:

```text
Task ID: DB-03
Goal: Historical CVaR 95% 구현

Allowed files:
- src/modeling/downside.py
- tests/unit/test_downside.py

Do not modify:
- data/reviewed/
- src/frontend/
- schemas/

Validation:
- pytest tests/unit/test_downside.py
```

Antigravity는 작업 시작 전에 `ROADMAP.md`와 `PROGRESS.md`를 읽고, 작업 시작·완료 시 진행 상태를 갱신해야 합니다.

자세한 규칙은 [`AGENTS.md`](./AGENTS.md)를 따릅니다.

---

## 11. Google Stitch 사용 규칙

Google Stitch 결과물은 완성 코드가 아니라 UI 초안입니다.

```text
Stitch에서 화면 생성
→ stitch-export/raw/ 저장
→ 팀 검토
→ 고정 숫자 제거
→ 컴포넌트 분리
→ 더미 JSON 연결
→ 실제 API 연결
→ stitch-export/approved/ 기록
```

주의사항:

- Stitch 결과를 프론트엔드 전체에 덮어쓰지 않습니다.
- 고정된 추천 비중을 남기지 않습니다.
- 390px 모바일 화면을 확인합니다.
- 한글 줄바꿈을 확인합니다.
- 색상만으로 위험을 표시하지 않습니다.
- 로딩·오류·샘플·폴백 상태를 구현합니다.
- 출처 링크와 면책 문구를 표시합니다.

---

## 12. 로컬 실행 준비

현재 기술 스택의 기본 방향:

- Python 3.11 이상
- FastAPI
- Pandas / NumPy
- 프론트엔드: React 기반 권장
- Google Stitch
- Google Antigravity

### 환경변수

```bash
cp .env.example .env
```

`.env`에 실제 키를 입력합니다.

```dotenv
APP_ENV=development
DATA_MODE=sample

DART_API_KEY=
NEWS_API_KEY=
GEMINI_API_KEY=

BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_API_BASE_URL=http://localhost:8000
```

> 실제 API 키가 없는 경우 `DATA_MODE=sample`로 실행합니다.

---

## 13. 권장 실행 명령

프로젝트 뼈대가 완성되면 다음과 같은 공통 명령을 제공하는 것을 권장합니다.

```bash
make install
make dev
make test
make validate-data
make demo
```

`Makefile`이 아직 없으면 각 서비스의 명령을 직접 실행합니다.

### 백엔드 예시

```bash
cd src/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Windows PowerShell:

```powershell
cd src/backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

기본 확인 주소:

```text
http://localhost:8000/health
http://localhost:8000/docs
```

### 프론트엔드 예시

```bash
cd src/frontend
npm install
npm run dev
```

기본 확인 주소:

```text
http://localhost:5173
```

> 실제 명령과 포트가 달라지면 이 README를 즉시 수정해야 합니다.

---

## 14. 최소 API

```text
GET  /health
POST /portfolio/calculate
POST /risk/esg
POST /risk/downside
POST /portfolio/optimize
GET  /issues/current
GET  /issues/historical
POST /data/refresh
```

`POST /data/refresh`는 raw 또는 candidate 데이터를 갱신하는 용도입니다. 검수 없이 `data/reviewed/`를 덮어쓰면 안 됩니다.

---

## 15. 테스트와 완료 조건

작업 완료 전 담당 영역에 맞는 검증을 실행합니다.

### 데이터

- 필수 열 존재
- 자료형 검사
- 중복 검사
- 날짜 형식
- 허용 enum
- 범위 정보
- 출처 존재
- 검수 상태

### 모델링

- 동일 입력에서 동일 결과
- 추천 비중 합계 100%
- 각 종목 비중 20%~80%
- CVaR 데이터 부족 처리
- 결측값 처리
- 미확정 사건 필터

### 백엔드

- 요청·응답 스키마
- 422·404·500 처리
- OpenAPI 예시
- sample·reviewed·fallback 상태
- 모델 함수 연결

### 프론트엔드

- lint
- build
- 모바일 390px
- 전체 페이지 이동
- 로딩·오류·빈 상태
- 고정 추천값 제거
- API 필드 호환

### 통합

```text
투자 진단
→ 포트폴리오 입력
→ 현재 비중 계산
→ 위험 계산
→ 추천 비중 계산
→ 화면 표시
→ 포트폴리오 수정
→ 재계산
```

작업 상태를 `done`으로 바꾸기 전에 `PROGRESS.md`와 `ROADMAP.md`를 함께 갱신합니다.

---

## 16. Git 협업 규칙

권장 브랜치:

```text
main
feature/data-a-*
feature/data-b-*
feature/backend-*
feature/frontend-*
fix/*
docs/*
```

권장 커밋 메시지:

```text
feat: add portfolio optimization endpoint
fix: filter reported events from ESG score
data: add reviewed ESG indicators
test: add CVaR constraint tests
docs: update roadmap and progress rules
chore: initialize repository structure
```

PR에는 다음 내용을 포함합니다.

- 변경 목적
- 변경 파일
- 데이터·API 형식 변화
- 검증 명령과 결과
- 샘플 또는 실제 데이터 여부
- Stitch 또는 Antigravity 사용 여부
- 남은 문제와 롤백 방법

---

## 17. 진행 관리

### `ROADMAP.md`

앞으로 무엇을 언제 누가 완료할지 관리합니다.

### `PROGRESS.md`

현재 무엇이 완료됐고, 진행 중이며, 막혀 있는지 기록합니다.

작업 시작:

```text
todo → in_progress
```

구현 완료 후 다른 역할의 검토가 필요함:

```text
in_progress → review
```

검증까지 완료:

```text
review → done
```

작업을 진행할 수 없음:

```text
in_progress → blocked
```

허용 상태:

```text
todo
in_progress
blocked
review
done
```

---

## 18. 최종 데모 흐름

1. 투자 위험 우선순위를 선택합니다.
2. 삼성전자와 SK하이닉스 보유 정보를 입력합니다.
3. 현재 비중과 위험 상태를 확인합니다.
4. ESG 위험과 가격 하방위험을 비교합니다.
5. 추천 비중과 예상 위험 감소율을 확인합니다.
6. 추천 이유를 확인합니다.
7. 과거 유사 사건 이후 주가 흐름을 확인합니다.
8. 데이터 상태, 출처, 한계를 확인합니다.
9. 보유 정보를 수정하고 재계산합니다.

---

## 19. 프로젝트 한계

- 두 종목만 비교합니다.
- 두 기업 모두 반도체 산업 위험에 노출됩니다.
- 과거 가격과 사건 데이터는 미래 결과를 보장하지 않습니다.
- ESG 데이터의 사업범위와 기준연도가 다를 수 있습니다.
- 삼성전자 연결 전체 자료는 DS부문과 직접 비교하기 어렵습니다.
- 미확정 뉴스는 위험 점수에 반영하지 않습니다.
- 본 결과는 투자 자문이나 매매 지시가 아닙니다.

---

## 20. 시작 순서

처음 참여하는 팀원은 다음 순서로 시작합니다.

```text
1. 레포지토리 최신 상태 받기
2. AGENTS.md 읽기
3. ROADMAP.md 읽기
4. PROGRESS.md 읽기
5. 담당 Task ID 확인
6. 필요한 샘플 데이터와 스키마 확인
7. PROGRESS.md에서 작업을 in_progress로 변경
8. 담당 작업 수행
9. 테스트와 검증 실행
10. PROGRESS.md와 ROADMAP.md 갱신
11. PR 생성
```

가장 중요한 원칙은 다음과 같습니다.

> 완벽한 데이터나 복잡한 모델보다, 작지만 검증된 데이터와 재현 가능한 계산으로 전체 사용자 흐름을 끝까지 완성하는 것을 우선합니다.
