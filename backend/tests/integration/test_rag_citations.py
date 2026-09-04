"""Integration tests for RAG citation population (T062 / VS-5)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from langchain_core.embeddings import FakeEmbeddings
from tests.helpers.fake_llm import pipeline_fake_llm
from tests.integration.conftest import load_test_settings

from app.api import deps
from app.config import get_settings
from app.main import create_app
from app.retrieval.index import set_knowledge_index
from app.retrieval.retriever import build_knowledge_index
from app.schemas.message import TurnStatus


@pytest.fixture
def knowledge_client(db, tmp_path: Path) -> Iterator[TestClient]:
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()
    (knowledge_dir / "refunds.md").write_text(
        "# Digital Product Refunds\n\n"
        "Refunds for digital products are available within 14 days of purchase "
        "if the download was not completed.\n",
        encoding="utf-8",
    )

    index = build_knowledge_index(
        FakeEmbeddings(size=32),
        knowledge_dir=knowledge_dir,
        persist_directory=str(tmp_path / "chroma"),
        max_distance=None,
    )

    get_settings.cache_clear()
    deps.reset_chat_model_factory()
    deps.override_chat_model_factory(lambda _settings: pipeline_fake_llm())

    # Lifespan may clear a failed OpenAI index load; inject the fake index after.
    client = TestClient(create_app(load_test_settings()))
    set_knowledge_index(index)
    yield client

    deps.reset_chat_model_factory()
    get_settings.cache_clear()
    set_knowledge_index(None)


@pytest.fixture
def session_id(session_service) -> UUID:
    return session_service.create().id


def test_policy_question_returns_citations(
    knowledge_client: TestClient,
    session_id: UUID,
) -> None:
    response = knowledge_client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"message": "What is your refund policy for digital products?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == TurnStatus.SUCCESS
    assert body["citations"]
    assert body["citations"][0]["source_id"] == "faq-refunds"
    assert body["citations"][0]["title"] == "Digital Product Refunds"
    assert "14 days" in body["citations"][0]["excerpt"]


def test_off_topic_question_skips_retrieval_citations(
    knowledge_client: TestClient,
    session_id: UUID,
) -> None:
    response = knowledge_client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"message": "What's the weather in Paris?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == TurnStatus.SUCCESS
    assert body["citations"] == []


def test_ready_reports_knowledge_loaded(knowledge_client: TestClient) -> None:
    response = knowledge_client.get("/ready")
    assert response.status_code == 200
    assert response.json()["knowledge_loaded"] is True
