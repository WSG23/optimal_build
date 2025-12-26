import importlib
import os
from types import SimpleNamespace

import pytest

# Ensure configuration can load during tests
os.environ.setdefault("SECRET_KEY", "test-secret-key")

import app.core.config as config  # noqa: E402
import app.core.database as database  # noqa: E402


def _reload_database(monkeypatch, *, uri: str = "sqlite+aiosqlite:///:memory:", threshold: float = 0.01):
    """Reload the database module with patched settings."""

    monkeypatch.setattr(config.settings, "SQLALCHEMY_DATABASE_URI", uri)
    monkeypatch.setattr(config.settings, "SLOW_QUERY_THRESHOLD_SECONDS", threshold)
    reloaded = importlib.reload(database)
    return reloaded


def test_sqlite_fallback_prefers_env_override(monkeypatch):
    monkeypatch.setenv("DEV_SQLITE_URL", "sqlite+aiosqlite:///override.db")
    assert database._sqlite_fallback_url() == "sqlite+aiosqlite:///override.db"


def test_sqlite_fallback_builds_repo_path(monkeypatch):
    monkeypatch.delenv("DEV_SQLITE_URL", raising=False)
    url = database._sqlite_fallback_url()
    assert url.startswith("sqlite+aiosqlite:///")
    assert url.endswith("/.devstack/app.db")


def test_resolve_database_url_falls_back_when_asyncpg_missing(monkeypatch):
    monkeypatch.setattr(
        database.settings,
        "SQLALCHEMY_DATABASE_URI",
        "postgresql+asyncpg://user:pass@localhost:5432/db",
    )
    monkeypatch.setattr(database, "_sqlite_fallback_url", lambda: "sqlite+aiosqlite:///fallback.db")
    monkeypatch.setattr(database, "find_spec", lambda _name: None)

    assert database._resolve_database_url() == "sqlite+aiosqlite:///fallback.db"


def test_resolve_database_url_returns_config_when_asyncpg_available(monkeypatch):
    uri = "postgresql+asyncpg://user:pass@localhost:5432/db"
    monkeypatch.setattr(database, "find_spec", lambda _name: object())
    monkeypatch.setattr(database.settings, "SQLALCHEMY_DATABASE_URI", uri)
    assert database._resolve_database_url() == uri

    sqlite_uri = "sqlite+aiosqlite:///:memory:"
    monkeypatch.setattr(database.settings, "SQLALCHEMY_DATABASE_URI", sqlite_uri)
    assert database._resolve_database_url() == sqlite_uri


@pytest.mark.anyio
async def test_slow_query_hooks_log_and_close_session(monkeypatch, caplog):
    db_module = _reload_database(
        monkeypatch,
        uri="sqlite+aiosqlite:///:memory:",
        threshold=0.0001,
    )
    caplog.set_level("WARNING")

    context = SimpleNamespace()
    db_module._before_cursor_execute(
        None, None, "SELECT 1", (), context, False
    )
    start_time = context._query_start_time
    monkeypatch.setattr(
        db_module.time, "perf_counter", lambda: start_time + db_module._SLOW_QUERY_THRESHOLD + 0.01
    )
    db_module._after_cursor_execute(
        None, None, "SELECT 1", (), context, False
    )
    db_module._after_cursor_execute(
        None, None, "SELECT 1", (), SimpleNamespace(), False
    )
    assert any("Slow query detected" in record.message for record in caplog.records)

    long_statement = "SELECT " + "x" * 600
    long_params = {"payload": "y" * 600}
    db_module._after_cursor_execute(
        None, None, long_statement, long_params, context, False
    )

    monkeypatch.setattr(db_module.time, "perf_counter", lambda: start_time)
    db_module._after_cursor_execute(
        None, None, "SELECT 1", (), context, False
    )

    gen = db_module.get_session()
    session = await gen.__anext__()
    assert session is not None
    await gen.aclose()
    await db_module.engine.dispose()

    # Restore module state for subsequent tests
    monkeypatch.setattr(config.settings, "SLOW_QUERY_THRESHOLD_SECONDS", 0.0)
    monkeypatch.setattr(config.settings, "SQLALCHEMY_DATABASE_URI", "sqlite+aiosqlite:///:memory:")
    importlib.reload(database)
