"""Reddit connector via the public ``search.json`` endpoint.

Reddit's per-URL ``.json`` API is public, unauthenticated, and not deprecated;
it only requires a descriptive User-Agent and tolerates ~60 req/min. That's
plenty for monitoring. When higher volume is needed, an OAuth app-only flow
slots in behind this same connector without touching anything downstream.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import httpx
import structlog

from brandpulse.domain.models import ContentItem, SourceKind
from brandpulse.sources.base import Query, SourceConnector, register

log = structlog.get_logger(__name__)

_SEARCH_URL = "https://www.reddit.com/search.json"
# Reddit explicitly throttles generic UAs; a unique, descriptive one is required.
_USER_AGENT = "python:brandpulse:0.1.0 (by /u/brandpulse-bot)"


class RedditConnector(SourceConnector):
    kind = SourceKind.REDDIT

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(
            timeout=10.0, headers={"User-Agent": _USER_AGENT}
        )

    async def fetch(self, query: Query) -> AsyncIterator[ContentItem]:
        params = {
            "q": " OR ".join(query.terms),
            "sort": "new",
            "limit": str(min(query.limit, 100)),
            "type": "link",
        }
        try:
            resp = await self._client.get(
                _SEARCH_URL, params=params, headers={"User-Agent": _USER_AGENT}
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            log.warning("reddit.search_failed", error=str(exc))
            return

        children = resp.json().get("data", {}).get("children", [])
        for child in children:
            item = self._to_item(child.get("data", {}))
            if item is not None:
                yield item

    def _to_item(self, post: dict[str, object]) -> ContentItem | None:
        post_id = post.get("id")
        title = post.get("title")
        if not post_id or not title:
            return None
        permalink = post.get("permalink", "")
        url = f"https://www.reddit.com{permalink}" if permalink else post.get("url", "")
        created = post.get("created_utc", 0)
        created_ts = float(created) if isinstance(created, (int, float, str)) else 0.0
        author = post.get("author")
        return ContentItem(
            source=self.kind,
            external_id=str(post_id),
            url=str(url),
            title=str(title),
            body=str(post.get("selftext") or ""),
            author=str(author) if isinstance(author, str) else None,
            published_at=datetime.fromtimestamp(created_ts, tz=UTC),
            raw=post,
        )


@register(SourceKind.REDDIT)
def _factory() -> RedditConnector:
    return RedditConnector()
