"""Pytest plugin implementing the subset of pytest-asyncio behaviour used in tests."""

from __future__ import annotations

import asyncio
import inspect
from typing import Any

import pytest


def pytest_configure(
    config: pytest.Config,
) -> None:  # pragma: no cover - configuration hook
    config.addinivalue_line("markers", "asyncio: mark test as running in an event loop")


def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool | None:
    testfunction = pyfuncitem.obj
    if inspect.iscoroutinefunction(testfunction):
        loop = pyfuncitem.funcargs.get("event_loop")
        cleanup_loop = False
        if loop is None:
            loop = asyncio.new_event_loop()
            cleanup_loop = True
        try:
            signature = inspect.signature(testfunction)
            kwargs = {
                name: pyfuncitem.funcargs[name]
                for name in signature.parameters
                if name in pyfuncitem.funcargs
            }
            loop.run_until_complete(testfunction(**kwargs))
        finally:
            if cleanup_loop:
                loop.close()
        return True
    return None


def _ensure_loop(request: pytest.FixtureRequest) -> asyncio.AbstractEventLoop:
    if "event_loop" in request.fixturenames:
        loop = request.getfixturevalue("event_loop")
        if loop is not None:
            return loop
    loop = asyncio.new_event_loop()
    request.addfinalizer(loop.close)
    return loop


def pytest_fixture_setup(
    fixturedef: pytest.FixtureDef[Any], request: pytest.FixtureRequest
) -> Any:
    func = fixturedef.func
    if inspect.iscoroutinefunction(func):
        loop = _ensure_loop(request)
        kwargs = {name: request.getfixturevalue(name) for name in fixturedef.argnames}
        return loop.run_until_complete(func(**kwargs))
    if inspect.isasyncgenfunction(func):
        loop = _ensure_loop(request)
        kwargs = {name: request.getfixturevalue(name) for name in fixturedef.argnames}
        agen = func(**kwargs)
        value = loop.run_until_complete(agen.__anext__())

        def _finalizer() -> None:
            try:
                loop.run_until_complete(agen.__anext__())
            except StopAsyncIteration:
                pass
            loop.run_until_complete(agen.aclose())

        request.addfinalizer(_finalizer)
        return value
    return None
