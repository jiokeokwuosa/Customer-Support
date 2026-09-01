"""ORM ↔ Pydantic mapping for session persistence."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from app.models.session import SessionRecord, TurnRecord
from app.schemas.message import Citation, LookupResult
from app.schemas.session import Session, Turn
from app.schemas.triage import TriageMetadata


def turn_record_to_domain(record: TurnRecord) -> Turn:
    citations_raw: list[dict[str, Any]] = json.loads(record.citations_json)
    lookup_raw = json.loads(record.lookup_json) if record.lookup_json else None
    return Turn(
        id=UUID(record.id),
        user_message=record.user_message,
        assistant_message=record.assistant_message,
        triage=TriageMetadata.model_validate_json(record.triage_json),
        citations=[Citation.model_validate(item) for item in citations_raw],
        lookup=(
            LookupResult.model_validate(lookup_raw) if lookup_raw is not None else None
        ),
        created_at=record.created_at,
    )


def session_record_to_domain(record: SessionRecord) -> Session:
    return Session(
        id=UUID(record.id),
        created_at=record.created_at,
        updated_at=record.updated_at,
        turns=[turn_record_to_domain(turn) for turn in record.turns],
    )
