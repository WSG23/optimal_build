"""Compatibility wrapper for the bundled pytest-asyncio stub."""

from backend import pytest_asyncio as _pytest_asyncio

fixture = _pytest_asyncio.fixture
pytest_pyfunc_call = getattr(_pytest_asyncio, "pytest_pyfunc_call")
pytest_configure = getattr(_pytest_asyncio, "pytest_configure")

__all__ = getattr(_pytest_asyncio, "__all__", ["fixture"])
