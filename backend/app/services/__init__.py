"""Service layer exports.

Each service module may depend on optional third-party packages. Importing all of
them eagerly can therefore fail in lightweight environments used for tests. To
make the package robust, modules are imported lazily and skipped if their
dependencies are unavailable. Consumers can still access available services via
``from app.services import products`` while missing services simply do not
appear in ``__all__``.
"""

from __future__ import annotations

from importlib import import_module
from typing import List

_SERVICE_MODULES = [
    "alerts",
    "buildable",
    "costs",
    "ingestion",
    "normalize",
    "overlay_ingest",
    "products",
    "pwp",
    "reference_parsers",
    "reference_sources",
    "reference_storage",
    "standards",
    "storage",
]

__all__: List[str] = []

for module_name in _SERVICE_MODULES:
    try:
        module = import_module(f"{__name__}.{module_name}")
    except ModuleNotFoundError:  # pragma: no cover - triggered when optional deps missing
        continue
    globals()[module_name] = module
    __all__.append(module_name)
