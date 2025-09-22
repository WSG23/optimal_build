"""Delegate to the repository-level Pydantic stub when running backend tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_stub() -> ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    stub_init = repo_root / "pydantic" / "__init__.py"
    if not stub_init.exists():
        raise ModuleNotFoundError(
            "No module named 'pydantic' and Pydantic stub missing in repository root"
        )

    spec = importlib.util.spec_from_file_location(
        __name__,
        stub_init,
        submodule_search_locations=[str(stub_init.parent)],
    )
    if spec is None or spec.loader is None:
        raise ModuleNotFoundError("Unable to load Pydantic stub module")

    module = importlib.util.module_from_spec(spec)
    sys.modules[__name__] = module
    spec.loader.exec_module(module)
    return module


globals().update(_load_stub().__dict__)
