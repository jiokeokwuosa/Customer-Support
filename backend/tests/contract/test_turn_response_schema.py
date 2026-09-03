"""Contract tests: TurnResponse.triage matches OpenAPI TriageMetadata (T047)."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest
import yaml
from pydantic import ValidationError

from app.schemas.message import TurnResponse, TurnStatus
from app.schemas.triage import (
    SentimentLabel,
    TopicCategory,
    TriageMetadata,
    UrgencyLevel,
)

_OPENAPI_PATH = (
    Path(__file__).resolve().parents[3]
    / "specs"
    / "001-ticket-triage"
    / "contracts"
    / "openapi.yaml"
)


def _openapi_schemas() -> dict:
    document = yaml.safe_load(_OPENAPI_PATH.read_text(encoding="utf-8"))
    return document["components"]["schemas"]


def _sample_turn_response() -> TurnResponse:
    return TurnResponse(
        turn_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        session_id=UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8"),
        status=TurnStatus.SUCCESS,
        message="I understand your frustration regarding the duplicate charge.",
        triage=TriageMetadata(
            topic=TopicCategory.BILLING,
            sentiment=SentimentLabel.FRUSTRATED,
            urgency=UrgencyLevel.HIGH,
            rationale="Duplicate charge complaint with urgent refund request",
        ),
        citations=[],
        lookup=None,
        error_code=None,
        next_actions=[],
    )


def test_openapi_triage_metadata_requires_four_fields() -> None:
    schemas = _openapi_schemas()
    triage_schema = schemas["TriageMetadata"]

    assert set(triage_schema["required"]) == {
        "topic",
        "sentiment",
        "urgency",
        "rationale",
    }
    assert triage_schema["properties"]["rationale"]["maxLength"] == 200


def test_openapi_turn_response_requires_triage() -> None:
    schemas = _openapi_schemas()
    turn_schema = schemas["TurnResponse"]

    assert "triage" in turn_schema["required"]
    assert turn_schema["properties"]["triage"] == {
        "$ref": "#/components/schemas/TriageMetadata",
    }


def test_turn_response_json_includes_all_triage_fields() -> None:
    payload = _sample_turn_response().model_dump(mode="json")

    assert "triage" in payload
    assert set(payload["triage"]) == {
        "topic",
        "sentiment",
        "urgency",
        "rationale",
    }
    assert payload["triage"]["topic"] == "billing"
    assert payload["triage"]["sentiment"] == "frustrated"
    assert payload["triage"]["urgency"] == "high"
    assert payload["triage"]["rationale"]


def test_turn_response_triage_enums_match_openapi() -> None:
    schemas = _openapi_schemas()

    assert {member.value for member in TopicCategory} == set(
        schemas["TopicCategory"]["enum"]
    )
    assert {member.value for member in SentimentLabel} == set(
        schemas["SentimentLabel"]["enum"]
    )
    assert {member.value for member in UrgencyLevel} == set(
        schemas["UrgencyLevel"]["enum"]
    )


def test_turn_response_rejects_payload_missing_triage_field() -> None:
    with pytest.raises(ValidationError):
        TurnResponse.model_validate(
            {
                "turn_id": "550e8400-e29b-41d4-a716-446655440000",
                "session_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "status": "success",
                "message": "Thanks",
                "triage": {
                    "topic": "billing",
                    "sentiment": "frustrated",
                    "urgency": "high",
                    # rationale intentionally omitted
                },
                "citations": [],
                "error_code": None,
                "next_actions": [],
            }
        )
