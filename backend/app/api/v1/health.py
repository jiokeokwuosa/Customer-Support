"""Liveness and readiness probes at the app root (`/health`, `/ready`)."""

from fastapi import APIRouter

from app.schemas.health import HealthResponse, HealthStatus, ReadyResponse, ReadyStatus

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> HealthResponse:
    """Process is up — no dependency checks."""
    return HealthResponse(status=HealthStatus.OK)


@router.get("/ready")
def readiness_check() -> ReadyResponse:
    """Accept traffic; knowledge index status comes in T068."""
    return ReadyResponse(status=ReadyStatus.READY, knowledge_loaded=False)
