"""Unit tests for message endpoints (T042)."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from tests.helpers.fake_llm import pipeline_fake_llm

from app.api import deps
from app.config import Settings, get_settings
from app.main import create_app
from app.schemas.message import ErrorCode, TurnStatus
from app.schemas.triage import TopicCategory


def load_settings_from_env() -> Settings:
    return Settings(_env_file=None)  # type: ignore[call-arg]


@pytest.fixture
def client(db, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    get_settings.cache_clear()
    deps.reset_chat_model_factory()
    deps.override_chat_model_factory(lambda _settings: pipeline_fake_llm())
    yield TestClient(create_app(load_settings_from_env()))
    deps.reset_chat_model_factory()


def test_send_message_returns_turn_response(client: TestClient) -> None:
    session_id = client.post("/api/v1/sessions").json()["session_id"]

    response = client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"message": "I was charged twice on my invoice."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == TurnStatus.SUCCESS
    assert body["session_id"] == session_id
    assert body["message"] == "Polished billing reply."
    assert body["triage"]["topic"] == TopicCategory.BILLING


def test_send_message_returns_404_for_unknown_session(client: TestClient) -> None:
    response = client.post(
        f"/api/v1/sessions/{uuid4()}/messages",
        json={"message": "Hello"},
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == ErrorCode.SESSION_NOT_FOUND


def test_send_message_returns_422_for_blank_message(client: TestClient) -> None:
    session_id = client.post("/api/v1/sessions").json()["session_id"]

    response = client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"message": "   "},
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == ErrorCode.VALIDATION_ERROR
