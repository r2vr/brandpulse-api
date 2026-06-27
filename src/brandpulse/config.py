"""Typed application settings.

Twelve-factor config: everything tunable comes from the environment, validated
once at startup. Importing :data:`settings` anywhere gives a single, immutable,
type-checked source of truth.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BRANDPULSE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")

    http_timeout_seconds: float = Field(default=10.0, gt=0)
    default_result_limit: int = Field(default=50, gt=0, le=500)

    # Async SQLAlchemy URL. SQLite by default so the app runs with zero setup;
    # production overrides with postgresql+asyncpg://... via the environment.
    database_url: str = Field(default="sqlite+aiosqlite:///./brandpulse.db")
    db_echo: bool = Field(default=False)

    @field_validator("database_url")
    @classmethod
    def _ensure_async_driver(cls, url: str) -> str:
        """Coerce a managed host's sync Postgres URL onto the async driver.

        Render/Heroku/Railway hand out ``postgres://`` or ``postgresql://``
        connection strings; the async engine needs ``postgresql+asyncpg://``.
        Rewriting here means the deploy can wire the raw env var verbatim.
        """
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://") :]
        if url.startswith("postgresql://"):
            url = "postgresql+asyncpg://" + url[len("postgresql://") :]
        return url

    # Optional credentials for scoped official connectors (Instagram/LinkedIn).
    instagram_access_token: str | None = None
    linkedin_access_token: str | None = None

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached accessor so config is parsed exactly once per process."""
    return Settings()
