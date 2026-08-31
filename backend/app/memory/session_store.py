"""Save and load chat sessions in SQLite.

Think of this module as the app's notebook for conversations:
- A *session* is one chat thread (one customer conversation).
- A *turn* is one back-and-forth (user message + assistant reply + triage).

`SessionStore` lists the operations callers need. `SqliteSessionStore` is the
real implementation that writes to a `.db` file (or `:memory:` in tests).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, runtime_checkable
from uuid import UUID, uuid4

from app.models.message import Citation, LookupResult
from app.models.session import Session, Turn
from app.models.triage import TriageMetadata

# Relational core for sessions/turns. Nested triage/citations/lookup stay as
# JSON text so we do not need extra tables for every nested Pydantic field.
_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS turns (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_message TEXT NOT NULL,
    assistant_message TEXT NOT NULL,
    triage_json TEXT NOT NULL,
    citations_json TEXT NOT NULL,
    lookup_json TEXT,
    created_at TEXT NOT NULL,
    -- Stable order within a session (0, 1, 2, ...). Used instead of relying
    -- only on timestamps, which can collide under fast successive writes.
    position INTEGER NOT NULL,
    -- Deleting a session automatically removes its turns.
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_turns_session_position
    ON turns(session_id, position);
"""


class SessionNotFoundError(KeyError):
    """Raised when a session_id is unknown to the store."""

    def __init__(self, session_id: UUID) -> None:
        self.session_id = session_id
        super().__init__(f"Session not found: {session_id}")


@runtime_checkable
class SessionStore(Protocol):
    """Typed checklist of session operations (create/get/append/delete).

    Callers can depend on these method names without importing SQLite details.
    """

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


def _to_iso(value: datetime) -> str:
    # SQLite has no native timezone-aware datetime type; store UTC ISO strings.
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


def _from_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


class SqliteSessionStore:
    """Writes sessions/turns to a SQLite database file.

    Pass a filesystem path for durable storage across restarts, or `:memory:`
    for ephemeral test databases.
    """

    def __init__(self, database_path: str | Path) -> None:
        self._database_path = str(database_path)
        if self._database_path != ":memory:":
            Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)

        # One long-lived connection per store instance.
        # - :memory: DBs are wiped if you reconnect, so we must keep this open.
        # - check_same_thread=False lets FastAPI workers share the connection;
        #   SQLite still serializes writes internally.
        self._connection = sqlite3.connect(
            self._database_path,
            check_same_thread=False,
        )
        # Rows behave like dicts: row["id"] instead of row[0].
        self._connection.row_factory = sqlite3.Row
        # SQLite does not enforce foreign keys unless this pragma is on.
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.executescript(_SCHEMA)
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()

    def create(self) -> Session:
        """Start a new empty chat and persist its metadata row."""
        now = datetime.now(UTC)
        session = Session(id=uuid4(), created_at=now, updated_at=now, turns=[])
        self._connection.execute(
            "INSERT INTO sessions (id, created_at, updated_at) VALUES (?, ?, ?)",
            (str(session.id), _to_iso(session.created_at), _to_iso(session.updated_at)),
        )
        self._connection.commit()
        return session

    def get(self, session_id: UUID) -> Session | None:
        """Load one session and all of its turns in order."""
        row = self._connection.execute(
            "SELECT id, created_at, updated_at FROM sessions WHERE id = ?",
            (str(session_id),),
        ).fetchone()
        if row is None:
            return None
        turns = self._load_turns(session_id)
        return Session(
            id=UUID(row["id"]),
            created_at=_from_iso(row["created_at"]),
            updated_at=_from_iso(row["updated_at"]),
            turns=turns,
        )

    def append_turn(self, session_id: UUID, turn: Turn) -> Session:
        """Add one completed exchange to an existing session."""
        session = self.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)

        # Next slot in this chat (0-based). Trimming to max 20 turns is T057.
        position = len(session.turns)
        updated_at = datetime.now(UTC)
        self._connection.execute(
            """
            INSERT INTO turns (
                id, session_id, user_message, assistant_message,
                triage_json, citations_json, lookup_json, created_at, position
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(turn.id),
                str(session_id),
                turn.user_message,
                turn.assistant_message,
                # Serialize nested Pydantic models to JSON text columns.
                turn.triage.model_dump_json(),
                json.dumps(
                    [citation.model_dump(mode="json") for citation in turn.citations]
                ),
                (turn.lookup.model_dump_json() if turn.lookup is not None else None),
                _to_iso(turn.created_at),
                position,
            ),
        )
        self._connection.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (_to_iso(updated_at), str(session_id)),
        )
        self._connection.commit()

        # Re-read so the returned Session matches what is actually on disk.
        loaded = self.get(session_id)
        if loaded is None:  # pragma: no cover - defensive after successful write
            raise SessionNotFoundError(session_id)
        return loaded

    def delete(self, session_id: UUID) -> None:
        """Drop a session; CASCADE removes its turns. Safe to call twice."""
        self._connection.execute(
            "DELETE FROM sessions WHERE id = ?",
            (str(session_id),),
        )
        self._connection.commit()

    def _load_turns(self, session_id: UUID) -> list[Turn]:
        rows = self._connection.execute(
            """
            SELECT id, user_message, assistant_message, triage_json,
                   citations_json, lookup_json, created_at
            FROM turns
            WHERE session_id = ?
            ORDER BY position ASC
            """,
            (str(session_id),),
        ).fetchall()
        return [_row_to_turn(row) for row in rows]


def _row_to_turn(row: sqlite3.Row) -> Turn:
    """Convert one SQL row back into the Pydantic Turn model."""
    citations_raw: list[dict[str, Any]] = json.loads(row["citations_json"])
    lookup_raw = json.loads(row["lookup_json"]) if row["lookup_json"] else None
    return Turn(
        id=UUID(row["id"]),
        user_message=row["user_message"],
        assistant_message=row["assistant_message"],
        triage=TriageMetadata.model_validate_json(row["triage_json"]),
        citations=[Citation.model_validate(item) for item in citations_raw],
        lookup=(
            LookupResult.model_validate(lookup_raw) if lookup_raw is not None else None
        ),
        created_at=_from_iso(row["created_at"]),
    )
