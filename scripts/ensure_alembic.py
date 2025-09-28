"""Ensure Alembic is available before running migrations."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_REQUIREMENTS = _REPO_ROOT / "backend" / "requirements.txt"


def _module_exists(name: str) -> bool:
    try:
        __import__(name)
    except ModuleNotFoundError:
        return False
    except ImportError:
        return False
    return True


def _print_error(lines: Iterable[str]) -> None:
    for line in lines:
        print(line, file=sys.stderr, flush=True)


def _in_virtualenv() -> bool:
    if sys.prefix != getattr(sys, "base_prefix", sys.prefix):
        return True

    real_prefix = getattr(sys, "real_prefix", None)
    if real_prefix and real_prefix != sys.prefix:
        return True

    if os.environ.get("VIRTUAL_ENV") or os.environ.get("CONDA_PREFIX"):
        return True

    return False


def _safe_to_install() -> bool:
    """Return ``True`` when it's safe to install requirements automatically."""

    if os.environ.get("PIP_REQUIRE_VIRTUALENV"):
        return False

    if _in_virtualenv():
        return True

    if os.environ.get("CI"):
        return True

    return False


def _install_requirements(requirements: Path) -> None:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", str(requirements)]
    )


def ensure_alembic(requirements: Path | None = None) -> None:
    """Install or prompt for Alembic when it's missing."""

    if _module_exists("alembic"):
        return

    requirements_path = Path(requirements) if requirements else _DEFAULT_REQUIREMENTS

    if not requirements_path.exists():
        _print_error(
            [
                f"Error: requirements file not found at '{requirements_path}'.",
                "Install backend dependencies manually before rerunning 'make db.upgrade'.",
            ]
        )
        raise SystemExit(1)

    try:
        requirement_display = requirements_path.relative_to(_REPO_ROOT)
    except ValueError:
        requirement_display = requirements_path

    if _safe_to_install():
        print(
            f"Alembic not found; installing backend dependencies ({requirement_display}).",
            flush=True,
        )
        try:
            _install_requirements(requirements_path)
        except subprocess.CalledProcessError as exc:
            _print_error(
                [
                    "Failed to install backend requirements automatically.",
                    f"Run 'pip install -r {requirement_display}' and rerun 'make db.upgrade'.",
                ]
            )
            raise SystemExit(exc.returncode) from exc

        if not _module_exists("alembic"):
            _print_error(
                [
                    "Alembic is still unavailable after installing backend requirements.",
                    f"Verify that '{requirement_display}' pins Alembic and reinstall manually.",
                ]
            )
            raise SystemExit(1)
        return

    _print_error(
        [
            "Error: Alembic is not installed.",
            (
                "Install backend dependencies with "
                f"'pip install -r {requirement_display}' before rerunning."
            ),
            "If you prefer an isolated environment:",
            "  python -m venv .venv",
            "  source .venv/bin/activate  # (use .venv\\Scripts\\activate on Windows)",
            f"  pip install -r {requirement_display}",
        ]
    )
    raise SystemExit(1)


if __name__ == "__main__":
    ensure_alembic()
