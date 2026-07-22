import os
import csv
import json
import jsonschema
from app.core.config import BASE_DIR
from app.core.exceptions import CSVValidationError

# 스키마 파일 경로 설정
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas", "data")
ESG_SCHEMA_PATH = os.path.join(SCHEMAS_DIR, "esg-indicators.schema.json")
EVENTS_SCHEMA_PATH = os.path.join(SCHEMAS_DIR, "events.schema.json")
PRICES_SCHEMA_PATH = os.path.join(SCHEMAS_DIR, "stock-prices.schema.json")

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
        
        if isinstance(prop_type, list):
            types = [t for t in prop_type if t != "null"]
            prop_type = types[0] if types else "string"
        
        # oneOf나 anyOf 등 다중 타입 대응 (null 허용 등)
        if not prop_type and "oneOf" in prop_info:
            types = []
            for t in prop_info["oneOf"]:
                t_type = t.get("type")
                if t_type:
                    if isinstance(t_type, list):
                        types.extend([x for x in t_type if x != "null"])
                    elif t_type != "null":
                        types.append(t_type)
            prop_type = types[0] if types else "string"
            
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
                    jsonschema.validate(instance=cast_row, schema=schema)
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

    return parsed_rows
