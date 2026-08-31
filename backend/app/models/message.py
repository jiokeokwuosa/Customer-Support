"""Message request/response API models."""

from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.triage import TriageMetadata


class LookupType(StrEnum):
    ORDER = "order"
    ACCOUNT = "account"


class Citation(BaseModel):
    source_id: str
    title: str
    excerpt: str = Field(max_length=300)


class LookupResult(BaseModel):
    lookup_type: LookupType
    identifier: str
    found: bool
    summary: str
    details: dict[str, Any] | None = None


class SendMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message", mode="before")
    @classmethod
    def strip_message(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("message")
    @classmethod
    def validate_message_not_blank(cls, value: str) -> str:
        if not value:
            msg = "message must not be empty or whitespace-only"
            raise ValueError(msg)
        return value


class TurnStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"


class TurnResponse(BaseModel):
    turn_id: UUID
    session_id: UUID
    status: TurnStatus
    message: str
    triage: TriageMetadata
    citations: list[Citation] = Field(default_factory=list)
    lookup: LookupResult | None = None
    error_code: str | None = None
    next_actions: list[str] = Field(default_factory=list)


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    LLM_ERROR = "LLM_ERROR"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    message: str
    error_code: ErrorCode
    next_actions: list[str] = Field(default_factory=list)
