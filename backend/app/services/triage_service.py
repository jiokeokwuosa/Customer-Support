"""Orchestrate triage pipeline execution and session turn persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from langchain_core.language_models.chat_models import BaseChatModel

from app.exceptions import SessionNotFoundError
from app.llm.chains.pipeline import build_triage_pipeline
from app.llm.utils.history import turns_to_history
from app.llm.utils.state import require_triage
from app.logging import bind_log_context, clear_log_context, get_logger, log_step
from app.retrieval.retriever import KnowledgeIndex
from app.schemas.message import (
    Citation,
    ErrorCode,
    LookupResult,
    TurnResponse,
    TurnStatus,
)
from app.schemas.session import Turn
from app.schemas.triage import TriageMetadata
from app.services.session_service import SessionService

_ERROR_MESSAGE = "Sorry, we could not process your message. Please try again."


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
