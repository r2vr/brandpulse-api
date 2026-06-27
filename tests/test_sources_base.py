"""Tests for the registry contract and domain invariants."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from hypothesis import given
from hypothesis import strategies as st

from brandpulse import sources
from brandpulse.domain.models import ContentItem, SourceKind
from brandpulse.sources.base import build


def test_registry_exposes_builtin_connectors() -> None:
    available = sources.available()
    assert SourceKind.RSS in available
    assert SourceKind.HACKERNEWS in available


def test_build_unknown_kind_raises() -> None:
    with pytest.raises(LookupError):
        build(SourceKind.LINKEDIN)  # registered later, scoped adapter


def test_naive_datetime_is_coerced_to_utc(make_item) -> None:
    item = make_item(published_at=datetime(2025, 1, 1, 12, 0))  # naive
    assert item.published_at.tzinfo is UTC


@given(title=st.text(min_size=1, max_size=50))
def test_fingerprint_is_case_and_whitespace_insensitive(title: str) -> None:
    base = ContentItem(
        source=SourceKind.RSS,
        external_id="1",
        url="https://example.com/x",
        title=title,
        published_at=datetime.now(tz=UTC),
    )
    noisy = base.model_copy(update={"title": f"  {title.upper()}  "})
    assert base.fingerprint == noisy.fingerprint
