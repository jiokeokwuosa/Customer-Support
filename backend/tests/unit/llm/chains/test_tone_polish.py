"""Unit tests for tone polish chain (T029)."""

from __future__ import annotations

from langchain_core.language_models.fake_chat_models import FakeListChatModel

from app.llm.chains.refinement.tone_polish import build_tone_polish_chain
from app.schemas.triage import (
    SentimentLabel,
    TopicCategory,
    TriageMetadata,
    UrgencyLevel,
)


def _state(
    *,
    topic: TopicCategory = TopicCategory.BILLING,
    sentiment: SentimentLabel = SentimentLabel.FRUSTRATED,
    urgency: UrgencyLevel = UrgencyLevel.HIGH,
) -> dict:
    return {
        "user_message": "I need a refund",
        "topic_draft": "We can review your billing concern.",
        "triage": TriageMetadata(
            topic=topic,
            sentiment=sentiment,
            urgency=urgency,
            rationale="Billing dispute",
        ),
    }


def test_tone_polish_returns_polished_message() -> None:
    llm = FakeListChatModel(responses=["Polished support reply."])

    chain = build_tone_polish_chain(llm)
    result = chain.invoke(_state())

    assert result == "Polished support reply."


def test_tone_polish_chain_handles_general_topic() -> None:
    llm = FakeListChatModel(responses=["Final polished message."])

    chain = build_tone_polish_chain(llm)
    result = chain.invoke(
        _state(
            topic=TopicCategory.GENERAL,
            sentiment=SentimentLabel.NEUTRAL,
            urgency=UrgencyLevel.LOW,
        )
    )

    assert result == "Final polished message."
