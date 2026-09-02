"""Prompt templates for message classification chains."""

from langchain_core.prompts import ChatPromptTemplate

SENTIMENT_URGENCY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Analyze the customer support message. "
            "Return sentiment and urgency only.",
        ),
        ("human", "{user_message}"),
    ]
)

TOPIC_CLASSIFIER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Classify the customer support message topic and explain why "
            "in one short rationale.",
        ),
        ("human", "{user_message}"),
    ]
)
