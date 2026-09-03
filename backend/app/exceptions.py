"""Domain exceptions raised by services and mapped in the API layer."""

from __future__ import annotations

from uuid import UUID


class SessionNotFoundError(KeyError):
    """Raised when a session_id is unknown."""

    def __init__(self, session_id: UUID) -> None:
        self.session_id = session_id
        super().__init__(f"Session not found: {session_id}")
