"""SQLAlchemy ORM models for mock order/account lookup data."""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class OrderRecord(Base):
    """Mock order row used by lookup_order tools."""

    __tablename__ = "orders"

    identifier: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(64))
    summary: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")


class AccountRecord(Base):
    """Mock account row used by lookup_account tools."""

    __tablename__ = "accounts"

    identifier: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(64))
    summary: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
