import pytest
from pydantic import ValidationError

from app.schemas.triage import (
    SentimentLabel,
    TopicCategory,
    TriageMetadata,
    UrgencyLevel,
)


def test_triage_metadata_accepts_valid_payload() -> None:
    triage = TriageMetadata(
        topic=TopicCategory.BILLING,
        sentiment=SentimentLabel.FRUSTRATED,
        urgency=UrgencyLevel.HIGH,
        rationale="Customer mentions duplicate charge and wants refund.",
    )

    assert triage.topic == TopicCategory.BILLING
    assert triage.urgency == UrgencyLevel.HIGH


def test_triage_metadata_rejects_empty_rationale() -> None:
    with pytest.raises(ValidationError):
        TriageMetadata(
            topic=TopicCategory.GENERAL,
            sentiment=SentimentLabel.NEUTRAL,
            urgency=UrgencyLevel.MEDIUM,
            rationale="",
        )


def test_triage_metadata_rejects_rationale_over_max_length() -> None:
    with pytest.raises(ValidationError):
        TriageMetadata(
            topic=TopicCategory.GENERAL,
            sentiment=SentimentLabel.NEUTRAL,
            urgency=UrgencyLevel.MEDIUM,
            rationale="x" * 201,
        )


def test_low_confidence_fallback_uses_documented_defaults() -> None:
    triage = TriageMetadata.low_confidence_fallback("Parser failed")

    assert triage.topic == TopicCategory.GENERAL
    assert triage.sentiment == SentimentLabel.NEUTRAL
    assert triage.urgency == UrgencyLevel.MEDIUM
    assert triage.rationale == "Parser failed"
