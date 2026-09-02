"""Shared helpers for pipeline state dicts passed between LCEL steps."""

from __future__ import annotations

from typing import Any

from app.schemas.triage import TriageMetadata


def require_triage(state: dict[str, Any]) -> TriageMetadata:
    """Return validated triage metadata from pipeline state."""
    triage = state["triage"]
    if not isinstance(triage, TriageMetadata):
        msg = "triage must be TriageMetadata"
        raise TypeError(msg)
    return triage
