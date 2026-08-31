"""Application services for chat sessions.

Services orchestrate repositories and enforce product rules (e.g. turn cap).
Routes/deps should call here — not repositories or raw `app.db` helpers.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, runtime_checkable
from uuid import UUID

from app.db.sqlite import connect_sqlite
from app.models.session import Session, Turn
from app.repositories.session_repository import SessionRepository

# Matches Session.turns max_length / product memory cap (spec VR-003).
MAX_SESSION_TURNS = 20


class SessionNotFoundError(KeyError):
    """Raised when a session_id is unknown."""

    def __init__(self, session_id: UUID) -> None:
        self.session_id = session_id
        super().__init__(f"Session not found: {session_id}")


@runtime_checkable
class SessionStore(Protocol):
    """Typed checklist of session operations (create/get/append/delete)."""

    def create(self) -> Session:
        """Create an empty session and return it."""
        ...

    def get(self, session_id: UUID) -> Session | None:
        """Return the session if present; otherwise None."""
        ...

    def append_turn(self, session_id: UUID, turn: Turn) -> Session:
        """Append a turn and bump updated_at. Raises SessionNotFoundError."""
        ...

    def delete(self, session_id: UUID) -> None:
        """Remove a session if it exists (idempotent)."""
        ...


class SqliteSessionStore:
    """Session service backed by SQLite via SessionRepository."""

    def __init__(self, database_path: str | Path) -> None:
        self._connection = connect_sqlite(database_path)
        self._repo = SessionRepository(self._connection)

    def close(self) -> None:
        self._connection.close()

    def create(self) -> Session:
        """Start a new empty chat."""
        return self._repo.create_session()

    def get(self, session_id: UUID) -> Session | None:
        """Load one session and all of its turns in order."""
        return self._repo.get_session(session_id)

    def append_turn(self, session_id: UUID, turn: Turn) -> Session:
        """Add one completed exchange; keep only the newest 20 turns."""
        session = self._repo.get_session(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)

        position = len(session.turns)
        self._repo.insert_turn(
            session_id,
            turn,
            position=position,
            updated_at=datetime.now(UTC),
        )
        # Trim after write so Session.turns max_length=20 never fails on reload.
        self._repo.trim_turns(session_id, keep=MAX_SESSION_TURNS)

        loaded = self._repo.get_session(session_id)
        if loaded is None:  # pragma: no cover - defensive after successful write
            raise SessionNotFoundError(session_id)
        return loaded

    def delete(self, session_id: UUID) -> None:
        """Drop a session (and its turns). Safe to call twice."""
        self._repo.delete_session(session_id)
