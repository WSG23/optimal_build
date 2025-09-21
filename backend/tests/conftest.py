"""Test configuration and shared fixtures."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from pathlib import Path
import sys

import pytest

try:
    import pytest_asyncio
except ModuleNotFoundError:  # pragma: no cover - fallback stub import
    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    import pytest_asyncio  # type: ignore  # noqa: F401

pytest_plugins = ("pytest_asyncio.plugin",)

from app.utils import metrics


@pytest.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def reset_metrics() -> Iterator[None]:
    metrics.reset_metrics()
    yield
    metrics.reset_metrics()
