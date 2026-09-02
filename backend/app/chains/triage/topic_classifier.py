"""Topic classification and rationale for a customer message."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field

from app.schemas.triage import TopicCategory

_TOPIC_CLASSIFIER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Classify the customer support message topic and explain why "
            "in one short rationale.",
        ),
        ("human", "{user_message}"),
    ]
)


class TopicClassificationOutput(BaseModel):
    """Structured topic label and rationale from the LLM."""

    topic: TopicCategory
    rationale: str = Field(min_length=1, max_length=200)


def build_topic_classifier_chain(llm: BaseChatModel) -> Runnable:
    """Build an LCEL chain: prompt → structured LLM output."""
    structured_llm = llm.with_structured_output(TopicClassificationOutput)
    return _TOPIC_CLASSIFIER_PROMPT | structured_llm
