"""Unit tests for the topic classifier triage chain (T027)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnableLambda
from pydantic import ValidationError

from app.chains.triage.topic_classifier import (
    TopicClassificationOutput,
    build_topic_classifier_chain,
)
from app.schemas.triage import TopicCategory


def _fake_structured_llm(output: TopicClassificationOutput) -> MagicMock:
    llm = MagicMock(spec=BaseChatModel)
    llm.with_structured_output.return_value = RunnableLambda(lambda _: output)
    return llm


def test_topic_classifier_returns_billing_topic() -> None:
    llm = _fake_structured_llm(
        TopicClassificationOutput(
            topic=TopicCategory.BILLING,
            rationale="Customer reports a duplicate charge and requests a refund.",
        )
    )

    chain = build_topic_classifier_chain(llm)
    result = chain.invoke(
        {"user_message": "I was charged twice on my last invoice."}
    )

    assert result.topic == TopicCategory.BILLING
    assert "duplicate charge" in result.rationale


def test_topic_classifier_returns_technical_topic() -> None:
    llm = _fake_structured_llm(
        TopicClassificationOutput(
            topic=TopicCategory.TECHNICAL,
            rationale="Customer cannot log in after a password reset.",
        )
    )

    chain = build_topic_classifier_chain(llm)
    result = chain.invoke(
        {"user_message": "Password reset link is not working."}
    )

    assert result.topic == TopicCategory.TECHNICAL


def test_topic_classifier_returns_general_topic() -> None:
    llm = _fake_structured_llm(
        TopicClassificationOutput(
            topic=TopicCategory.GENERAL,
            rationale="Customer asks about standard support hours.",
        )
    )

    chain = build_topic_classifier_chain(llm)
    result = chain.invoke({"user_message": "What are your support hours?"})

    assert result.topic == TopicCategory.GENERAL


def test_topic_classification_output_rejects_empty_rationale() -> None:
    with pytest.raises(ValidationError):
        TopicClassificationOutput(
            topic=TopicCategory.GENERAL,
            rationale="",
        )


def test_build_topic_classifier_chain_uses_structured_output() -> None:
    llm = _fake_structured_llm(
        TopicClassificationOutput(
            topic=TopicCategory.BILLING,
            rationale="Billing dispute",
        )
    )
    chain = build_topic_classifier_chain(llm)
    chain.invoke({"user_message": "Refund my payment"})

    llm.with_structured_output.assert_called_once_with(TopicClassificationOutput)
