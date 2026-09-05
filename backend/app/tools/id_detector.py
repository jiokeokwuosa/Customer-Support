"""Detect order/account identifiers in customer messages (US5)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas.message import LookupType

# Research: ORD-\d+, order #?\d+, ACC-[A-Z0-9-]+ (case-insensitive).
_PATTERNS: tuple[tuple[re.Pattern[str], LookupType, str], ...] = (
    (re.compile(r"\bORD-(\d+)\b", re.IGNORECASE), LookupType.ORDER, "ORD-{0}"),
    (re.compile(r"\border\s+#?(\d+)\b", re.IGNORECASE), LookupType.ORDER, "ORD-{0}"),
    (
        re.compile(r"\bACC-([A-Z0-9-]+)\b", re.IGNORECASE),
        LookupType.ACCOUNT,
        "ACC-{0}",
    ),
)


@dataclass(frozen=True)
class DetectedId:
    """One identifier found in free text, ready for mock lookup."""

    lookup_type: LookupType
    identifier: str


def detect_ids(text: str) -> list[DetectedId]:
    """Return unique order/account IDs in first-seen order."""
    hits: list[tuple[int, DetectedId]] = []
    for pattern, lookup_type, template in _PATTERNS:
        for match in pattern.finditer(text):
            raw = match.group(1)
            identifier = template.format(
                raw if lookup_type is LookupType.ORDER else raw.upper()
            )
            hits.append(
                (
                    match.start(),
                    DetectedId(lookup_type=lookup_type, identifier=identifier),
                )
            )

    hits.sort(key=lambda item: item[0])
    found: list[DetectedId] = []
    seen: set[tuple[LookupType, str]] = set()
    for _start, detected in hits:
        key = (detected.lookup_type, detected.identifier)
        if key in seen:
            continue
        seen.add(key)
        found.append(detected)
    return found
