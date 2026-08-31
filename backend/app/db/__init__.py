"""Database package: low-level connections and schema only."""

from app.db.sqlite import connect_sqlite

__all__ = ["connect_sqlite"]
