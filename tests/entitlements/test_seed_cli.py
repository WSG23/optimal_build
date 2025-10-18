"""CLI coverage for the entitlement seed script."""

from __future__ import annotations

import asyncio

import pytest

pytest.importorskip("sqlalchemy")

from backend.scripts import seed_entitlements_sg as script
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

PROJECT_ID = 90301


def test_seed_cli_main_executes(monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI entry point should run to completion using the test database."""

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    monkeypatch.setattr(script, "engine", engine)
    monkeypatch.setattr(script, "AsyncSessionLocal", session_factory)

    try:
        summary = script.main(["--project-id", str(PROJECT_ID)])
    finally:
        asyncio.run(engine.dispose())

    assert summary.authorities > 0
    assert summary.roadmap_items > 0
