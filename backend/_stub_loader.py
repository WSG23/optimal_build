"""Utility helpers for loading stub packages within the backend tests."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

_REPO_ROOT = Path(__file__).resolve().parents[1]


def load_package_stub(module_name: str, package: str, friendly_name: str) -> ModuleType:
    """Load a stub package from the repository root.

    Parameters
    ----------
    module_name:
        Fully qualified name that the stub should be loaded as.
    package:
        Directory name containing the stub package in the repository root.
    friendly_name:
        Human readable name used in error messages when the stub is absent.
    """

    stub_dir = _REPO_ROOT / package
    stub_init = stub_dir / "__init__.py"
    if not stub_init.exists():
        raise ModuleNotFoundError(
            f"No module named '{package}' and {friendly_name} stub missing in repository root"
        )

    module = ModuleType(module_name)
    module.__file__ = str(stub_init)
    module.__path__ = [str(stub_dir)]
    module.__spec__ = None

    sys.modules[module_name] = module
    module.__dict__.setdefault("__builtins__", __builtins__)
    code = compile(stub_init.read_text(encoding="utf-8"), str(stub_init), "exec")
    exec(code, module.__dict__)
    return module


def load_module_from_path(module_name: str, path: Path) -> ModuleType:
    """Load a Python module from the provided filesystem path."""

    module = ModuleType(module_name)
    module.__file__ = str(path)
    sys.modules[module_name] = module
    module.__dict__.setdefault("__builtins__", __builtins__)
    code = compile(path.read_text(encoding="utf-8"), str(path), "exec")
    exec(code, module.__dict__)
    return module
