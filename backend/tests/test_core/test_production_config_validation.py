from __future__ import annotations

import pytest

from app.core.config import Settings


def test_production_requires_backend_allowed_origins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("BACKEND_ALLOWED_ORIGINS", raising=False)
    monkeypatch.setenv(
        "SQLALCHEMY_DATABASE_URI", "postgresql+asyncpg://user:pass@db:5432/app"
    )

    with pytest.raises(RuntimeError, match="BACKEND_ALLOWED_ORIGINS must be set"):
        Settings(validate_production=True)


def test_production_requires_database_uri(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("BACKEND_ALLOWED_ORIGINS", '["https://example.run.app"]')
    monkeypatch.delenv("SQLALCHEMY_DATABASE_URI", raising=False)

    with pytest.raises(RuntimeError, match="SQLALCHEMY_DATABASE_URI must be set"):
        Settings(validate_production=True)
