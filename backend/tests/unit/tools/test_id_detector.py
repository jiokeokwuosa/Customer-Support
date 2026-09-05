"""Unit tests for order/account ID regex detection (T071)."""

from __future__ import annotations

from app.schemas.message import LookupType
from app.tools.id_detector import DetectedId, detect_ids


def test_detects_ord_prefix() -> None:
    result = detect_ids("I was charged twice for order ORD-12345.")

    assert result == [DetectedId(lookup_type=LookupType.ORDER, identifier="ORD-12345")]


def test_detects_order_phrase_with_hash() -> None:
    result = detect_ids("Please check order #98765 status.")

    assert result == [DetectedId(lookup_type=LookupType.ORDER, identifier="ORD-98765")]


def test_detects_order_phrase_without_hash() -> None:
    result = detect_ids("My order 55501 never arrived.")

    assert result == [DetectedId(lookup_type=LookupType.ORDER, identifier="ORD-55501")]


def test_detects_account_id_case_insensitive() -> None:
    result = detect_ids("My account acc-99 shows the wrong plan.")

    assert result == [DetectedId(lookup_type=LookupType.ACCOUNT, identifier="ACC-99")]


def test_detects_multiple_ids_in_first_seen_order() -> None:
    result = detect_ids("Account ACC-42 and ORD-100 are linked; also order #100 again.")

    assert result == [
        DetectedId(lookup_type=LookupType.ACCOUNT, identifier="ACC-42"),
        DetectedId(lookup_type=LookupType.ORDER, identifier="ORD-100"),
    ]


def test_returns_empty_when_no_ids() -> None:
    assert detect_ids("What's the weather in Paris?") == []


def test_normalizes_ord_prefix_to_uppercase() -> None:
    result = detect_ids("status for ord-42 please")

    assert result == [DetectedId(lookup_type=LookupType.ORDER, identifier="ORD-42")]
