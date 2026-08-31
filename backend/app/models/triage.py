"""Triage enums and metadata models."""

from enum import StrEnum

from pydantic import BaseModel, Field


class TopicCategory(StrEnum):
    TECHNICAL = "technical"
    BILLING = "billing"
    GENERAL = "general"


class SentimentLabel(StrEnum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    FRUSTRATED = "frustrated"


class UrgencyLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TriageMetadata(BaseModel):
    """Structured output from parallel sentiment/topic/urgency analysis."""

    topic: TopicCategory
    sentiment: SentimentLabel
    urgency: UrgencyLevel
    rationale: str = Field(min_length=1, max_length=200)

    @classmethod
    def low_confidence_fallback(cls, rationale: str) -> "TriageMetadata":
        """Default triage when chain output cannot be parsed reliably."""
        return cls(
            topic=TopicCategory.GENERAL,
            sentiment=SentimentLabel.NEUTRAL,
            urgency=UrgencyLevel.MEDIUM,
            rationale=rationale[:200],
        )
