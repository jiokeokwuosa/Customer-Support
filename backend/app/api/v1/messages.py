"""Message endpoints under /api/v1/sessions/{session_id}/messages."""

from uuid import UUID

from fastapi import APIRouter

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
