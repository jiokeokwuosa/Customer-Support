"""Unit tests for lookup seed / repository."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.lookup import AccountRecord, OrderRecord
from app.repositories.lookup_repository import LookupRepository


def test_seed_populates_orders_and_accounts(db: Session) -> None:
    orders = db.scalar(select(func.count()).select_from(OrderRecord)) or 0
    accounts = db.scalar(select(func.count()).select_from(AccountRecord)) or 0

    assert orders >= 2
    assert accounts >= 2


def test_lookup_repository_reads_seeded_order(db: Session) -> None:
    repo = LookupRepository(db)
    result = repo.get_order("ORD-12345")

    assert result.found is True
    assert result.details is not None
    assert result.details["status"] == "shipped"
