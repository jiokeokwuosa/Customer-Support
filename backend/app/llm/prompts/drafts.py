"""Prompt templates for draft response chains."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

DRAFT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Draft a helpful support reply. Topic: {topic}. "
            "Sentiment: {sentiment}. Urgency: {urgency}.\n"
            "When knowledge context is provided, ground the reply in it and "
            "do not invent policy details. If knowledge context is empty and "
            "the customer asks about policy, say no matching policy source "
            "was found.\n"
            "Knowledge context:\n{knowledge_context}",
        ),
        MessagesPlaceholder("history", optional=True),
        ("human", "{user_message}"),
    ]
)
