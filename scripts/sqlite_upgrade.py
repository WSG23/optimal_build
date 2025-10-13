"""Simple SQLite migration runner for offline environments."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _ensure_sqlite_directory(database_url: str) -> None:
    url = make_url(database_url)
    if url.drivername.startswith("sqlite"):
        database = url.database
        if database and database != ":memory:":
            Path(database).parent.mkdir(parents=True, exist_ok=True)


async def apply_migrations(database_url: str) -> None:
    _ensure_sqlite_directory(database_url)
    engine = create_async_engine(database_url)
    try:
        import backend.app.models.audit  # noqa: F401
        import backend.app.models.developer_checklists  # noqa: F401
        import backend.app.models.entitlements  # noqa: F401
        import backend.app.models.finance  # noqa: F401
        import backend.app.models.imports  # noqa: F401
        import backend.app.models.overlay  # noqa: F401
        import backend.app.models.rkp  # noqa: F401
        import backend.app.models.rulesets  # noqa: F401
        from backend.app.models.base import Base
    except ImportError as exc:  # pragma: no cover - defensive
        raise SystemExit(f"Failed to import models: {exc}") from exc

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        fallback = os.environ.get("DEV_SQLITE_URL") or "sqlite+aiosqlite:///" + str(
            ROOT / ".devstack" / "app.db"
        )
        database_url = fallback
    asyncio.run(apply_migrations(database_url))


if __name__ == "__main__":
    main()
