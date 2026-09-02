"""Shared fixtures for HTTP integration tests."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from langchain_community.chat_models.fake import FakeListChatModel
from langchain_core.runnables import RunnableLambda

from app.api import deps
from app.config import Settings, get_settings
from app.llm.chains.classification.sentiment_urgency import SentimentUrgencyOutput
from app.llm.chains.classification.topic_classifier import TopicClassificationOutput
from app.main import create_app
from app.schemas.triage import SentimentLabel, TopicCategory, UrgencyLevel
from app.services.session_store import SqliteSessionStore


def load_test_settings(database_path: Path) -> Settings:
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        openai_api_key="sk-test-key",
        database_path=str(database_path),
    )


def _structured_output_factory(model: type) -> RunnableLambda:
    if model is SentimentUrgencyOutput:
        return RunnableLambda(
            lambda _: SentimentUrgencyOutput(
                sentiment=SentimentLabel.FRUSTRATED,
                urgency=UrgencyLevel.HIGH,
            )
        )
    if model is TopicClassificationOutput:
        return RunnableLambda(
            lambda _: TopicClassificationOutput(
                topic=TopicCategory.BILLING,
                rationale="Customer reports duplicate billing charge.",
            )
        )
    msg = f"Unexpected structured output model: {model}"
    raise ValueError(msg)


def _pipeline_fake_llm(_settings: Settings) -> FakeListChatModel:
    llm = FakeListChatModel(
        responses=["Billing draft reply.", "Polished billing reply."]
    )
    object.__setattr__(
        llm,
        "with_structured_output",
        MagicMock(side_effect=_structured_output_factory),
    )
    return llm


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "integration.db"


@pytest.fixture
def session_store(db_path: Path) -> Iterator[SqliteSessionStore]:
    store = SqliteSessionStore(db_path)
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
    deps.override_chat_model_factory(_pipeline_fake_llm)

    client = TestClient(create_app(load_test_settings(db_path)))
    yield client

    deps.reset_session_store_override()
    deps.reset_chat_model_factory()
    deps.reset_cached_session_store()
    get_settings.cache_clear()


@pytest.fixture
def session_id(session_store: SqliteSessionStore) -> UUID:
    return session_store.create().id
