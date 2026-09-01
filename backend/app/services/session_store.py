"""Application services for chat sessions.

Services orchestrate repositories and enforce product rules (e.g. turn cap).
Routes/deps should call here — not repositories or ORM models directly.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import sessionmaker

from app.db.engine import create_db_engine, create_session_factory, init_db
from app.repositories.session_repository import SessionRepository
from app.schemas.session import Session, Turn

# Matches Session.turns max_length / product memory cap (spec VR-003).
MAX_SESSION_TURNS = 20


class SessionNotFoundError(KeyError):
    """Raised when a session_id is unknown."""

    def __init__(self, session_id: UUID) -> None:
        self.session_id = session_id
        super().__init__(f"Session not found: {session_id}")


class SqliteSessionStore:
    """Session service backed by SQLite + SQLAlchemy ORM."""

    def __init__(self, database_path: str | Path) -> None:
        self._engine: Engine = create_db_engine(database_path)
        init_db(self._engine)
        self._session_factory: sessionmaker[OrmSession] = create_session_factory(
            self._engine
        )

    @contextmanager
    def _repository(self) -> Iterator[SessionRepository]:
        # Short-lived ORM session per operation — safe under concurrent requests.
        db = self._session_factory()
        try:
            yield SessionRepository(db)
        finally:
            db.close()

    def close(self) -> None:
        self._engine.dispose()

    def create(self) -> Session:
        """Start a new empty chat."""
        with self._repository() as repo:
            return repo.create_session()

    def get(self, session_id: UUID) -> Session | None:
        """Load one session and all of its turns in order."""
        with self._repository() as repo:
            return repo.get_session(session_id)

    def append_turn(self, session_id: UUID, turn: Turn) -> Session:
        """Add one completed exchange; keep only the newest 20 turns."""
        with self._repository() as repo:
            session = repo.get_session(session_id)
            if session is None:
                raise SessionNotFoundError(session_id)

            position = len(session.turns)
            repo.insert_turn(
                session_id,
                turn,
                position=position,
                updated_at=datetime.now(UTC),
            )
            # Trim after write so Session.turns max_length=20 never fails on reload.
            repo.trim_turns(session_id, keep=MAX_SESSION_TURNS)

            loaded = repo.get_session(session_id)
            if loaded is None:  # pragma: no cover - defensive after successful write
                raise SessionNotFoundError(session_id)
            return loaded

    def delete(self, session_id: UUID) -> None:
        """Drop a session (and its turns). Safe to call twice."""
        with self._repository() as repo:
            repo.delete_session(session_id)
