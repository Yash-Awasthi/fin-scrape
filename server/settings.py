"""Typed settings for the WorldFin backend (pydantic-settings).

One typed object, imported everywhere — no scattered os.getenv. Reads from the
process env / .env. BYOK and Ollama keys are the SAME ones finscrape already uses
(OPENAI_BASE_URL / OPENROUTER_API_KEY), so a single .env drives both halves.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", case_sensitive=False
    )

    # --- Database ---
    # asyncpg DSN. Compose injects this; default points at the compose service.
    database_url: str = Field(
        default="postgresql://worldfin:worldfin@localhost:5432/worldfin",
        validation_alias="WORLDFIN_DATABASE_URL",
    )
    db_pool_min: int = Field(default=2, validation_alias="WORLDFIN_DB_POOL_MIN")
    db_pool_max: int = Field(default=10, validation_alias="WORLDFIN_DB_POOL_MAX")
    run_migrations_on_startup: bool = Field(
        default=True, validation_alias="WORLDFIN_RUN_MIGRATIONS"
    )

    # --- Ingest auth (the 4 mutating routes) ---
    api_key: str = Field(default="local-dev-key", validation_alias="FINSCRAPE_API_KEY")

    # --- LLM (shared with finscrape: BYOK or local Ollama) ---
    openai_base_url: str = Field(default="", validation_alias="OPENAI_BASE_URL")
    openrouter_api_key: str = Field(default="", validation_alias="OPENROUTER_API_KEY")
    ai_model: str = Field(default="auto", validation_alias="FINSCRAPE_MODEL")

    # --- Optional infra ---
    redis_url: str = Field(default="", validation_alias="WORLDFIN_REDIS_URL")

    # --- Feature flags (default off; flip on as phases land) ---
    enable_council: bool = Field(
        default=False, validation_alias="WORLDFIN_ENABLE_COUNCIL"
    )
    enable_correlation: bool = Field(
        default=True, validation_alias="WORLDFIN_ENABLE_CORRELATION"
    )

    # --- Worker (Phase 3) ---
    worker_interval_minutes: int = Field(
        default=15, validation_alias="WORLDFIN_WORKER_INTERVAL_MIN"
    )
    worker_max_articles: int = Field(
        default=20, validation_alias="WORLDFIN_WORKER_MAX_ARTICLES"
    )
    source_stale_after_minutes: int = Field(
        default=60, validation_alias="WORLDFIN_SOURCE_STALE_MIN"
    )

    # --- Server ---
    host: str = Field(default="0.0.0.0", validation_alias="WORLDFIN_HOST")
    port: int = Field(default=8000, validation_alias="WORLDFIN_PORT")
    cors_origins: str = Field(default="*", validation_alias="WORLDFIN_CORS_ORIGINS")

    @property
    def has_llm(self) -> bool:
        """True if any LLM backend is configured (Ollama proxy or OpenRouter BYOK)."""
        return bool(self.openai_base_url or self.openrouter_api_key)

    @property
    def redis_enabled(self) -> bool:
        return bool(self.redis_url)


@lru_cache
def get_settings() -> Settings:
    """Cached singleton. Tests can clear with get_settings.cache_clear()."""
    return Settings()
