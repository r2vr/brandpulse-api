"""Repository tests against an isolated in-memory SQLite database."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from brandpulse.curation.scoring import ScoredItem
from brandpulse.db.base import Base
from brandpulse.db.repository import CampaignRepository, ContentRepository


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    # Each test gets a fresh in-memory schema; nothing leaks between tests.
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


async def test_create_campaign_with_keywords(session: AsyncSession) -> None:
    repo = CampaignRepository(session)
    campaign = await repo.create("Acme Q3", ["acme", "widget", "acme"])  # dup dropped
    await session.commit()

    fetched = await repo.get(campaign.id)
    assert fetched is not None
    assert fetched.name == "Acme Q3"
    assert sorted(k.term for k in fetched.keywords) == ["acme", "widget"]


async def test_upsert_is_idempotent(session: AsyncSession, make_item) -> None:
    repo = ContentRepository(session)
    scored = [ScoredItem(item=make_item(title="Acme news"), score=0.9, signals={})]

    first = await repo.upsert_many(scored)
    second = await repo.upsert_many(scored)  # same fingerprint

    assert first == 1
    assert second == 0  # no duplicate inserted
    assert len(await repo.top()) == 1


async def test_top_orders_by_score_desc(session: AsyncSession, make_item) -> None:
    repo = ContentRepository(session)
    await repo.upsert_many(
        [
            ScoredItem(item=make_item(title="low", url="https://e.com/1"), score=0.1, signals={}),
            ScoredItem(item=make_item(title="high", url="https://e.com/2"), score=0.9, signals={}),
        ]
    )
    top = await repo.top()
    assert [c.title for c in top] == ["high", "low"]
