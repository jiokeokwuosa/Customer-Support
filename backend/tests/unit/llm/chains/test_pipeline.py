"""Unit tests for pipeline triage merge helpers (T030)."""

from __future__ import annotations

from app.llm.chains.classification.sentiment_urgency import SentimentUrgencyOutput
from app.llm.chains.classification.topic_classifier import TopicClassificationOutput
from app.llm.chains.pipeline import _attach_triage_info, _merge_triage_info
from app.schemas.triage import (
    SentimentLabel,
    TopicCategory,
    TriageMetadata,
    UrgencyLevel,
)


def test_merge_triage_info_combines_parallel_outputs() -> None:
    triage = _merge_triage_info(
        {
            "sentiment_urgency": SentimentUrgencyOutput(
                sentiment=SentimentLabel.FRUSTRATED,
                urgency=UrgencyLevel.HIGH,
            ),
            "topic": TopicClassificationOutput(
                topic=TopicCategory.BILLING,
                rationale="Customer reports duplicate billing charge.",
            ),
        }
    )

    assert isinstance(triage, TriageMetadata)
    assert triage.topic == TopicCategory.BILLING
    assert triage.sentiment == SentimentLabel.FRUSTRATED
    assert triage.urgency == UrgencyLevel.HIGH
    assert "duplicate billing" in triage.rationale


def test_attach_triage_info_adds_merged_metadata_to_state() -> None:
    state = {
        "user_message": "I was charged twice on my invoice.",
        "sentiment_urgency": SentimentUrgencyOutput(
            sentiment=SentimentLabel.FRUSTRATED,
            urgency=UrgencyLevel.HIGH,
        ),
        "topic": TopicClassificationOutput(
            topic=TopicCategory.BILLING,
            rationale="Customer reports duplicate billing charge.",
        ),
    }

    result = _attach_triage_info(state)

    assert result["user_message"] == state["user_message"]
    assert "sentiment_urgency" not in result
    assert "topic" not in result
    assert isinstance(result["triage"], TriageMetadata)
    assert result["triage"].topic == TopicCategory.BILLING
