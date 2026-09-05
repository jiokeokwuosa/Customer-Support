"""Seed SQLite with mock order/account rows (from JSON seed files)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.lookup import AccountRecord, OrderRecord


def default_fixtures_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "fixtures"


def seed_lookup_data(
    db: Session,
    *,
    fixtures_dir: Path | None = None,
) -> None:
    """Insert demo orders/accounts when tables are empty.

    JSON under ``data/fixtures/`` is the seed source only — runtime reads SQLite.
    """
    root = fixtures_dir if fixtures_dir is not None else default_fixtures_dir()
    _seed_orders(db, root / "orders.json")
    _seed_accounts(db, root / "accounts.json")
    db.commit()


def _seed_orders(db: Session, path: Path) -> None:
    count = db.scalar(select(func.count()).select_from(OrderRecord)) or 0
    if count > 0 or not path.is_file():
        return
    for item in _read_json_list(path):
        identifier = str(item["identifier"]).upper()
        db.add(
            OrderRecord(
                identifier=identifier,
                status=str(item["status"]),
                summary=str(item["summary"]),
                metadata_json=json.dumps(item.get("metadata") or {}),
            )
        )


def _seed_accounts(db: Session, path: Path) -> None:
    count = db.scalar(select(func.count()).select_from(AccountRecord)) or 0
    if count > 0 or not path.is_file():
        return
    for item in _read_json_list(path):
        identifier = str(item["identifier"]).upper()
        db.add(
            AccountRecord(
                identifier=identifier,
                status=str(item["status"]),
                summary=str(item["summary"]),
                metadata_json=json.dumps(item.get("metadata") or {}),
            )
        )


def _read_json_list(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        msg = f"Expected a JSON list in {path}"
        raise TypeError(msg)
    return raw
