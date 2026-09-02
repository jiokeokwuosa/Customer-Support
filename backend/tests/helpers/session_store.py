"""Test helpers for constructing a wired SqliteSessionStore."""

from __future__ import annotations

from pathlib import Path

from app.db.engine import create_db_engine, create_session_factory, init_db
from app.services.session_store import SqliteSessionStore


def make_sqlite_session_store(database_path: Path | str) -> SqliteSessionStore:
    """Build a session store with engine setup (for tests and local scripts)."""
    engine = create_db_engine(database_path)
    init_db(engine)
    return SqliteSessionStore(create_session_factory(engine))
