"""Integration tests for POST .../messages/stream SSE events (T079 / VS-7)."""

from __future__ import annotations

import json
from uuid import UUID, uuid4

from fastapi.testclient import TestClient


def _parse_sse(raw: str) -> list[tuple[str, str]]:
    """Parse `event:` / `data:` pairs from an SSE body."""
    events: list[tuple[str, str]] = []
    event_name = "message"
    data_lines: list[str] = []

    def flush() -> None:
        nonlocal event_name, data_lines
        if data_lines:
            events.append((event_name, "\n".join(data_lines)))
        event_name = "message"
        data_lines = []

    for line in raw.splitlines():
        if line.startswith("event:"):
            event_name = line.removeprefix("event:").strip()
        elif line.startswith("data:"):
            data_lines.append(line.removeprefix("data:").lstrip())
        elif line == "":
            flush()
    flush()
    return events


def test_stream_emits_triage_token_and_done(
    integration_client: TestClient,
    session_id: UUID,
) -> None:
    with integration_client.stream(
        "POST",
        f"/api/v1/sessions/{session_id}/messages/stream",
        json={"message": "I was charged twice on my invoice."},
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        raw = "".join(response.iter_text())

    events = _parse_sse(raw)
    names = [name for name, _ in events]

    assert "triage" in names
    assert "token" in names
    assert "done" in names
    assert names.index("triage") < names.index("token") < names.index("done")

    triage_payload = json.loads(next(data for name, data in events if name == "triage"))
    assert triage_payload["topic"] == "billing"

    token_chunks = [
        json.loads(data)["text"] for name, data in events if name == "token"
    ]
    assert "".join(token_chunks) == "Polished billing reply."

    done_payload = json.loads(next(data for name, data in events if name == "done"))
    assert done_payload["status"] == "success"
    assert done_payload["message"] == "Polished billing reply."
    assert done_payload["session_id"] == str(session_id)
    assert done_payload["triage"]["topic"] == "billing"


def test_stream_returns_404_for_unknown_session(
    integration_client: TestClient,
) -> None:
    response = integration_client.post(
        f"/api/v1/sessions/{uuid4()}/messages/stream",
        json={"message": "Hello"},
    )
    assert response.status_code == 404
    assert response.json()["error_code"] == "SESSION_NOT_FOUND"


def test_stream_returns_422_for_blank_message(
    integration_client: TestClient,
    session_id: UUID,
) -> None:
    response = integration_client.post(
        f"/api/v1/sessions/{session_id}/messages/stream",
        json={"message": "   "},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "error"
    assert body["error_code"] == "VALIDATION_ERROR"
