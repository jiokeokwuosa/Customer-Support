"""Shared fixtures for HTTP integration tests."""

from __future__ import annotations

from collections.abc import Iterator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from tests.helpers.fake_llm import pipeline_fake_llm

from app.api import deps
from app.config import Settings, get_settings
from app.main import create_app


def load_test_settings() -> Settings:
    return Settings(_env_file=None)  # type: ignore[call-arg]


def _pipeline_fake_llm_factory(_settings: Settings):
    return pipeline_fake_llm()


@pytest.fixture
def integration_client(db) -> Iterator[TestClient]:
    get_settings.cache_clear()
    deps.reset_chat_model_factory()
    deps.override_chat_model_factory(_pipeline_fake_llm_factory)

    client = TestClient(create_app(load_test_settings()))
    yield client

    deps.reset_chat_model_factory()
    get_settings.cache_clear()


@pytest.fixture
def session_id(session_service) -> UUID:
    return session_service.create().id
