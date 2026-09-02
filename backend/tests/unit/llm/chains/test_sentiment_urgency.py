"""Unit tests for the sentiment & urgency triage chain (T026).

These tests define the expected chain contract before implementation (T033).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnableLambda
from pydantic import ValidationError

from app.llm.chains.classification.sentiment_urgency import (
    SentimentUrgencyOutput,
    build_sentiment_urgency_chain,
)
from app.schemas.triage import SentimentLabel, UrgencyLevel


def _fake_structured_llm(output: SentimentUrgencyOutput) -> MagicMock:
    """Fake LLM that returns a fixed structured output (no live OpenAI)."""
    llm = MagicMock(spec=BaseChatModel)
    llm.with_structured_output.return_value = RunnableLambda(lambda _: output)
    return llm


def test_build_sentiment_urgency_chain_returns_structured_output() -> None:
    llm = _fake_structured_llm(
        SentimentUrgencyOutput(
            sentiment=SentimentLabel.FRUSTRATED,
            urgency=UrgencyLevel.HIGH,
        )
    )

    chain = build_sentiment_urgency_chain(llm)
    result = chain.invoke({"user_message": "I was charged twice and need a refund!"})

    assert isinstance(result, SentimentUrgencyOutput)
    assert result.sentiment == SentimentLabel.FRUSTRATED
    assert result.urgency == UrgencyLevel.HIGH


def test_sentiment_urgency_chain_accepts_calm_general_message() -> None:
    llm = _fake_structured_llm(
        SentimentUrgencyOutput(
            sentiment=SentimentLabel.NEUTRAL,
            urgency=UrgencyLevel.LOW,
        )
    )

    chain = build_sentiment_urgency_chain(llm)
    result = chain.invoke(
        {"user_message": "What are your support hours?"}
    )

    assert result.sentiment == SentimentLabel.NEUTRAL
    assert result.urgency == UrgencyLevel.LOW


def test_sentiment_urgency_output_rejects_invalid_labels() -> None:
    with pytest.raises(ValidationError):
        SentimentUrgencyOutput(
            sentiment="angry",  # type: ignore[arg-type]
            urgency=UrgencyLevel.MEDIUM,
        )


def test_build_sentiment_urgency_chain_uses_structured_output() -> None:
    llm = _fake_structured_llm(
        SentimentUrgencyOutput(
            sentiment=SentimentLabel.POSITIVE,
            urgency=UrgencyLevel.LOW,
        )
    )
    chain = build_sentiment_urgency_chain(llm)
    chain.invoke({"user_message": "Thanks for the great help!"})

    llm.with_structured_output.assert_called_once_with(SentimentUrgencyOutput)
