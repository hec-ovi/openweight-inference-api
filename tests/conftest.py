"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from app.core.config import get_settings
from app.core.config import Settings


@pytest.fixture(autouse=True)
def _test_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set deterministic env values for tests."""

    monkeypatch.setenv("API_BEARER_KEYS", "test-token")
    monkeypatch.setenv("MODEL_PROFILE", "qwen3.5-light")
    monkeypatch.setenv("VLLM_BASE_URL", "http://vllm.test")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_LOG_LEVEL", "WARNING")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://localhost:3000")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def settings() -> Settings:
    """Return settings for direct route and service tests."""

    return get_settings()
