"""Shared test fixtures for database-backed services."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from sqlalchemy.orm import Session

os.environ.setdefault("OPENAI_API_KEY", "sk-test-key")
os.environ.setdefault("DATABASE_PATH", "test_sessions.db")

from app.config import get_settings

get_settings.cache_clear()

from app.db.database import Base, SessionLocal, engine, init_db
from app.rate_limit import limiter
from app.repositories.session_repository import SessionRepository
from app.services.session_service import SessionService


@pytest.fixture(autouse=True)
def reset_message_rate_limiter() -> Iterator[None]:
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def db() -> Iterator[Session]:
    Base.metadata.drop_all(bind=engine)
    init_db()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def session_service(db: Session) -> SessionService:
    return SessionService(SessionRepository(db))
