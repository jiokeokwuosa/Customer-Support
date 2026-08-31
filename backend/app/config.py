"""Load app settings from environment variables / `.env`.

All secrets (API keys) stay on the server. Call `get_settings()` instead of
reading `os.environ` directly so defaults and validation stay in one place.
"""

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Server-side settings. Secrets stay backend-only."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # SecretStr avoids accidental printing/logging of the raw key.
    openai_api_key: SecretStr
    openai_model: str = "gpt-4o-mini"
    # NoDecode: allow "http://a,http://b" in .env instead of requiring JSON.
    cors_origins: Annotated[
        list[str],
        NoDecode,
        Field(default_factory=lambda: ["http://localhost:3000"]),
    ]
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    message_max_length: int = Field(default=4000, ge=1)
    chain_timeout_seconds: float = Field(default=60.0, gt=0)
    chain_target_seconds: float = Field(default=30.0, gt=0)
    # Relative to the backend working directory unless absolute.
    database_path: str = Field(default="data/sessions.db")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, list):
            return value
        msg = "cors_origins must be a comma-separated string or list of strings"
        raise TypeError(msg)


@lru_cache
def get_settings() -> Settings:
    """Load once and reuse — settings should not be re-parsed every request."""
    return Settings()  # type: ignore[call-arg]
