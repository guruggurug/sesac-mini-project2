# 이슈 자동 수집·검증 계약

이 문서는 Chip Buddy의 전자공시·뉴스 이슈가 사람의 승인 없이 `raw → candidate → automated validation → processed → API → UI`로 이동하는 기준을 정의한다. 기계 판정의 단일 원본은 `schemas/data/issue-pipeline-rules.json`이며, 문서와 구현이 다르면 해당 JSON 규칙을 우선한다.

## 1. Candidate 계약

- 후보 행은 `schemas/data/event-candidates.schema.json`을 만족해야 한다.
- `raw` 수집 성공만으로 발행할 수 없다. 정규화·중복 검사·출처 확인을 모두 통과한 후보만 `validation_status=validated`와 `matched_event_id`를 갖는다.
- 공식 출처와 연결되지 않거나 계약을 위반한 후보는 `rejected`로 보존하고 `rejection_reason`을 기록한다.
- `pending` 후보는 처리 사건에 포함하지 않으며 ESG 점수나 추천 비중 계산의 입력이 될 수 없다.
- candidate의 `content_hash`는 본문 hash가 아니라 `company_id + normalized title + published_at`으로 만든 후보 identity hash다. 실제 원문 SHA-256은 source registry의 `content_hash`에 별도로 저장한다.

후보 중복 키는 다음 순서로 처음 사용 가능한 키를 선택한다.

1. `detection_source_type + source_name + external_id`
2. 추적 파라미터와 fragment를 제거한 `canonical_url`
3. `company_id + content_hash`

동일 키가 이미 있으면 새 후보를 추가하지 않고 기존 후보의 수집 시각과 원본 메타데이터만 갱신한다.

## 2. Source 계약

- 검증 출처는 `schemas/data/sources.schema.json`, 사건 연결은 `schemas/data/event-sources.schema.json`을 만족해야 한다.
- DART는 접수번호(`dart_receipt`), 정부·규제기관·기업 공식 사이트는 허용 도메인(`official_domain`), 뉴스는 canonical URL(`news_canonical_url`)로 검증한다.
- `validated=true`인 출처만 processed 사건의 근거가 될 수 있다.
- processed 출처는 `data/raw/reports/` 원문 파일, `file_name`, SHA-256 `content_hash`가 모두 존재하고 일치해야 한다.
- 사건마다 `is_primary=true`인 `official_confirmation` 출처가 정확히 하나 있어야 한다. 뉴스 탐지 링크는 `detection`, 기업 해명은 `company_response`로 별도 보존한다.
- 같은 DART 접수번호는 중복이다. 접수번호가 없으면 URL과 문서 제목이 모두 같은 경우에만 동일 출처로 본다. 같은 목록 URL에 게시된 서로 다른 보고서는 별도 출처로 허용한다.

## 3. 사건 중복 판정과 병합

다음 조건을 모두 만족하면 같은 사건으로 판정한다.

- `company_id`, `event_category`, `linked_indicator_id`가 같다.
- `market_event_date` 차이가 3일 이하다.
- `summary + severity_evidence`의 토큰 Jaccard 유사도가 0.65 이상이다.

위 3일·0.65 기준은 2026-07-22 팀 결정으로 MVP 자동 중복 판정 기준에 승인되었다. 규칙 변경 전에는 대표 중복·비중복 사건 표본으로 회귀 테스트를 먼저 추가한다.

중복 사건은 새 ID를 만들지 않고 다음과 같이 병합한다.

- 시장 사건일: 가장 이른 날짜
- 해결일: null이 아닌 가장 늦은 날짜
- 상태와 처분: 정의된 우선순위 중 가장 높은 값
- 출처: 합집합
- severity: 병합된 근거로 재계산

동일성 필드가 상충하면 자동 병합하지 않고 새 후보를 `rejected`로 남긴다. 불확실한 유사도는 ESG 점수에 반영하지 않는다.

## 4. Severity 자동 산정

- 규칙 버전은 사건의 `severity_rule_version`에 저장한다.
- 처분 기준 점수와 텍스트 키워드 점수 중 최댓값을 사용한다.
- 여러 키워드가 일치해도 합산하지 않는다. 상한은 5점이다.
- `negated_keyword_phrases`에 등록된 명시적 부정 문구는 키워드 판정 전에 제거한다. 예를 들어 `사망 없음`은 `사망` 5점 규칙을 작동시키지 않는다. 같은 문장에 별도의 실제 사망 표현이 있으면 그 표현은 계속 판정한다.
- 일치 키워드가 없으면 처분 기준 점수, 처분도 없으면 기본 1점을 사용한다.
- 실행 함수는 `calculate_event_severity`이며 동일 입력과 동일 규칙 버전은 항상 동일 결과를 내야 한다.

규칙 변경 시 `issue-pipeline-rules.json`의 버전을 올리고, 기존 processed 사건을 전부 재산정한 뒤 계약 테스트를 통과해야 한다.

## 5. 발행 조건

processed 사건은 다음을 모두 만족할 때만 발행한다.

1. 사건·출처·연결 스키마 통과
2. 날짜·URI format과 회사 ID·회사명 조합 통과
3. 공식 1차 출처 정확히 하나 존재하고 raw SHA-256 일치
4. 후보 및 사건 중복 검사 통과 또는 기존 사건으로 결정적 병합
5. candidate canonical URL·identity hash 재계산 값 일치
6. 저장 severity와 현재 규칙 재계산 값 일치
7. candidate→event→event-source→source 및 ESG→source 교차 참조 통과
8. `reported` 사건은 경고 표시는 가능하나 ESG 점수 계산에서는 제외
9. `confirmed` 또는 `resolved` 사건만 모델 재계산 요청 가능
