# 칩버디 (Chip Buddy) 기능 구현 현황 분석 보고서

본 보고서는 **칩버디 (Chip Buddy) 기능 전수조사 보고서**를 기준으로 현재 프로젝트 소스 코드 및 템플릿 파일 구조를 면밀히 분석하여, **구현이 완료된 기능**과 **구현되지 않았거나 누락된 기능**을 구체적으로 대조한 분석 결과입니다.

---

## 1. 핵심 기능 (Must Have / Core) 구현 현황

| 기능명 | 요구사항 상세 | 구현 여부 | 대조 코드 / 파일 및 진단 결과 |
| :--- | :--- | :---: | :--- |
| **1.1 투자 분석 및 조정 기준 설정** | • 매수 이유 1문항 선택을 통한 설명 수준 설정<br>• 사용자 직접 조정 기준 선택을 통한 턴오버 가중치 연계 | **구현 완료** | • `/diagnosis` (매수이유) ➔ `/rebalancing-profile` (조정기준) ➔ `/settings-result` (설정완료) 다단계 마법사 및 세션 저장소(`SessionMiddleware`) 도입 완료.<br>• 조정 기준 유형별로 `turnover_weight` ($0.20$ / $0.10$ / $0.02$) 가중치가 최적화 엔진에 자동 매핑됨. |
| **1.2 포트폴리오 정보 입력 및 자동 계산** | • 입력 항목: 종목명, 보유 수량, 평균 매수가, 매수 이유(정성용)<br>• 입력 즉시 평가금액, 비중, 손익 실시간 자동 연산<br>• 한 종목만 입력해도 작동 (입력 유연성)<br>• 샘플 포트폴리오 원클릭 불러오기 | **구현 완료** | • 삼성전자와 SK하이닉스 각각 정성 분석용 **매수 이유** textarea 필드 추가 완료.<br>• `calculateRealtimeWeights()` JS 리스너로 수량 입력 시 실시간 평가액 및 비중 간이 자동 연산 지원.<br>• `required` 속성을 제거하여 한 종목만 입력해도 에러 없이 작동하도록 유연성 확보.<br>• '샘플 로드' 버튼 탑재로 원클릭 샘플 포트폴리오 자동 기입 구현 완료. |
| **1.3 내 투자 내비게이션 홈 (진단 대시보드)** | • 포트폴리오 종합 상태 점수 (0~100)<br>• 3색 직관적 위험 신호등 (초록/노랑/빨강)<br>• AI 포트폴리오 요약 리포트 (3문장 이내)<br>• 현재 비중 시각화 바<br>• 종목별 상태 카드 및 최적화 결과 미리보기 | **미구현**<br>(일부 누락) | • **종합 상태 점수 및 3색 신호등** 로직과 UI가 전혀 없음.<br>• **AI 포트폴리오 요약 리포트** 생성 및 전시 영역 부재.<br>• 최적화 이후 결과 비교 바와 개별 리스크 카드는 [risk_result.html](file:///c:/dev/sesac-mini-pjt2/src/frontend/templates/components/risk_result.html)에 부분 구현되었으나, 홈 화면 진입 시 대시보드 요약 형태로 렌더링되지는 않음. |
| **1.4 포트폴리오 최적화 엔진** | • 가격 하락 리스크 분석 (CVaR 95%, MDD, Downside Dev)<br>• ESG 관리위험 분석 (반도체 핵심 12개 지표, Residual Risk, Issue Risk 수식)<br>• 1% 그리드 서치 최적화 (20~80% 범위, 턴오버 페널티 반영) | **부분 구현** | • CVaR 및 MDD 등 하방위험은 [downside.py](file:///c:/dev/sesac-mini-pjt2/src/modeling/downside.py)에 연산 구현 완료.<br>• 그리드 서치(1% 단위) 및 턴오버 페널티 적용 목적함수는 [optimizer.py](file:///c:/dev/sesac-mini-pjt2/src/modeling/optimizer.py#L180-L244)에 구현됨.<br>• ⚠️ **ESG 관리위험**: PRD의 정교한 잔여/사건 위험 수식($Exposure \times (1 - Management) + Controversy + Uncertainty$)이 미적용되었으며, 사전에 고정된 단일 점수만 로드하여 연산함. |
| **1.5 최적화 결과 리포트** | • 추천 비중 비교 바<br>• 예상 위험 변화 분석<br>• 정성적 추천 근거 요약 (3문장 이내)<br>• 범위 불일치 경고 (`scope_mismatch = true`) 및 출처 표기<br>• 투자 면책 고지 | **구현 완료** | • [risk_result.html](file:///c:/dev/sesac-mini-pjt2/src/frontend/templates/components/risk_result.html)에 비중 비교, 감소율, 처방전 문구, 범위 불일치 경고(`scope_mismatch`) 및 면책 고지가 스키마에 맞추어 잘 반영됨. |
| **1.6 이슈 분석 화면** | • **현재 이슈 탭**: 공시/뉴스 정보 (Confirmed/Sanctioned 이상만 모델 반영), 요약문<br>• **과거 흐름 탭**: 유사 사건(1~3건)의 주가 수익률(1d/3d/5d), MDD, 회복 기간 시각화 | **미구현** | • **치명적 누락**: 백엔드에 HTML 렌더링을 위한 `/issues` 라우터가 없어 하단 탭 내비게이션 클릭 시 404 에러가 발생함.<br>• [issue_cards.html](file:///c:/dev/sesac-mini-pjt2/src/frontend/templates/components/issue_cards.html) 템플릿이 존재하나, 과거 흐름 탭의 수익률 데이터가 **완전히 하드코딩**(-1.8%, -4.2%, -6.1%)되어 있어 사건 반응 계산 모듈([events.py](file:///c:/dev/sesac-mini-pjt2/src/modeling/events.py))과 연동되지 않음. |
| **1.7 내 포트폴리오 수정 및 실시간 재연산** | • 수량, 매수가, 매수 이유 수정 기능<br>• 저장 시 실시간(2초 이내) 홈 화면 지표 재계산 및 업데이트 | **구현 완료** | • 메인 포트폴리오 입력 폼 상단에 `기준 변경` 링크 추가로 언제든 조정 기준 재설정 가능.<br>• 조정 기준 변경 시 세션의 `turnover_weight`가 즉시 갱신되어 최적화 재계산 및 비중 그래프 비동기 리프레시 반영 완료. |

---

## 2. 보조 기능 (Should Have / Supplementary) 구현 현황

| 기능명 | 요구사항 상세 | 구현 여부 | 대조 코드 / 파일 및 진단 결과 |
| :--- | :--- | :---: | :--- |
| **샘플 포트폴리오 원클릭 로드** | • 삼성전자 70%, SK하이닉스 30% 등 초기 데이터 자동 로드 | **구현 완료** | • '샘플 로드' 버튼 탑재 및 보유 수량, 평단가, 매수 이유 자동 로딩 JS 함수 바인딩 완료. |
| **최적화 가중치 설명 바텀시트** | • $\alpha$(하방), $\beta$(ESG), $\gamma$(턴오버) 가중치 설명 바텀시트 | **미구현** | • 관련 설명 UI 및 트리거 링크가 전혀 구현되지 않음. |
| **점수 및 최적화 근거 바텀시트** | • 상태 점수 및 추천 비중 계산 규칙 상세 팝업 | **미구현** | • 목적함수나 점수 산출 로직을 조회할 수 있는 팝업창 없음. |
| **ESG/하락 리스크 세부 지표 카드** | • 12개 ESG 지표 추세(개선/유지/악화) 및 개별 위험 정보 제공 | **미구현** | • 12개 지표의 현황을 시각화하거나 수준을 보여주는 카드가 누락됨. |
| **서버 세션 캐싱 / SQLite 임시 저장** | • 새로고침 시 입력 데이터 유실 방지를 위한 캐싱/SQLite 저장 | **미구현** | • 백엔드에 SQLite 의존성이나 세션 캐싱 로직이 전혀 없으며, 새로고침 시 폼이 완전히 리셋됨. |
| **데이터 리프레시 API (관리자용)** | • OpenDART, Yahoo Finance, 뉴스 API 기반 동적 갱신 (`POST /data/refresh`) | **미구현**<br>(Mock만 존재) | • [data.py](file:///c:/dev/sesac-mini-pjt2/src/backend/app/routes/data.py)에 라우터는 등록되어 있으나, 실제 외부 API 연동 없이 고정된 성공 메시지만 반환하는 Mock 상태임. |
| **폴백(Fallback) 안전 메커니즘** | • 갱신 실패 시 로컬의 최종 정상 검수 완료 데이터나 sample 데이터 활용 연산 보장 | **구현 완료** | • [esg_repository.py](file:///c:/dev/sesac-mini-pjt2/src/backend/app/repositories/esg_repository.py#L25-L36) 및 [price_repository.py](file:///c:/dev/sesac-mini-pjt2/src/backend/app/repositories/price_repository.py#L26-L35) 등 리포지토리 레이어에서 검증 실패 시 sample/fallback 데이터를 반환하는 예외 처리가 체계적으로 구현되어 있음. |

---

## 3. 핵심 발견 및 보완 요구 사안 요약

1. **치명적인 경로/라우팅 에러 (404)**
   - 하단 탭 내비게이션에는 '이슈 분석' 탭으로 가는 링크(`/issues`)가 지정되어 있으나, 백엔드 라우터([main.py](file:///c:/dev/sesac-mini-pjt2/src/backend/app/main.py)) 및 이슈 라우터([issues.py](file:///c:/dev/sesac-mini-pjt2/src/backend/app/routes/issues.py))에 HTML 페이지를 렌더링하는 경로가 없어 접근 시 에러가 발생합니다.
2. **과거 유사 사례 분석 하드코딩**
   - 과거 유사 사례 주가 분석 기능([issue_cards.html](file:///c:/dev/sesac-mini-pjt2/src/frontend/templates/components/issue_cards.html#L35-L45))이 완전히 고정된 텍스트로 하드코딩되어 있습니다. 동적 연산 모듈([events.py](file:///c:/dev/sesac-mini-pjt2/src/modeling/events.py))과 결합하여 동적으로 주가 반응률과 MDD를 계산 및 렌더링하도록 수정해야 합니다.
3. **투자 진단 설문 및 포트폴리오 입력 사안 누락** ➔ **해결 완료**
   - 간이 조정 기준 설정 마법사 도입 및 정성적 매수 이유 입력 textarea 구현, 샘플 데이터 원클릭 불러오기 연동 완료.
4. **실시간 자동 연산(Interactive 계산) 부재** ➔ **해결 완료**
   - `calculateRealtimeWeights()` JS 리스너를 결합하여 수량 변경 시 실시간 평가액 및 비중 간이 자동 연산 레이어를 폼 내에 반영 완료.
5. **서버 세션 캐싱 / SQLite 미반영**
   - 데이터 유실을 방지할 수 있는 브라우저/서버 세션 처리나 SQLite 로컬 임시 저장이 전혀 고려되어 있지 않습니다. (세션 미들웨어를 도입하여 분석 가중치 세션 저장은 완료되었으나 포트폴리오 폼 데이터 유실 방지는 미완 상태입니다.)
