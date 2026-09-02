"""Shared fixtures for HTTP integration tests."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from tests.helpers.fake_llm import pipeline_fake_llm
from tests.helpers.session_store import make_sqlite_session_store

from app.api import deps
from app.config import Settings, get_settings
from app.main import create_app
from app.services.session_store import SqliteSessionStore


def load_test_settings(database_path: Path) -> Settings:
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        openai_api_key="sk-test-key",
        database_path=str(database_path),
    )


def _pipeline_fake_llm_factory(_settings: Settings):
    return pipeline_fake_llm()


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "integration.db"


@pytest.fixture
def session_store(db_path: Path) -> Iterator[SqliteSessionStore]:
    store = make_sqlite_session_store(db_path)
    yield store
    store.close()


@pytest.fixture
def integration_client(
    session_store: SqliteSessionStore,
    db_path: Path,
) -> Iterator[TestClient]:
    get_settings.cache_clear()
    deps.reset_session_store_override()
    deps.reset_chat_model_factory()
    deps.reset_cached_session_store()

    deps.override_session_store(session_store)
    deps.override_chat_model_factory(_pipeline_fake_llm_factory)

    client = TestClient(create_app(load_test_settings(db_path)))
    yield client

    deps.reset_session_store_override()
    deps.reset_chat_model_factory()
    deps.reset_cached_session_store()
    get_settings.cache_clear()


@pytest.fixture
def session_id(session_store: SqliteSessionStore) -> UUID:
    return session_store.create().id
