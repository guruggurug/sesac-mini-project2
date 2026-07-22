import os
import csv
import hashlib
import json
import jsonschema
from urllib.parse import urlsplit
from app.core.config import BASE_DIR
from app.core.exceptions import CSVValidationError
from app.utils.issue_rules import (
    calculate_event_severity,
    candidate_content_hash,
    candidate_dedup_key,
    canonicalize_url,
    load_issue_rules,
    source_dedup_key,
    events_are_duplicates,
)

# 스키마 파일 경로 설정
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas", "data")
ESG_SCHEMA_PATH = os.path.join(SCHEMAS_DIR, "esg-indicators.schema.json")
EVENTS_SCHEMA_PATH = os.path.join(SCHEMAS_DIR, "events.schema.json")
PRICES_SCHEMA_PATH = os.path.join(SCHEMAS_DIR, "stock-prices.schema.json")
CANDIDATES_SCHEMA_PATH = os.path.join(SCHEMAS_DIR, "event-candidates.schema.json")
SOURCES_SCHEMA_PATH = os.path.join(SCHEMAS_DIR, "sources.schema.json")
EVENT_SOURCES_SCHEMA_PATH = os.path.join(SCHEMAS_DIR, "event-sources.schema.json")
COMPANY_NAMES = {"005930": "삼성전자", "000660": "SK하이닉스"}
FORMAT_CHECKER = jsonschema.FormatChecker()

def load_schema(schema_path: str) -> dict:
    """
    JSON Schema 파일을 로드
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

def safe_cast_value(val: str, target_type: str):
    """
    문자열 값을 스키마에 정의된 적절한 기본 타입으로 변환
    """
    if val == "" or val.lower() in ("null", "nan", "none"):
        return None
    
    if target_type == "number":
        try:
            return float(val)
        except ValueError:
            return val
    elif target_type == "integer":
        try:
            return int(val)
        except ValueError:
            return val
    elif target_type == "boolean":
        if val.lower() in ("true", "1", "t", "y", "yes"):
            return True
        elif val.lower() in ("false", "0", "f", "n", "no"):
            return False
        return val
    return val

def parse_and_cast_row(row: dict, schema: dict) -> dict:
    """
    JSON Schema의 properties 정보를 활용하여 CSV 행 데이터의 타입을 강제 캐스팅
    """
    properties = schema.get("properties", {})
    cast_row = {}
    
    for key, val in row.items():
        if key not in properties:
            cast_row[key] = val
            continue
            
        prop_info = properties[key]
        prop_type = prop_info.get("type")

        # JSON Schema permits nullable unions such as
        # {"type": ["number", "null"]}. CSV values arrive as strings, so
        # select the concrete non-null type before casting. Empty values are
        # still converted to None by safe_cast_value.
        if isinstance(prop_type, list):
            concrete_types = [item for item in prop_type if item != "null"]
            prop_type = concrete_types[0] if concrete_types else "string"

        # oneOf/anyOf 다중 타입 대응 (null 허용 등)
        if not prop_type:
            alternatives = prop_info.get("oneOf") or prop_info.get("anyOf") or []
            types = [
                item.get("type")
                for item in alternatives
                if item.get("type") and item.get("type") != "null"
            ]
            if types:
                prop_type = types[0]
            elif isinstance(prop_info.get("const"), bool):
                prop_type = "boolean"
            elif isinstance(prop_info.get("const"), int):
                prop_type = "integer"
            else:
                prop_type = "string"
            
        cast_row[key] = safe_cast_value(val, prop_type)
        
    return cast_row

def validate_csv_file(file_path: str, schema_type: str) -> list[dict]:
    """
    주어진 CSV 파일을 읽어 유형에 맞는 JSON Schema로 각 행을 검증합니다.
    검증에 통과한 캐스팅된 데이터 리스트를 반환합니다.
    """
    if not os.path.exists(file_path):
        raise CSVValidationError(
            code=f"MISSING_{schema_type.upper()}_FILE",
            message=f"필요한 데이터 파일이 없습니다: {os.path.basename(file_path)}"
        )
        
    # 1. 파일 비어있는지 확인
    if os.path.getsize(file_path) == 0:
        raise CSVValidationError(
            code=f"EMPTY_{schema_type.upper()}_FILE",
            message=f"데이터 파일이 비어 있습니다: {os.path.basename(file_path)}"
        )

    # 2. 스키마 로드
    if schema_type == "esg":
        schema = load_schema(ESG_SCHEMA_PATH)
        code_prefix = "INVALID_ESG"
    elif schema_type == "event":
        schema = load_schema(EVENTS_SCHEMA_PATH)
        code_prefix = "INVALID_EVENT"
    elif schema_type == "price":
        schema = load_schema(PRICES_SCHEMA_PATH)
        code_prefix = "INVALID_PRICE"
    elif schema_type == "candidate":
        schema = load_schema(CANDIDATES_SCHEMA_PATH)
        code_prefix = "INVALID_CANDIDATE"
    elif schema_type == "source":
        schema = load_schema(SOURCES_SCHEMA_PATH)
        code_prefix = "INVALID_SOURCE"
    elif schema_type == "event_source":
        schema = load_schema(EVENT_SOURCES_SCHEMA_PATH)
        code_prefix = "INVALID_EVENT_SOURCE"
    else:
        raise ValueError(f"Unknown schema type: {schema_type}")

    # 3. 필수 컬럼 헤더 매칭 검사
    required_cols = schema.get("required", [])
    
    parsed_rows = []
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            
            # 헤더 검사
            headers = reader.fieldnames
            if not headers:
                raise CSVValidationError(
                    code=f"{code_prefix}_HEADER",
                    message=f"{os.path.basename(file_path)}에 유효한 헤더가 존재하지 않습니다."
                )
                
            missing_cols = [col for col in required_cols if col not in headers]
            if missing_cols:
                raise CSVValidationError(
                    code=f"{code_prefix}_SCHEMA",
                    message=f"{os.path.basename(file_path)}에 필수 열이 누락되었습니다: {', '.join(missing_cols)}"
                )

            # 4. 각 행 데이터 타입 캐스팅 및 스키마 검증
            for line_num, raw_row in enumerate(reader, start=2): # 1은 헤더이므로 데이터는 2번 라인부터 시작
                # 중복 컬럼 등으로 인한 None 키 처리 방지
                clean_row = {k: v for k, v in raw_row.items() if k is not None}
                
                try:
                    cast_row = parse_and_cast_row(clean_row, schema)
                    jsonschema.validate(
                        instance=cast_row,
                        schema=schema,
                        format_checker=FORMAT_CHECKER,
                    )
                    parsed_rows.append(cast_row)
                except jsonschema.ValidationError as ve:
                    raise CSVValidationError(
                        code=f"{code_prefix}_VALIDATION",
                        message=f"{os.path.basename(file_path)}의 {line_num}번째 줄 검증 실패: {ve.message}"
                    )
    except CSVValidationError:
        raise
    except Exception as e:
        raise CSVValidationError(
            code=f"{code_prefix}_PARSING",
            message=f"{os.path.basename(file_path)} 파싱 중 치명적 오류 발생: {str(e)}"
        )

    # 5. 데이터 논리적 중복 등 추가 제약조건 확인
    if schema_type == "price":
        # 날짜 오름차순 및 중복 여부 확인
        # 종목별 시계열 데이터 확보
        dates_by_ticker = {}
        for row in parsed_rows:
            ticker = row["ticker"]
            date_str = row["date"]
            if ticker not in dates_by_ticker:
                dates_by_ticker[ticker] = []
            if date_str in dates_by_ticker[ticker]:
                raise CSVValidationError(
                    code="INVALID_PRICE_DUPLICATE",
                    message=f"주가 데이터에 중복된 날짜가 존재합니다: {ticker} 종목의 {date_str}"
                )
            dates_by_ticker[ticker].append(date_str)
            
    elif schema_type == "event":
        # event_id 중복 검사
        event_ids = set()
        for row in parsed_rows:
            evt_id = row["event_id"]
            if evt_id in event_ids:
                raise CSVValidationError(
                    code="INVALID_EVENT_DUPLICATE",
                    message=f"사건 데이터에 중복된 사건 ID가 존재합니다: {evt_id}"
                )
            event_ids.add(evt_id)
            _validate_company_pair(row, "event")
            rules = load_issue_rules()
            calculated_severity, _ = calculate_event_severity(row, rules)
            if row["severity_rule_version"] != rules["version"]:
                raise CSVValidationError(
                    code="INVALID_EVENT_SEVERITY_VERSION",
                    message=f"현재 규칙 버전과 다른 사건입니다: {evt_id}",
                )
            if row["severity"] != calculated_severity:
                raise CSVValidationError(
                    code="INVALID_EVENT_SEVERITY",
                    message=f"자동 재계산 severity와 다릅니다: {evt_id}",
                )

    elif schema_type == "candidate":
        candidate_ids = set()
        dedup_keys = set()
        for row in parsed_rows:
            _validate_company_pair(row, "candidate")
            host = urlsplit(row["url"]).netloc.lower()
            if row["source_name"].lower() != host:
                raise CSVValidationError(
                    code="INVALID_CANDIDATE_SOURCE_NAME",
                    message=f"URL host와 source_name이 다릅니다: {row['candidate_id']}",
                )
            if row["canonical_url"] != canonicalize_url(row["url"]):
                raise CSVValidationError(
                    code="INVALID_CANDIDATE_CANONICAL_URL",
                    message=f"canonical URL 재계산값과 다릅니다: {row['candidate_id']}",
                )
            if row["content_hash"] != candidate_content_hash(row):
                raise CSVValidationError(
                    code="INVALID_CANDIDATE_CONTENT_HASH",
                    message=f"candidate identity hash 재계산값과 다릅니다: {row['candidate_id']}",
                )
            if row["detection_source_type"] == "dart_disclosure" and (
                host != "dart.fss.or.kr" or not row.get("external_id")
            ):
                raise CSVValidationError(
                    code="INVALID_CANDIDATE_DART_SOURCE",
                    message=f"DART 후보의 도메인 또는 접수번호가 잘못되었습니다: {row['candidate_id']}",
                )
            if row["candidate_id"] in candidate_ids:
                raise CSVValidationError(
                    code="INVALID_CANDIDATE_DUPLICATE_ID",
                    message=f"중복 후보 ID가 존재합니다: {row['candidate_id']}",
                )
            dedup_key = candidate_dedup_key(row)
            if dedup_key in dedup_keys:
                raise CSVValidationError(
                    code="INVALID_CANDIDATE_DUPLICATE_CONTENT",
                    message=f"후보 중복 키가 충돌합니다: {'|'.join(dedup_key)}",
                )
            candidate_ids.add(row["candidate_id"])
            dedup_keys.add(dedup_key)

    elif schema_type == "source":
        source_ids = set()
        source_keys = set()
        for row in parsed_rows:
            _validate_source_method(row)
            if row["source_id"] in source_ids:
                raise CSVValidationError(
                    code="INVALID_SOURCE_DUPLICATE_ID",
                    message=f"중복 출처 ID가 존재합니다: {row['source_id']}",
                )
            source_key = source_dedup_key(row)
            if source_key in source_keys:
                raise CSVValidationError(
                    code="INVALID_SOURCE_DUPLICATE_CONTENT",
                    message=f"동일 출처가 중복 등록되었습니다: {'|'.join(source_key)}",
                )
            source_ids.add(row["source_id"])
            source_keys.add(source_key)

    elif schema_type == "event_source":
        links = set()
        primary_by_event = {}
        for row in parsed_rows:
            link = (row["event_id"], row["source_id"])
            if link in links:
                raise CSVValidationError(
                    code="INVALID_EVENT_SOURCE_DUPLICATE",
                    message=f"사건-출처 연결이 중복되었습니다: {link[0]} / {link[1]}",
                )
            links.add(link)
            if row["is_primary"]:
                primary_by_event[row["event_id"]] = primary_by_event.get(row["event_id"], 0) + 1
        invalid_primary = [event_id for event_id, count in primary_by_event.items() if count != 1]
        events = {row["event_id"] for row in parsed_rows}
        missing_primary = sorted(events - set(primary_by_event))
        if invalid_primary or missing_primary:
            raise CSVValidationError(
                code="INVALID_EVENT_SOURCE_PRIMARY",
                message="사건마다 공식 1차 출처가 정확히 하나 필요합니다: "
                + ", ".join(sorted(invalid_primary + missing_primary)),
            )

    return parsed_rows


def _validate_company_pair(row: dict, schema_type: str) -> None:
    expected_name = COMPANY_NAMES.get(str(row.get("company_id")))
    if expected_name and row.get("company_name") != expected_name:
        raise CSVValidationError(
            code=f"INVALID_{schema_type.upper()}_COMPANY_PAIR",
            message=f"회사 ID와 회사명이 일치하지 않습니다: {row.get('company_id')}",
        )


def _host_matches(host: str, allowed_domain: str) -> bool:
    return host == allowed_domain or host.endswith(f".{allowed_domain}")


def _validate_source_method(row: dict) -> None:
    host = urlsplit(row["url"]).netloc.lower()
    method = row["validation_method"]
    if method == "dart_receipt":
        if host != "dart.fss.or.kr" or not row.get("external_id"):
            raise CSVValidationError(
                code="INVALID_SOURCE_DART_RECEIPT",
                message=f"DART 출처의 도메인 또는 접수번호가 잘못되었습니다: {row['source_id']}",
            )
    elif method == "official_domain":
        allowed_domains = load_issue_rules()["automated_validation"]["official_domains"]
        if not any(_host_matches(host, domain) for domain in allowed_domains):
            raise CSVValidationError(
                code="INVALID_SOURCE_OFFICIAL_DOMAIN",
                message=f"허용되지 않은 공식 출처 도메인입니다: {row['source_id']}",
            )
    elif method == "news_canonical_url" and row["source_type"] != "news":
        raise CSVValidationError(
            code="INVALID_SOURCE_NEWS_METHOD",
            message=f"뉴스 검증 방식은 news 출처에만 사용할 수 있습니다: {row['source_id']}",
        )


def validate_data_a_bundle(base_dir: str = BASE_DIR) -> dict[str, list[dict]]:
    """Validate the complete Data A publish boundary and all cross-file references."""
    paths = {
        "candidates": ("data/candidate/news_candidates.csv", "candidate"),
        "sources": ("data/processed/sources.csv", "source"),
        "event_sources": ("data/processed/event_sources.csv", "event_source"),
        "events": ("data/processed/events.csv", "event"),
        "esg": ("data/processed/esg_indicators.csv", "esg"),
    }
    bundle = {
        name: validate_csv_file(os.path.join(base_dir, relative_path), schema_type)
        for name, (relative_path, schema_type) in paths.items()
    }

    for row in bundle["esg"]:
        _validate_company_pair(row, "esg")

    sources = {row["source_id"]: row for row in bundle["sources"]}
    events = {row["event_id"]: row for row in bundle["events"]}

    # Check for duplicate events by semantic similarity
    events_list = list(events.values())
    for i in range(len(events_list)):
        for j in range(i + 1, len(events_list)):
            if events_are_duplicates(events_list[i], events_list[j]):
                raise CSVValidationError(
                    code="INVALID_EVENT_SEMANTIC_DUPLICATE",
                    message=f"의미상 중복된 사건이 발견되었습니다: {events_list[i]['event_id']} / {events_list[j]['event_id']}",
                )

    indicators = {
        (row["company_id"], row["indicator_id"])
        for row in bundle["esg"]
    }

    raw_reports_dir = os.path.join(base_dir, "data", "raw", "reports")
    for source in sources.values():
        content_hash = source.get("content_hash")
        file_name = source.get("file_name")
        if not content_hash or not file_name:
            raise CSVValidationError(
                code="INVALID_SOURCE_RAW_EVIDENCE",
                message=f"processed 출처에 원문 파일 또는 SHA-256이 없습니다: {source['source_id']}",
            )
        artifact_path = os.path.join(raw_reports_dir, file_name)
        if not os.path.isfile(artifact_path):
            raise CSVValidationError(
                code="INVALID_SOURCE_RAW_ARTIFACT",
                message=f"raw 원문 파일이 없습니다: {source['source_id']}",
            )
        with open(artifact_path, "rb") as artifact:
            actual_hash = hashlib.sha256(artifact.read()).hexdigest()
        if actual_hash != content_hash:
            raise CSVValidationError(
                code="INVALID_SOURCE_CONTENT_HASH",
                message=f"raw 원문 SHA-256이 registry와 다릅니다: {source['source_id']}",
            )

    primary_links: dict[str, dict] = {}
    for link in bundle["event_sources"]:
        if link["event_id"] not in events or link["source_id"] not in sources:
            raise CSVValidationError(
                code="INVALID_EVENT_SOURCE_REFERENCE",
                message=f"존재하지 않는 사건 또는 출처 참조입니다: {link['event_id']} / {link['source_id']}",
            )
        if link["is_primary"]:
            primary_links[link["event_id"]] = link

    for event_id, event in events.items():
        primary = primary_links.get(event_id)
        if not primary:
            raise CSVValidationError(
                code="INVALID_EVENT_PRIMARY_SOURCE",
                message=f"공식 1차 출처가 없습니다: {event_id}",
            )
        source = sources[primary["source_id"]]
        if event["official_source_url"] != source["url"]:
            raise CSVValidationError(
                code="INVALID_EVENT_OFFICIAL_SOURCE_URL",
                message=f"사건 URL과 공식 1차 출처 URL이 다릅니다: {event_id}",
            )
        if (event["company_id"], event["linked_indicator_id"]) not in indicators:
            raise CSVValidationError(
                code="INVALID_EVENT_INDICATOR_REFERENCE",
                message=f"기업에 존재하지 않는 ESG 지표 참조입니다: {event_id}",
            )

    referenced_event_ids = set()
    for candidate in bundle["candidates"]:
        matched_event_id = candidate.get("matched_event_id")
        if candidate["validation_status"] == "validated":
            event = events.get(matched_event_id)
            if not event or event["company_id"] != candidate["company_id"]:
                raise CSVValidationError(
                    code="INVALID_CANDIDATE_EVENT_REFERENCE",
                    message=f"검증 후보의 사건 참조가 잘못되었습니다: {candidate['candidate_id']}",
                )
            if matched_event_id:
                referenced_event_ids.add(matched_event_id)

    for event_id in events:
        if event_id not in referenced_event_ids:
            raise CSVValidationError(
                code="INVALID_EVENT_CANDIDATE_REFERENCE",
                message=f"연결되지 않은 고아 사건(orphan event)이 존재합니다: {event_id}",
            )

    for indicator in bundle["esg"]:
        source = sources.get(indicator["source_id"])
        if not source or source["url"] != indicator["source_url"]:
            raise CSVValidationError(
                code="INVALID_ESG_SOURCE_REFERENCE",
                message=f"ESG 출처 참조가 잘못되었습니다: {indicator['company_id']} / {indicator['indicator_id']}",
            )
        target_source_id = indicator.get("target_source_id")
        if target_source_id and target_source_id not in sources:
            raise CSVValidationError(
                code="INVALID_ESG_TARGET_SOURCE_REFERENCE",
                message=f"ESG 목표 출처 참조가 잘못되었습니다: {target_source_id}",
            )

    return bundle
