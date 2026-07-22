from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates


router = APIRouter(include_in_schema=False)


def _render(request: Request, template_name: str):
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={"data_status": "sample"},
    )


@router.get("/", response_class=HTMLResponse)
@router.get("/home", response_class=HTMLResponse)
def home(request: Request):
    return _render(request, "home.html")


@router.get("/portfolio/input", response_class=HTMLResponse)
@router.get("/portfolio/setup", response_class=HTMLResponse)
def portfolio_input(request: Request):
    return _render(request, "portfolio_input.html")


@router.get("/portfolio/edit", response_class=HTMLResponse)
@router.get("/rebalancing-profile", response_class=HTMLResponse)
def portfolio_edit(request: Request):
    return _render(request, "portfolio_edit.html")


@router.get("/portfolio/summary", response_class=HTMLResponse)
def portfolio_summary(request: Request):
    return _render(request, "portfolio_summary.html")


@router.get("/diagnosis/result", response_class=HTMLResponse)
@router.get("/diagnosis", response_class=HTMLResponse)
@router.get("/settings-result", response_class=HTMLResponse)
def diagnosis_result(request: Request):
    return _render(request, "diagnosis_result.html")


@router.get("/issue/analysis", response_class=HTMLResponse)
@router.get("/issues", response_class=HTMLResponse)
def issue_analysis(request: Request):
    return _render(request, "issue_analysis.html")
