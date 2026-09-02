"""Unit tests for topic-aware draft chain (T028)."""

from __future__ import annotations

from langchain_core.language_models.fake_chat_models import FakeListChatModel

from app.llm.chains.drafts.draft import build_draft_chain
from app.schemas.triage import (
    SentimentLabel,
    TopicCategory,
    TriageMetadata,
    UrgencyLevel,
)


def _state_for(topic: TopicCategory) -> dict:
    return {
        "user_message": "Help me with my account",
        "triage": TriageMetadata(
            topic=topic,
            sentiment=SentimentLabel.NEUTRAL,
            urgency=UrgencyLevel.MEDIUM,
            rationale="Test draft",
        ),
    }


def test_draft_chain_returns_text_for_billing_topic() -> None:
    llm = FakeListChatModel(responses=["Billing draft reply."])

    chain = build_draft_chain(llm)
    result = chain.invoke(_state_for(TopicCategory.BILLING))

    assert result == "Billing draft reply."


def test_draft_chain_returns_text_for_technical_topic() -> None:
    llm = FakeListChatModel(responses=["Technical draft reply."])

    chain = build_draft_chain(llm)
    result = chain.invoke(_state_for(TopicCategory.TECHNICAL))

    assert result == "Technical draft reply."


def test_draft_chain_returns_text_for_general_topic() -> None:
    llm = FakeListChatModel(responses=["General draft reply."])

    chain = build_draft_chain(llm)
    result = chain.invoke(_state_for(TopicCategory.GENERAL))

    assert result == "General draft reply."
