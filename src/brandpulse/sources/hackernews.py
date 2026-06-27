"""Hacker News connector via the public Algolia search API.

A second, structurally different source proves the abstraction holds: HN exposes
real full-text search over a JSON API (no auth), so this connector honours
``query.terms`` natively instead of filtering client-side like RSS does.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import httpx
import structlog

from brandpulse.domain.models import ContentItem, SourceKind
from brandpulse.sources.base import Query, SourceConnector, register

log = structlog.get_logger(__name__)

_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"


class HackerNewsConnector(SourceConnector):
    kind = SourceKind.HACKERNEWS

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(timeout=10.0)

    async def fetch(self, query: Query) -> AsyncIterator[ContentItem]:
        params = {
            "query": " ".join(query.terms),
            "tags": "story",
            "hitsPerPage": str(min(query.limit, 100)),
        }
        try:
            resp = await self._client.get(_SEARCH_URL, params=params)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            log.warning("hn.search_failed", error=str(exc))
            return

        for hit in resp.json().get("hits", []):
            item = self._to_item(hit)
            if item is not None:
                yield item

    def _to_item(self, hit: dict[str, object]) -> ContentItem | None:
        object_id = hit.get("objectID")
        title = hit.get("title")
        if not object_id or not title:
            return None
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
        created_raw = hit.get("created_at_i", 0)
        created = int(created_raw) if isinstance(created_raw, (int, float, str)) else 0
        author = hit.get("author")
        return ContentItem(
            source=self.kind,
            external_id=str(object_id),
            url=str(url),
            title=str(title),
            body=str(hit.get("story_text") or ""),
            author=str(author) if isinstance(author, str) else None,
            published_at=datetime.fromtimestamp(created, tz=UTC),
            raw=hit,
        )

    async def healthcheck(self) -> bool:
        try:
            resp = await self._client.get(_SEARCH_URL, params={"hitsPerPage": "0"})
            return resp.status_code == httpx.codes.OK
        except httpx.HTTPError:
            return False


@register(SourceKind.HACKERNEWS)
def _factory() -> HackerNewsConnector:
    return HackerNewsConnector()
