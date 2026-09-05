"""Pydantic schemas for sample prompt gallery (US7)."""

from pydantic import BaseModel, Field

from app.schemas.triage import TopicCategory


class SamplePrompt(BaseModel):
    """Predefined demo message for UI chips."""

    id: str
    label: str
    message: str = Field(min_length=1, max_length=4000)
    expected_topic: TopicCategory | None = None


class SamplePromptsResponse(BaseModel):
    prompts: list[SamplePrompt]
