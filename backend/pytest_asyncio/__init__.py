"""Minimal ``pytest_asyncio`` shim providing async fixtures and marks."""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from typing import Any, TypeVar

import _pytest.python
import pytest

from . import plugin as _plugin


def _install_pyfunc_patch() -> None:
    original_runtest = _pytest.python.Function.runtest

    def _patched_runtest(self: _pytest.python.Function) -> None:
        handled = _plugin.pytest_pyfunc_call(self)
        if handled:
            return
        return original_runtest(self)

    _pytest.python.Function.runtest = _patched_runtest  # type: ignore[assignment]


_install_pyfunc_patch()

pytest_plugins = ["pytest_asyncio.plugin"]

F = TypeVar("F", bound=Callable[..., Any])


def fixture(*decorator_args: Any, **decorator_kwargs: Any):  # type: ignore[override]
    """Wrap coroutine and async generator fixtures so pytest can consume them."""

    if (
        decorator_args
        and callable(decorator_args[0])
        and len(decorator_args) == 1
        and not decorator_kwargs
    ):
        func = decorator_args[0]
        return fixture()(func)  # type: ignore[misc]

    def _decorate(func: F) -> F:
        parameter_names = list(inspect.signature(func).parameters)

        request_signature = inspect.Signature(
            [inspect.Parameter("request", inspect.Parameter.POSITIONAL_OR_KEYWORD)]
        )

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            def _wrapped(request: pytest.FixtureRequest):
                loop = _plugin._ensure_loop(request)
                kwargs = {
                    name: request.getfixturevalue(name) for name in parameter_names
                }
                return loop.run_until_complete(func(**kwargs))

            _wrapped.__signature__ = request_signature  # type: ignore[attr-defined]
            return pytest.fixture(*decorator_args, **decorator_kwargs)(_wrapped)  # type: ignore[return-value]

        if inspect.isasyncgenfunction(func):

            @functools.wraps(func)
            def _generator(request: pytest.FixtureRequest):
                loop = _plugin._ensure_loop(request)
                kwargs = {
                    name: request.getfixturevalue(name) for name in parameter_names
                }
                agen = func(**kwargs)
                value = loop.run_until_complete(agen.__anext__())
                try:
                    yield value
                finally:
                    try:
                        loop.run_until_complete(agen.__anext__())
                    except StopAsyncIteration:
                        pass
                    loop.run_until_complete(agen.aclose())

            _generator.__signature__ = request_signature  # type: ignore[attr-defined]
            return pytest.fixture(*decorator_args, **decorator_kwargs)(_generator)  # type: ignore[return-value]

        return pytest.fixture(*decorator_args, **decorator_kwargs)(func)  # type: ignore[return-value]

    return _decorate


__all__ = ["fixture", "pytest_plugins"]


def pytest_configure(config: pytest.Config) -> None:  # pragma: no cover - pytest hook
    if not config.pluginmanager.has_plugin("pytest_asyncio_stub"):
        config.pluginmanager.register(_plugin, "pytest_asyncio_stub")
    _plugin.pytest_configure(config)


def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool | None:  # pragma: no cover
    return _plugin.pytest_pyfunc_call(pyfuncitem)
