"""SQLAlchemy ORM models (database tables).

API/domain shapes live in `app.schemas` (Pydantic). Repositories translate
between the two — never expose ORM rows to routes.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class SessionRecord(Base):
    """One chat thread row."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column()
    updated_at: Mapped[datetime] = mapped_column()
    turns: Mapped[list[TurnRecord]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="TurnRecord.position",
    )


class TurnRecord(Base):
    """One user/assistant exchange row."""

    __tablename__ = "turns"
    __table_args__ = (Index("idx_turns_session_position", "session_id", "position"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"),
        index=True,
    )
    user_message: Mapped[str] = mapped_column(Text)
    assistant_message: Mapped[str] = mapped_column(Text)
    # Nested Pydantic payloads stored as JSON text (triage, citations, lookup).
    triage_json: Mapped[str] = mapped_column(Text)
    citations_json: Mapped[str] = mapped_column(Text)
    lookup_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column()
    position: Mapped[int] = mapped_column()
    session: Mapped[SessionRecord] = relationship(back_populates="turns")
