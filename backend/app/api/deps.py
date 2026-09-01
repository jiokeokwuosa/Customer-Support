"""FastAPI dependency injection for settings, stores, and LLM clients.

Routes depend on these callables; tests swap implementations via the override
hooks below or FastAPI's `app.dependency_overrides`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.config import Settings, get_settings
from app.services.session_store import SqliteSessionStore

SettingsDep = Annotated[Settings, Depends(get_settings)]

ChatModelFactory = Callable[[Settings], BaseChatModel]

_session_store: SqliteSessionStore | None = None
_session_store_override: SqliteSessionStore | None = None
_chat_model_factory_override: ChatModelFactory | None = None


def override_session_store(store: SqliteSessionStore) -> None:
    """Inject a test double for the session store dependency."""
    global _session_store_override
    _session_store_override = store


def reset_cached_session_store() -> None:
    """Close and drop the process-wide store instance."""
    global _session_store
    if _session_store is not None:
        _session_store.close()
        _session_store = None


def reset_session_store_override() -> None:
    """Clear the session store test override and close any cached instance."""
    global _session_store_override
    _session_store_override = None
    reset_cached_session_store()


def get_session_store(settings: SettingsDep) -> SqliteSessionStore:
    """Return a process-wide session store (one SQLite file per app process)."""
    global _session_store
    if _session_store_override is not None:
        return _session_store_override
    if _session_store is None:
        _session_store = SqliteSessionStore(settings.database_path)
    return _session_store


SessionStoreDep = Annotated[SqliteSessionStore, Depends(get_session_store)]


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
