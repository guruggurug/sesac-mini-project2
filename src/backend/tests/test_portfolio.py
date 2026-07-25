import sys
import os
import pytest
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


@pytest.fixture(autouse=True)
def mock_market_quotes(monkeypatch):
    """Keep API regression tests deterministic and independent of external networks."""
    from app.utils import realtime_price

    class StubQuote:
        def __init__(self, price):
            self.price = price

    class StubService:
        def get_quote(self, ticker):
            prices = {"005930": 80000.0, "000660": 200000.0}
            return StubQuote(prices[ticker])

    monkeypatch.setattr(realtime_price, "_DEFAULT_SERVICE", StubService())


def test_app_startup_runs_runtime_state_recovery(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "app.main.recover_runtime_state_after_restart",
        lambda: calls.append("recovered"),
    )

    with TestClient(app) as startup_client:
        assert startup_client.get("/health").status_code == 200

    assert calls == ["recovered"]


def test_app_lifespan_starts_and_stops_scheduler_only_when_enabled(monkeypatch):
    calls = []

    class StubScheduler:
        async def start(self):
            calls.append("started")

        async def stop(self):
            calls.append("stopped")

    monkeypatch.setattr("app.main.recover_runtime_state_after_restart", lambda: None)
    monkeypatch.setattr("app.main.ENABLE_ISSUE_SCHEDULER", True)
    monkeypatch.setattr("app.main.daily_issue_scheduler", StubScheduler())

    with TestClient(app) as startup_client:
        assert startup_client.get("/health").status_code == 200
        assert calls == ["started"]

    assert calls == ["started", "stopped"]

def test_health_check():
    """
    GET /health API가 정상 동작하는지 테스트
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "FastAPI server is running" in data["message"]


def test_data_refresh_does_not_report_false_success_before_sync_implementation():
    response = client.post("/data/refresh")

    assert response.status_code == 501
    assert response.json()["detail"]["code"] == "ISSUE_SYNC_NOT_IMPLEMENTED"

def test_get_diagnosis_page():
    """GET /home renders the API-driven market dashboard."""
    response = client.get("/home")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "시장 현황" in response.text
    assert 'fetch("/market/quotes"' in response.text
    assert "AbortController" in response.text
    assert "Chip Buddy" in response.text

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
    assert "진단 결과" in html_content
    assert "최적화 전략" in html_content
    assert "삼성전자" in html_content
    assert "SK하이닉스" in html_content
    assert "예상 CVaR" in html_content

    summary_page = client.get("/portfolio/summary")
    assert summary_page.status_code == 200
    assert '"ticker": "005930"' in summary_page.text
    assert '"quantity": 70' in summary_page.text
    assert '"average_price": 70000.0' in summary_page.text


def test_portfolio_optimize_renders_model_result_instead_of_fixed_values(monkeypatch):
    model_result = {
        "current_weights": {"005930": 0.4, "000660": 0.6},
        "recommended_weights": {"005930": 0.55, "000660": 0.45},
        "current_total_risk": 0.5,
        "optimized_total_risk": 0.4,
        "risk_reduction_rate": 0.2,
        "current_cvar": 0.05,
        "optimized_cvar": 0.04,
        "current_esg_risk": 0.3,
        "optimized_esg_risk": 0.25,
        "company_risks": {
            "005930": {
                "esg_risk": 0.2,
                "downside_risk": 0.03,
                "total_risk": 0.22,
                "risk_level": "low",
                "data_confidence": "high",
                "scope_mismatch": False,
            },
            "000660": {
                "esg_risk": 0.4,
                "downside_risk": 0.06,
                "total_risk": 0.45,
                "risk_level": "medium",
                "data_confidence": "high",
                "scope_mismatch": False,
            },
        },
        "explanation": [
            "테스트 모델이 삼성전자 추천 비중을 55%로 계산했습니다.",
            "가격 하방위험과 ESG 관리위험을 함께 반영했습니다.",
        ],
        "warnings": ["미래 수익률을 예측하는 결과가 아닙니다."],
        "data_status": "validated",
    }
    monkeypatch.setattr(
        "app.routes.portfolio.run_optimize",
        lambda **_: model_result,
    )

    response = client.post(
        "/portfolio/optimize",
        data={
            "samsung_qty": 4,
            "samsung_price": 70000,
            "sk_qty": 6,
            "sk_price": 180000,
            "risk_priority": "balanced",
        },
    )

    assert response.status_code == 200
    assert 'data-current-samsung-weight="40.0"' in response.text
    assert 'data-recommended-samsung-weight="55.0"' in response.text
    assert "종합 위험 20.0% 개선" in response.text
    assert "-4.00%" in response.text
    assert "테스트 모델이 삼성전자 추천 비중을 55%로 계산했습니다." in response.text
    assert "미래 수익률을 예측하는 결과가 아닙니다." in response.text
    assert "위험을 12.5% 감소" not in response.text
    assert "샘플 데이터" not in response.text

def test_issues_endpoints():
    """
    이슈 분석 JSON API가 정상 동작하는지 테스트
    """
    res_current = client.get("/issues/current")
    assert res_current.status_code == 200
    data_current = res_current.json()
    assert "events" in data_current
    assert data_current["data_status"] in ("sample", "validated", "fallback")
    
    res_historical = client.get("/issues/historical")
    assert res_historical.status_code == 200
    data_historical = res_historical.json()
    assert "events" in data_historical
    assert data_historical["data_status"] in ("sample", "validated", "fallback")

def test_esg_repository_processed_loading():
    """
    자동 검증된 ESG indicators 파일이 validated 상태로 로드되는지 검증
    """
    repo = ESGRepository()
    data, status, warning = repo.load_data()
    
    assert status == "validated"
    assert warning is None
    assert len(data) > 0
    
    # 필수 필드 구조 검증
    for row in data:
        assert "company_id" in row
        assert "indicator_id" in row
        assert "availability" in row
        assert "raw_value" in row

def test_event_repository_processed_loading_and_filtering():
    """
    자동 검증된 사건 파일이 validated 상태로 로드되며 필터링되는지 검증
    """
    repo = EventRepository()
    data, status, warning = repo.load_data()
    
    assert status == "validated"
    assert warning is None
    assert len(data) > 0
    
    # 모델 사용 불가 사건(reported)을 걸러내는지 검사
    model_ready = repo.get_model_ready_events(data)
    for evt in model_ready:
        assert evt["status"] in ("confirmed", "resolved")
        assert evt["authority_confirmed"] is True
        assert evt["official_source_url"]


def test_event_repository_automatic_verification_gate():
    repo = EventRepository()
    events = [
        {
            "event_id": "EVT-1001",
            "status": "confirmed",
            "authority_confirmed": True,
            "official_source_url": "https://example.com/official",
        },
        {
            "event_id": "EVT-1002",
            "status": "confirmed",
            "authority_confirmed": False,
            "official_source_url": "https://example.com/news",
        },
        {
            "event_id": "EVT-1003",
            "status": "reported",
            "authority_confirmed": False,
            "official_source_url": None,
        },
    ]

    model_ready = repo.get_model_ready_events(events)

    assert [event["event_id"] for event in model_ready] == ["EVT-1001"]

def test_price_repository_processed_loading():
    """
    주가 데이터 로딩 검증 (processed 데이터가 없으면 sample로 fallback 됨)
    """
    repo = PriceRepository()
    df, status, warning = repo.load_data_as_df()
    
    if os.path.exists(repo.processed_path):
        assert status == "validated"
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
    assert data["data_status"] in ("sample", "validated", "fallback")

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
    assert data["005930"]["esg_risk"] is None
    assert data["005930"]["risk_level"] == "unavailable"
    assert "warning" in data
    assert data["data_status"] in ("sample", "validated", "fallback")

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
    assert data["data_status"] in ("sample", "validated", "fallback")

def test_realtime_price_utility():
    """
    실시간 가격 조회 유틸리티가 정상적으로 float 가격을 반환하는지 테스트
    """
    class StubQuote:
        def __init__(self, price):
            self.price = price

    class StubService:
        def get_quote(self, ticker):
            return StubQuote({"005930": 80000.0, "000660": 200000.0}[ticker])

    price_sam = get_realtime_price("005930", service=StubService())
    price_sk = get_realtime_price("000660", service=StubService())
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
    assert "진단 결과" in response.text

def test_issues_page_rendering():
    """
    GET /issues 웹 페이지가 API 기반 이슈 분석 UI를 렌더링하는지 테스트
    """
    response = client.get("/issues")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "이슈 분석" in response.text
    assert 'data-ui-screen="issue-analysis"' in response.text
    assert 'fetch("/issues/current"' in response.text
    assert 'fetch("/issues/historical"' in response.text
    assert 'fetch("/sync/issues"' in response.text
    assert '"/sync/status"' in response.text
    assert "새 이슈 확인" in response.text
    assert "과거 사건 주가 영향" in response.text
    assert "HBM 공급망 관련 공정거래 이슈" not in response.text
    assert "78,200원" not in response.text
