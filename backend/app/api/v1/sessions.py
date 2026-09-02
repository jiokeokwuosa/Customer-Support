"""Session lifecycle endpoints (create, reset)."""

from uuid import UUID

from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse

from app.api.deps import SessionServiceDep
from app.schemas.message import ErrorCode, ErrorResponse
from app.schemas.session import CreateSessionResponse

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_session(session_service: SessionServiceDep) -> CreateSessionResponse:
    session = session_service.create()
    return CreateSessionResponse(
        session_id=session.id,
        created_at=session.created_at,
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def reset_session(
    session_id: UUID,
    session_service: SessionServiceDep,
) -> Response:
    if session_service.get(session_id) is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                message="Session not found",
                error_code=ErrorCode.SESSION_NOT_FOUND,
            ).model_dump(mode="json"),
        )
    session_service.delete(session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
