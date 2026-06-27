"""Reddit and Mastodon connector tests with a mocked transport."""

from __future__ import annotations

import httpx
import respx

from brandpulse.domain.models import SourceKind
from brandpulse.sources.base import Query
from brandpulse.sources.mastodon import MastodonConnector
from brandpulse.sources.reddit import RedditConnector


@respx.mock
async def test_reddit_normalises_posts() -> None:
    payload = {
        "data": {
            "children": [
                {
                    "data": {
                        "id": "abc",
                        "title": "Acme launches",
                        "permalink": "/r/tech/comments/abc/acme/",
                        "author": "user1",
                        "created_utc": 1_700_000_000,
                        "selftext": "details",
                    }
                }
            ]
        }
    }
    respx.get("https://www.reddit.com/search.json").mock(
        return_value=httpx.Response(200, json=payload)
    )
    connector = RedditConnector(client=httpx.AsyncClient())
    items = [i async for i in connector.fetch(Query(terms=("acme",)))]

    assert len(items) == 1
    assert items[0].source is SourceKind.REDDIT
    assert str(items[0].url).startswith("https://www.reddit.com/r/tech")


@respx.mock
async def test_reddit_survives_429() -> None:
    respx.get("https://www.reddit.com/search.json").mock(return_value=httpx.Response(429))
    connector = RedditConnector(client=httpx.AsyncClient())
    items = [i async for i in connector.fetch(Query(terms=("acme",)))]
    assert items == []  # rate-limited -> degrades, never raises


@respx.mock
async def test_mastodon_strips_html_and_normalises() -> None:
    payload = [
        {
            "id": "99",
            "url": "https://mastodon.social/@u/99",
            "uri": "https://mastodon.social/users/u/statuses/99",
            "content": "<p>Loving <b>Acme</b> widgets</p>",
            "created_at": "2025-01-01T10:00:00.000Z",
            "account": {"acct": "u@mastodon.social"},
        }
    ]
    respx.get("https://mastodon.social/api/v1/timelines/tag/acme").mock(
        return_value=httpx.Response(200, json=payload)
    )
    connector = MastodonConnector(client=httpx.AsyncClient())
    items = [i async for i in connector.fetch(Query(terms=("acme",)))]

    assert len(items) == 1
    assert items[0].body == "Loving Acme widgets"  # HTML stripped
    assert items[0].author == "u@mastodon.social"


@respx.mock
async def test_mastodon_skips_failed_tags() -> None:
    respx.get("https://mastodon.social/api/v1/timelines/tag/acme").mock(
        return_value=httpx.Response(503)
    )
    connector = MastodonConnector(client=httpx.AsyncClient())
    items = [i async for i in connector.fetch(Query(terms=("acme",)))]
    assert items == []
