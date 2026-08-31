"""Session memory: swappable store protocol and in-memory implementation.

API and services depend on `SessionStore`, not a concrete backend, so tests
and a later Redis/DB store can swap in without changing callers.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol, runtime_checkable
from uuid import UUID, uuid4

from app.models.session import Session, Turn


class SessionNotFoundError(KeyError):
    """Raised when a session_id is unknown to the store."""

    def __init__(self, session_id: UUID) -> None:
        self.session_id = session_id
        super().__init__(f"Session not found: {session_id}")


@runtime_checkable
class SessionStore(Protocol):
    """Persistence boundary for conversation sessions."""

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


class InMemorySessionStore:
    """Process-local session store for v1 demos and tests.

    Not shared across workers; replace via SessionStore for production.
    """

    def __init__(self) -> None:
        self._sessions: dict[UUID, Session] = {}

    def create(self) -> Session:
        now = datetime.now(UTC)
        session = Session(id=uuid4(), created_at=now, updated_at=now, turns=[])
        self._sessions[session.id] = session
        return session

    def get(self, session_id: UUID) -> Session | None:
        return self._sessions.get(session_id)

    def append_turn(self, session_id: UUID, turn: Turn) -> Session:
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)

        # In-place append; max-turn trimming is handled later (T057).
        updated = session.model_copy(
            update={
                "turns": [*session.turns, turn],
                "updated_at": datetime.now(UTC),
            }
        )
        self._sessions[session_id] = updated
        return updated

    def delete(self, session_id: UUID) -> None:
        self._sessions.pop(session_id, None)
