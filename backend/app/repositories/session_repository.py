"""Session persistence via SQLAlchemy ORM.

Uses `app.models` table classes and returns `app.schemas` domain objects.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import selectinload

from app.models.session import SessionRecord, TurnRecord
from app.repositories.mappers import session_record_to_domain
from app.schemas.session import Session, Turn


class SessionRepository:
    """CRUD for sessions and turns using SQLAlchemy."""

    def __init__(self, db: OrmSession) -> None:
        self._db = db

    def create_session(self) -> Session:
        now = datetime.now(UTC)
        record = SessionRecord(
            id=str(uuid4()),
            created_at=now,
            updated_at=now,
        )
        self._db.add(record)
        self._db.commit()
        self._db.refresh(record)
        return session_record_to_domain(record)

    def get_session(self, session_id: UUID) -> Session | None:
        record = self._db.get(
            SessionRecord,
            str(session_id),
            options=(selectinload(SessionRecord.turns),),
        )
        if record is None:
            return None
        return session_record_to_domain(record)

    def insert_turn(
        self,
        session_id: UUID,
        turn: Turn,
        *,
        position: int,
        updated_at: datetime,
    ) -> None:
        record = self._db.get(SessionRecord, str(session_id))
        if record is None:
            return

        record.turns.append(
            TurnRecord(
                id=str(turn.id),
                session_id=str(session_id),
                user_message=turn.user_message,
                assistant_message=turn.assistant_message,
                triage_json=turn.triage.model_dump_json(),
                citations_json=json.dumps(
                    [citation.model_dump(mode="json") for citation in turn.citations]
                ),
                lookup_json=(
                    turn.lookup.model_dump_json() if turn.lookup is not None else None
                ),
                created_at=turn.created_at,
                position=position,
            )
        )
        record.updated_at = updated_at
        self._db.flush()

    def delete_session(self, session_id: UUID) -> None:
        record = self._db.get(SessionRecord, str(session_id))
        if record is not None:
            self._db.delete(record)
            self._db.commit()

    def trim_turns(self, session_id: UUID, keep: int) -> None:
        """Keep only the newest `keep` turns; drop older ones and renumber."""
        turns = self._db.scalars(
            select(TurnRecord)
            .where(TurnRecord.session_id == str(session_id))
            .order_by(TurnRecord.position.asc())
        ).all()
        if len(turns) <= keep:
            return

        for turn in turns[:-keep]:
            self._db.delete(turn)
        self._db.flush()

        remaining = self._db.scalars(
            select(TurnRecord)
            .where(TurnRecord.session_id == str(session_id))
            .order_by(TurnRecord.position.asc())
        ).all()
        for index, turn in enumerate(remaining):
            turn.position = index
        self._db.flush()

    def commit(self) -> None:
        self._db.commit()
