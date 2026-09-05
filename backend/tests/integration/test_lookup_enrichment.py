"""Integration tests for mock order/account lookup enrichment (T073 / VS-6)."""

from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient

from app.schemas.message import TurnStatus


def test_known_order_id_returns_lookup(
    integration_client: TestClient,
    session_id: UUID,
) -> None:
    response = integration_client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"message": "Where is order ORD-12345?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == TurnStatus.SUCCESS
    assert body["lookup"] is not None
    assert body["lookup"]["lookup_type"] == "order"
    assert body["lookup"]["identifier"] == "ORD-12345"
    assert body["lookup"]["found"] is True
    assert "shipped" in body["lookup"]["summary"].lower()
    assert body["lookup"]["details"]["carrier"] == "UPS"


def test_unknown_order_id_returns_not_found_lookup(
    integration_client: TestClient,
    session_id: UUID,
) -> None:
    response = integration_client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"message": "Status for ORD-99999 please."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == TurnStatus.SUCCESS
    assert body["lookup"] is not None
    assert body["lookup"]["identifier"] == "ORD-99999"
    assert body["lookup"]["found"] is False
    assert body["lookup"]["details"] is None
    assert "no order found" in body["lookup"]["summary"].lower()


def test_message_without_id_has_null_lookup(
    integration_client: TestClient,
    session_id: UUID,
) -> None:
    response = integration_client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"message": "Hello, I need general help."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == TurnStatus.SUCCESS
    assert body["lookup"] is None
