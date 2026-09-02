"""Aggregate all v1 API routes under `/api/v1`.

Feature routers (sessions, messages, prompts) register here as they land.
Health checks live at the app root (`/health`, `/ready`) per OpenAPI.
"""

from fastapi import APIRouter

from app.api.v1.sessions import router as sessions_router

router = APIRouter(prefix="/api/v1")

router.include_router(sessions_router)
# T042/T081: router.include_router(messages.router, tags=["messages"])
# T091: router.include_router(prompts.router, tags=["prompts"])
