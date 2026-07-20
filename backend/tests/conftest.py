import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.loader import load_vertical_config
from app.db.session import Base
from app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "config" / "verticals" / "moving.yaml"

TEST_ENGINE = create_async_engine(os.environ["DATABASE_URL"], echo=False)
TestSessionLocal = async_sessionmaker(TEST_ENGINE, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
def vertical_config():
    return load_vertical_config(CONFIG_PATH)


@pytest.fixture
async def app(vertical_config, monkeypatch):
    async def override_get_session():
        async with TestSessionLocal() as session:
            yield session

    application = create_app(config=vertical_config)
    from app.db import session as db_session
    from app.api.routes import jobs, reports

    monkeypatch.setattr(db_session, "engine", TEST_ENGINE)
    monkeypatch.setattr(db_session, "SessionLocal", TestSessionLocal)

    application.dependency_overrides[db_session.get_session] = override_get_session

    async with TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield application
    application.dependency_overrides.clear()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
