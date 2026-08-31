"""Request/response models for sending a message and getting a turn result.

Aligned with `specs/001-ticket-triage/contracts/openapi.yaml` so the API
and frontend TypeScript types stay in sync conceptually.
"""

from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.triage import TriageMetadata


class LookupType(StrEnum):
    ORDER = "order"
    ACCOUNT = "account"


class Citation(BaseModel):
    """A short pointer to a knowledge doc used in the reply (RAG)."""

    source_id: str
    title: str
    excerpt: str = Field(max_length=300)


class LookupResult(BaseModel):
    """Outcome of a mock order/account tool lookup."""

    lookup_type: LookupType
    identifier: str
    found: bool
    summary: str
    details: dict[str, Any] | None = None


class SendMessageRequest(BaseModel):
    """Body for POST .../messages — only the customer text."""

    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message", mode="before")
    @classmethod
    def strip_message(cls, value: object) -> object:
        # Trim before length/blank checks so "  hi  " becomes a valid "hi".
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("message")
    @classmethod
    def validate_message_not_blank(cls, value: str) -> str:
        # After strip, whitespace-only input must still fail (FR-016).
        if not value:
            msg = "message must not be empty or whitespace-only"
            raise ValueError(msg)
        return value


class TurnStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"


class TurnResponse(BaseModel):
    """Unified success/error contract returned after processing a message."""

    turn_id: UUID
    session_id: UUID
    status: TurnStatus
    message: str
    triage: TriageMetadata
    citations: list[Citation] = Field(default_factory=list)
    lookup: LookupResult | None = None
    error_code: str | None = None
    # UI hints such as ["retry", "new_conversation"] — empty on success.
    next_actions: list[str] = Field(default_factory=list)


class ErrorCode(StrEnum):
    """Stable machine codes the frontend can branch on."""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    LLM_ERROR = "LLM_ERROR"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class ErrorResponse(BaseModel):
    """Standalone error body for non-turn endpoints (e.g. missing session)."""

    status: Literal["error"] = "error"
    message: str
    error_code: ErrorCode
    next_actions: list[str] = Field(default_factory=list)
