"""SQLite connection helpers and schema bootstrap.

This is the low-level DB layer only: open a connection, enable pragmas, create
tables. Domain CRUD lives in `app.repositories`; orchestration in `app.services`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

# Relational core for sessions/turns. Nested triage/citations/lookup stay as
# JSON text so we do not need extra tables for every nested Pydantic field.
SESSION_SCHEMA = """
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


def connect_sqlite(database_path: str | Path) -> sqlite3.Connection:
    """Open SQLite, apply session schema, and return a ready connection.

    Pass a filesystem path for durable storage, or `:memory:` for tests.
    """
    path = str(database_path)
    if path != ":memory:":
        # SQLite will not create missing parent directories for us.
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    # One long-lived connection is expected by callers.
    # - :memory: DBs are wiped if you reconnect, so keep this open.
    # - check_same_thread=False lets FastAPI workers share the connection;
    #   SQLite still serializes writes internally.
    connection = sqlite3.connect(path, check_same_thread=False)
    # Rows behave like dicts: row["id"] instead of row[0].
    connection.row_factory = sqlite3.Row
    # SQLite does not enforce foreign keys unless this pragma is on.
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SESSION_SCHEMA)
    connection.commit()
    return connection
