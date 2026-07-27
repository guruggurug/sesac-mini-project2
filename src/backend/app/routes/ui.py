from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.templates import templates


router = APIRouter(include_in_schema=False)

# 발표용 데모 계정. 실제 회원 시스템이 없어 임시로 하드코딩한다.
# 보유 수량/평균 매수가는 portfolio_edit.html에 이미 있던 예시 값을 그대로 재사용한다
# (임의로 새로 지어낸 값이 아니라, 프로젝트에서 기존에 쓰던 예시 값을 데모 계정에도 맞춰 쓴 것).
DEMO_USERNAME = "demo_user"
DEMO_PASSWORD = "demo1234"
DEMO_DISPLAY_NAME = "김버디"
DEMO_HOLDINGS = [
    {"ticker": "005930", "quantity": 150, "average_price": 72500},
    {"ticker": "000660", "quantity": 30, "average_price": 180000},
]


def _render(request: Request, template_name: str, **context):
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={
            "data_status": "sample",
            "user_name": request.session.get("user_name"),
            **context,
        },
    )


@router.get("/splash", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def splash(request: Request):
    return _render(request, "splash.html")


@router.get("/login", response_class=HTMLResponse)
def login(request: Request):
    return _render(request, "login.html")


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if username.strip() == DEMO_USERNAME and password == DEMO_PASSWORD:
        request.session["user_name"] = DEMO_DISPLAY_NAME
        request.session["portfolio_holdings"] = DEMO_HOLDINGS
    # 데모 계정이 아니어도 기존처럼(별도 회원 검증 없이) 홈으로 보낸다 —
    # 실제 회원가입/인증 시스템은 이번 범위 밖이라 그대로 둔다.
    return RedirectResponse(url="/home", status_code=303)


@router.get("/home", response_class=HTMLResponse)
def home(request: Request):
    return _render(request, "home.html")


@router.get("/settings", response_class=HTMLResponse)
def settings(request: Request):
    return _render(request, "setting.html")


@router.get("/portfolio/input", response_class=HTMLResponse)
@router.get("/portfolio/setup", response_class=HTMLResponse)
def portfolio_input(request: Request):
    holdings_by_ticker = {
        h["ticker"]: h for h in request.session.get("portfolio_holdings", [])
    }
    return _render(
        request,
        "portfolio_input.html",
        holdings_by_ticker=holdings_by_ticker,
    )


@router.get("/portfolio/edit", response_class=HTMLResponse)
@router.get("/rebalancing-profile", response_class=HTMLResponse)
def portfolio_edit(request: Request):
    return _render(request, "portfolio_edit.html")


@router.get("/portfolio/summary", response_class=HTMLResponse)
def portfolio_summary(request: Request):
    return _render(
        request,
        "portfolio_summary.html",
        data_status=None,
        holdings=request.session.get("portfolio_holdings", []),
    )


@router.get("/diagnosis/result", response_class=HTMLResponse)
@router.get("/diagnosis", response_class=HTMLResponse)
@router.get("/settings-result", response_class=HTMLResponse)
def diagnosis_result(request: Request):
    return _render(request, "diagnosis_result.html")


@router.get("/issue/analysis", response_class=HTMLResponse)
@router.get("/issues", response_class=HTMLResponse)
def issue_analysis(request: Request):
    return _render(request, "issue_analysis.html")
