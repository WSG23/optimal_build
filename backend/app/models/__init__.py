"""Model package exports."""

from __future__ import annotations

import sys
from types import ModuleType


def _counterpart(name: str) -> str | None:
    """Return the alternate import path for ``app``/``backend.app`` modules."""

    if name.startswith("backend."):
        return name.removeprefix("backend.")
    if name.startswith("app."):
        return f"backend.{name}"
    return None


_ALIAS = _counterpart(__name__)
if _ALIAS and _ALIAS in sys.modules:
    _existing: ModuleType = sys.modules[_ALIAS]
    globals().update(_existing.__dict__)
    sys.modules[__name__] = _existing
else:
    # Import model modules so their metadata is registered with SQLAlchemy.
    from . import (  # noqa: F401  pylint: disable=unused-import
        audit,
        entitlements,
        finance,
        imports,
        overlay,
        rkp,
        rulesets,
    )
    from .base import Base  # noqa: F401

    _SUBMODULES: dict[str, ModuleType] = {
        "audit": audit,
        "entitlements": entitlements,
        "finance": finance,
        "imports": imports,
        "overlay": overlay,
        "rkp": rkp,
        "rulesets": rulesets,
    }

    for _name, _module in _SUBMODULES.items():
        _module_alias = _counterpart(f"{__name__}.{_name}")
        if _module_alias and _module_alias not in sys.modules:
            sys.modules[_module_alias] = _module

    __all__ = ["Base"]

    if _ALIAS:
        sys.modules[_ALIAS] = sys.modules[__name__]
