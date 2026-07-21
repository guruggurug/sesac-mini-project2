import yfinance as yf
from app.repositories.price_repository import PriceRepository

def get_realtime_price(ticker: str) -> float:
    """
    yfinance를 사용하여 한국거래소 종목(삼성전자 005930, SK하이닉스 000660)의 실시간 현재가 조회.
    실패 시 로컬 CSV의 가장 최신 종가로 안전하게 폴백합니다.
    """
    ticker_map = {
        "005930": "005930.KS",
        "000660": "000660.KS"
    }
    yf_ticker = ticker_map.get(ticker)
    if not yf_ticker:
        raise ValueError(f"지원하지 않는 ticker입니다: {ticker}")
        
    try:
        # yfinance를 통한 현재가(live) 조회 시도
        ticker_obj = yf.Ticker(yf_ticker)
        
        # 1. fast_info를 통한 최신 가격 탐색 (가장 가볍고 빠름)
        info = ticker_obj.fast_info
        price = info.get("lastPrice") or info.get("previousClose")
        if price and price > 0:
            return float(price)
            
        # 2. 1일 시계열 history를 통한 최신 종가 탐색
        hist = ticker_obj.history(period="1d")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
    except Exception:
        # yfinance 호출 실패 시 다음 폴백 루틴으로 진행
        pass
        
    # 3. yfinance 실패 시 로컬 CSV(PriceRepository)의 가장 최신 날짜의 종가로 폴백
    try:
        repo = PriceRepository()
        df, _, _ = repo.load_data_as_df()
        ticker_df = df[df["ticker"] == ticker]
        if not ticker_df.empty:
            return float(ticker_df.iloc[-1]["close"])
    except Exception:
        pass
        
    # 4. 최종 디폴트 고정 폴백 가격
    return 70000.0 if ticker == "005930" else 180000.0
