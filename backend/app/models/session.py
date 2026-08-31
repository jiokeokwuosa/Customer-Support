"""Shapes for a chat session and one turn inside it.

These are in-memory / API models (Pydantic). Persistence lives in
`app.memory.session_store` — this file only describes the data shape.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.message import Citation, LookupResult
from app.models.triage import TriageMetadata


class TurnRole(StrEnum):
    """Who spoke — useful when converting turns into chat history later."""

    USER = "user"
    ASSISTANT = "assistant"


class Turn(BaseModel):
    """One full exchange: customer message + assistant reply + triage extras."""

    id: UUID
    user_message: str = Field(min_length=1, max_length=4000)
    assistant_message: str = Field(min_length=1)
    triage: TriageMetadata
    citations: list[Citation] = Field(default_factory=list)
    lookup: LookupResult | None = None
    created_at: datetime


class Session(BaseModel):
    """A whole conversation thread the client identifies by `id`."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    # Spec/constitution: keep recent context only (trim logic comes in T057).
    turns: list[Turn] = Field(default_factory=list, max_length=20)


class CreateSessionResponse(BaseModel):
    """API payload after POST /sessions — client stores session_id for later."""

    session_id: UUID
    created_at: datetime
