"""Full triage pipeline: parallel triage → optional RAG → lookup → draft → polish."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import Runnable, RunnableLambda, RunnableParallel

from app.llm.chains.classification.sentiment_urgency import (
    build_sentiment_urgency_chain,
)
from app.llm.chains.classification.topic_classifier import build_topic_classifier_chain
from app.llm.chains.drafts.draft import build_draft_chain
from app.llm.chains.refinement.tone_polish import build_tone_polish_chain
from app.retrieval.retriever import (
    KnowledgeIndex,
    documents_to_citations,
    format_knowledge_context,
    needs_retrieval,
)
from app.schemas.message import LookupResult, LookupType
from app.schemas.triage import TriageMetadata
from app.tools.id_detector import detect_ids
from app.tools.lookup import lookup_account_record, lookup_order_record


def _merge_triage_info(parallel_output: dict[str, Any]) -> TriageMetadata:
    sentiment_urgency = parallel_output["sentiment_urgency"]
    topic = parallel_output["topic"]
    return TriageMetadata(
        topic=topic.topic,
        sentiment=sentiment_urgency.sentiment,
        urgency=sentiment_urgency.urgency,
        rationale=topic.rationale,
    )


def _attach_triage_info(state: dict[str, Any]) -> dict[str, Any]:
    triage = _merge_triage_info(
        {
            "sentiment_urgency": state["sentiment_urgency"],
            "topic": state["topic"],
        }
    )
    return {
        "user_message": state["user_message"],
        "history": state.get("history", []),
        "triage": triage,
    }


def _format_lookup_context(result: LookupResult) -> str:
    lines = [result.summary]
    if result.details:
        details = ", ".join(f"{key}={value}" for key, value in result.details.items())
        lines.append(f"Details: {details}")
    return "\n".join(lines)


def attach_lookup(state: dict[str, Any]) -> dict[str, Any]:
    """Detect IDs and run the first matching mock CRM lookup."""
    detected = detect_ids(state["user_message"])
    if not detected:
        return {**state, "lookup": None, "lookup_context": ""}

    first = detected[0]
    if first.lookup_type is LookupType.ORDER:
        result = lookup_order_record(first.identifier)
    else:
        result = lookup_account_record(first.identifier)

    return {
        **state,
        "lookup": result,
        "lookup_context": _format_lookup_context(result),
    }


def build_triage_pipeline(
    llm: BaseChatModel,
    *,
    knowledge_index: KnowledgeIndex | None = None,
) -> Runnable:
    """Compose triage → optional RAG → lookup → draft → polish."""
    triage_parallel = RunnableParallel(
        sentiment_urgency=build_sentiment_urgency_chain(llm),
        topic=build_topic_classifier_chain(llm),
    )
    draft = build_draft_chain(llm)
    polish = build_tone_polish_chain(llm)

    def run_triage(state: dict[str, Any]) -> dict[str, Any]:
        return {**state, **triage_parallel.invoke(state)}

    def attach_retrieval(state: dict[str, Any]) -> dict[str, Any]:
        if knowledge_index is None or not needs_retrieval(state["user_message"]):
            return {
                **state,
                "citations": [],
                "knowledge_context": "",
            }
        docs = knowledge_index.retrieve(state["user_message"])
        return {
            **state,
            "citations": documents_to_citations(docs),
            "knowledge_context": format_knowledge_context(docs),
        }

    def attach_draft(state: dict[str, Any]) -> dict[str, Any]:
        return {**state, "topic_draft": draft.invoke(state)}

    def attach_polish(state: dict[str, Any]) -> dict[str, Any]:
        return {**state, "final_response": polish.invoke(state)}

    return (
        RunnableLambda(run_triage)
        | RunnableLambda(_attach_triage_info)
        | RunnableLambda(attach_retrieval)
        | RunnableLambda(attach_lookup)
        | RunnableLambda(attach_draft)
        | RunnableLambda(attach_polish)
    )
