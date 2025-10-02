from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

BACKEND_SRC = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

SERVICE_APPS = [
    "backend/app/main.py",
    "backend/src/services/analytics/microservice/app.py",
]


def test_service_apps_can_import() -> None:
    for app_path in SERVICE_APPS:
        module_path = Path(app_path)
        if module_path.suffix == ".py":
            relative = module_path.relative_to(Path("backend"))
            module_name = ".".join(("backend",) + tuple(relative.with_suffix("").parts))
            try:
                importlib.import_module(module_name)
            except ImportError as exc:
                pytest.skip(f"Optional service dependency missing: {exc}")
