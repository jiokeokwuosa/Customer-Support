"""API tests for LLM message rate limiting via SlowAPI."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from tests.helpers.fake_llm import pipeline_fake_llm

from app.api import deps
from app.config import Settings, get_settings
from app.main import create_app
from app.rate_limit import limiter
from app.schemas.message import ErrorCode


def _settings(*, requests: int = 20, enabled: bool = True) -> Settings:
    return Settings(
        _env_file=None,
        openai_api_key="sk-test-key",
        rate_limit_enabled=enabled,
        rate_limit_requests=requests,
        rate_limit_window_seconds=60,
    )  # type: ignore[call-arg]


@pytest.fixture
def client(db, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    get_settings.cache_clear()
    limiter.reset()
    deps.reset_chat_model_factory()
    deps.override_chat_model_factory(lambda _settings: pipeline_fake_llm())
    yield TestClient(create_app(_settings(requests=2)))
    deps.reset_chat_model_factory()
    limiter.reset()


def test_message_endpoint_returns_429_when_rate_limited(
    client: TestClient,
) -> None:
    session_id = client.post("/api/v1/sessions").json()["session_id"]
    path = f"/api/v1/sessions/{session_id}/messages"
    payload = {"message": "I was charged twice on my invoice."}

    assert client.post(path, json=payload).status_code == 200
    assert client.post(path, json=payload).status_code == 200

    blocked = client.post(path, json=payload)
    assert blocked.status_code == 429
    body = blocked.json()
    assert body["error_code"] == ErrorCode.RATE_LIMITED
    assert body["status"] == "error"
    assert "retry" in body["next_actions"]
    assert "Retry-After" in blocked.headers


def test_stream_endpoint_returns_429_when_rate_limited(
    client: TestClient,
) -> None:
    session_id = client.post("/api/v1/sessions").json()["session_id"]
    path = f"/api/v1/sessions/{session_id}/messages/stream"
    payload = {"message": "Where is order ORD-12345?"}

    assert client.post(path, json=payload).status_code == 200
    assert client.post(path, json=payload).status_code == 200

    blocked = client.post(path, json=payload)
    assert blocked.status_code == 429
    assert blocked.json()["error_code"] == ErrorCode.RATE_LIMITED


def test_full_and_stream_share_the_same_limit(client: TestClient) -> None:
    session_id = client.post("/api/v1/sessions").json()["session_id"]
    full = f"/api/v1/sessions/{session_id}/messages"
    stream = f"/api/v1/sessions/{session_id}/messages/stream"
    payload = {"message": "I need help with billing."}

    assert client.post(full, json=payload).status_code == 200
    assert client.post(stream, json=payload).status_code == 200
    assert client.post(full, json=payload).status_code == 429


def test_rate_limit_can_be_disabled(db, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    get_settings.cache_clear()
    limiter.reset()
    deps.reset_chat_model_factory()
    deps.override_chat_model_factory(lambda _settings: pipeline_fake_llm())
    client = TestClient(create_app(_settings(requests=1, enabled=False)))

    session_id = client.post("/api/v1/sessions").json()["session_id"]
    path = f"/api/v1/sessions/{session_id}/messages"
    payload = {"message": "Hello again"}

    assert client.post(path, json=payload).status_code == 200
    assert client.post(path, json=payload).status_code == 200

    deps.reset_chat_model_factory()
    limiter.reset()
