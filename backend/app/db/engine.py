"""Database engine and session factory (SQLAlchemy)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.schema import SessionRecord, TurnRecord  # noqa: F401 — register tables


def create_db_engine(database_path: str | Path) -> Engine:
    """Build a SQLite engine for a file path or in-memory tests."""
    path = str(database_path)
    if path == ":memory:":
        # StaticPool keeps one connection so :memory: data survives across sessions.
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(
            f"sqlite:///{path}",
            connect_args={"check_same_thread": False},
        )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(
        dbapi_connection: sqlite3.Connection,
        _connection_record: object,
    ) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    return engine


def init_db(engine: Engine) -> None:
    """Create tables from ORM metadata if they do not exist."""
    Base.metadata.create_all(bind=engine)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)
