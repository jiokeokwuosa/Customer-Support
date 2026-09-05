"""Contract tests: FastAPI routes and schemas align with OpenAPI (T094)."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.main import create_app
from app.schemas.message import Citation, ErrorResponse, LookupResult, TurnResponse
from app.schemas.prompts import SamplePrompt
from app.schemas.session import CreateSessionResponse
from app.schemas.triage import TriageMetadata

_OPENAPI_PATH = (
    Path(__file__).resolve().parents[3]
    / "specs"
    / "001-ticket-triage"
    / "contracts"
    / "openapi.yaml"
)


def _load_openapi() -> dict:
    return yaml.safe_load(_OPENAPI_PATH.read_text(encoding="utf-8"))


def _app_paths() -> set[str]:
    get_settings.cache_clear()
    app = create_app(Settings(_env_file=None))  # type: ignore[call-arg]
    # Prefer generated OpenAPI paths — FastAPI may wrap routers as _IncludedRouter.
    return set(app.openapi()["paths"].keys())


def test_openapi_paths_are_mounted_on_app() -> None:
    openapi = _load_openapi()
    mounted = _app_paths()

    for path in openapi["paths"]:
        assert path in mounted, f"OpenAPI path missing from app: {path}"


def test_openapi_required_fields_exist_on_pydantic_models() -> None:
    """OpenAPI `required` fields must exist on the corresponding Pydantic model."""
    schemas = _load_openapi()["components"]["schemas"]

    checks: list[tuple[str, type[BaseModel]]] = [
        ("TriageMetadata", TriageMetadata),
        ("Citation", Citation),
        ("LookupResult", LookupResult),
        ("TurnResponse", TurnResponse),
        ("ErrorResponse", ErrorResponse),
        ("CreateSessionResponse", CreateSessionResponse),
        ("SamplePrompt", SamplePrompt),
    ]

    for name, model in checks:
        required = set(schemas[name].get("required", []))
        model_fields = set(model.model_fields.keys())
        missing = required - model_fields
        assert not missing, (
            f"{name}: OpenAPI required fields missing on model: {missing}"
        )
