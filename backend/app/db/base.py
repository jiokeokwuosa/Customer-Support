"""SQLAlchemy declarative base and engine helpers."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared metadata registry for all ORM table classes."""
