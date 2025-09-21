"""Minimal pytest plugin that emulates the behaviour of ``pytest-asyncio``.

The real project offers a rich integration with pytest.  This module
only implements the tiny subset that the test-suite relies on: running
``async def`` tests marked with ``@pytest.mark.asyncio`` and supporting
``async`` fixtures via :func:`pytest_asyncio.fixture`.
"""
from __future__ import annotations

import asyncio
import inspect
from collections.abc import Callable, Generator, Iterable
from functools import wraps
from typing import Any, Awaitable, TypeVar

import pytest

_T = TypeVar("_T")
_EventLoop = asyncio.AbstractEventLoop

_EVENT_LOOP: _EventLoop | None = None


def _ensure_event_loop() -> _EventLoop:
    """Return the shared event loop, creating it on first use."""

    global _EVENT_LOOP
    loop = _EVENT_LOOP
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        _EVENT_LOOP = loop
    return loop


def _close_event_loop() -> None:
    """Cleanly shut down the shared event loop."""

    global _EVENT_LOOP
    loop = _EVENT_LOOP
    if loop is None:
        return
    if loop.is_closed():
        _EVENT_LOOP = None
        return
    try:
        loop.run_until_complete(loop.shutdown_asyncgens())
    except (RuntimeError, AttributeError):
        pass
    try:
        loop.run_until_complete(loop.shutdown_default_executor())
    except (RuntimeError, AttributeError):
        pass
    loop.close()
    _EVENT_LOOP = None


def _run(coro: Awaitable[_T]) -> _T:
    loop = _ensure_event_loop()
    return loop.run_until_complete(coro)


def wrap_async_fixture(
    func: Callable[..., Any],
    args: Iterable[Any],
    kwargs: dict[str, Any],
) -> Any:
    """Wrap an async fixture so pytest can execute it synchronously."""

    if inspect.isasyncgenfunction(func):
        async_gen = func

        @wraps(async_gen)
        @pytest.fixture(*args, **kwargs)
        def wrapper(*fargs: Any, **fkwargs: Any) -> Generator[Any, None, None]:
            loop = _ensure_event_loop()
            agen = async_gen(*fargs, **fkwargs)
            value = loop.run_until_complete(agen.__anext__())
            try:
                yield value
            finally:
                try:
                    loop.run_until_complete(agen.aclose())
                except RuntimeError:
                    pass

        return wrapper

    if inspect.iscoroutinefunction(func):
        async_func = func

        @wraps(async_func)
        @pytest.fixture(*args, **kwargs)
        def wrapper(*fargs: Any, **fkwargs: Any) -> Any:
            return _run(async_func(*fargs, **fkwargs))

        return wrapper

    return pytest.fixture(*args, **kwargs)(func)


def pytest_configure(config: pytest.Config) -> None:  # pragma: no cover - pytest hook
    config.addinivalue_line(
        "markers",
        "asyncio: run the marked test inside an asyncio event loop",
    )


def pytest_unconfigure(config: pytest.Config) -> None:  # pragma: no cover - pytest hook
    _close_event_loop()


def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool | None:  # pragma: no cover - pytest hook
    test_function = pyfuncitem.obj
    marker = pyfuncitem.get_closest_marker("asyncio")
    if marker is None and not inspect.iscoroutinefunction(test_function):
        return None

    loop = _ensure_event_loop()
    coroutine = test_function(**pyfuncitem.funcargs)
    loop.run_until_complete(coroutine)
    return True


__all__ = ["wrap_async_fixture"]
