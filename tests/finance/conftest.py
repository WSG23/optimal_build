"""Finance test configuration hooks."""

from __future__ import annotations

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register async marker for local tests when pytest-asyncio is absent."""

    config.addinivalue_line("markers", "asyncio: mark tests as asynchronous")
