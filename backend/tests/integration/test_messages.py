"""Integration tests for POST /api/v1/sessions/{session_id}/messages (T031)."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.schemas.message import TurnStatus
from app.schemas.triage import TopicCategory


def test_send_message_returns_turn_response(
    integration_client: TestClient,
    session_id: UUID,
) -> None:
    response = integration_client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"message": "I was charged twice on my invoice."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == TurnStatus.SUCCESS
    assert body["session_id"] == str(session_id)
    assert body["message"] == "Polished billing reply."
    assert body["triage"]["topic"] == TopicCategory.BILLING
    assert body["triage"]["sentiment"] == "frustrated"
    assert body["triage"]["urgency"] == "high"
    assert "duplicate billing" in body["triage"]["rationale"]
    assert body["citations"] == []
    assert body["lookup"] is None
    assert body["error_code"] is None


def test_send_message_returns_404_for_unknown_session(
    integration_client: TestClient,
) -> None:
    response = integration_client.post(
        f"/api/v1/sessions/{uuid4()}/messages",
        json={"message": "Hello"},
    )

    assert response.status_code == 404
    body = response.json()
    assert body["error_code"] == "SESSION_NOT_FOUND"


def test_send_message_returns_422_for_blank_message(
    integration_client: TestClient,
    session_id: UUID,
) -> None:
    response = integration_client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"message": "   "},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error_code"] == "VALIDATION_ERROR"
