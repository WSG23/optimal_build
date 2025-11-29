"""Tests for the rate limiter configuration."""

from __future__ import annotations

import importlib

import pytest

from app import main as main_module
from app.core import config as config_module


class DummyLimiter:
    """Minimal limiter stub capturing constructor arguments."""

    def __init__(self, *, key_func, default_limits, storage_uri):
        self.key_func = key_func
        self.default_limits = default_limits
        self.storage_uri = storage_uri


@pytest.fixture
def fresh_settings(monkeypatch):
    """Return a factory that reloads settings with the provided storage URI."""

    def _factory(storage_uri: str | None) -> config_module.Settings:
        if storage_uri is None:
            monkeypatch.delenv("RATE_LIMIT_STORAGE_URI", raising=False)
        else:
            monkeypatch.setenv("RATE_LIMIT_STORAGE_URI", storage_uri)

        importlib.reload(config_module)
        settings = config_module.Settings()
        monkeypatch.setattr(config_module, "settings", settings)
        return settings

    yield _factory
    importlib.reload(config_module)


def test_rate_limit_storage_defaults_to_memory_under_pytest(fresh_settings):
    """Pytest environments should prefer in-memory rate limit storage."""

    settings = fresh_settings(None)
    assert settings.RATE_LIMIT_STORAGE_URI == "memory://"


def test_rate_limit_storage_env_override(fresh_settings):
    """Environment variable should override default storage URI."""

    custom_uri = "redis://cache.internal:6379/9"
    settings = fresh_settings(custom_uri)

    assert settings.RATE_LIMIT_STORAGE_URI == custom_uri


def test_create_rate_limiter_prefers_available_storage(monkeypatch):
    """Limiter should use configured storage when available."""

    monkeypatch.setattr(main_module, "_storage_available", lambda _: True)

    limiter, active_storage = main_module._create_rate_limiter(
        rate_limit="5/minute",
        storage_uri="redis://cache.internal:6379/9",
        limiter_class=DummyLimiter,
    )

    assert active_storage == "redis://cache.internal:6379/9"
    assert limiter.storage_uri == "redis://cache.internal:6379/9"


def test_create_rate_limiter_falls_back_to_memory(monkeypatch):
    """Limiter should fall back to memory storage when backend is unavailable."""

    monkeypatch.setattr(main_module, "_storage_available", lambda _: False)

    limiter, active_storage = main_module._create_rate_limiter(
        rate_limit="5/minute",
        storage_uri="redis://cache.internal:6379/9",
        limiter_class=DummyLimiter,
    )

    assert active_storage == "memory://"
    assert limiter.storage_uri == "memory://"
