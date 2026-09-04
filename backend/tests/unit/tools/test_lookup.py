"""Unit tests for mock lookup tools against the database (T072)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.schemas.message import LookupType
from app.tools.lookup import (
    lookup_account,
    lookup_account_record,
    lookup_order,
    lookup_order_record,
)


def test_lookup_order_found(db: Session) -> None:
    result = lookup_order_record("ORD-12345", db=db)

    assert result.found is True
    assert result.lookup_type is LookupType.ORDER
    assert result.identifier == "ORD-12345"
    assert "shipped" in result.summary.lower()
    assert result.details is not None
    assert result.details["carrier"] == "UPS"


def test_lookup_order_not_found(db: Session) -> None:
    result = lookup_order_record("ORD-99999", db=db)

    assert result.found is False
    assert result.identifier == "ORD-99999"
    assert result.details is None
    assert "no order found" in result.summary.lower()


def test_lookup_order_normalizes_case(db: Session) -> None:
    result = lookup_order_record("ord-12345", db=db)
    assert result.found is True
    assert result.identifier == "ORD-12345"


def test_lookup_account_found(db: Session) -> None:
    result = lookup_account_record("ACC-99", db=db)

    assert result.found is True
    assert result.lookup_type is LookupType.ACCOUNT
    assert "Pro" in result.summary
    assert result.details is not None
    assert result.details["plan"] == "Pro"


def test_lookup_account_not_found(db: Session) -> None:
    result = lookup_account_record("ACC-MISSING", db=db)

    assert result.found is False
    assert result.details is None
    assert "no account found" in result.summary.lower()


def test_langchain_tools_invoke_fixtures(db: Session) -> None:
    # Tools open their own sessions; `db` fixture ensures tables are seeded.
    _ = db
    order = lookup_order.invoke({"order_id": "ORD-12345"})
    account = lookup_account.invoke({"account_id": "acc-99"})

    assert order["found"] is True
    assert order["identifier"] == "ORD-12345"
    assert account["found"] is True
    assert account["identifier"] == "ACC-99"
