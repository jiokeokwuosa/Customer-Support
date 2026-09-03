"""Integration tests for multi-turn session memory (T054 / VS-4)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from langchain_community.chat_models.fake import FakeListChatModel
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from pydantic import PrivateAttr
from tests.helpers.fake_llm import structured_output_factory
from tests.integration.conftest import load_test_settings

from app.api import deps
from app.config import Settings, get_settings
from app.main import create_app
from app.schemas.message import TurnStatus
from app.services.session_service import SessionService


class CapturingFakeChatModel(FakeListChatModel):
    """FakeListChatModel that records every message list passed to generate."""

    _captured_prompts: list[list[BaseMessage]] = PrivateAttr(default_factory=list)

    @property
    def captured_prompts(self) -> list[list[BaseMessage]]:
        return self._captured_prompts

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        self._captured_prompts.append(list(messages))
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)


def _memory_fake_llm() -> CapturingFakeChatModel:
    # Two full pipeline runs: draft + polish per turn (structured output is mocked).
    # Responses deliberately omit the order id so capture assertions only pass when
    # prior-turn history is injected into the follow-up prompts (T055/T056).
    llm = CapturingFakeChatModel(
        responses=[
            "Draft: looking into your request.",
            "Polished: I can help with your request.",
            "Draft: that usually takes 5-7 business days.",
            "Polished: That typically takes 5-7 business days.",
        ]
    )
    object.__setattr__(
        llm,
        "with_structured_output",
        MagicMock(side_effect=structured_output_factory),
    )
    return llm


@pytest.fixture
def memory_llm() -> CapturingFakeChatModel:
    return _memory_fake_llm()


@pytest.fixture
def memory_client(db, memory_llm: CapturingFakeChatModel) -> Iterator[TestClient]:
    get_settings.cache_clear()
    deps.reset_chat_model_factory()

    def factory(_settings: Settings) -> BaseChatModel:
        return memory_llm

    deps.override_chat_model_factory(factory)
    client = TestClient(create_app(load_test_settings()))
    yield client
    deps.reset_chat_model_factory()
    get_settings.cache_clear()


def _prompt_blob(prompts: list[list[BaseMessage]]) -> str:
    parts: list[str] = []
    for messages in prompts:
        for message in messages:
            content = message.content
            if isinstance(content, str):
                parts.append(content)
            else:
                parts.append(str(content))
    return "\n".join(parts)


def test_follow_up_passes_prior_turn_into_llm_context(
    memory_client: TestClient,
    memory_llm: CapturingFakeChatModel,
    session_id: UUID,
    session_service: SessionService,
) -> None:
    """VS-4: second message omits order context; pipeline still sees turn 1."""
    first = memory_client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"message": "I need a refund for order ORD-12345."},
    )
    assert first.status_code == 200
    assert first.json()["status"] == TurnStatus.SUCCESS

    prompts_after_first = len(memory_llm.captured_prompts)

    second = memory_client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"message": "How long will that take?"},
    )
    assert second.status_code == 200
    assert second.json()["status"] == TurnStatus.SUCCESS

    follow_up_prompts = memory_llm.captured_prompts[prompts_after_first:]
    assert follow_up_prompts, "expected draft/polish LLM calls on the follow-up turn"

    blob = _prompt_blob(follow_up_prompts).lower()
    assert "ord-12345" in blob, (
        "follow-up LLM prompts must include prior-turn order context (session history)"
    )

    stored = session_service.get(session_id)
    assert stored is not None
    assert len(stored.turns) == 2
    assert stored.turns[0].user_message == "I need a refund for order ORD-12345."
    assert stored.turns[1].user_message == "How long will that take?"
