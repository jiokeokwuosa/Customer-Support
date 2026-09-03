"""Application service for chat session lifecycle and turn memory."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from app.exceptions import SessionNotFoundError
from app.repositories.session_repository import SessionRepository
from app.schemas.session import Session, Turn

# Matches Session.turns max_length / product memory cap (spec VR-003).
MAX_SESSION_TURNS = 20


class SessionService:
    """Session orchestration backed by a request-scoped repository."""

    def __init__(self, repository: SessionRepository) -> None:
        self._repository = repository

    def create(self) -> Session:
        """Start a new empty chat."""
        return self._repository.create_session()

    def get(self, session_id: UUID) -> Session | None:
        """Load one session and all of its turns in order."""
        return self._repository.get_session(session_id)

    def require(self, session_id: UUID) -> Session:
        """Return a session or raise SessionNotFoundError."""
        session = self.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)
        return session

    def append_turn(
        self,
        session_id: UUID,
        turn: Turn,
        *,
        session: Session | None = None,
    ) -> Session:
        """Add one completed exchange; keep only the newest 20 turns."""
        if session is not None:
            if session.id != session_id:
                msg = "session id mismatch"
                raise ValueError(msg)
            position = len(session.turns)
        else:
            loaded = self._repository.get_session(session_id)
            if loaded is None:
                raise SessionNotFoundError(session_id)
            position = len(loaded.turns)

        self._repository.insert_turn(
            session_id,
            turn,
            position=position,
            updated_at=datetime.now(UTC),
        )
        self._repository.trim_turns(session_id, keep=MAX_SESSION_TURNS)
        self._repository.commit()

        loaded = self._repository.get_session(session_id)
        if loaded is None:  # pragma: no cover - defensive after successful write
            raise SessionNotFoundError(session_id)
        return loaded

    def delete(self, session_id: UUID) -> None:
        """Drop a session (and its turns). Safe to call twice."""
        self._repository.delete_session(session_id)
