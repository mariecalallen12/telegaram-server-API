"""API configuration.

Keep configuration centralized and environment-driven so the server can be deployed
cleanly (local dev, Windows service, container, etc.).
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and optional `.env`."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "telegram-automation-api"
    environment: str = Field(default="dev", description="Environment name (dev/staging/prod)")

    host: str = Field(default="127.0.0.1", description="Bind host for uvicorn")
    port: int = Field(default=8000, description="Bind port for uvicorn")

    # Browser defaults used by API if caller doesn't specify.
    default_headless: bool = Field(default=True, description="Default headless mode for automation")
    use_enhanced_browser: bool = Field(default=True, description="Use EnhancedBrowserAdapter by default")

    # CORS (optional). Set to '*' for dev, a list of origins for production.
    cors_allow_origins: str = Field(default="*", description="Comma-separated list of allowed CORS origins")


def get_settings() -> Settings:
    # cached singleton is fine for process-level config
    return Settings()


