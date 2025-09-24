"""Verify key imports are available."""

from __future__ import annotations

import importlib.util as import_util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MODULES = [
    "backend.app.main",
    "backend.app.core.database",
    "backend.app.models.base",
]

for module in MODULES:
    print(module, "=>", bool(import_util.find_spec(module)))
