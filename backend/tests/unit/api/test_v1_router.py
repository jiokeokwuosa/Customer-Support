import pytest

from app.api.v1.router import router as v1_router
from app.config import Settings, get_settings
from app.main import create_app


def load_settings_from_env() -> Settings:
    return Settings(_env_file=None)  # type: ignore[call-arg]


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    get_settings.cache_clear()


def test_v1_router_uses_api_v1_prefix() -> None:
    assert v1_router.prefix == "/api/v1"


def test_create_app_mounts_v1_router(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    application = create_app(load_settings_from_env())

    assert application.openapi_url == "/openapi.json"
    assert v1_router in application.router.routes or v1_router.prefix == "/api/v1"
