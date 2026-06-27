"""ORM models — the persistence representation.

These are intentionally separate from the pure domain model
(:class:`~brandpulse.domain.models.ContentItem`). The domain never imports
SQLAlchemy; the repository layer maps between the two. That boundary is what lets
the storage engine change without rippling into business logic.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from brandpulse.db.base import Base, TimestampMixin
from brandpulse.domain.models import SourceKind


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str] = mapped_column(String(500), default="")

    keywords: Mapped[list[Keyword]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Keyword(Base, TimestampMixin):
    __tablename__ = "keywords"
    __table_args__ = (UniqueConstraint("campaign_id", "term"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    term: Mapped[str] = mapped_column(String(120))

    campaign: Mapped[Campaign] = relationship(back_populates="keywords")


class StoredContent(Base, TimestampMixin):
    """A curated item persisted for later review.

    ``fingerprint`` is unique so re-running curation never inserts duplicates;
    the repository upserts on it.
    """

    __tablename__ = "stored_content"

    id: Mapped[int] = mapped_column(primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    source: Mapped[SourceKind] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(2000))
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    score: Mapped[float] = mapped_column(default=0.0)
    published_at: Mapped[datetime]
