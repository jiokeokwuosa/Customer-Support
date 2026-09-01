"""FastAPI application factory.

`create_app()` builds the app so tests can inject settings without touching
the process environment. Uvicorn imports the module-level `app` instance.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.config import Settings, get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown hook — extend when wiring stores and retrievers."""
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure the FastAPI application."""
    resolved = settings if settings is not None else get_settings()

    application = FastAPI(
        title="Customer Support Triage API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Frontend (Next.js dev server) calls this API from another origin.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(v1_router)

    return application


_app: FastAPI | None = None


def __getattr__(name: str) -> FastAPI:
    """Lazy `app` so importing this module in tests does not require `.env`."""
    if name == "app":
        global _app
        if _app is None:
            _app = create_app()
        return _app
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


# uvicorn app.main:app --reload
