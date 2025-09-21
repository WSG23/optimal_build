"""A minimal pytest-asyncio shim for offline testing."""

from __future__ import annotations

import asyncio
import inspect
from typing import Any, Callable, TypeVar

import pytest

_F = TypeVar("_F", bound=Callable[..., Any])


def _ensure_loop() -> asyncio.AbstractEventLoop:
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def _wrap_fixture(func: Callable[..., Any], *args: Any, **kwargs: Any):
    if inspect.isasyncgenfunction(func):
        @pytest.fixture(*args, **kwargs)
        def wrapper(*fixture_args: Any, **fixture_kwargs: Any):
            loop = _ensure_loop()
            agen = func(*fixture_args, **fixture_kwargs)
            try:
                value = loop.run_until_complete(agen.__anext__())
                yield value
            finally:
                try:
                    loop.run_until_complete(agen.__anext__())
                except StopAsyncIteration:
                    pass
        return wrapper

    if inspect.iscoroutinefunction(func):
        @pytest.fixture(*args, **kwargs)
        def wrapper(*fixture_args: Any, **fixture_kwargs: Any):
            loop = _ensure_loop()
            return loop.run_until_complete(func(*fixture_args, **fixture_kwargs))
        return wrapper

    return pytest.fixture(*args, **kwargs)(func)


def fixture(*args: Any, **kwargs: Any):
    if args and callable(args[0]) and not kwargs:
        return _wrap_fixture(args[0])

    def decorator(func: _F) -> Any:
        return _wrap_fixture(func, *args, **kwargs)

    return decorator


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool | None:
    test_function = pyfuncitem.obj
    if inspect.iscoroutinefunction(test_function):
        loop = _ensure_loop()
        loop.run_until_complete(test_function(**pyfuncitem.funcargs))
        return True
    return None


def pytest_configure(config: pytest.Config) -> None:  # pragma: no cover - pytest hook
    config.addinivalue_line(
        "markers",
        "asyncio: mark the test as using the asyncio event loop",
    )


__all__ = ["fixture"]
