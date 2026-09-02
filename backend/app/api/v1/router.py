"""Aggregate all v1 API routes under `/api/v1`.

Feature routers (sessions, messages, prompts) register here as they land.
Health checks live at the app root (`/health`, `/ready`) per OpenAPI.
"""

from fastapi import APIRouter

from app.api.v1.messages import router as messages_router
from app.api.v1.sessions import router as sessions_router

router = APIRouter(prefix="/api/v1")

router.include_router(sessions_router)
router.include_router(messages_router)
# T091: router.include_router(prompts.router, tags=["prompts"])
