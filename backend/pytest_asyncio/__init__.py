"""Minimal stub of :mod:`pytest_asyncio` for asynchronous test support."""

from __future__ import annotations

import pytest
import _pytest.config
import _pytest.fixtures
import _pytest.python

from . import plugin as _plugin

pytest_plugins = ["pytest_asyncio.plugin"]


def fixture(*args, **kwargs):  # type: ignore[override]
    """Proxy to :func:`pytest.fixture` used by async fixtures."""

    return pytest.fixture(*args, **kwargs)


def _install_hooks() -> None:
    try:
        config = _pytest.config.get_config()
    except Exception:  # pragma: no cover - fallback when config unavailable
        config = None
    if config is not None:
        try:
            _plugin.pytest_configure(config)
        except Exception:  # pragma: no cover - defensive
            pass

    original_runtest = _pytest.python.Function.runtest

    def _patched_runtest(self: _pytest.python.Function) -> None:
        handled = _plugin.pytest_pyfunc_call(self)
        if handled:
            return
        return original_runtest(self)

    _pytest.python.Function.runtest = _patched_runtest  # type: ignore[assignment]

    original_execute = _pytest.fixtures.FixtureDef.execute

    def _patched_execute(self, request):
        outcome = _plugin.pytest_fixture_setup(self, request)
        if outcome is not None:
            return outcome
        return original_execute(self, request)

    _pytest.fixtures.FixtureDef.execute = _patched_execute  # type: ignore[assignment]


_install_hooks()


__all__ = ["fixture", "pytest_plugins"]
