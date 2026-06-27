"""Connector and curation tests with a mocked transport (no real network)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import respx

from brandpulse.curation.scoring import HeuristicScorer, curate
from brandpulse.sources.base import Query
from brandpulse.sources.hackernews import HackerNewsConnector


@respx.mock
async def test_hackernews_fetch_normalises_hits() -> None:
    payload = {
        "hits": [
            {
                "objectID": "42",
                "title": "Acme raises Series B",
                "url": "https://news.example/acme",
                "author": "pg",
                "created_at_i": 1_700_000_000,
                "story_text": "",
            }
        ]
    }
    respx.get("https://hn.algolia.com/api/v1/search_by_date").mock(
        return_value=httpx.Response(200, json=payload)
    )

    connector = HackerNewsConnector(client=httpx.AsyncClient())
    items = [i async for i in connector.fetch(Query(terms=("acme",)))]

    assert len(items) == 1
    assert items[0].external_id == "42"
    assert items[0].published_at.tzinfo is UTC


@respx.mock
async def test_hackernews_fetch_survives_http_error() -> None:
    respx.get("https://hn.algolia.com/api/v1/search_by_date").mock(return_value=httpx.Response(503))
    connector = HackerNewsConnector(client=httpx.AsyncClient())
    items = [i async for i in connector.fetch(Query(terms=("acme",)))]
    assert items == []  # degrades gracefully, never raises


def test_curate_dedupes_and_ranks_recent_higher(make_item) -> None:
    now = datetime.now(tz=UTC)
    fresh = make_item(title="Acme news", published_at=now, external_id="1")
    stale = make_item(
        title="Acme news",  # same fingerprint -> deduped
        published_at=now - timedelta(days=3),
        external_id="2",
    )
    other = make_item(title="Unrelated", published_at=now, external_id="3")

    ranked = curate([stale, fresh, other], terms=["acme"])

    fingerprints = [s.item.fingerprint for s in ranked]
    assert len(fingerprints) == len(set(fingerprints))  # deduped
    assert ranked[0].item.title == "Acme news"  # relevant + fresh wins


def test_recency_decays_monotonically(make_item) -> None:
    scorer = HeuristicScorer()
    now = datetime.now(tz=UTC)
    new = scorer.score(make_item(published_at=now), ["acme"])
    old = scorer.score(make_item(published_at=now - timedelta(hours=48)), ["acme"])
    assert new.signals["recency"] > old.signals["recency"]
