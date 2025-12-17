"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from importlib import metadata

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routes.auth import router as auth_router
from .routes.contacts import router as contacts_router
from .routes.groups import router as groups_router
from .routes.notes import router as notes_router
from .routes.runs import router as runs_router
from .routes.sessions import router as sessions_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Telegram Automation API",
        description="Server API for automating Telegram Web operations (Playwright).",
        version=_get_version(),
    )

    allow_origins = [o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins if allow_origins else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/version")
    async def version() -> dict[str, str]:
        return {"version": _get_version()}

    app.include_router(auth_router)
    app.include_router(sessions_router)
    app.include_router(contacts_router)
    app.include_router(groups_router)
    app.include_router(runs_router)
    app.include_router(notes_router)

    return app


def _get_version() -> str:
    # Best-effort. When running from source without an installed package, fallback.
    try:
        return metadata.version("telegram-automation")
    except Exception:
        return "0.0.0"


app = create_app()


