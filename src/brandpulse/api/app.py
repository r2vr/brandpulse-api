"""FastAPI application — the HTTP adapter over the service and persistence layers.

Endpoints are deliberately thin: validate input, call the service or a
repository, project the result into wire schemas. No business logic lives here.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse

from brandpulse import service, sources
from brandpulse.api.landing import render_landing
from brandpulse.api.routers_campaigns import router as campaigns_router
from brandpulse.api.schemas import (
    CuratedItem,
    HealthResponse,
    MonitorResponse,
    SourcesResponse,
)
from brandpulse.config import get_settings
from brandpulse.db.engine import create_all, get_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Dev/first-run convenience: ensure tables exist. Production relies on
    # Alembic migrations, but create_all is idempotent and harmless here.
    await create_all()
    yield
    await get_engine().dispose()


def create_app() -> FastAPI:
    """Application factory — keeps construction testable and import-safe."""
    app = FastAPI(
        title="BrandPulse",
        version="0.1.0",
        summary="Brand monitoring & content curation engine.",
        lifespan=lifespan,
    )

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def index(request: Request) -> HTMLResponse:
        return HTMLResponse(render_landing(str(request.base_url)))

    @app.get("/health", response_model=HealthResponse, tags=["meta"])
    async def health() -> HealthResponse:
        settings = get_settings()
        return HealthResponse(status="ok", environment=settings.environment)

    @app.get("/sources", response_model=SourcesResponse, tags=["meta"])
    async def list_sources() -> SourcesResponse:
        return SourcesResponse(sources=list(sources.available()))

    @app.get("/monitor", response_model=MonitorResponse, tags=["curation"])
    async def monitor(
        q: Annotated[list[str], Query(min_length=1, description="Terms to track.")],
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
        per_source: Annotated[int, Query(ge=1, le=200)] = 50,
    ) -> MonitorResponse:
        ranked = await service.monitor(q, per_source=per_source, limit=limit)
        return MonitorResponse(
            terms=q,
            count=len(ranked),
            items=[CuratedItem.from_scored(s) for s in ranked],
        )

    app.include_router(campaigns_router)
    return app


app = create_app()
