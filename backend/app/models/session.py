"""Session domain and API models."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.message import Citation, LookupResult
from app.models.triage import TriageMetadata


class TurnRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class Turn(BaseModel):
    id: UUID
    user_message: str = Field(min_length=1, max_length=4000)
    assistant_message: str = Field(min_length=1)
    triage: TriageMetadata
    citations: list[Citation] = Field(default_factory=list)
    lookup: LookupResult | None = None
    created_at: datetime


class Session(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    turns: list[Turn] = Field(default_factory=list, max_length=20)


class CreateSessionResponse(BaseModel):
    session_id: UUID
    created_at: datetime
