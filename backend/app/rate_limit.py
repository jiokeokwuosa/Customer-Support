"""Rate limiting for LLM-bound message endpoints via SlowAPI.

Uses an in-memory store by default (fine for a single process). Point
``Limiter`` at Redis via ``storage_uri`` if you run multiple workers.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import Settings, get_settings

limiter = Limiter(key_func=get_remote_address)

# Populated by ``configure_rate_limits`` in ``create_app`` so tests can inject
# settings without SlowAPI needing a Request-aware limit callable.
_configured_settings: Settings | None = None


def configure_rate_limits(settings: Settings) -> None:
    """Bind active settings used by the dynamic limit / exempt callables."""
    global _configured_settings
    _configured_settings = settings


def _active_settings() -> Settings:
    return _configured_settings if _configured_settings is not None else get_settings()


def message_limit_value() -> str:
    """Limit string from settings (e.g. ``20/60seconds``)."""
    settings = _active_settings()
    window = max(int(settings.rate_limit_window_seconds), 1)
    return f"{settings.rate_limit_requests}/{window}seconds"


def rate_limit_exempt() -> bool:
    """Skip limiting when disabled in settings."""
    return not _active_settings().rate_limit_enabled


# Shared across full-reply and stream endpoints so both draw from one budget.
limit_llm_messages = limiter.shared_limit(
    message_limit_value,
    scope="llm_messages",
    exempt_when=rate_limit_exempt,
)
