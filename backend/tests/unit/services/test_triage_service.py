"""Unit tests for TriageService (T040)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from langchain_core.runnables import RunnableLambda
from tests.helpers.fake_llm import failing_structured_output_llm, pipeline_fake_llm

from app.schemas.message import ErrorCode, TurnStatus
from app.schemas.triage import SentimentLabel, TopicCategory, UrgencyLevel
from app.services.session_service import SessionNotFoundError, SessionService
from app.services.triage_service import TriageService


def test_process_message_returns_turn_response_and_persists_turn(
    session_service: SessionService,
) -> None:
    session = session_service.create()
    service = TriageService(session_service, pipeline_fake_llm())

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
    assert "duplicate billing" in response.triage.rationale
    assert response.error_code is None

    updated = session_service.get(session.id)
    assert updated is not None
    assert len(updated.turns) == 1
    assert updated.turns[0].assistant_message == "Polished billing reply."
    assert "duplicate billing" in updated.turns[0].triage.rationale


def test_process_message_raises_for_unknown_session(
    session_service: SessionService,
) -> None:
    service = TriageService(session_service, pipeline_fake_llm())

    with pytest.raises(SessionNotFoundError):
        service.process_message(uuid4(), "Hello")


def test_process_message_returns_error_response_when_pipeline_fails(
    session_service: SessionService,
) -> None:
    session = session_service.create()
    service = TriageService(session_service, failing_structured_output_llm())

    response = service.process_message(session.id, "Help me")

    assert response.status == TurnStatus.ERROR
    assert response.error_code == ErrorCode.LLM_ERROR
    assert response.next_actions == ["retry"]
    assert "could not process" in response.message.lower()

    updated = session_service.get(session.id)
    assert updated is not None
    assert updated.turns == []


def test_process_message_propagates_pipeline_contract_errors(
    session_service: SessionService,
) -> None:
    session = session_service.create()
    broken_pipeline = RunnableLambda(
        lambda _: {"triage": "not-metadata", "final_response": "x"}
    )
    service = TriageService(session_service, pipeline_fake_llm())
    service._pipeline = broken_pipeline

    with pytest.raises(TypeError, match="triage must be TriageMetadata"):
        service.process_message(session.id, "Help me")
