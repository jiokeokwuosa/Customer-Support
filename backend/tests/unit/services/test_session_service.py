from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.db.database import SessionLocal
from app.exceptions import SessionNotFoundError
from app.repositories.session_repository import SessionRepository
from app.schemas.message import Citation, LookupResult, LookupType
from app.schemas.session import Turn
from app.schemas.triage import (
    SentimentLabel,
    TopicCategory,
    TriageMetadata,
    UrgencyLevel,
)
from app.services.session_service import SessionService


@pytest.fixture
def service(session_service: SessionService) -> SessionService:
    return session_service


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


def test_create_returns_empty_session(service: SessionService) -> None:
    session = service.create()
    stored = service.get(session.id)

    assert isinstance(session.id, UUID)
    assert session.turns == []
    assert stored is not None
    assert stored.id == session.id


def test_get_unknown_session_returns_none(service: SessionService) -> None:
    assert service.get(uuid4()) is None


def test_require_unknown_session_raises(service: SessionService) -> None:
    with pytest.raises(SessionNotFoundError):
        service.require(uuid4())


def test_require_returns_existing_session(service: SessionService) -> None:
    session = service.create()
    assert service.require(session.id).id == session.id


def test_append_turn_persists_across_reload(service: SessionService) -> None:
    session = service.create()
    turn = _sample_turn(with_extras=True)
    service.append_turn(session.id, turn)

    reloaded = SessionService(SessionRepository(SessionLocal()))
    stored = reloaded.get(session.id)

    assert stored is not None
    assert len(stored.turns) == 1
    assert stored.turns[0].user_message == "My order is late"
    assert stored.turns[0].citations[0].source_id == "faq-shipping"
    assert stored.turns[0].lookup is not None
    assert stored.turns[0].lookup.identifier == "ORD-12345"


def test_append_turn_missing_session_raises(service: SessionService) -> None:
    with pytest.raises(SessionNotFoundError):
        service.append_turn(uuid4(), _sample_turn())


def test_delete_is_idempotent(service: SessionService) -> None:
    session = service.create()
    service.append_turn(session.id, _sample_turn())

    service.delete(session.id)
    service.delete(session.id)

    assert service.get(session.id) is None


def test_append_turn_trims_to_max_twenty(service: SessionService) -> None:
    session = service.create()
    first = _sample_turn()
    service.append_turn(session.id, first)

    for _ in range(20):
        service.append_turn(session.id, _sample_turn())

    stored = service.get(session.id)
    assert stored is not None
    assert len(stored.turns) == 20
    assert all(turn.id != first.id for turn in stored.turns)


def test_append_turn_keeps_newest_twenty_in_order(service: SessionService) -> None:
    """VR-003: after overflow, retained turns are the latest 20 in FIFO order."""
    session = service.create()
    turn_ids: list[UUID] = []

    for _ in range(25):
        turn = _sample_turn()
        turn_ids.append(turn.id)
        service.append_turn(session.id, turn)

    stored = service.get(session.id)
    assert stored is not None
    assert [turn.id for turn in stored.turns] == turn_ids[-20:]


def test_append_exactly_twenty_turns_does_not_drop_any(service: SessionService) -> None:
    session = service.create()
    turn_ids: list[UUID] = []

    for _ in range(20):
        turn = _sample_turn()
        turn_ids.append(turn.id)
        service.append_turn(session.id, turn)

    stored = service.get(session.id)
    assert stored is not None
    assert len(stored.turns) == 20
    assert [turn.id for turn in stored.turns] == turn_ids
