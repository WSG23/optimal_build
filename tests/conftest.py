"""Shared fixtures for reference tests."""

from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path
from types import ModuleType

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_ROOT = _PROJECT_ROOT / "backend"
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

try:  # pragma: no cover - optional dependency for async fixtures
    import pytest_asyncio
except ModuleNotFoundError:  # pragma: no cover - fallback stub when plugin missing
    pytest_asyncio = ModuleType("pytest_asyncio")
    pytest_asyncio.fixture = pytest.fixture  # type: ignore[attr-defined]
    sys.modules.setdefault("pytest_asyncio", pytest_asyncio)

import backend.tests.conftest  # noqa: F401 - ensure fallback stubs are registered

pytest_plugins = ["backend.tests.conftest"]

from app.core import database as app_database
from backend.scripts.seed_nonreg import seed_nonregulated_reference_data


@pytest_asyncio.fixture(autouse=True)
async def _override_app_database(async_session_factory, monkeypatch):
    """Ensure application session factories use the in-memory test database."""

    monkeypatch.setattr(app_database, "AsyncSessionLocal", async_session_factory, raising=False)

    sync_products = import_module("backend.flows.sync_products")
    monkeypatch.setattr(sync_products, "AsyncSessionLocal", async_session_factory, raising=False)
    yield


@pytest_asyncio.fixture
async def app_client(client, async_session_factory):
    """Seed reference data before returning the shared API client."""

    async with async_session_factory() as session:
        await seed_nonregulated_reference_data(session, commit=True)
    yield client
