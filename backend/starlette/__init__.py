"""Expose Starlette via a bundled stub when available, fall back to the real package."""

from __future__ import annotations

from types import ModuleType

import sys

from backend._stub_loader import load_optional_package


def _load_module() -> ModuleType:
    return load_optional_package(
        __name__,
        "starlette",
        "Starlette",
    )


_starlette = _load_module()
globals().update(_starlette.__dict__)
sys.modules[__name__] = _starlette
