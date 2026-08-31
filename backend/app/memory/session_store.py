"""Application-facing session memory API.

Callers (FastAPI deps, services) use `SessionStore` / `SqliteSessionStore`.
SQL details live under `app.db` so storage stays a separate layer.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, runtime_checkable
from uuid import UUID

from app.db.session_repository import SessionRepository
from app.db.sqlite import connect_sqlite
from app.models.session import Session, Turn


class SessionNotFoundError(KeyError):
    """Raised when a session_id is unknown to the store."""

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
    """SessionStore adapter over SQLite (`app.db`).

    Thin wrapper: orchestration and domain errors here; SQL in the repository.
    """

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
        """Add one completed exchange to an existing session."""
        session = self._repo.get_session(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)

        # Next slot in this chat (0-based). Trimming to max 20 turns is T057.
        position = len(session.turns)
        self._repo.insert_turn(
            session_id,
            turn,
            position=position,
            updated_at=datetime.now(UTC),
        )

        loaded = self._repo.get_session(session_id)
        if loaded is None:  # pragma: no cover - defensive after successful write
            raise SessionNotFoundError(session_id)
        return loaded

    def delete(self, session_id: UUID) -> None:
        """Drop a session (and its turns). Safe to call twice."""
        self._repo.delete_session(session_id)
