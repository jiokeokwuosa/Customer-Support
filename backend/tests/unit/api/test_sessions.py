"""Unit tests for session endpoints (T041)."""

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import create_app
from app.schemas.message import ErrorCode


def load_settings_from_env() -> Settings:
    return Settings(_env_file=None)  # type: ignore[call-arg]


@pytest.fixture
def client(db, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    get_settings.cache_clear()
    return TestClient(create_app(load_settings_from_env()))


def test_create_session_returns_201_with_session_id(client: TestClient) -> None:
    response = client.post("/api/v1/sessions")

    assert response.status_code == 201
    body = response.json()
    assert UUID(body["session_id"])
    assert body["created_at"]


def test_delete_session_returns_204(client: TestClient) -> None:
    session_id = client.post("/api/v1/sessions").json()["session_id"]

    response = client.delete(f"/api/v1/sessions/{session_id}")

    assert response.status_code == 204
    assert response.content == b""


def test_delete_unknown_session_returns_404(client: TestClient) -> None:
    response = client.delete(f"/api/v1/sessions/{uuid4()}")

    assert response.status_code == 404
    body = response.json()
    assert body["error_code"] == ErrorCode.SESSION_NOT_FOUND
    assert body["status"] == "error"


def test_delete_session_is_not_idempotent_via_api(client: TestClient) -> None:
    session_id = client.post("/api/v1/sessions").json()["session_id"]

    assert client.delete(f"/api/v1/sessions/{session_id}").status_code == 204
    assert client.delete(f"/api/v1/sessions/{session_id}").status_code == 404
