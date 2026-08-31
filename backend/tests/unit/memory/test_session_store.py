from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.memory.session_store import InMemorySessionStore, SessionNotFoundError
from app.models.session import Turn
from app.models.triage import (
    SentimentLabel,
    TopicCategory,
    TriageMetadata,
    UrgencyLevel,
)


def _sample_turn() -> Turn:
    return Turn(
        id=uuid4(),
        user_message="My order is late",
        assistant_message="I am looking into that now.",
        triage=TriageMetadata(
            topic=TopicCategory.GENERAL,
            sentiment=SentimentLabel.NEUTRAL,
            urgency=UrgencyLevel.MEDIUM,
            rationale="Order status question",
        ),
        created_at=datetime.now(UTC),
    )


def test_create_returns_empty_session() -> None:
    store = InMemorySessionStore()

    session = store.create()
    stored = store.get(session.id)

    assert isinstance(session.id, UUID)
    assert session.turns == []
    assert stored is not None
    assert stored.id == session.id


def test_get_unknown_session_returns_none() -> None:
    store = InMemorySessionStore()

    assert store.get(uuid4()) is None


def test_append_turn_updates_session() -> None:
    store = InMemorySessionStore()
    session = store.create()
    turn = _sample_turn()

    updated = store.append_turn(session.id, turn)
    stored = store.get(session.id)

    assert len(updated.turns) == 1
    assert updated.turns[0].user_message == "My order is late"
    assert updated.updated_at >= session.updated_at
    assert stored is not None
    assert len(stored.turns) == 1


def test_append_turn_missing_session_raises() -> None:
    store = InMemorySessionStore()

    with pytest.raises(SessionNotFoundError):
        store.append_turn(uuid4(), _sample_turn())


def test_delete_is_idempotent() -> None:
    store = InMemorySessionStore()
    session = store.create()

    store.delete(session.id)
    store.delete(session.id)

    assert store.get(session.id) is None
