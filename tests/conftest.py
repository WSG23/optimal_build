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

from backend.tests import conftest as backend_conftest  # noqa: F401 - ensure fallback stubs are registered

pytest_plugins = ["backend.tests.conftest"]

# Re-export backend fixtures in this namespace for pytest discovery.
flow_session_factory = backend_conftest.flow_session_factory
async_session_factory = backend_conftest.async_session_factory
session = backend_conftest.session
session_factory = backend_conftest.session_factory
reset_metrics = backend_conftest.reset_metrics
app_client = backend_conftest.app_client
client = backend_conftest.client_fixture

from backend.app.core import database as app_database
from backend.scripts.seed_nonreg import seed_nonregulated_reference_data


def pytest_configure(config: pytest.Config) -> None:
    """Register project-specific markers to silence pytest warnings."""

    config.addinivalue_line(
        "markers", "asyncio: mark test as requiring asyncio event loop support"
    )


@pytest_asyncio.fixture(autouse=True)
async def _override_app_database(async_session_factory, monkeypatch):
    """Ensure application session factories use the in-memory test database."""

    monkeypatch.setattr(app_database, "AsyncSessionLocal", async_session_factory, raising=False)

    sync_products = import_module("backend.flows.sync_products")
    watch_fetch = import_module("backend.flows.watch_fetch")
    parse_segment = import_module("backend.flows.parse_segment")

    for module in (sync_products, watch_fetch, parse_segment):
        monkeypatch.setattr(module, "AsyncSessionLocal", async_session_factory, raising=False)
    yield


@pytest_asyncio.fixture
async def reference_data(async_session_factory):
    """Populate non-regulated reference data for tests that require it."""

    async with async_session_factory() as session:
        await seed_nonregulated_reference_data(session, commit=True)
