"""HTTP response schemas.

Kept separate from the domain models on purpose: the wire format is an API
concern that should be free to evolve without dragging the domain with it. These
are read-only projections built from :class:`~brandpulse.domain.models.ContentItem`.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from brandpulse.curation.scoring import ScoredItem
from brandpulse.domain.models import SourceKind


class HealthResponse(BaseModel):
    status: str
    environment: str


class SourcesResponse(BaseModel):
    sources: list[SourceKind]


class CuratedItem(BaseModel):
    source: SourceKind
    title: str
    url: str
    author: str | None
    published_at: datetime
    score: float
    signals: dict[str, float]

    @classmethod
    def from_scored(cls, scored: ScoredItem) -> CuratedItem:
        item = scored.item
        return cls(
            source=item.source,
            title=item.title,
            url=str(item.url),
            author=item.author,
            published_at=item.published_at,
            score=scored.score,
            signals=scored.signals,
        )


class MonitorResponse(BaseModel):
    terms: list[str]
    count: int
    items: list[CuratedItem]


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    terms: list[str] = Field(min_length=1)


class CampaignResponse(BaseModel):
    id: int
    name: str
    description: str
    terms: list[str]

    @classmethod
    def from_orm_campaign(cls, campaign: object) -> CampaignResponse:
        return cls(
            id=campaign.id,  # type: ignore[attr-defined]
            name=campaign.name,  # type: ignore[attr-defined]
            description=campaign.description,  # type: ignore[attr-defined]
            terms=[k.term for k in campaign.keywords],  # type: ignore[attr-defined]
        )
