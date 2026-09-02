"""FastAPI application factory.

`create_app()` builds the app so tests can inject settings without touching
the process environment. Uvicorn imports the module-level `app` instance.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.health import router as health_router
from app.api.v1.router import router as v1_router
from app.config import Settings, get_settings
from app.db.database import init_db, settings as db_settings
from app.schemas.message import ErrorCode, ErrorResponse
from app.services.session_service import SessionNotFoundError


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown hook — extend when wiring stores and retrievers."""
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure the FastAPI application.

    When ``settings`` is passed, only the FastAPI ``get_settings`` dependency
    is overridden (e.g. CORS, model name). The database path always comes from
    the environment / import-time ``database`` settings module.
    """
    resolved = settings if settings is not None else get_settings()
    Path(db_settings.database_path).parent.mkdir(parents=True, exist_ok=True)
    init_db()

    application = FastAPI(
        title="Customer Support Triage API",
        version="0.1.0",
        lifespan=lifespan,
    )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request,
        _exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                message="Invalid request body",
                error_code=ErrorCode.VALIDATION_ERROR,
            ).model_dump(mode="json"),
        )

    @application.exception_handler(SessionNotFoundError)
    async def session_not_found_handler(
        _request: Request,
        exc: SessionNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                message="Session not found",
                error_code=ErrorCode.SESSION_NOT_FOUND,
            ).model_dump(mode="json"),
        )

    if settings is not None:
        application.dependency_overrides[get_settings] = lambda: resolved

    # Frontend (Next.js dev server) calls this API from another origin.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health_router)
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
