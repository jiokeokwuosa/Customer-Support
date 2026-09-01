import pytest
from fastapi import APIRouter, FastAPI

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
    included_routers: list[APIRouter] = []
    original_include_router = FastAPI.include_router

    def tracking_include_router(
        self: FastAPI,
        router: APIRouter,
        *args: object,
        **kwargs: object,
    ) -> None:
        included_routers.append(router)
        original_include_router(self, router, *args, **kwargs)

    monkeypatch.setattr(FastAPI, "include_router", tracking_include_router)

    create_app(load_settings_from_env())

    assert v1_router in included_routers
