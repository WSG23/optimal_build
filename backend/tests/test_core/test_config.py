"""Tests for Settings helper functions."""

from __future__ import annotations

import importlib

from app.core import config as config_module


def _fresh_settings(monkeypatch, value: str | None):
    if value is None:
        monkeypatch.delenv("FINANCE_SENSITIVITY_MAX_SYNC_BANDS", raising=False)
    else:
        monkeypatch.setenv("FINANCE_SENSITIVITY_MAX_SYNC_BANDS", value)
    importlib.reload(config_module)
    return config_module.Settings()


def test_finance_sensitivity_max_sync_bands_default(monkeypatch):
    """Ensure defaults fall back to three bands when env var missing or invalid."""

    settings = _fresh_settings(monkeypatch, None)
    assert settings.FINANCE_SENSITIVITY_MAX_SYNC_BANDS == 3

    settings = _fresh_settings(monkeypatch, "0")
    assert settings.FINANCE_SENSITIVITY_MAX_SYNC_BANDS == 3

    settings = _fresh_settings(monkeypatch, "abc")
    assert settings.FINANCE_SENSITIVITY_MAX_SYNC_BANDS == 3


def test_finance_sensitivity_max_sync_bands_env_override(monkeypatch):
    """Env variable should override the default when positive integers supplied."""

    settings = _fresh_settings(monkeypatch, "5")
    assert settings.FINANCE_SENSITIVITY_MAX_SYNC_BANDS == 5

    settings = _fresh_settings(monkeypatch, "9")
    assert settings.FINANCE_SENSITIVITY_MAX_SYNC_BANDS == 9


def test_local_dotenv_loader_preserves_secret_special_characters(
    monkeypatch,
    tmp_path,
):
    """Local env files should load secrets literally, without shell expansion."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ONEMAP_EMAIL", raising=False)
    monkeypatch.setenv("ONEMAP_PASSWORD", "shell-expanded")
    (tmp_path / ".env").write_text(
        "ONEMAP_EMAIL=base@example.com\nONEMAP_PASSWORD=base\n",
        encoding="utf-8",
    )
    (tmp_path / ".env.local").write_text(
        "ONEMAP_EMAIL=capture@example.com\nONEMAP_PASSWORD=pa$$word#literal\n",
        encoding="utf-8",
    )

    importlib.reload(config_module)

    assert config_module.settings.ONEMAP_EMAIL == "capture@example.com"
    assert config_module.settings.ONEMAP_PASSWORD == "pa$$word#literal"
