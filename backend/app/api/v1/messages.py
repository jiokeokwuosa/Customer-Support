"""Message endpoints under /api/v1/sessions/{session_id}/messages."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any
from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.deps import TriageServiceDep
from app.schemas.message import SendMessageRequest, TurnResponse

router = APIRouter(prefix="/sessions", tags=["messages"])


@router.post("/{session_id}/messages", response_model=TurnResponse)
def send_message(
    session_id: UUID,
    body: SendMessageRequest,
    triage_service: TriageServiceDep,
) -> TurnResponse:
    return triage_service.process_message(session_id, body.message)


@router.post("/{session_id}/messages/stream")
def send_message_stream(
    session_id: UUID,
    body: SendMessageRequest,
    triage_service: TriageServiceDep,
) -> StreamingResponse:
    """Stream triage metadata and assistant tokens as Server-Sent Events."""
    # Validate session before StreamingResponse starts so 404 is not mid-stream.
    events = triage_service.stream_message(session_id, body.message)

    def event_stream() -> Iterator[str]:
        for event_name, payload in events:
            yield _format_sse(event_name, payload)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _format_sse(event: str, payload: Any) -> str:
    if isinstance(payload, BaseModel):
        data = payload.model_dump_json()
    elif isinstance(payload, list):
        data = json.dumps(
            [
                item.model_dump(mode="json") if isinstance(item, BaseModel) else item
                for item in payload
            ]
        )
    else:
        data = json.dumps(payload)
    return f"event: {event}\ndata: {data}\n\n"
