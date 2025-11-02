"""Bridge module exposing the project-level Starlette stub or real package."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from backend._stub_loader import import_runtime_dependency

_package = __name__.split(".", 1)[-1]
_current_file = Path(__file__).resolve()
_root = _current_file.parents[2]
_target_dir = _root / _package
_target_file = _target_dir / "__init__.py"
_REQUIRED_SUBMODULES = ("routing",)


def _needs_reload(module: ModuleType | None) -> bool:
    if module is None:
        return True
    module_file = getattr(module, "__file__", None)
    if module_file is None:
        return True
    try:
        return Path(module_file).resolve() == _current_file
    except OSError:
        return True


def _remove_cached_stub() -> None:
    prefix = f"{_package}."
    for name in list(sys.modules):
        if name == _package or name.startswith(prefix):
            sys.modules.pop(name, None)


def _load_stub() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        _package,
        _target_file,
        submodule_search_locations=[str(_target_dir)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load stub package '{_package}' from {_target_file}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_package] = module
    sys.modules[__name__] = module
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    return module


def _load_runtime() -> ModuleType:
    module = import_runtime_dependency("starlette", "Starlette")
    sys.modules[__name__] = module
    return module


def _validate_stub(module: ModuleType) -> bool:
    try:
        for submodule in _REQUIRED_SUBMODULES:
            importlib.import_module(f"{_package}.{submodule}")
    except ModuleNotFoundError:
        return False
    return True


_module = sys.modules.get(_package)
if _needs_reload(_module):
    try:
        candidate = _load_stub()
        if not _validate_stub(candidate):
            raise ModuleNotFoundError(_package)
        _module = candidate
    except (ImportError, ModuleNotFoundError):
        _remove_cached_stub()
        _module = _load_runtime()

sys.modules[__name__] = _module
