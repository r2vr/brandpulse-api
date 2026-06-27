"""Campaign API tests with the DB dependency overridden to in-memory SQLite."""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from brandpulse.api import create_app
from brandpulse.api.deps import get_session
from brandpulse.db.base import Base


@pytest_asyncio.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    # StaticPool keeps a single shared in-memory connection so the schema
    # created here is visible to every request-scoped session.
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async def _override() -> AsyncIterator[AsyncSession]:
        async with maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app = create_app()
    app.dependency_overrides[get_session] = _override
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await engine.dispose()


async def test_create_and_fetch_campaign(client: httpx.AsyncClient) -> None:
    resp = await client.post("/campaigns", json={"name": "Acme Q3", "terms": ["acme", "widget"]})
    assert resp.status_code == 201
    created = resp.json()
    assert created["terms"] == ["acme", "widget"]

    got = await client.get(f"/campaigns/{created['id']}")
    assert got.status_code == 200
    assert got.json()["name"] == "Acme Q3"


async def test_duplicate_campaign_name_conflicts(client: httpx.AsyncClient) -> None:
    body = {"name": "Dup", "terms": ["x"]}
    assert (await client.post("/campaigns", json=body)).status_code == 201
    assert (await client.post("/campaigns", json=body)).status_code == 409


async def test_missing_campaign_returns_404(client: httpx.AsyncClient) -> None:
    assert (await client.get("/campaigns/999")).status_code == 404


async def test_create_requires_at_least_one_term(client: httpx.AsyncClient) -> None:
    resp = await client.post("/campaigns", json={"name": "NoTerms", "terms": []})
    assert resp.status_code == 422
