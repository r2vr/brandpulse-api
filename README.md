# BrandPulse

[![CI](https://github.com/r2vr/brandpulse/actions/workflows/ci.yml/badge.svg)](https://github.com/r2vr/brandpulse/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)
![Checked with mypy](https://img.shields.io/badge/mypy-strict-blue)
![Ruff](https://img.shields.io/badge/ruff-enabled-orange)

A brand-monitoring and content-curation engine built around a **pluggable source
layer**. Point it at a set of keywords or brands; it fans out across content
sources, normalises everything into a single domain model, then deduplicates and
ranks the results into a curated shortlist.

The project is deliberately small but built the way a production service is:
clean layering, typed boundaries, dependency injection, graceful degradation,
and tests that assert behaviour rather than implementation.

## Why the architecture looks like this

The keystone is `brandpulse.sources.base.SourceConnector`. Every platform —open
and locked-down alike— is reduced to one contract: *given a query, yield
normalised `ContentItem`s*. Nothing downstream imports a connector directly; it
asks the **registry**. Adding Reddit, Mastodon or a scoped Instagram adapter is a
localised change, never a refactor.

```
domain/      pure models, no I/O           (the currency: ContentItem)
sources/     SourceConnector + registry    (RSS, HN, Reddit, Mastodon)
curation/    explainable scoring + dedupe  (swap in ML behind Scorer)
service.py   orchestration (fan-out)       (shared by every adapter)
db/          SQLAlchemy 2.0 async + repos  (ORM kept out of the domain)
cli.py       CLI adapter over the service
api/         FastAPI adapter (+ campaigns) over service & repositories
config.py    twelve-factor typed settings
```

## A deliberate, honest scoping decision

Instagram and LinkedIn are included as **first-class connectors against their
official APIs**, but their reach is intentionally limited to what those
platforms actually permit in 2026:

- **Instagram Graph API** only exposes hashtag search and mentions of accounts
  you own/manage — not arbitrary public search — and requires a Business account
  plus app review.
- **LinkedIn** requires approved partner access with no public content search.

Scraping either one violates their terms and is brittle, so the design treats
them as scoped adapters behind the same `SourceConnector` interface. The honest
engineering signal here is knowing *what not to build* and structuring the system
so today's limits don't become tomorrow's rewrite. The open connectors (RSS,
Hacker News, and next Reddit/Mastodon) carry the real coverage.

## Quickstart

```bash
pip install -e ".[dev]"
brandpulse sources                 # list registered connectors
brandpulse monitor acme widget -n 15
```

### HTTP API

```bash
uvicorn brandpulse.api:app --reload
# then open http://127.0.0.1:8000/docs  (interactive OpenAPI UI)
curl "http://127.0.0.1:8000/monitor?q=acme&limit=10"
```

### Database & migrations

Persistence uses SQLAlchemy 2.0 (async). It defaults to SQLite so everything
runs with zero setup; production points `BRANDPULSE_DATABASE_URL` at Postgres
(`postgresql+asyncpg://...`). Schema changes are managed with Alembic:

```bash
alembic upgrade head                       # apply migrations
alembic revision --autogenerate -m "..."   # generate the next one
```

### Deploy (free tier)

The repo ships a `render.yaml` blueprint and a production `Dockerfile`. On
[Render](https://render.com): **New → Blueprint → point at this repo**. The
service builds the image, serves the API, and uses `/health` for health checks.
The same Dockerfile runs on Fly.io or Railway free tiers.

## Development

```bash
ruff check . && ruff format --check .
mypy
pytest                              # coverage report included
```

## Roadmap

- [x] FastAPI transport (health, sources, curated monitor endpoint)
- [x] Persistence layer (SQLAlchemy 2.0 async + Alembic) with campaigns API
- [x] Reddit + Mastodon connectors (open, unauthenticated coverage)
- [ ] Sentiment + topic clustering behind the `Scorer` protocol
- [ ] Observability: Prometheus metrics, structured logs, Grafana dashboards
- [ ] Scheduled ingestion worker

## License

MIT
# brandpulse-api
