# syntax=docker/dockerfile:1

# ---- builder ----------------------------------------------------------------
FROM python:3.12-slim AS builder
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --prefix=/install .

# ---- runtime ----------------------------------------------------------------
FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PORT=8000
RUN useradd --create-home --uid 1000 appuser
COPY --from=builder /install /usr/local
# Migrations ship with the image so the container can bring the schema to head
# on boot — no separate release step needed on any PaaS.
COPY alembic.ini ./
COPY migrations ./migrations
USER appuser
EXPOSE 8000
# Apply migrations, then serve the API; bind to $PORT for PaaS hosts (Render/Fly/Railway).
CMD ["sh", "-c", "alembic upgrade head && uvicorn brandpulse.api:app --host 0.0.0.0 --port ${PORT}"]
