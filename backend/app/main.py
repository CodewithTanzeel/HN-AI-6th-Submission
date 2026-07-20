from pathlib import Path
import os

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import jobs, pages, reports, webhook
from app.config.loader import VerticalConfig, load_vertical_config
from app.config.settings import settings
from app.db.session import init_db
from app.middleware.cache import CacheMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

REPO_ROOT = Path(__file__).resolve().parents[2]


def get_cors_origins() -> list[str]:
    """Get CORS origins including ngrok URL if available."""
    origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
    ngrok_url = os.getenv("NGROK_URL", "")
    if ngrok_url:
        # Add ngrok URL for webhook callbacks
        origins.append(ngrok_url)
    return origins


def create_app(config: VerticalConfig | None = None) -> FastAPI:
    app = FastAPI(title="The Negotiator", version="0.1.0")
    app.state.vertical_config = config or load_vertical_config(settings.config_path)

    templates_dir = REPO_ROOT / "frontend" / "templates"
    static_dir = REPO_ROOT / "frontend" / "static"
    app.state.templates = Jinja2Templates(directory=str(templates_dir))
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.on_event("startup")
    async def startup() -> None:
        await init_db()

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "vertical": app.state.vertical_config.vertical}

    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
    app.add_middleware(CacheMiddleware, ttl_seconds=300)

    app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
    app.include_router(reports.router, prefix="/api/jobs", tags=["reports"])
    app.include_router(pages.router, tags=["pages"])
    app.include_router(webhook.router, prefix="/api/webhook", tags=["webhook"])

    return app


app = create_app()