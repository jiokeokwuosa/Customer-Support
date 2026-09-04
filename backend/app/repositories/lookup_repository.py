"""Repository for order/account lookup records."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session as OrmSession

from app.models.lookup import AccountRecord, OrderRecord
from app.schemas.message import LookupResult, LookupType


class LookupRepository:
    """Read mock CRM rows from SQLite."""

    def __init__(self, db: OrmSession) -> None:
        self._db = db

    def get_order(self, order_id: str) -> LookupResult:
        key = order_id.strip().upper()
        record = self._db.get(OrderRecord, key)
        if record is None:
            return LookupResult(
                lookup_type=LookupType.ORDER,
                identifier=key,
                found=False,
                summary=f"No order found for {key}.",
                details=None,
            )
        return _order_to_result(record)

    def get_account(self, account_id: str) -> LookupResult:
        key = account_id.strip().upper()
        record = self._db.get(AccountRecord, key)
        if record is None:
            return LookupResult(
                lookup_type=LookupType.ACCOUNT,
                identifier=key,
                found=False,
                summary=f"No account found for {key}.",
                details=None,
            )
        return _account_to_result(record)


def _parse_metadata(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _order_to_result(record: OrderRecord) -> LookupResult:
    details = _parse_metadata(record.metadata_json)
    details["status"] = record.status
    return LookupResult(
        lookup_type=LookupType.ORDER,
        identifier=record.identifier,
        found=True,
        summary=record.summary,
        details=details,
    )


def _account_to_result(record: AccountRecord) -> LookupResult:
    details = _parse_metadata(record.metadata_json)
    details["status"] = record.status
    return LookupResult(
        lookup_type=LookupType.ACCOUNT,
        identifier=record.identifier,
        found=True,
        summary=record.summary,
        details=details,
    )
