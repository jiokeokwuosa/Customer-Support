from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from app.schemas.message import Citation, LookupResult, LookupType
from app.schemas.session import Turn
from app.schemas.triage import (
    SentimentLabel,
    TopicCategory,
    TriageMetadata,
    UrgencyLevel,
)
from app.services.session_store import SessionNotFoundError, SqliteSessionStore


@pytest.fixture
def store(tmp_path: Path) -> SqliteSessionStore:
    db = SqliteSessionStore(tmp_path / "sessions.db")
    yield db
    db.close()


def _sample_turn(*, with_extras: bool = False) -> Turn:
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
        citations=(
            [
                Citation(
                    source_id="faq-shipping",
                    title="Shipping",
                    excerpt="Orders ship in 3-5 days.",
                )
            ]
            if with_extras
            else []
        ),
        lookup=(
            LookupResult(
                lookup_type=LookupType.ORDER,
                identifier="ORD-12345",
                found=True,
                summary="Shipped",
                details={"carrier": "UPS"},
            )
            if with_extras
            else None
        ),
        created_at=datetime.now(UTC),
    )


def test_create_returns_empty_session(store: SqliteSessionStore) -> None:
    session = store.create()
    stored = store.get(session.id)

    assert isinstance(session.id, UUID)
    assert session.turns == []
    assert stored is not None
    assert stored.id == session.id


def test_get_unknown_session_returns_none(store: SqliteSessionStore) -> None:
    assert store.get(uuid4()) is None


def test_require_unknown_session_raises(store: SqliteSessionStore) -> None:
    with pytest.raises(SessionNotFoundError):
        store.require(uuid4())


def test_require_returns_existing_session(store: SqliteSessionStore) -> None:
    session = store.create()
    assert store.require(session.id).id == session.id


def test_append_turn_persists_across_reload(tmp_path: Path) -> None:
    db_path = tmp_path / "sessions.db"
    store = SqliteSessionStore(db_path)
    session = store.create()
    turn = _sample_turn(with_extras=True)
    store.append_turn(session.id, turn)
    store.close()

    reloaded = SqliteSessionStore(db_path)
    stored = reloaded.get(session.id)
    reloaded.close()

    assert stored is not None
    assert len(stored.turns) == 1
    assert stored.turns[0].user_message == "My order is late"
    assert stored.turns[0].citations[0].source_id == "faq-shipping"
    assert stored.turns[0].lookup is not None
    assert stored.turns[0].lookup.identifier == "ORD-12345"


def test_append_turn_missing_session_raises(store: SqliteSessionStore) -> None:
    with pytest.raises(SessionNotFoundError):
        store.append_turn(uuid4(), _sample_turn())


def test_delete_is_idempotent(store: SqliteSessionStore) -> None:
    session = store.create()
    store.append_turn(session.id, _sample_turn())

    store.delete(session.id)
    store.delete(session.id)

    assert store.get(session.id) is None


def test_append_turn_trims_to_max_twenty(store: SqliteSessionStore) -> None:
    session = store.create()
    first = _sample_turn()
    store.append_turn(session.id, first)

    for _ in range(20):
        store.append_turn(session.id, _sample_turn())

    stored = store.get(session.id)
    assert stored is not None
    assert len(stored.turns) == 20
    assert all(turn.id != first.id for turn in stored.turns)
