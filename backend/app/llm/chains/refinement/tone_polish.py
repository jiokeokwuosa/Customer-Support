"""Tone polish refinement chain."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable, RunnableLambda

from app.llm.prompts.refinement import TONE_POLISH_PROMPT
from app.schemas.triage import TriageMetadata


def _polish_input(state: dict[str, Any]) -> dict[str, str]:
    triage = state["triage"]
    if not isinstance(triage, TriageMetadata):
        msg = "triage must be TriageMetadata"
        raise TypeError(msg)
    return {
        "user_message": state["user_message"],
        "topic_draft": state["topic_draft"],
        "sentiment": triage.sentiment.value,
        "urgency": triage.urgency.value,
    }


def build_tone_polish_chain(llm: BaseChatModel) -> Runnable:
    """Build an LCEL chain: map state → prompt → LLM → text."""
    return (
        RunnableLambda(_polish_input)
        | TONE_POLISH_PROMPT
        | llm
        | StrOutputParser()
    )
