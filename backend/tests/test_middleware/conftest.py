"""Lightweight fixture overrides for middleware-specific tests."""

from __future__ import annotations

import pytest


@pytest.fixture()
def flow_session_factory() -> None:
    """Provide a no-op session factory to bypass global database setup."""
    return None


@pytest.fixture(autouse=True)
def _cleanup_flow_session_factory() -> None:
    """Skip automatic database cleanup for middleware-only tests."""
    return None
