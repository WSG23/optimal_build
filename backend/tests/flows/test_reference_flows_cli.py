"""Compat wrapper for relocated flow tests."""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from types import ModuleType
from typing import Any, cast


def _find_repo_root(current: Path) -> Path:
    for parent in current.parents:
        if (parent / ".git").exists():
            return parent
    return current.parents[-1]


def _load_module(name: str, file_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {name!r} from {file_path}")
    module = importlib.util.module_from_spec(spec)
    loader = cast(Any, spec.loader)
    loader.exec_module(module)
    sys.modules[name] = module
    return module


ROOT = _find_repo_root(Path(__file__).resolve())
MODULE_NAME = "tests.flows.test_reference_flows_cli"
MODULE_PATH = ROOT / "tests" / "flows" / "test_reference_flows_cli.py"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_IMPL = _load_module(MODULE_NAME, MODULE_PATH)


def _mirror(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def _wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    return _wrapper


for _name in dir(_IMPL):
    if _name.startswith("test_"):
        globals()[_name] = _mirror(getattr(_IMPL, _name))

__all__ = [name for name in globals() if name.startswith("test_")]
