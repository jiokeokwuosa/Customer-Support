"""Labels the triage pipeline puts on each customer message.

These enums match the OpenAPI contract so backend JSON and frontend types
use the same string values (e.g. topic="billing").
"""

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
    """Four fields produced by parallel sentiment/topic/urgency analysis."""

    topic: TopicCategory
    sentiment: SentimentLabel
    urgency: UrgencyLevel
    rationale: str = Field(min_length=1, max_length=200)

    @classmethod
    def low_confidence_fallback(cls, rationale: str) -> "TriageMetadata":
        """Safe defaults when the LLM output cannot be parsed cleanly.

        Spec edge case: prefer a cautious general/neutral/medium label over
        crashing the turn.
        """
        return cls(
            topic=TopicCategory.GENERAL,
            sentiment=SentimentLabel.NEUTRAL,
            urgency=UrgencyLevel.MEDIUM,
            rationale=rationale[:200],
        )
