# Data Dictionary & Data A Notes

이 문서는 **데이터 A**가 원문(지속가능경영보고서 6종: 삼성전자/SK하이닉스 각 2024~2026)을 직접 대조해 검증한 ESG 지표(`esg_indicators.csv`), ESG 사건(`events.csv`), 출처(`sources.csv`) 데이터셋의 스키마 및 수치 집계 기준을 명시합니다.

> 2026-07-24 갱신: 이전 버전은 원문 대조 없이 생성된 72행(2022~2024, 12지표 완비) 가정을 기술하고 있었으나 실제와 달랐습니다. 아래는 원문 재대조본(64행, 2020~2026)을 기준으로 다시 작성했습니다. 근거: `progress/DATA-A.md` 2026-07-24 작업 로그.
> 2026-07-25 갱신: DART 사업보고서(XI.3 제재 등과 관련된 사항)와 KRX KIND 기업지배구조보고서 원문을 확보해 SK하이닉스 G03(2022~2024년, 3행)과 G01(2025년, 1행)을 추가했습니다(총 68행). G01은 양사 산식이 완전히 동일해 이 데이터셋 최초의 `direct`(직접비교 가능) 지표가 되었습니다.

---

## 1. ESG 지표 정의 (`esg_indicators.csv`)

### 지표 목록 및 확보 현황 (총 68행 = 삼성전자 29행 + SK하이닉스 39행)

| Indicator ID | Category | Indicator Name(원문 기준) | Unit | Risk Direction | 확보 현황 |
|---|---|---|---|---|---|
| `E01` | E | 온실가스 배출집약도 (market-based) | `tCO2e(q)/억원` 등 | `higher_is_worse` | 양사 확보 (삼성 5행, SK 6행) |
| `E02` | E | 용수 재이용률/재이용량 | `%` 또는 `1,000 tonnes` | `higher_is_better` | 양사 확보하나 **단위 불일치**(삼성=재이용량 절대치, SK=재이용률 %) → `not_comparable` |
| `E03` | E | 폐기물 재활용률 | `%` | `higher_is_better` | 양사 확보 (SK=SASB 유해폐기물 재활용률, 삼성=DS부문 폐기물 재활용률 — 모집단 상이, `partial`) |
| `E04` | E | 공정가스 처리/감축 효율 | `%` | `higher_is_better` | 양사 확보하나 **지표 정의 상이**(SK=전사 배출감소율 단일지표, 삼성=PFC처리효율·NF3저감률 등 하위지표 3종) → `not_comparable` |
| `E05` | E | 유해물질/환경법규 관련 지표 | `건` 또는 `ton` | `higher_is_worse` | 양사 확보하나 **정의 상이**(삼성=유해물질 유출건수, SK=환경법규 위반건수+대기오염물질 총배출량 대체) → `not_comparable` |
| `S01` | S | 산업재해율 (LTIR/LTIFR) | `%` 또는 `건/20만시간` | `higher_is_worse` | 양사 확보하나 **단위 상이**(삼성=LTIR %, SK=LTIFR 빈도수) → `partial` |
| `S02` | S | 협력사 ESG 실사 / 책임광물 검증 | `개사` 또는 `%` | `higher_is_better` | 양사 확보하나 정의 상이(삼성=현장감사 건수기반, SK=이행률 %기반) → `partial` |
| `S03` | S | 임직원 이직률 | `%` | `higher_is_worse`(원문 lower_better를 동일 방향으로 환산) | 양사 확보하나 삼성 수치가 자발/비자발 포함 여부 불명 → `partial` |
| `S04` | S | 정보보안/개인정보 관리 | `%`, `건`, 또는 `boolean` | 삼성=`higher_is_better`, SK 인증행=`qualitative` | 양사 확보하나 성격 상이(삼성=정량 컨설팅 건수, SK=인증 여부(정성)+교육이수율(정량) 혼재) → `not_comparable` |
| `S05` | S | 책임광물(RMAP) 제3자 인증률 | `%` | `higher_is_better` | **SK만 확보**(1행). 삼성은 별도 외부보고서(Responsible Minerals Report)로 위임, 이 보고서엔 수치 없음 → `one_sided` |
| `G01` | G | 사외이사 비율 | `%` | `higher_is_better` | 양사 확보. 삼성 2행(2025=66.7%, 2026=62.5%), SK 1행(2025=55.6%, 9명 중 5명) — 산식 동일(사외이사/이사회 총원) → **`direct`(직접비교 가능)** |
| `G02` | G | 정정공시 건수 | `건` | `higher_is_worse` | **양사 미확보**. 지속가능경영보고서 범위 밖(DART 조사 필요, 별도 트랙) — `esg_indicators.csv`에 행 자체가 존재하지 않음 |
| `G03` | G | 개인정보위 제재/준법·제재 현황 | `건` | `higher_is_worse` | 양사 확보. 삼성=PIPC 단일 제재 1행(2023), SK=DART 사업보고서 XI.3 전 규제기관 제재 3행(2022~2024, 연도별 6/3/2건) — 정의 상이(`not_comparable`) |

**직접 비교 가능(`direct`)한 지표는 `G01` 1개입니다.** 나머지는 `partial`/`not_comparable`/`one_sided` 중 하나이며, 상세 근거는 `data/docs/indicator_comparability.csv`를 참고하세요. `not_comparable`/`one_sided` 지표는 기업 간 상대평가나 평균 계산에 사용하면 안 되며 개별 기업 설명용으로만 사용해야 합니다.

### 사업 범위 (Business Scope) 및 불일치 (Scope Mismatch) — 실측 기준

- **삼성전자**: 지표별로 공시 범위가 다릅니다.
  - `DS`(디바이스솔루션 반도체 사업부 단독): `E02`(용수 재이용량), `E03`(폐기물 재활용률), `E04`(공정가스 처리효율) — `scope_mismatch=false`
  - `consolidated`(DX+DS 전사 연결, 원문 표기 "DX+DS" 포함): `E01`(온실가스 배출집약도 — **DS 단독 원단위는 원문에 미공시**), `E05`, `S01`~`S04`, `G01`, `G03` — 스키마 규칙상 `scope_mismatch=true` 강제
- **SK하이닉스**: 사실상 반도체 단일 사업 회사이므로 전 지표를 `consolidated`로 공시하며 `scope_mismatch`는 항상 `false`입니다(스키마 규칙이 이 플래그를 강제하는 대상은 삼성전자뿐).

### 목표값(`target_*`) 컬럼

원문에서 지표 정의와 **정확히 일치**하는 수치 목표가 확인된 경우에만 채웠습니다(2건: SK E01 배출집약도 70%감축/2030/기준2020, 삼성 E03 DS한국 폐기물 재활용률 99.9%/2030). 그 외 지표는 Net Zero 선언, 취수량 목표(재이용량과 다른 지표) 등 정의가 다르거나 정성적 서술이라 `target_value`를 임의로 대응시키지 않고 `null` 처리했으며, 원문 목표는 각 행의 `note`에 그대로 남겨두었습니다. 반드시 `note`를 확인한 뒤 목표 대비 진행률을 계산하세요.

현재 결측(`unavailable`) 처리된 행은 없습니다(64행 전부 `availability=available`). `G02`는 행 자체가 없다는 점에 유의하세요(0으로 채우거나 평균에 포함하면 안 됩니다).

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

> 2026-07-25: 위 결함은 해소되었습니다 — 이벤트 증거 원문 3건을 사용자가 직접 다운로드해 `data/raw/reports/`에 저장했고, `validate_data_a_bundle()`이 전체 통과합니다(`progress/DATA-A.md` DATA-A-B01 참고).

---

## 3. Data B & Backend 팀 전달용 메모

1. **데이터 스키마 준수**: 모든 데이터는 JSON 스키마 (`schemas/data/*.schema.json`)의 필수 조건 및 Enum 값을 100% 만족합니다(ESG 지표 68행 개별 검증 통과).
2. **범위 불일치 (`scope_mismatch`)**: 백엔드 및 UI에서는 삼성전자 `E01`, `E05`, `S01`~`S04`, `G01`, `G03` 노출 시 DX+DS 연결 기준 수치임을 알리는 경고 아이콘/툴팁을 노출해야 합니다(위 1절 참고, 과거 문서의 "S02/G01만 해당" 기술은 부정확했습니다).
3. **사건 날짜**: 주가 영향 분석은 발생일인 `event_date`가 아니라 최초 시장 공개일인 `market_event_date`를 기준으로 수행해야 합니다.
4. **기존 산출물 무효화**: 이전 72행(허구 데이터) 기반으로 계산된 `event_reactions.json`/`optimization_result.json` 등은 무효이며 새 68행 기준으로 재계산이 필요합니다(`PROGRESS.md` Active Blockers `DATA-A-B02` 참고).
5. **비교 금지 지표**: `not_comparable`/`one_sided`로 분류된 지표(`E02`,`E04`,`E05`,`S04`,`S05`,`G03`)는 양사 평균이나 상대 순위 계산에 사용하지 말고 개별 기업 설명 카드에만 사용하세요. `G01`은 이제 유일하게 `direct` 비교가 가능합니다(2025년 기준 삼성 66.7% vs SK 55.6%).
