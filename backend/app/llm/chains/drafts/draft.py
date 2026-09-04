"""Topic-aware draft response chain."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable, RunnableLambda

from app.llm.prompts.drafts import DRAFT_PROMPT
from app.llm.utils.state import require_triage


def _draft_input(state: dict[str, Any]) -> dict[str, Any]:
    triage = require_triage(state)
    return {
        "user_message": state["user_message"],
        "history": state.get("history", []),
        "knowledge_context": state.get("knowledge_context") or "",
        "topic": triage.topic.value,
        "sentiment": triage.sentiment.value,
        "urgency": triage.urgency.value,
    }


def build_draft_chain(llm: BaseChatModel) -> Runnable:
    """Build an LCEL chain: map state → prompt → LLM → text."""
    return RunnableLambda(_draft_input) | DRAFT_PROMPT | llm | StrOutputParser()
