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

## 6. Production complete-bundle normalizer

- 운영 분류 규칙은 `issue-pipeline-rules.json`의 `candidate_classification`을 단일 원본으로 사용한다. Python 코드에 별도의 ESG 분류 키워드를 하드코딩하지 않는다.
- Open DART 후보 중 승인된 정규식 규칙과 일치하고 유효한 접수번호·공식 URL·raw 응답 SHA-256을 가진 후보만 `validated` 사건으로 변환한다.
- Open DART 목록 후보는 공식 `GET /api/document.xml`로 접수번호별 원문 ZIP을 추가 수집한다. 목록 제목만으로 사건을 확정하지 않으며, 원문 저장·안전 추출·본문 근거 확인을 먼저 통과해야 한다.
- 원문 ZIP은 `raw/dart/documents/<date>/`에 먼저 저장하고 SHA-256을 source evidence로 사용한다. ZIP member를 파일시스템에 직접 풀지 않으며 path traversal, 암호화 member, 파일 수 500개 초과, 압축 해제 총량 100 MiB 초과를 거절한다.
- XML·HTML·TXT에서 추출한 전체 텍스트는 최대 5,000,000자로 제한한다. candidate에는 승인된 `body_pattern` 주변의 근거 구간만 최대 2,000자로 저장한다.
- 제목과 본문이 같은 규칙으로 일치한 DART 법정공시는 `confirmed` 후보가 될 수 있다. 제목은 일반적이지만 본문에서만 탐지된 경우에는 `reported` 경고로 발행하며 `authority_confirmed=false`로 모델 재계산에서 제외한다.
- 본문에 승인된 사건 패턴이 없으면 `dart_document_no_approved_esg_event_match`로 거절한다. `산업재해율` 같은 단순 지표명은 본문 사건으로 분류하지 않도록 제목 패턴과 더 엄격한 `body_pattern`을 분리한다.
- 개별 원문 부재(`013`, `014`)는 해당 후보를 거절한다. 인증·네트워크·호출 제한·서버 장애는 회사 batch 실패로 전달하여 불완전한 rejected snapshot을 발행하지 않고 마지막 정상 데이터를 유지한다.
- 승인 규칙과 일치하지 않는 일반 공시는 `rejected`와 `no_approved_esg_event_rule_match` 사유로 보존한다. 임의로 `other` 사건을 만들지 않는다.
- 공식 확인 근거가 없는 뉴스 후보는 `official_confirmation_required`로 거절하며 모델 입력에 포함하지 않는다.
- 새 사건은 DART 공시일을 `official_disclosure_date`로 사용하고, 상세 발생일이나 해결일을 추측하지 않는다. 이후 공식 상태 변경 공시가 들어오면 같은 중복·병합 규칙으로 재평가한다.
- normalizer는 현재 활성 스냅샷을 직접 수정하지 않는다. 별도의 임시 complete bundle을 만들고 전체 검증 후 publisher에 전달하며, 성공·실패와 관계없이 임시 bundle을 정리한다.
- 한 회사의 DART 수집만 실패하고 다른 회사의 수집이 성공하면 `partial_success`로 정상 후보를 처리한다. 양사 모두 실패하면 발행하지 않고 기존 활성 스냅샷을 유지한다.
- 현재 운영 runtime에 실제 provider가 연결된 범위는 Open DART다.

## 7. 뉴스 collector 경계

- 뉴스 계층은 특정 API에 종속되지 않는 `NewsProvider` 계약을 사용한다. provider adapter는 로컬 보존이 허용된 응답 메타데이터만 `NewsRawPage.payload`로 반환해야 한다.
- provider 응답은 정규화보다 먼저 `raw/news/<provider>/<date>/`에 저장한다. 정규화 또는 provider 범위 검증이 실패해도 raw 근거는 남기며 active snapshot은 변경하지 않는다.
- provider 결과의 회사·검색어·시작일·종료일은 요청과 정확히 같아야 한다. 다르면 candidate를 만들지 않는다.
- 유효한 기사 URL은 host를 `source_name`으로 사용하고 추적 파라미터를 제거한 canonical URL을 계산한다. 기사 ID, canonical URL, company/content hash 순서로 중복을 판정한다.
- 형식이 유효한 새 뉴스는 먼저 `pending` candidate가 된다. malformed 또는 같은 batch 안의 중복 기사는 `rejected`와 구체적인 사유로 보존한다.
- complete-bundle normalizer에서 ESG 분류 규칙과 일치하더라도 뉴스만으로는 사건을 확정하지 않는다. 공식 근거가 없으면 `official_confirmation_required`로 거절한다.
- 향후 DART·정부기관·기업 공식 발표가 같은 사건을 확인하면 뉴스는 `detection` 출처로 연결할 수 있다. 뉴스 원문만으로 `confirmed`, severity 또는 Data B 재계산을 만들 수 없다.
- production 뉴스 제공자, 검색어, 호출 제한과 원문 보존 범위는 별도 승인 후 adapter로 연결한다. provider-neutral collector 기반 구현 자체는 외부 뉴스 API를 호출하지 않는다.
