"""Unit tests for TriageService (T040)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from langchain_community.chat_models.fake import FakeListChatModel
from langchain_core.runnables import RunnableLambda

from app.llm.chains.classification.sentiment_urgency import SentimentUrgencyOutput
from app.llm.chains.classification.topic_classifier import TopicClassificationOutput
from app.schemas.message import ErrorCode, TurnStatus
from app.schemas.triage import SentimentLabel, TopicCategory, UrgencyLevel
from app.services.session_store import SessionNotFoundError, SqliteSessionStore
from app.services.triage_service import TriageService


def _structured_output_factory(model: type) -> RunnableLambda:
    if model is SentimentUrgencyOutput:
        return RunnableLambda(
            lambda _: SentimentUrgencyOutput(
                sentiment=SentimentLabel.FRUSTRATED,
                urgency=UrgencyLevel.HIGH,
            )
        )
    if model is TopicClassificationOutput:
        return RunnableLambda(
            lambda _: TopicClassificationOutput(
                topic=TopicCategory.BILLING,
                rationale="Customer reports duplicate billing charge.",
            )
        )
    msg = f"Unexpected structured output model: {model}"
    raise ValueError(msg)


def _pipeline_fake_llm() -> FakeListChatModel:
    llm = FakeListChatModel(
        responses=["Billing draft reply.", "Polished billing reply."]
    )
    object.__setattr__(
        llm,
        "with_structured_output",
        MagicMock(side_effect=_structured_output_factory),
    )
    return llm


@pytest.fixture
def store(tmp_path: Path) -> SqliteSessionStore:
    db = SqliteSessionStore(tmp_path / "sessions.db")
    yield db
    db.close()


def test_process_message_returns_turn_response_and_persists_turn(
    store: SqliteSessionStore,
) -> None:
    session = store.create()
    service = TriageService(store, _pipeline_fake_llm())

    response = service.process_message(
        session.id,
        "I was charged twice on my invoice.",
    )

    assert response.status == TurnStatus.SUCCESS
    assert response.session_id == session.id
    assert response.message == "Polished billing reply."
    assert response.triage.topic == TopicCategory.BILLING
    assert response.triage.sentiment == SentimentLabel.FRUSTRATED
    assert response.triage.urgency == UrgencyLevel.HIGH
    assert response.error_code is None

    updated = store.get(session.id)
    assert updated is not None
    assert len(updated.turns) == 1
    assert updated.turns[0].assistant_message == "Polished billing reply."


def test_process_message_raises_for_unknown_session(
    store: SqliteSessionStore,
) -> None:
    service = TriageService(store, _pipeline_fake_llm())

    with pytest.raises(SessionNotFoundError):
        service.process_message(uuid4(), "Hello")


def test_process_message_returns_error_response_when_pipeline_fails(
    store: SqliteSessionStore,
) -> None:
    session = store.create()
    llm = FakeListChatModel(responses=["unused", "unused"])
    object.__setattr__(
        llm,
        "with_structured_output",
        MagicMock(
            return_value=RunnableLambda(
                lambda _: (_ for _ in ()).throw(RuntimeError("LLM unavailable"))
            )
        ),
    )
    service = TriageService(store, llm)

    response = service.process_message(session.id, "Help me")

    assert response.status == TurnStatus.ERROR
    assert response.error_code == ErrorCode.LLM_ERROR
    assert response.next_actions == ["retry"]
    assert "could not process" in response.message.lower()

    updated = store.get(session.id)
    assert updated is not None
    assert updated.turns == []
