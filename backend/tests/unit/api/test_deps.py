from pathlib import Path

import pytest
from langchain_community.chat_models.fake import FakeListChatModel
from langchain_openai import ChatOpenAI

from app.api import deps
from app.config import Settings, get_settings
from app.main import create_app
from app.services.session_store import SqliteSessionStore


def load_settings_from_env() -> Settings:
    return Settings(_env_file=None)  # type: ignore[call-arg]


@pytest.fixture(autouse=True)
def clear_dependency_state() -> None:
    get_settings.cache_clear()
    deps.reset_session_store_override()
    deps.reset_chat_model_factory()
    yield
    deps.reset_session_store_override()
    deps.reset_chat_model_factory()


def test_get_session_store_creates_sqlite_store(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "sessions.db"))
    settings = load_settings_from_env()

    store = deps.get_session_store(settings)

    assert isinstance(store, SqliteSessionStore)
    session = store.create()
    assert session.turns == []
    store.close()


def test_get_session_store_reuses_singleton(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "sessions.db"))
    settings = load_settings_from_env()

    first = deps.get_session_store(settings)
    second = deps.get_session_store(settings)

    assert first is second
    first.close()


def test_override_session_store_returns_injected_instance(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    settings = load_settings_from_env()
    injected = SqliteSessionStore(tmp_path / "injected.db")
    deps.override_session_store(injected)

    assert deps.get_session_store(settings) is injected

    injected.close()


def test_create_chat_model_builds_openai_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    settings = load_settings_from_env()

    model = deps.create_chat_model(settings)

    assert isinstance(model, ChatOpenAI)
    assert model.model_name == "gpt-4o-mini"


def test_create_app_overrides_get_settings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "from-env.db"))
    custom_settings = load_settings_from_env().model_copy(
        update={"database_path": str(tmp_path / "injected.db")}
    )

    application = create_app(custom_settings)

    assert application.dependency_overrides[get_settings]() is custom_settings


def test_override_chat_model_factory_returns_fake(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    settings = load_settings_from_env()
    fake = FakeListChatModel(responses=["test response"])
    deps.override_chat_model_factory(lambda _settings: fake)

    assert deps.create_chat_model(settings) is fake
