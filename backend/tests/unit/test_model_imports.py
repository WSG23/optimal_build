"""Tests ensuring model imports remain lightweight until explicitly loaded."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

pytestmark = [pytest.mark.no_db]


def _pythonpath() -> str:
    """Build a PYTHONPATH that resolves both ``app`` and ``backend.app`` imports."""

    repo_root = Path(__file__).resolve().parents[3]
    entries = [str(repo_root), str(repo_root / "backend")]
    existing = os.environ.get("PYTHONPATH")
    if existing:
        entries.append(existing)
    return os.pathsep.join(entries)


def test_model_submodule_import_stays_scoped_until_registry_load() -> None:
    """Importing one model module should not eagerly import unrelated ORM modules."""

    script = """
import importlib
import json
import sys

for name in (
    "app.models",
    "app.models.rkp",
    "app.models.toronto_property",
    "backend.app.models",
    "backend.app.models.rkp",
    "backend.app.models.toronto_property",
):
    sys.modules.pop(name, None)

rkp_module = importlib.import_module("app.models.rkp")
models_package = sys.modules["app.models"]

before = {
    "rkp_loaded": "app.models.rkp" in sys.modules,
    "toronto_loaded": "app.models.toronto_property" in sys.modules,
    "backend_toronto_loaded": "backend.app.models.toronto_property" in sys.modules,
}

models_package.load_model_modules()

after = {
    "toronto_loaded": "app.models.toronto_property" in sys.modules,
    "backend_toronto_loaded": "backend.app.models.toronto_property" in sys.modules,
}

print(
    json.dumps(
        {
            "has_ref_rule": hasattr(rkp_module, "RefRule"),
            "before": before,
            "after": after,
        }
    )
)
"""

    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        env={
            **os.environ,
            "PYTHONPATH": _pythonpath(),
            "SECRET_KEY": os.environ.get("SECRET_KEY", "test-secret"),
        },
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout.strip().splitlines()[-1])

    assert payload["has_ref_rule"] is True
    assert payload["before"] == {
        "rkp_loaded": True,
        "toronto_loaded": False,
        "backend_toronto_loaded": False,
    }
    assert payload["after"] == {
        "toronto_loaded": True,
        "backend_toronto_loaded": True,
    }
