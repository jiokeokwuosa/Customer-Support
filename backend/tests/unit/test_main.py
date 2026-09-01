import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import create_app


def load_settings_from_env() -> Settings:
    return Settings(_env_file=None)  # type: ignore[call-arg]


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    get_settings.cache_clear()


def test_create_app_returns_fastapi_instance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    application = create_app(load_settings_from_env())

    assert application.title == "Customer Support Triage API"


def test_cors_allows_configured_origin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    settings = load_settings_from_env()
    client = TestClient(create_app(settings))

    response = client.get("/", headers={"Origin": "http://localhost:3000"})

    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_cors_rejects_unlisted_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    client = TestClient(create_app(load_settings_from_env()))

    response = client.get("/", headers={"Origin": "http://evil.example"})

    assert "access-control-allow-origin" not in response.headers
