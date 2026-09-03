"""Prompt templates for response refinement."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

TONE_POLISH_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Polish the draft support reply for tone. "
            "Match sentiment ({sentiment}) and urgency ({urgency}). "
            "Return only the final customer-facing message.",
        ),
        MessagesPlaceholder("history", optional=True),
        (
            "human",
            "Customer message:\n{user_message}\n\nDraft reply:\n{topic_draft}",
        ),
    ]
)
