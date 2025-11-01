"""Backend package namespace for tests and application modules."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _ensure_repo_root_on_path() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


_ensure_repo_root_on_path()

# Expose the optional stub loader so callers importing ``backend`` retain the
# historical behaviour of ``backend.tests`` relying on it for namespace setup.
try:  # pragma: no cover - legacy compatibility path
    importlib.import_module("backend._stub_loader")
except ModuleNotFoundError:
    pass

