"""Shared test fixtures."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from brandpulse.domain.models import ContentItem, SourceKind


@pytest.fixture
def make_item():
    """Factory for ContentItem with sensible defaults; override per test."""

    def _make(
        *,
        title: str = "Acme launches widget",
        body: str = "",
        source: SourceKind = SourceKind.RSS,
        published_at: datetime | None = None,
        url: str = "https://example.com/a",
        external_id: str = "1",
    ) -> ContentItem:
        return ContentItem(
            source=source,
            external_id=external_id,
            url=url,
            title=title,
            body=body,
            published_at=published_at or datetime.now(tz=UTC),
        )

    return _make
