"""Mastodon connector via public hashtag timelines.

Most Mastodon instances expose ``/api/v1/timelines/tag/{tag}`` publicly without
auth. Like the Instagram Graph adapter, this connector treats query terms as
hashtags — an honest reflection of what's reachable unauthenticated. The
instance is configurable; federation means one well-chosen instance sees a broad
slice of the network.
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import httpx
import structlog

from brandpulse.domain.models import ContentItem, SourceKind
from brandpulse.sources.base import Query, SourceConnector, register

log = structlog.get_logger(__name__)

DEFAULT_INSTANCE = "https://mastodon.social"
_TAG_RE = re.compile(r"[^0-9a-zA-Z]+")
_HTML_RE = re.compile(r"<[^>]+>")


class MastodonConnector(SourceConnector):
    kind = SourceKind.MASTODON

    def __init__(
        self,
        instance: str = DEFAULT_INSTANCE,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._instance = instance.rstrip("/")
        self._client = client or httpx.AsyncClient(timeout=10.0)

    async def fetch(self, query: Query) -> AsyncIterator[ContentItem]:
        per_tag = max(1, query.limit // max(1, len(query.terms)))
        yielded = 0
        for term in query.terms:
            tag = _TAG_RE.sub("", term)
            if not tag:
                continue
            url = f"{self._instance}/api/v1/timelines/tag/{tag}"
            try:
                resp = await self._client.get(url, params={"limit": str(min(per_tag, 40))})
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                log.warning("mastodon.tag_failed", tag=tag, error=str(exc))
                continue
            for status in resp.json():
                if yielded >= query.limit:
                    return
                item = self._to_item(status)
                if item is not None:
                    yielded += 1
                    yield item

    def _to_item(self, status: dict[str, object]) -> ContentItem | None:
        status_id = status.get("id")
        url = status.get("url") or status.get("uri")
        if not status_id or not url:
            return None
        account = status.get("account")
        author = account.get("acct") if isinstance(account, dict) else None
        content = _HTML_RE.sub("", str(status.get("content", ""))).strip()
        return ContentItem(
            source=self.kind,
            external_id=str(status_id),
            url=str(url),
            title=content[:140] or "(no text)",
            body=content,
            author=str(author) if isinstance(author, str) else None,
            published_at=_parse_iso(status.get("created_at")),
            raw=status,
        )


def _parse_iso(value: object) -> datetime:
    if not isinstance(value, str):
        return datetime.now(tz=UTC)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(tz=UTC)


@register(SourceKind.MASTODON)
def _factory() -> MastodonConnector:
    return MastodonConnector()
