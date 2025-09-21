"""Lightweight pytest_asyncio stub for offline testing."""

from __future__ import annotations

import asyncio
import contextvars
import inspect
from typing import Any, Callable

import pytest

__all__ = [
    "fixture",
    "pytest_asyncio",
    "_ASYNC_FIXTURE_MARKER",
    "_ensure_loop",
    "_consume_async_fixture",
]

_ASYNC_FIXTURE_MARKER = "_pytest_asyncio_is_async_fixture"
_CURRENT_LOOP: contextvars.ContextVar[asyncio.AbstractEventLoop | None] = (
    contextvars.ContextVar("pytest_asyncio_current_loop", default=None)
)


class _AsyncioStub:
    """Minimal stub of :mod:`pytest_asyncio` for offline test execution."""

    @staticmethod
    def fixture(
        func: Callable[..., Any] | None = None, *dargs: Any, **dkwargs: Any
    ) -> Callable[..., Any]:
        def _apply(target: Callable[..., Any]) -> Callable[..., Any]:
            setattr(target, _ASYNC_FIXTURE_MARKER, True)
            return pytest.fixture(*dargs, **dkwargs)(target)

        if func is not None and callable(func) and not dargs and not dkwargs:
            return _apply(func)

        def decorator(target: Callable[..., Any]) -> Callable[..., Any]:
            return _apply(target)

        if func is not None and callable(func):
            return decorator(func)

        return decorator


def _ensure_loop(request: pytest.FixtureRequest) -> asyncio.AbstractEventLoop:
    try:
        loop = request.getfixturevalue("event_loop")
        created = False
    except pytest.FixtureLookupError:
        loop = _CURRENT_LOOP.get()
        created = False
        if loop is None:
            loop = asyncio.new_event_loop()
            created = True
    asyncio.set_event_loop(loop)
    if created:
        request.addfinalizer(loop.close)
    return loop


def _finish_async_gen(async_gen: Any, loop: asyncio.AbstractEventLoop) -> None:
    try:
        loop.run_until_complete(async_gen.aclose())
    except RuntimeError:
        pass


def _consume_async_fixture(
    func: Callable[..., Any], request: pytest.FixtureRequest, kwargs: dict[str, Any]
) -> Any:
    loop = _ensure_loop(request)
    token = _CURRENT_LOOP.set(loop)
    try:
        result = func(**kwargs)
        if inspect.iscoroutine(result):
            return loop.run_until_complete(result)
        if inspect.isasyncgen(result):
            async_gen = result
            try:
                value = loop.run_until_complete(async_gen.__anext__())
            except StopAsyncIteration as exc:  # pragma: no cover - defensive
                raise RuntimeError(
                    f"Async fixture {request.fixturename} did not yield a value"
                ) from exc

            def _finalizer() -> None:
                _finish_async_gen(async_gen, loop)

            request.addfinalizer(_finalizer)
            return value
        return result
    finally:
        _CURRENT_LOOP.reset(token)


pytest_asyncio = _AsyncioStub()
fixture = _AsyncioStub.fixture
