"""Lightweight fixture overrides for middleware-specific tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest


@pytest.fixture(scope="session")
async def flow_session_factory() -> AsyncGenerator[None, None]:
    """Provide a no-op session factory to bypass global database setup."""

    yield None


@pytest.fixture(autouse=True)
async def _cleanup_flow_session_factory() -> AsyncGenerator[None, None]:
    """Skip automatic database cleanup for middleware-only tests."""

    yield
