import pytest
from pydantic import ValidationError

from app.models.message import (
    ErrorCode,
    ErrorResponse,
    SendMessageRequest,
    TurnResponse,
    TurnStatus,
)
from app.models.triage import (
    SentimentLabel,
    TopicCategory,
    TriageMetadata,
    UrgencyLevel,
)


def test_send_message_request_strips_whitespace() -> None:
    request = SendMessageRequest(message="  hello  ")

    assert request.message == "hello"


def test_send_message_request_rejects_blank_message() -> None:
    with pytest.raises(ValidationError):
        SendMessageRequest(message="   ")


def test_error_response_matches_openapi_shape() -> None:
    error = ErrorResponse(
        message="Session not found",
        error_code=ErrorCode.SESSION_NOT_FOUND,
        next_actions=["new_conversation"],
    )

    assert error.status == "error"
    assert error.error_code == ErrorCode.SESSION_NOT_FOUND


def test_turn_response_accepts_success_payload() -> None:
    from uuid import UUID

    response = TurnResponse(
        turn_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        session_id=UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8"),
        status=TurnStatus.SUCCESS,
        message="Thanks for reaching out.",
        triage=TriageMetadata(
            topic=TopicCategory.BILLING,
            sentiment=SentimentLabel.FRUSTRATED,
            urgency=UrgencyLevel.HIGH,
            rationale="Billing dispute",
        ),
        error_code=None,
        next_actions=[],
    )

    assert response.status == TurnStatus.SUCCESS
    assert response.lookup is None
