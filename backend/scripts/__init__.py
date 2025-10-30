"""Utility command modules for backend workflows."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.append(str(_BACKEND_ROOT))

_IMPORTS = {
    "SeedSummary": (".seed_screening", "SeedSummary"),
    "seed_screening_sample_data": (".seed_screening", "seed_screening_sample_data"),
    "NonRegSeedSummary": (".seed_nonreg", "NonRegSeedSummary"),
    "seed_nonregulated_reference_data": (".seed_nonreg", "seed_nonregulated_reference_data"),
    "FinanceDemoSummary": (".seed_finance_demo", "FinanceDemoSummary"),
    "seed_finance_demo": (".seed_finance_demo", "seed_finance_demo"),
    "ensure_finance_demo_schema": (".seed_finance_demo", "ensure_schema"),
}

__all__ = list(_IMPORTS.keys())


def __getattr__(name: str) -> Any:
    try:
        module_name, attribute = _IMPORTS[name]
    except KeyError as exc:  # pragma: no cover - defensive guard
        raise AttributeError(name) from exc

    module = importlib.import_module(f"{__name__}{module_name}")
    value = getattr(module, attribute)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(__all__ + [*globals().keys()])
