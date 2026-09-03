"""Convert persisted session turns into LangChain chat history."""

from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.schemas.session import Turn


def turns_to_history(turns: list[Turn]) -> list[BaseMessage]:
    """Flatten turns into alternating human / assistant messages for prompts."""
    history: list[BaseMessage] = []
    for turn in turns:
        history.append(HumanMessage(content=turn.user_message))
        history.append(AIMessage(content=turn.assistant_message))
    return history
