"""FastAPI dependency injection for settings, DB sessions, and LLM clients.

Routes depend on these callables; tests swap implementations via FastAPI's
`app.dependency_overrides`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.database import get_db
from app.repositories.session_repository import SessionRepository
from app.retrieval.index import get_knowledge_index
from app.services.session_service import SessionService
from app.services.triage_service import TriageService

SettingsDep = Annotated[Settings, Depends(get_settings)]

ChatModelFactory = Callable[[Settings], BaseChatModel]

_chat_model_factory_override: ChatModelFactory | None = None


def override_chat_model_factory(factory: ChatModelFactory) -> None:
    """Inject a factory that returns fake LLMs in tests."""
    global _chat_model_factory_override
    _chat_model_factory_override = factory


def reset_chat_model_factory() -> None:
    """Clear the LLM factory test override."""
    global _chat_model_factory_override
    _chat_model_factory_override = None


def create_chat_model(settings: Settings) -> BaseChatModel:
    """Build the default OpenAI chat model, or a test override when set."""
    if _chat_model_factory_override is not None:
        return _chat_model_factory_override(settings)
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        timeout=settings.chain_timeout_seconds,
    )


def get_chat_model(settings: SettingsDep) -> BaseChatModel:
    return create_chat_model(settings)


ChatModelDep = Annotated[BaseChatModel, Depends(get_chat_model)]


def get_session_service(db: Session = Depends(get_db)) -> SessionService:
    return SessionService(SessionRepository(db))


SessionServiceDep = Annotated[SessionService, Depends(get_session_service)]


def get_triage_service(
    session_service: SessionServiceDep,
    llm: ChatModelDep,
) -> TriageService:
    return TriageService(
        session_service,
        llm,
        knowledge_index=get_knowledge_index(),
    )


TriageServiceDep = Annotated[TriageService, Depends(get_triage_service)]
