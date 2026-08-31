"""SQL access for sessions and turns.

Repositories talk to SQLite and return domain models (`Session`, `Turn`).
Higher layers (API/services) should use `SessionStore` from `app.db.session_store`,
not this module directly.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from app.models.message import Citation, LookupResult
from app.models.session import Session, Turn
from app.models.triage import TriageMetadata


def _to_iso(value: datetime) -> str:
    # SQLite has no native timezone-aware datetime type; store UTC ISO strings.
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


def _from_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


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


class SessionRepository:
    """CRUD for the `sessions` and `turns` tables."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create_session(self) -> Session:
        now = datetime.now(UTC)
        session = Session(id=uuid4(), created_at=now, updated_at=now, turns=[])
        self._connection.execute(
            "INSERT INTO sessions (id, created_at, updated_at) VALUES (?, ?, ?)",
            (str(session.id), _to_iso(session.created_at), _to_iso(session.updated_at)),
        )
        self._connection.commit()
        return session

    def get_session(self, session_id: UUID) -> Session | None:
        row = self._connection.execute(
            "SELECT id, created_at, updated_at FROM sessions WHERE id = ?",
            (str(session_id),),
        ).fetchone()
        if row is None:
            return None
        turns = self.list_turns(session_id)
        return Session(
            id=UUID(row["id"]),
            created_at=_from_iso(row["created_at"]),
            updated_at=_from_iso(row["updated_at"]),
            turns=turns,
        )

    def list_turns(self, session_id: UUID) -> list[Turn]:
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

    def insert_turn(
        self,
        session_id: UUID,
        turn: Turn,
        *,
        position: int,
        updated_at: datetime,
    ) -> None:
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

    def delete_session(self, session_id: UUID) -> None:
        # CASCADE on the FK removes related turns.
        self._connection.execute(
            "DELETE FROM sessions WHERE id = ?",
            (str(session_id),),
        )
        self._connection.commit()

    def trim_turns(self, session_id: UUID, keep: int) -> None:
        """Keep only the newest `keep` turns; drop older ones and renumber."""
        rows = self._connection.execute(
            """
            SELECT id FROM turns
            WHERE session_id = ?
            ORDER BY position ASC
            """,
            (str(session_id),),
        ).fetchall()
        if len(rows) <= keep:
            return

        # Oldest first; drop everything before the trailing window.
        overflow = rows[:-keep]
        self._connection.executemany(
            "DELETE FROM turns WHERE id = ?",
            [(row["id"],) for row in overflow],
        )
        remaining = self._connection.execute(
            """
            SELECT id FROM turns
            WHERE session_id = ?
            ORDER BY position ASC
            """,
            (str(session_id),),
        ).fetchall()
        for index, row in enumerate(remaining):
            self._connection.execute(
                "UPDATE turns SET position = ? WHERE id = ?",
                (index, row["id"]),
            )
        self._connection.commit()
