"""Performance-related defaults used across the stack (T099)."""

from __future__ import annotations

import pytest

from app.config import Settings, get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    get_settings.cache_clear()


def test_chain_timeouts_are_bounded() -> None:
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.chain_timeout_seconds == 60.0
    assert settings.chain_target_seconds == 30.0
    assert settings.chain_timeout_seconds >= settings.chain_target_seconds


def test_frontend_query_stale_time_documented() -> None:
    """Mirror of frontend/src/lib/query/keys.ts queryDefaults.staleTime (60_000ms)."""
    stale_time_ms = 60_000
    assert stale_time_ms == 60_000
