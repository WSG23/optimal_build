"""CLI wrapper for seeding finance demo data from the repository root."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"

# Ensure imports like ``app.models`` resolve when the script is executed directly.
for candidate in (REPO_ROOT, BACKEND_DIR):
    candidate_path = str(candidate)
    if candidate_path not in sys.path:
        sys.path.insert(0, candidate_path)

# After adjusting sys.path we can import the backend module safely.
from backend.scripts.seed_finance_demo import main as backend_main


def main(argv: list[str] | None = None) -> None:
    """Delegate execution to :mod:`backend.scripts.seed_finance_demo`."""

    backend_main(argv)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
