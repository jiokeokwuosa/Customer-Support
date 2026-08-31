from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.models.session import CreateSessionResponse, Session, Turn
from app.models.triage import (
    SentimentLabel,
    TopicCategory,
    TriageMetadata,
    UrgencyLevel,
)


def test_create_session_response_shape() -> None:
    created_at = datetime(2026, 8, 31, 12, 0, tzinfo=UTC)
    response = CreateSessionResponse(
        session_id=UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8"),
        created_at=created_at,
    )

    assert response.session_id == UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
    assert response.created_at == created_at


def test_session_limits_turn_history_to_twenty() -> None:
    now = datetime(2026, 8, 31, 12, 0, tzinfo=UTC)
    triage = TriageMetadata(
        topic=TopicCategory.GENERAL,
        sentiment=SentimentLabel.NEUTRAL,
        urgency=UrgencyLevel.LOW,
        rationale="Test",
    )
    turn = Turn(
        id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        user_message="Hi",
        assistant_message="Hello",
        triage=triage,
        created_at=now,
    )
    session = Session(
        id=UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8"),
        created_at=now,
        updated_at=now,
        turns=[turn],
    )

    assert len(session.turns) == 1

    with pytest.raises(ValidationError):
        Session(
            id=UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8"),
            created_at=now,
            updated_at=now,
            turns=[turn] * 21,
        )
