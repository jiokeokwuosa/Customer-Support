"""Mock order/account lookup tools backed by SQLite."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.repositories.lookup_repository import LookupRepository
from app.schemas.message import LookupResult


def lookup_order_record(
    order_id: str,
    *,
    db: Session | None = None,
) -> LookupResult:
    """Resolve an order id against the database (no LLM)."""
    return _with_repo(db, lambda repo: repo.get_order(order_id))


def lookup_account_record(
    account_id: str,
    *,
    db: Session | None = None,
) -> LookupResult:
    """Resolve an account id against the database (no LLM)."""
    return _with_repo(db, lambda repo: repo.get_account(account_id))


def _with_repo(
    db: Session | None,
    action: Callable[[LookupRepository], LookupResult],
) -> LookupResult:
    owns_session = db is None
    session = db if db is not None else SessionLocal()
    try:
        return action(LookupRepository(session))
    finally:
        if owns_session:
            session.close()


@tool  # type: ignore[untyped-decorator]
def lookup_order(order_id: str) -> dict[str, Any]:
    """Look up a mock customer order by identifier (e.g. ORD-12345)."""
    return lookup_order_record(order_id).model_dump(mode="json")


@tool  # type: ignore[untyped-decorator]
def lookup_account(account_id: str) -> dict[str, Any]:
    """Look up a mock customer account by identifier (e.g. ACC-99)."""
    return lookup_account_record(account_id).model_dump(mode="json")
