# Data Dictionary & Data A Notes

이 문서는 **데이터 A**가 수집 및 검수한 ESG 지표(`esg_indicators.csv`), ESG 사건(`events.csv`), 출처(`sources.csv`) 데이터셋의 스키마 및 수치 집계 기준, 데이터 B 및 백엔드 팀을 위한 주의사항을 명시합니다.

---

## 1. ESG 지표 정의 (`esg_indicators.csv`)

### 지표 목록 및 위험 방향

| Indicator ID | Category | Indicator Name | Unit | Risk Direction | 설명 |
|---|---|---|---|---|---|
| `E01` | E (환경) | 온실가스 배출집약도 | `tCO2e/억원` | `higher_is_worse` | 매출액 억원당 온실가스 배출량 (높을수록 위험) |
| `E02` | E (환경) | 용수 재이용률 | `%` | `higher_is_better` | 총 용수 사용량 대비 재이용수 비율 (높을수록 우수) |
| `E03` | E (환경) | 폐기물 재활용률 | `%` | `higher_is_better` | 총 발생 폐기물 대비 재활용 비율 (높을수록 우수) |
| `S01` | S (사회) | 산업재해율 (LTIR) | `건/백만시간` | `higher_is_worse` | 근로시간 100만시간 당 손실일수 재해 건수 (높을수록 위험) |
| `S02` | S (사회) | 협력사 ESG 실사 / 책임광물 비율 | `%` | `higher_is_better` | 협력사 ESG 평가 및 책임광물 검증 비율 (높을수록 우수) |
| `G01` | G (지배구조) | 사외이사 비율 | `%` | `higher_is_better` | 이사회 총 인원 대비 사외이사 비율 (높을수록 우수) |

### 사업 범위 (Business Scope) 및 불일치 (Scope Mismatch) 처리

- **삼성전자**:
  - `DS` (디바이스솔루션 / 반도체 사업부): `E01`, `E02`, `E03`, `S01` 지표 적용 (`scope_mismatch = false`)
  - `consolidated` (연결 전사): `S02` (협력사 ESG), `G01` (사외이사 비율) 지표 적용 (`scope_mismatch = true`)
- **SK하이닉스**:
  - `semiconductor`: `E01`, `E02`, `E03`, `S01`, `S02` 지표 적용 (`scope_mismatch = false`)
  - `consolidated`: `G01` 지표 적용 (`scope_mismatch = false`, SK하이닉스는 순수 반도체 기업)

---

## 2. 과거 사건 정의 (`events.csv`)

### 사건 상태 (Status) 및 모델 반영 가이드라인

| Status | 의미 | 모델 반영 기준 |
|---|---|---|
| `confirmed` | 공식기관/회사 공식 확인 | 모델 점수 반영 가능 |
| `sanctioned` | 정부/감독기관 행정처분/과징금 확정 | 강한 모델 점수 반영 |
| `resolved` | 보완 조치 완료 및 사건 종료 | 시간에 따른 감쇠 (Decay) 적용 대상 |
| `reported` | 언론 보도만 존재, 공식 확인 미완 | 모델 점수 반영 불가 (경고 표시 전용) |
| `rumor` | 소문/출처 미상 | 모델 반영 불가 |

---

## 3. Data B & Backend 팀 전달용 메모

1. **데이터 스키마 준수**: 모든 데이터는 JSON 스키마 (`schemas/data/*.schema.json`)의 필수 조건 및 Enum 값을 100% 만족합니다.
2. **범위 불일치 (`scope_mismatch`)**: 백엔드 및 UI에서는 삼성전자 `S02`, `G01` 수치 노출 시 연결 기준 수치임을 알리는 경고 아이콘/툴팁을 노출해야 합니다.
3. **사건 날짜 (`event_date_type`)**: 주가 영향 분석 시 최초 시장 공개일인 `event_date` 기준 1일, 3일, 5일 전후 수익률 변화 분석에 활용할 수 있습니다.
