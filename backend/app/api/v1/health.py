"""Liveness and readiness probes at the app root (`/health`, `/ready`)."""

from fastapi import APIRouter

from app.retrieval.index import get_knowledge_index
from app.schemas.health import HealthResponse, HealthStatus, ReadyResponse, ReadyStatus

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> HealthResponse:
    """Process is up — no dependency checks."""
    return HealthResponse(status=HealthStatus.OK)


@router.get("/ready")
def readiness_check() -> ReadyResponse:
    """Accept traffic when the process is up; report knowledge index status."""
    index = get_knowledge_index()
    loaded = index is not None and index.is_loaded
    return ReadyResponse(status=ReadyStatus.READY, knowledge_loaded=loaded)
