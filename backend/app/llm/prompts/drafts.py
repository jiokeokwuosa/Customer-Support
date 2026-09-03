"""Prompt templates for draft response chains."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

DRAFT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Draft a helpful support reply. Topic: {topic}. "
            "Sentiment: {sentiment}. Urgency: {urgency}.",
        ),
        MessagesPlaceholder("history", optional=True),
        ("human", "{user_message}"),
    ]
)
