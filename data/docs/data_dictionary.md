# Data Dictionary & Data A Notes

이 문서는 **데이터 A**가 수집하고 자동 검증 규칙을 통과시킨 ESG 지표(`esg_indicators.csv`), ESG 사건(`events.csv`), 출처(`sources.csv`) 데이터셋의 스키마 및 수치 집계 기준을 명시합니다.

---

## 1. ESG 지표 정의 (`esg_indicators.csv`)

### 지표 목록 및 위험 방향

| Indicator ID | Category | Indicator Name | Unit | Risk Direction | 설명 |
|---|---|---|---|---|---|
| `E01` | E (환경) | 온실가스 배출집약도 | `tCO2e/억원` | `higher_is_worse` | 매출액 억원당 온실가스 배출량 (높을수록 위험) |
| `E02` | E (환경) | 용수 재이용률 | `%` | `higher_is_better` | 총 용수 사용량 대비 재이용수 비율 (높을수록 우수) |
| `E03` | E (환경) | 폐기물 재활용률 | `%` | `higher_is_better` | 총 발생 폐기물 대비 재활용 비율 (높을수록 우수) |
| `E04` | E (환경) | 공정가스 감축률 | `%` | `higher_is_better` | 반도체 공정가스 처리·저감 수준 (높을수록 우수) |
| `E05` | E (환경) | 유해화학물질 배출량 | `톤` | `higher_is_worse` | 유해화학물질 배출량 (높을수록 위험) |
| `S01` | S (사회) | 산업재해율 (LTIR) | `건/백만시간` | `higher_is_worse` | 근로시간 100만시간 당 손실일수 재해 건수 (높을수록 위험) |
| `S02` | S (사회) | 협력사 ESG 현장실사 비율 | `%` | `higher_is_better` | 협력사 ESG 평가 및 현장실사 비율 (높을수록 우수) |
| `S03` | S (사회) | 임직원 자발적 이직률 | `%` | `higher_is_worse` | 자발적으로 퇴사한 임직원 비율 (높을수록 위험) |
| `S04` | S (사회) | 정보보호 관리 수준 | `%` | `higher_is_better` | 정보보호 통제 및 관리 수준 (높을수록 우수) |
| `S05` | S (사회) | 책임광물 제3자 검증률 | `%` | `higher_is_better` | 책임광물 공급망 제3자 검증 비율 (높을수록 우수) |
| `G01` | G (지배구조) | 사외이사 비율 | `%` | `higher_is_better` | 이사회 총 인원 대비 사외이사 비율 (높을수록 우수) |
| `G02` | G (지배구조) | 정정공시 건수 | `건` | `higher_is_worse` | 연간 정정공시 건수 (높을수록 위험) |
| `G03` | G (지배구조) | 준법·수출통제 위반 건수 | `건` | `higher_is_worse` | 공식 제재 및 준법 위반 건수 (높을수록 위험) |

### 사업 범위 (Business Scope) 및 불일치 (Scope Mismatch) 처리

- **삼성전자**:
  - `DS` (디바이스솔루션 / 반도체 사업부): `E01`~`E05`, `S01` 지표 적용 (`scope_mismatch = false`)
  - `consolidated` (연결 전사): `S02`, `S03`, `S04`, `G01`~`G03` 적용 (`scope_mismatch = true`)
  - `unknown`: `S05` 적용 (`availability = unavailable`, `scope_mismatch = false`)
- **SK하이닉스**:
  - `semiconductor`: `E01`~`E05`, `S01`, `S03`, `S04`, `S05` 지표 적용 (`scope_mismatch = false`)
  - `consolidated`: `G01`~`G03` 적용 (`scope_mismatch = false`, SK하이닉스는 순수 반도체 기업)
  - `unknown`: `S02` 적용 (`availability = unavailable`, `scope_mismatch = false`)

현재 `G01`~`G03` 18행 및 `S02`/`S05` 중 결측 항목(총 24행)은 기존 임시 DART 접수번호 폐기 또는 공시 부재로 인해 `availability=unavailable`, `raw_value=null`로 전환했습니다. 공식 원문을 다시 수집하기 전까지 모델 입력에 사용할 수 없습니다.

---

## 2. 과거 사건 정의 (`events.csv`)

### 사건 상태 (Status) 및 모델 반영 가이드라인

| Status | 의미 | 모델 반영 기준 |
|---|---|---|
| `confirmed` | 공식기관/회사 공식 확인 | 모델 점수 반영 가능 |
| `resolved` | 보완 조치 완료 및 사건 종료 | 시간에 따른 감쇠 (Decay) 적용 대상 |
| `reported` | 언론 보도만 존재, 공식 확인 미완 | 모델 점수 반영 불가 (경고 표시 전용) |

제재 여부는 사건 상태와 분리하여 `enforcement_action`에 `no_action`, `investigation`, `corrective_order`, `fine`, `sanctioned` 중 하나로 기록합니다. 소문·출처 미상 데이터는 raw 단계에서 제외합니다.

사건 탐지 출처는 `detection_source_type`에 `dart_disclosure` 또는 `news`로 기록합니다. 뉴스 탐지 사건은 DART 또는 연결된 공식 원문을 확인해야 `confirmed`나 `resolved`가 될 수 있습니다.

---

## 3. Data B & Backend 팀 전달용 메모

1. **데이터 스키마 준수**: 모든 데이터는 JSON 스키마 (`schemas/data/*.schema.json`)의 필수 조건 및 Enum 값을 100% 만족합니다.
2. **범위 불일치 (`scope_mismatch`)**: 백엔드 및 UI에서는 삼성전자 `S02`, `G01` 수치 노출 시 연결 기준 수치임을 알리는 경고 아이콘/툴팁을 노출해야 합니다.
3. **사건 날짜**: 주가 영향 분석은 발생일인 `event_date`가 아니라 최초 시장 공개일인 `market_event_date`를 기준으로 수행해야 합니다.
