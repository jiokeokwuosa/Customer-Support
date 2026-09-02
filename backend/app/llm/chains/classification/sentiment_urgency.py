"""Parallel sentiment and urgency analysis for a customer message."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import Runnable
from pydantic import BaseModel

from app.llm.prompts.classification import SENTIMENT_URGENCY_PROMPT
from app.schemas.triage import SentimentLabel, UrgencyLevel


class SentimentUrgencyOutput(BaseModel):
    """Structured sentiment and urgency labels from the LLM."""

    sentiment: SentimentLabel
    urgency: UrgencyLevel


def build_sentiment_urgency_chain(llm: BaseChatModel) -> Runnable:
    """Build an LCEL chain: prompt → structured LLM output."""
    structured_llm = llm.with_structured_output(SentimentUrgencyOutput)
    return SENTIMENT_URGENCY_PROMPT | structured_llm
