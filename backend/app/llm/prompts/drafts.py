"""Prompt templates for draft response chains."""

from langchain_core.prompts import ChatPromptTemplate

DRAFT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Draft a helpful support reply. Topic: {topic}. "
            "Sentiment: {sentiment}. Urgency: {urgency}.",
        ),
        ("human", "{user_message}"),
    ]
)
