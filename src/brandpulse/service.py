"""Application service layer.

The single place where the orchestration lives: fan out across registered
connectors concurrently, merge their streams, and curate the result. Both the
CLI and the HTTP API are thin adapters over this module — neither owns business
logic, so behaviour stays identical regardless of how it's invoked.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence

import structlog

from brandpulse import sources
from brandpulse.curation.scoring import ScoredItem, Scorer, curate
from brandpulse.domain.models import ContentItem, SourceKind
from brandpulse.sources.base import Query

log = structlog.get_logger(__name__)


async def gather(terms: Sequence[str], per_source: int = 50) -> list[ContentItem]:
    """Fetch from every registered source concurrently, tolerating failures."""
    query = Query(terms=tuple(terms), limit=per_source)
    kinds = sources.available()
    results = await asyncio.gather(
        *(_drain(kind, query) for kind in kinds),
        return_exceptions=True,
    )
    merged: list[ContentItem] = []
    for kind, result in zip(kinds, results, strict=True):
        if isinstance(result, BaseException):
            log.warning("source.failed", source=str(kind), error=str(result))
            continue
        merged.extend(result)
    return merged


async def monitor(
    terms: Sequence[str],
    per_source: int = 50,
    limit: int = 20,
    scorer: Scorer | None = None,
) -> list[ScoredItem]:
    """End-to-end: gather, then curate into a ranked, deduplicated shortlist."""
    items = await gather(terms, per_source=per_source)
    return curate(items, terms, scorer=scorer, limit=limit)


async def _drain(kind: SourceKind, query: Query) -> list[ContentItem]:
    connector = sources.build(kind)
    return [item async for item in connector.fetch(query)]
