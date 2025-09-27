"""Utility helpers for loading stub packages within the backend tests."""

from __future__ import annotations

import sys
from importlib import machinery, util
from pathlib import Path
from types import ModuleType

_REPO_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_ROOT = _REPO_ROOT / "backend"


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


def _filter_runtime_search_paths() -> list[str]:
    """Return sys.path entries that are outside of the repository tree."""

    search_paths: list[str] = []
    for entry in sys.path:
        if entry in {"", "."}:
            continue
        try:
            resolved = Path(entry).resolve()
        except OSError:  # pragma: no cover - guard against malformed entries
            search_paths.append(entry)
            continue

        inside_repo = (
            resolved == _REPO_ROOT
            or resolved == _BACKEND_ROOT
            or _REPO_ROOT in resolved.parents
        )
        if inside_repo and not any(
            part in {"site-packages", "dist-packages"} for part in resolved.parts
        ):
            continue

        search_paths.append(str(resolved))
    return search_paths


def _load_runtime_distribution(package: str, friendly_name: str) -> ModuleType:
    """Import the real distribution for ``package`` outside of the repository."""

    search_paths = _filter_runtime_search_paths()
    spec = machinery.PathFinder.find_spec(package, search_paths)
    if spec is None or spec.loader is None:
        raise ModuleNotFoundError(
            f"No module named '{package}' and {friendly_name} distribution not installed"
        )

    module = util.module_from_spec(spec)
    # ``exec_module`` requires the module to be present in ``sys.modules`` beforehand.
    sys.modules[package] = module
    spec.loader.exec_module(module)
    return module


def load_optional_package(
    module_name: str, package: str, friendly_name: str
) -> ModuleType:
    """Load either the in-repo stub or the installed distribution.

    This allows test fixtures to run even when contributors rely on the real
    dependency instead of the lightweight stub version tracked in the repo.
    """

    try:
        return load_package_stub(module_name, package, friendly_name)
    except ModuleNotFoundError:
        module = _load_runtime_distribution(package, friendly_name)
        sys.modules[module_name] = module
        return module


def import_runtime_dependency(package: str, friendly_name: str) -> ModuleType:
    """Import a third-party dependency from the user's environment."""

    return _load_runtime_distribution(package, friendly_name)
