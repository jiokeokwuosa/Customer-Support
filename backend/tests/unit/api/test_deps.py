import pytest
from langchain_community.chat_models.fake import FakeListChatModel
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from app.api import deps
from app.config import Settings, get_settings
from app.db.database import get_db
from app.main import create_app
from app.repositories.session_repository import SessionRepository
from app.services.session_service import SessionService


def load_settings_from_env() -> Settings:
    return Settings(_env_file=None)  # type: ignore[call-arg]


@pytest.fixture(autouse=True)
def clear_dependency_state() -> None:
    get_settings.cache_clear()
    deps.reset_chat_model_factory()
    yield
    deps.reset_chat_model_factory()


def test_get_session_service_wires_repository(db: Session) -> None:
    service = deps.get_session_service(db)

    assert isinstance(service, SessionService)
    session = service.create()
    assert session.turns == []


def test_get_triage_service_wires_session_service_and_llm(
    monkeypatch: pytest.MonkeyPatch,
    db: Session,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    settings = load_settings_from_env()

    triage_service = deps.get_triage_service(
        deps.get_session_service(db),
        deps.create_chat_model(settings),
    )

    session = triage_service._session_service.create()
    assert session.turns == []


def test_create_chat_model_builds_openai_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    settings = load_settings_from_env()

    model = deps.create_chat_model(settings)

    assert isinstance(model, ChatOpenAI)
    assert model.model_name == "gpt-4o-mini"


def test_create_app_overrides_get_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    custom_settings = load_settings_from_env().model_copy(
        update={"openai_model": "gpt-4o"},
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


def test_get_db_yields_request_scoped_session(db: Session) -> None:
    generator = get_db()
    session = next(generator)
    try:
        assert isinstance(session, Session)
        repo = SessionRepository(session)
        assert isinstance(deps.get_session_service(session), SessionService)
        assert repo.create_session().turns == []
    finally:
        generator.close()
