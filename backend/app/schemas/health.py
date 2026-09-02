"""Health and readiness response schemas (OpenAPI contract)."""

from enum import StrEnum

from pydantic import BaseModel


class HealthStatus(StrEnum):
    OK = "ok"


class HealthResponse(BaseModel):
    status: HealthStatus


class ReadyStatus(StrEnum):
    READY = "ready"


class ReadyResponse(BaseModel):
    status: ReadyStatus
    # T068 will flip this when the knowledge index is built.
    knowledge_loaded: bool
