"""Unit tests for SlowAPI message rate limiting helpers."""

from __future__ import annotations

from app.config import Settings
from app.rate_limit import (
    configure_rate_limits,
    message_limit_value,
    rate_limit_exempt,
)


def test_message_limit_value_uses_settings() -> None:
    configure_rate_limits(
        Settings(
            _env_file=None,
            openai_api_key="sk-test-key",
            rate_limit_requests=12,
            rate_limit_window_seconds=60,
        )  # type: ignore[call-arg]
    )

    assert message_limit_value() == "12/60seconds"


def test_rate_limit_exempt_when_disabled() -> None:
    configure_rate_limits(
        Settings(
            _env_file=None,
            openai_api_key="sk-test-key",
            rate_limit_enabled=True,
        )  # type: ignore[call-arg]
    )
    assert rate_limit_exempt() is False

    configure_rate_limits(
        Settings(
            _env_file=None,
            openai_api_key="sk-test-key",
            rate_limit_enabled=False,
        )  # type: ignore[call-arg]
    )
    assert rate_limit_exempt() is True
