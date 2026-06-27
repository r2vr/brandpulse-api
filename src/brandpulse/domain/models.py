"""Core domain models.

These are deliberately framework-agnostic: no HTTP, no DB, no I/O. Every
connector normalises its raw payload into a :class:`ContentItem`, which is the
single currency the rest of the system speaks. Keeping the domain pure is what
lets us swap sources, storage and transport without touching business logic.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl, field_validator


class SourceKind(StrEnum):
    """Identifies which connector produced an item."""

    RSS = "rss"
    HACKERNEWS = "hackernews"
    REDDIT = "reddit"
    MASTODON = "mastodon"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"


class ContentItem(BaseModel):
    """A single normalised piece of content from any source.

    The ``fingerprint`` enables cross-source deduplication: the same article
    surfaced via RSS and Hacker News collapses into one logical item.
    """

    model_config = {"frozen": True}

    source: SourceKind
    external_id: str = Field(..., description="ID stable within the source.")
    url: HttpUrl
    title: str
    body: str = ""
    author: str | None = None
    published_at: datetime
    raw: dict[str, object] = Field(default_factory=dict, repr=False)

    @field_validator("published_at")
    @classmethod
    def _ensure_tz_aware(cls, value: datetime) -> datetime:
        """Naive datetimes are a classic source of silent bugs; reject them."""
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @property
    def fingerprint(self) -> str:
        """Content-based hash used for deduplication across sources."""
        # casefold(), not lower(): the correct primitive for case-insensitive
        # comparison across Unicode (micro sign vs Greek mu, eszett vs SS).
        # Surfaced by a Hypothesis property test.
        basis = (self.title.strip().casefold() or str(self.url)).encode("utf-8")
        return hashlib.sha256(basis).hexdigest()[:16]
