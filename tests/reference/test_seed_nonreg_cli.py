"""Sanity checks for the seed_nonreg CLI entry point."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Dict

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.app.models.base import BaseModel
from backend.scripts import seed_nonreg


def _load_fixture_count(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    assert isinstance(payload, list)
    return len(payload)


def test_seed_nonreg_cli_summary(monkeypatch) -> None:
    """The CLI should report counts matching the JSON seed fixtures."""

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _initialise_schema() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.create_all)

    asyncio.run(_initialise_schema())

    monkeypatch.setattr(seed_nonreg, "AsyncSessionLocal", session_factory, raising=False)
    monkeypatch.setattr(seed_nonreg, "engine", engine, raising=False)

    summary = seed_nonreg.main([])

    expected: Dict[str, int] = {
        "ergonomics": _load_fixture_count(seed_nonreg.ERGONOMICS_SEED),
        "standards": _load_fixture_count(seed_nonreg.STANDARDS_SEED),
        "cost_indices": _load_fixture_count(seed_nonreg.COST_INDEX_SEED),
    }
    assert summary.as_dict() == expected

    asyncio.run(engine.dispose())
