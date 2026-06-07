"""Application configuration via pydantic-settings.

All settings can be overridden by environment variables (prefix ``AGENTCANVAS_``)
or a ``.env`` file in the backend directory.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AGENTCANVAS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # SQLite for the MVP; swap for a postgresql+psycopg URL later (schema is portable).
    database_url: str = "sqlite:///./agentcanvas.db"

    # CORS origins allowed to call the API (the Vite dev server by default).
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Inline text payloads are truncated to this many characters before storage.
    # Full bodies belong in an object store (content_ref) in V1.
    max_inline_content_chars: int = 20_000

    api_prefix: str = "/api/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
