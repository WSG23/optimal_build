"""CLI entry point for the Singapore entitlement seeder."""

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
from backend.scripts.seed_entitlements_sg import main as backend_main


def main(argv: list[str] | None = None) -> None:
    """Proxy execution to the backend seeder module."""

    backend_main(argv)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
