"""Orchestrate triage pipeline execution and session turn persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from langchain_core.language_models.chat_models import BaseChatModel

from app.llm.chains.pipeline import build_triage_pipeline
from app.llm.chains.state import require_triage
from app.logging import bind_log_context, clear_log_context, get_logger, log_step
from app.schemas.message import ErrorCode, TurnResponse, TurnStatus
from app.schemas.session import Turn
from app.schemas.triage import TriageMetadata
from app.services.session_store import SessionNotFoundError, SqliteSessionStore

_ERROR_MESSAGE = "Sorry, we could not process your message. Please try again."


class TriageService:
    """Run the LangChain triage pipeline and persist completed turns."""

    def __init__(
        self,
        session_store: SqliteSessionStore,
        llm: BaseChatModel,
    ) -> None:
        self._session_store = session_store
        self._pipeline = build_triage_pipeline(llm)
        self._logger = get_logger(__name__)

    def process_message(self, session_id: UUID, message: str) -> TurnResponse:
        """Analyze a customer message and return a polished assistant reply."""
        # Fail fast before LLM work; append_turn re-validates on write.
        session = self._session_store.require(session_id)

        turn_id = uuid4()
        bind_log_context(session_id=str(session_id), turn_id=str(turn_id))
        try:
            with log_step(self._logger, step="triage_pipeline"):
                result = self._pipeline.invoke({"user_message": message})

            triage = require_triage(result)
            final_response = result["final_response"]
            turn = Turn(
                id=turn_id,
                user_message=message,
                assistant_message=final_response,
                triage=triage,
                created_at=datetime.now(UTC),
            )
            self._session_store.append_turn(session_id, turn, session=session)

            return TurnResponse(
                turn_id=turn_id,
                session_id=session_id,
                status=TurnStatus.SUCCESS,
                message=final_response,
                triage=triage,
            )
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
        finally:
            clear_log_context()
