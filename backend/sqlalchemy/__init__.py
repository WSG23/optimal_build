"""Bridge module exposing the project-level SQLAlchemy stub."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

_package = __name__.split(".", 1)[-1]
_current_file = Path(__file__).resolve()
_root = _current_file.parents[2]
_target_dir = _root / _package
_target_file = _target_dir / "__init__.py"


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


_module = sys.modules.get(_package)
if _needs_reload(_module):
    _spec = importlib.util.spec_from_file_location(
        _package,
        _target_file,
        submodule_search_locations=[str(_target_dir)],
    )
    if _spec is None or _spec.loader is None:
        raise ImportError(
            f"Unable to load stub package '{_package}' from {_target_file}"
        )
    _module = importlib.util.module_from_spec(_spec)
    sys.modules[_package] = _module
    sys.modules[__name__] = _module
    _spec.loader.exec_module(_module)  # type: ignore[arg-type]

sys.modules[__name__] = _module
