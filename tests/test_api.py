"""HTTP API tests driven through an in-process ASGI transport (no real server)."""

from __future__ import annotations

import httpx
import pytest
import respx

from brandpulse.api import create_app


@pytest.fixture
def client() -> httpx.AsyncClient:
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


async def test_root_serves_landing_page(client: httpx.AsyncClient) -> None:
    resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    assert "BrandPulse" in resp.text


async def test_health(client: httpx.AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_sources_lists_registered_connectors(client: httpx.AsyncClient) -> None:
    resp = await client.get("/sources")
    assert resp.status_code == 200
    assert "hackernews" in resp.json()["sources"]


async def test_monitor_requires_a_term(client: httpx.AsyncClient) -> None:
    resp = await client.get("/monitor")
    assert resp.status_code == 422  # validation: q is required


@respx.mock
async def test_monitor_returns_ranked_items(client: httpx.AsyncClient) -> None:
    respx.get("https://hn.algolia.com/api/v1/search_by_date").mock(
        return_value=httpx.Response(
            200,
            json={
                "hits": [
                    {
                        "objectID": "1",
                        "title": "Acme ships a thing",
                        "url": "https://news.example/acme",
                        "author": "dang",
                        "created_at_i": 1_700_000_000,
                    }
                ]
            },
        )
    )
    # RSS default feeds: return an empty feed so the fan-out is deterministic
    # and never touches the real network.
    respx.get(url__regex=r"https?://(hnrss|feeds)\..*").mock(
        return_value=httpx.Response(200, text="<rss><channel></channel></rss>")
    )

    resp = await client.get("/monitor", params={"q": "acme", "limit": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert body["terms"] == ["acme"]
    assert body["count"] >= 1
    assert body["items"][0]["score"] >= 0
