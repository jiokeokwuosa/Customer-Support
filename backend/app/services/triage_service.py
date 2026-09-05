"""Orchestrate triage pipeline execution and session turn persistence."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import Runnable

from app.exceptions import SessionNotFoundError
from app.llm.chains.drafts.draft import build_draft_chain
from app.llm.chains.pipeline import build_enrichment_pipeline, build_triage_pipeline
from app.llm.chains.refinement.tone_polish import build_tone_polish_chain
from app.llm.utils.history import turns_to_history
from app.llm.utils.state import require_triage
from app.logging import bind_log_context, clear_log_context, get_logger, log_step
from app.retrieval.retriever import KnowledgeIndex
from app.schemas.message import (
    Citation,
    ErrorCode,
    ErrorResponse,
    LookupResult,
    TurnResponse,
    TurnStatus,
)
from app.schemas.session import Session, Turn
from app.schemas.triage import TriageMetadata
from app.services.session_service import SessionService

_ERROR_MESSAGE = "Sorry, we could not process your message. Please try again."

StreamEvent = tuple[str, Any]


class TriageService:
    """Run the LangChain triage pipeline and persist completed turns."""

    def __init__(
        self,
        session_service: SessionService,
        llm: BaseChatModel,
        knowledge_index: KnowledgeIndex | None = None,
    ) -> None:
        self._session_service = session_service
        self._pipeline = build_triage_pipeline(llm, knowledge_index=knowledge_index)
        self._enrichment: Runnable = build_enrichment_pipeline(
            llm,
            knowledge_index=knowledge_index,
        )
        self._draft = build_draft_chain(llm)
        self._polish = build_tone_polish_chain(llm)
        self._logger = get_logger(__name__)

    def process_message(self, session_id: UUID, message: str) -> TurnResponse:
        """Analyze a customer message and return a polished assistant reply."""
        session = self._session_service.require(session_id)

        turn_id = uuid4()
        bind_log_context(session_id=str(session_id), turn_id=str(turn_id))
        try:
            try:
                with log_step(self._logger, step="triage_pipeline"):
                    result = self._pipeline.invoke(
                        {
                            "user_message": message,
                            "history": turns_to_history(session.turns),
                        }
                    )

                triage = require_triage(result)
                final_response = result["final_response"]
                citations = _coerce_citations(result.get("citations", []))
                lookup = _coerce_lookup(result.get("lookup"))
            except SessionNotFoundError:
                raise
            except (KeyError, TypeError, ValueError):
                raise
            except Exception:
                self._logger.exception("triage_pipeline_failed")
                return TurnResponse(
                    turn_id=turn_id,
                    session_id=session_id,
                    status=TurnStatus.ERROR,
                    message=_ERROR_MESSAGE,
                    triage=TriageMetadata.low_confidence_fallback(
                        "Unable to analyze message.",
                    ),
                    error_code=ErrorCode.LLM_ERROR,
                    next_actions=["retry"],
                )

            turn = Turn(
                id=turn_id,
                user_message=message,
                assistant_message=final_response,
                triage=triage,
                citations=citations,
                lookup=lookup,
                created_at=datetime.now(UTC),
            )
            self._session_service.append_turn(session_id, turn, session=session)

            return TurnResponse(
                turn_id=turn_id,
                session_id=session_id,
                status=TurnStatus.SUCCESS,
                message=final_response,
                triage=triage,
                citations=citations,
                lookup=lookup,
            )
        finally:
            clear_log_context()

    def stream_message(
        self,
        session_id: UUID,
        message: str,
    ) -> Iterator[StreamEvent]:
        """Yield SSE payload tuples after validating the session exists.

        Session lookup runs before the generator starts so 404 can be returned
        before the SSE response begins.
        """
        session = self._session_service.require(session_id)
        turn_id = uuid4()
        history = turns_to_history(session.turns)

        def events() -> Iterator[StreamEvent]:
            bind_log_context(session_id=str(session_id), turn_id=str(turn_id))
            try:
                try:
                    with log_step(self._logger, step="triage_pipeline_stream"):
                        yield from self._iter_stream_events(
                            session_id=session_id,
                            turn_id=turn_id,
                            message=message,
                            history=history,
                            session=session,
                        )
                except SessionNotFoundError:
                    raise
                except Exception:
                    self._logger.exception("triage_pipeline_stream_failed")
                    yield (
                        "error",
                        ErrorResponse(
                            message=_ERROR_MESSAGE,
                            error_code=ErrorCode.LLM_ERROR,
                            next_actions=["retry"],
                        ),
                    )
            finally:
                clear_log_context()

        return events()

    def _iter_stream_events(
        self,
        *,
        session_id: UUID,
        turn_id: UUID,
        message: str,
        history: list[Any],
        session: Session,
    ) -> Iterator[StreamEvent]:
        state = self._enrichment.invoke(
            {
                "user_message": message,
                "history": history,
            }
        )
        triage = require_triage(state)
        citations = _coerce_citations(state.get("citations", []))
        lookup = _coerce_lookup(state.get("lookup"))

        yield ("triage", triage)
        if citations:
            yield ("citations", citations)
        if lookup is not None:
            yield ("lookup", lookup)

        state = {**state, "topic_draft": self._draft.invoke(state)}
        token_parts: list[str] = []
        for part in self._stream_polish_tokens(state):
            token_parts.append(part)
            yield ("token", {"text": part})

        final_response = "".join(token_parts)
        turn = Turn(
            id=turn_id,
            user_message=message,
            assistant_message=final_response,
            triage=triage,
            citations=citations,
            lookup=lookup,
            created_at=datetime.now(UTC),
        )
        self._session_service.append_turn(session_id, turn, session=session)

        yield (
            "done",
            TurnResponse(
                turn_id=turn_id,
                session_id=session_id,
                status=TurnStatus.SUCCESS,
                message=final_response,
                triage=triage,
                citations=citations,
                lookup=lookup,
            ),
        )

    def _stream_polish_tokens(self, state: dict[str, Any]) -> Iterator[str]:
        """Yield polish text chunks from LangChain stream_events as they arrive."""
        emitted = False
        for text in _iter_stream_event_texts(self._polish, state):
            emitted = True
            yield text
        if not emitted:
            final = self._polish.invoke(state)
            if final:
                yield final


def _iter_stream_event_texts(chain: Runnable, state: dict[str, Any]) -> Iterator[str]:
    """Yield on_chat_model_stream texts from `astream_events` as they arrive.

    LangChain exposes v2 events only via the async API, so a worker thread bridges
    chunks into this sync iterator for FastAPI StreamingResponse.
    """
    import asyncio
    import queue
    import threading

    done = object()
    chunks: queue.Queue[str | BaseException | object] = queue.Queue()

    def _runner() -> None:
        async def _consume() -> None:
            async for event in chain.astream_events(state, version="v2"):
                if event.get("event") != "on_chat_model_stream":
                    continue
                text = _chunk_text(event.get("data", {}).get("chunk"))
                if text:
                    chunks.put(text)

        try:
            asyncio.run(_consume())
            chunks.put(done)
        except BaseException as exc:  # noqa: BLE001 — re-raise on consumer side
            chunks.put(exc)

    worker = threading.Thread(target=_runner, daemon=True)
    worker.start()
    while True:
        item = chunks.get()
        if item is done:
            break
        if isinstance(item, BaseException):
            worker.join(timeout=60)
            raise item
        yield item  # type: ignore[misc]
    worker.join(timeout=60)


def _chunk_text(chunk: object) -> str:
    content = getattr(chunk, "content", chunk)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "".join(parts)
    return ""


def _coerce_citations(raw: object) -> list[Citation]:
    if not isinstance(raw, list):
        return []
    citations: list[Citation] = []
    for item in raw:
        if isinstance(item, Citation):
            citations.append(item)
    return citations


def _coerce_lookup(raw: object) -> LookupResult | None:
    if isinstance(raw, LookupResult):
        return raw
    return None
