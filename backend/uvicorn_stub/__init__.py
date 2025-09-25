"""Delegate to the repository-level Uvicorn stub when running backend tests."""

from __future__ import annotations

import sys
from types import ModuleType

from backend._stub_loader import load_package_stub


def _load_stub() -> ModuleType:
    module = load_package_stub(
        __name__,
        "uvicorn_app",
        "Uvicorn",
    )
    sys.modules.setdefault("uvicorn", module)
    return module


globals().update(_load_stub().__dict__)
