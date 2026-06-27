"""Repository layer — the only place that speaks SQL.

Repositories take an :class:`AsyncSession` (dependency-injected, never created
internally) so they compose into a caller's unit of work and stay trivially
testable against an in-memory database.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from brandpulse.curation.scoring import ScoredItem
from brandpulse.db.models import Campaign, Keyword, StoredContent


class CampaignRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, name: str, terms: Sequence[str], description: str = "") -> Campaign:
        campaign = Campaign(
            name=name,
            description=description,
            keywords=[Keyword(term=t) for t in dict.fromkeys(terms)],
        )
        self._session.add(campaign)
        await self._session.flush()
        return campaign

    async def get(self, campaign_id: int) -> Campaign | None:
        return await self._session.get(Campaign, campaign_id)

    async def list(self) -> Sequence[Campaign]:
        result = await self._session.scalars(select(Campaign).order_by(Campaign.name))
        return result.all()


class ContentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_many(self, scored: Sequence[ScoredItem]) -> int:
        """Insert curated items, skipping fingerprints already stored.

        Returns the number of newly inserted rows. Idempotent: re-running
        curation for the same window never creates duplicates.
        """
        if not scored:
            return 0
        fingerprints = [s.item.fingerprint for s in scored]
        existing = set(
            (
                await self._session.scalars(
                    select(StoredContent.fingerprint).where(
                        StoredContent.fingerprint.in_(fingerprints)
                    )
                )
            ).all()
        )
        inserted = 0
        for s in scored:
            if s.item.fingerprint in existing:
                continue
            self._session.add(
                StoredContent(
                    fingerprint=s.item.fingerprint,
                    source=s.item.source,
                    title=s.item.title,
                    url=str(s.item.url),
                    author=s.item.author,
                    score=s.score,
                    published_at=s.item.published_at,
                )
            )
            existing.add(s.item.fingerprint)
            inserted += 1
        await self._session.flush()
        return inserted

    async def top(self, limit: int = 20) -> Sequence[StoredContent]:
        result = await self._session.scalars(
            select(StoredContent).order_by(StoredContent.score.desc()).limit(limit)
        )
        return result.all()
