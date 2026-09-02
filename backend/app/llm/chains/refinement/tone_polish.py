"""Tone polish refinement chain."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable, RunnableLambda

from app.llm.chains.state import require_triage
from app.llm.prompts.refinement import TONE_POLISH_PROMPT


def _polish_input(state: dict[str, Any]) -> dict[str, str]:
    triage = require_triage(state)
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
