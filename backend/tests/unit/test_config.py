import pytest

from app.config import Settings, get_settings


def load_settings_from_env() -> Settings:
    """Build settings from the current process environment only."""
    return Settings(_env_file=None)  # type: ignore[call-arg]


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    get_settings.cache_clear()


def test_settings_defaults_with_required_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.delenv("DATABASE_PATH", raising=False)

    settings = load_settings_from_env()

    assert settings.openai_api_key.get_secret_value() == "sk-test-key"
    assert settings.openai_model == "gpt-4o-mini"
    assert settings.cors_origins == ["http://localhost:3000"]
    assert settings.log_level == "INFO"
    assert settings.message_max_length == 4000
    assert settings.chain_timeout_seconds == 60.0
    assert settings.chain_target_seconds == 30.0
    assert settings.database_path == "data/sessions.db"


def test_settings_parses_comma_separated_cors_origins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )

    settings = load_settings_from_env()

    assert settings.cors_origins == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def test_get_settings_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    first = get_settings()
    second = get_settings()

    assert first is second
