from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter()


def _template(request: Request, name: str, context: dict | None = None) -> HTMLResponse:
    templates = request.app.state.templates
    payload = {"request": request, **(context or {})}
    return templates.TemplateResponse(name, payload)


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return _template(request, "home.html", {"vertical": request.app.state.vertical_config.display_name})


@router.get("/intake/voice", response_class=HTMLResponse)
async def voice_intake(request: Request, job_id: str | None = None) -> HTMLResponse:
    return _template(request, "voice_intake.html", {"job_id": job_id})


@router.get("/intake/documents", response_class=HTMLResponse)
async def document_intake(request: Request, job_id: str | None = None) -> HTMLResponse:
    return _template(request, "document_intake.html", {"job_id": job_id})


@router.get("/intake/confirm", response_class=HTMLResponse)
async def confirm_intake(request: Request, job_id: str | None = None) -> HTMLResponse:
    return _template(request, "confirm_spec.html", {"job_id": job_id})


@router.get("/calls", response_class=HTMLResponse)
async def calls_page(request: Request, job_id: str | None = None) -> HTMLResponse:
    return _template(request, "calls.html", {"job_id": job_id})


@router.get("/quotes", response_class=HTMLResponse)
async def quotes_page(request: Request, job_id: str | None = None) -> HTMLResponse:
    return _template(request, "quotes.html", {"job_id": job_id})


@router.get("/negotiate", response_class=HTMLResponse)
async def negotiate_page(request: Request, job_id: str | None = None) -> HTMLResponse:
    return _template(request, "negotiate.html", {"job_id": job_id})


@router.get("/report", response_class=HTMLResponse)
async def report_page(request: Request, job_id: str | None = None) -> HTMLResponse:
    return _template(request, "report.html", {"job_id": job_id})


@router.get("/demo")
async def demo_redirect() -> RedirectResponse:
    return RedirectResponse(url="/")
