#!/usr/bin/env python3
"""
Check for shadow directories that hijack Python package imports.

This enforces CODING_RULES.md Rule 13.1: NEVER Create Shadow Directories

Shadow directories are local directories matching installed package names.
They break ALL imports by shadowing the real packages from site-packages.

This has caused multiple production-breaking incidents with Codex Cloud.
"""

import sys
from pathlib import Path

# Repository root
REPO_ROOT = Path(__file__).parent.parent

# Legitimate vendor shims (created Sep 21-23, 2025)
# These are intentional wrapper modules for offline/test environments
# DO NOT delete these - they serve an architectural purpose
LEGITIMATE_VENDOR_SHIMS = {
    "prefect",
    "httpx",
    "structlog",
    "pydantic",
}

LEGITIMATE_BACKEND_SHIMS = {
    "sqlalchemy",
    "prefect",
}

# Common Python packages that MUST NOT be shadowed
FORBIDDEN_SHADOW_NAMES = {
    "fastapi",
    "starlette",
    "pydantic",
    "sqlalchemy",
    "pytest",
    "pytest_cov",
    "celery",
    "redis",
    "alembic",
    "prefect",
    "httpx",
    "requests",
    "numpy",
    "pandas",
    "asyncpg",
    "psycopg2",
    "jose",
    "passlib",
    "bcrypt",
    "cryptography",
    "jwt",
    "structlog",
    "prometheus_client",
    "uvicorn",
    "gunicorn",
}


def check_shadow_directories():
    """
    Check for shadow directories in repository.

    Returns:
        List of error messages (empty if no violations)
    """
    errors = []

    # Check root level
    for name in FORBIDDEN_SHADOW_NAMES:
        # Skip legitimate vendor shims
        if name in LEGITIMATE_VENDOR_SHIMS:
            continue

        shadow_path = REPO_ROOT / name
        if shadow_path.is_dir():
            errors.append(
                f"❌ FORBIDDEN shadow directory: {name}/\n"
                f"   Location: {shadow_path}\n"
                f"   This hijacks imports and breaks the entire application!\n"
                f"   Fix: rm -rf {shadow_path}\n"
                f"   See CODING_RULES.md Rule 13.1"
            )

    # Check backend/ subdirectory
    backend_dir = REPO_ROOT / "backend"
    if backend_dir.is_dir():
        for name in FORBIDDEN_SHADOW_NAMES:
            # Skip legitimate backend shims
            if name in LEGITIMATE_BACKEND_SHIMS:
                continue

            shadow_path = backend_dir / name
            if shadow_path.is_dir():
                errors.append(
                    f"❌ FORBIDDEN shadow directory: backend/{name}/\n"
                    f"   Location: {shadow_path}\n"
                    f"   This hijacks imports and breaks the entire application!\n"
                    f"   Fix: rm -rf {shadow_path}\n"
                    f"   See CODING_RULES.md Rule 13.1"
                )

    # Check for shadow backup directories (also forbidden)
    for pattern in ["*_shadow_*", "*_stub_*", "pytest_cov_backup"]:
        for shadow_path in REPO_ROOT.glob(pattern):
            if shadow_path.is_dir():
                errors.append(
                    f"❌ FORBIDDEN shadow backup directory: {shadow_path.name}/\n"
                    f"   Location: {shadow_path}\n"
                    f"   These are remnants of shadow directory attempts.\n"
                    f"   Fix: rm -rf {shadow_path}\n"
                    f"   See CODING_RULES.md Rule 13.1"
                )

    return errors


def main():
    """Run shadow directory check."""
    print("Checking for shadow directories (Rule 13.1)...")

    errors = check_shadow_directories()

    if errors:
        print("\n🚨 SHADOW DIRECTORY VIOLATIONS DETECTED:\n")
        for error in errors:
            print(error)
            print()

        print("=" * 70)
        print("CODING_RULES.md Rule 13.1: NEVER Create Shadow Directories")
        print("=" * 70)
        print()
        print("Shadow directories hijack Python's import system and break the app.")
        print("Codex Cloud has repeatedly created these, causing production failures.")
        print()
        print("If you encounter import errors, the CORRECT fixes are:")
        print("  1. Set PYTHONPATH correctly")
        print("  2. Use absolute imports in code")
        print("  3. Fix sys.path in conftest.py")
        print()
        print(
            "❌ NEVER create directories matching package names from requirements.txt"
        )
        print()
        print("See CODING_RULES.md Rule 13.1 for full details.")
        print("=" * 70)

        sys.exit(1)

    print("✅ No shadow directories detected")
    sys.exit(0)


if __name__ == "__main__":
    main()
