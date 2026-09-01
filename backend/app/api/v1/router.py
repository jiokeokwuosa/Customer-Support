"""Aggregate all v1 API routes under `/api/v1`.

Feature routers (sessions, messages, prompts) register here as they land.
Health checks live at the app root (`/health`, `/ready`) per OpenAPI.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")

# T041: router.include_router(sessions.router, tags=["sessions"])
# T042/T081: router.include_router(messages.router, tags=["messages"])
# T091: router.include_router(prompts.router, tags=["prompts"])
