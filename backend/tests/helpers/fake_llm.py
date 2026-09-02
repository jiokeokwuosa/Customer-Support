"""Shared fake LLM helpers for pipeline and service tests."""

from __future__ import annotations

from unittest.mock import MagicMock

from langchain_community.chat_models.fake import FakeListChatModel
from langchain_core.runnables import RunnableLambda

from app.llm.chains.classification.sentiment_urgency import SentimentUrgencyOutput
from app.llm.chains.classification.topic_classifier import TopicClassificationOutput
from app.schemas.triage import SentimentLabel, TopicCategory, UrgencyLevel


def structured_output_factory(model: type) -> RunnableLambda:
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


def pipeline_fake_llm(
    *,
    draft_response: str = "Billing draft reply.",
    polish_response: str = "Polished billing reply.",
) -> FakeListChatModel:
    """Fake chat model for full triage pipeline tests (structured + text steps)."""
    llm = FakeListChatModel(responses=[draft_response, polish_response])
    object.__setattr__(
        llm,
        "with_structured_output",
        MagicMock(side_effect=structured_output_factory),
    )
    return llm


def failing_structured_output_llm(
    *,
    draft_response: str = "unused",
    polish_response: str = "unused",
) -> FakeListChatModel:
    """Fake LLM whose structured-output chains fail on invoke."""
    llm = FakeListChatModel(responses=[draft_response, polish_response])
    object.__setattr__(
        llm,
        "with_structured_output",
        MagicMock(
            return_value=RunnableLambda(
                lambda _: (_ for _ in ()).throw(RuntimeError("LLM unavailable"))
            )
        ),
    )
    return llm
