"""RSS / Atom connector.

The simplest real connector: it pulls a configured set of feeds and keeps items
whose title or summary matches any query term. It demonstrates the contract end
to end —normalisation, timezone handling, graceful degradation— without auth.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from datetime import UTC, datetime
from time import struct_time

import feedparser
import httpx
import structlog

from brandpulse.domain.models import ContentItem, SourceKind
from brandpulse.sources.base import Query, SourceConnector, register

log = structlog.get_logger(__name__)

# A small, stable default set of tech/press feeds. In production this comes from
# config; hard-coding a default keeps the connector usable out of the box.
DEFAULT_FEEDS: tuple[str, ...] = (
    "https://hnrss.org/frontpage",
    "https://feeds.arstechnica.com/arstechnica/index",
)


class RSSConnector(SourceConnector):
    kind = SourceKind.RSS

    def __init__(
        self,
        feeds: Sequence[str] = DEFAULT_FEEDS,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._feeds = tuple(feeds)
        # Injected client => testable without real network calls.
        self._client = client or httpx.AsyncClient(timeout=10.0)

    async def fetch(self, query: Query) -> AsyncIterator[ContentItem]:
        terms = tuple(t.lower() for t in query.terms)
        yielded = 0
        for feed_url in self._feeds:
            try:
                resp = await self._client.get(feed_url)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                # One bad feed must never sink the whole fan-out.
                log.warning("rss.feed_failed", feed=feed_url, error=str(exc))
                continue

            parsed = feedparser.parse(resp.text)
            for entry in parsed.entries:
                if yielded >= query.limit:
                    return
                item = self._to_item(entry)
                if item is not None and _matches(item, terms):
                    yielded += 1
                    yield item

    def _to_item(self, entry: object) -> ContentItem | None:
        get = entry.get  # type: ignore[attr-defined]
        link = get("link")
        title = get("title")
        if not link or not title:
            return None
        return ContentItem(
            source=self.kind,
            external_id=get("id") or link,
            url=link,
            title=title,
            body=get("summary", ""),
            author=get("author"),
            published_at=_parse_time(get("published_parsed")),
            raw=dict(entry) if isinstance(entry, dict) else {},
        )


def _matches(item: ContentItem, terms: Sequence[str]) -> bool:
    """Empty query matches everything; otherwise any-term substring match."""
    if not terms:
        return True
    haystack = f"{item.title}\n{item.body}".lower()
    return any(term in haystack for term in terms)


def _parse_time(value: struct_time | None) -> datetime:
    if value is None:
        return datetime.now(tz=UTC)
    return datetime(*value[:6], tzinfo=UTC)


@register(SourceKind.RSS)
def _factory() -> RSSConnector:
    return RSSConnector()
