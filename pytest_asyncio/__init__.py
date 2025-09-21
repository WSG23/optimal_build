"""Lightweight fallback implementation of ``pytest-asyncio``.

This stub provides enough functionality for the test-suite to run in
restricted environments where installing external packages is not
possible.  It exposes a ``fixture`` decorator compatible with
``pytest_asyncio.fixture`` and registers a plugin that knows how to run
``async def`` tests using a shared event loop.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable

from . import plugin

pytest_plugins = ["pytest_asyncio.plugin"]

_FixtureFunc = Callable[..., Any]


def _wrap_async_fixture(func: _FixtureFunc, args: Iterable[Any], kwargs: dict[str, Any]):
    return plugin.wrap_async_fixture(func, tuple(args), dict(kwargs))


def fixture(*args: Any, **kwargs: Any):
    """Replacement for :func:`pytest_asyncio.fixture`.

    The decorator mirrors ``pytest.fixture`` and transparently converts
    ``async def`` fixtures into synchronous ones executed on the shared
    event loop managed by :mod:`pytest_asyncio.plugin`.
    """

    if args and callable(args[0]):
        func = args[0]
        return _wrap_async_fixture(func, (), {})

    def decorator(func: _FixtureFunc) -> Any:
        return _wrap_async_fixture(func, args, kwargs)

    return decorator


__all__ = ["fixture"]
