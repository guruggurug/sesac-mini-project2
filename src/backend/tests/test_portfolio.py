import sys
import os
from fastapi.testclient import TestClient

# PYTHONPATH에 app이 위치한 src/backend 디렉토리 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.repositories.esg_repository import ESGRepository
from app.repositories.event_repository import EventRepository
from app.repositories.price_repository import PriceRepository
from app.core.exceptions import CSVValidationError
from app.utils.realtime_price import get_realtime_price


client = TestClient(app)

def test_health_check():
    """
    GET /health API가 정상 동작하는지 테스트
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "FastAPI server is running" in data["message"]

def test_get_diagnosis_page():
    """
    GET / 진단 홈 페이지가 정상적으로 HTML을 렌더링하는지 테스트
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "반도체 가치투자 내비게이션" in response.text
    assert "Antigravity NAV" in response.text

def test_portfolio_optimize_form_submit():
    """
    POST /portfolio/optimize가 Form 파라미터를 받아 HTML 결과를 반환하는지 테스트
    """
    form_data = {
        "samsung_qty": 70,
        "samsung_price": 70000.0,
        "sk_qty": 30,
        "sk_price": 180000.0,
        "risk_priority": "balanced"
    }
    response = client.post("/portfolio/optimize", data=form_data)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    
    html_content = response.text
    assert "포트폴리오 비중 비교" in html_content
    assert "개별 위험 지표" in html_content
    assert "삼성전자" in html_content
    assert "SK하이닉스" in html_content
    assert "포트폴리오 처방전" in html_content

def test_issues_endpoints():
    """
    이슈 분석 JSON API가 정상 동작하는지 테스트
    """
    res_current = client.get("/issues/current")
    assert res_current.status_code == 200
    data_current = res_current.json()
    assert "events" in data_current
    assert data_current["data_status"] in ("sample", "reviewed", "fallback")
    
    res_historical = client.get("/issues/historical")
    assert res_historical.status_code == 200
    data_historical = res_historical.json()
    assert "events" in data_historical
    assert data_historical["data_status"] in ("sample", "reviewed", "fallback")

def test_esg_repository_reviewed_loading():
    """
    데이터 A의 실제 ESG indicators 파일이 무사히 reviewed 상태로 로드되는지 검증
    """
    repo = ESGRepository()
    data, status, warning = repo.load_data()
    
    # 깃허브 feature/data-a 브랜치로부터 가져왔으므로 reviewed 여야 함
    assert status == "reviewed"
    assert warning is None
    assert len(data) > 0
    
    # 필수 필드 구조 검증
    for row in data:
        assert "company_id" in row
        assert "indicator_id" in row
        assert "availability" in row
        assert "raw_value" in row

def test_event_repository_reviewed_loading_and_filtering():
    """
    데이터 A의 실제 사건 파일이 reviewed 상태로 로드되며 필터링이 잘 되는지 검증
    """
    repo = EventRepository()
    data, status, warning = repo.load_data()
    
    assert status == "reviewed"
    assert warning is None
    assert len(data) > 0
    
    # 모델 사용 불가 사건 (rumor, reported)을 걸러내는지 검사
    model_ready = repo.get_model_ready_events(data)
    for evt in model_ready:
        assert evt["status"] in ("confirmed", "sanctioned", "resolved")
        assert evt["review_status"] == "approved"

def test_price_repository_reviewed_loading():
    """
    주가 데이터 로딩 검증 (reviewed 데이터가 없으면 sample로 fallback 됨)
    """
    repo = PriceRepository()
    df, status, warning = repo.load_data_as_df()
    
    # main 브랜치와 data-a 브랜치 상태상 stock_prices.csv가 reviewed에 없다면 sample이 될 것임
    # stock_prices.csv가 reviewed 폴더에 있는지 확인 후 검증
    if os.path.exists(repo.reviewed_path):
        assert status == "reviewed"
    else:
        assert status == "sample"
        
    assert not df.empty
    assert "ticker" in df.columns
    assert "date" in df.columns
    assert "close" in df.columns

def test_calculate_portfolio_weights_endpoint():
    """
    POST /portfolio/calculate API가 정상적으로 비중을 계산하여 JSON으로 리턴하는지 테스트
    """
    form_data = {
        "samsung_qty": 70,
        "samsung_price": 70000.0,
        "sk_qty": 30,
        "sk_price": 180000.0
    }
    response = client.post("/portfolio/calculate", data=form_data)
    assert response.status_code == 200
    data = response.json()
    assert "current_weights" in data
    assert "005930" in data["current_weights"]
    assert "000660" in data["current_weights"]
    assert data["data_status"] in ("sample", "reviewed", "fallback")

def test_risk_esg_endpoint():
    """
    POST /risk/esg API가 두 기업의 ESG 리스크를 실제 계산/반환하는지 테스트
    """
    response = client.post("/risk/esg")
    assert response.status_code == 200
    data = response.json()
    assert "005930" in data
    assert "000660" in data
    assert "esg_risk" in data["005930"]
    assert "risk_level" in data["005930"]
    assert data["data_status"] in ("sample", "reviewed", "fallback")

def test_risk_downside_endpoint():
    """
    POST /risk/downside API가 두 기업의 하방 리스크(CVaR)를 계산/반환하는지 테스트
    """
    response = client.post("/risk/downside")
    assert response.status_code == 200
    data = response.json()
    assert "005930" in data
    assert "000660" in data
    assert "downside_risk" in data["005930"]
    assert "risk_level" in data["005930"]
    assert data["data_status"] in ("sample", "reviewed", "fallback")

def test_realtime_price_utility():
    """
    실시간 가격 조회 유틸리티가 정상적으로 float 가격을 반환하는지 테스트
    """
    price_sam = get_realtime_price("005930")
    price_sk = get_realtime_price("000660")
    assert isinstance(price_sam, float)
    assert price_sam > 0
    assert isinstance(price_sk, float)
    assert price_sk > 0

def test_portfolio_optimize_realtime_endpoint():
    """
    POST /portfolio/optimize에 가격 인자(samsung_price, sk_price)가 생략되어도
    실시간 주가를 연동하여 정상 동작하는지 테스트
    """
    form_data = {
        "samsung_qty": 70,
        "sk_qty": 30,
        "risk_priority": "balanced"
    }
    response = client.post("/portfolio/optimize", data=form_data)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "포트폴리오 비중 비교" in response.text


