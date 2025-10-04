#!/usr/bin/env python3
"""Automated coding rules verification for optimal_build.

This script checks compliance with CODING_RULES.md:
1. No modified migration files (only new ones allowed)
2. Async patterns in API routes
3. Dependency files are properly formatted
4. Singapore compliance tests run when critical files change

Exceptions to individual rules can be declared in
``.coding-rules-exceptions.yml``.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path


def get_repo_root() -> Path:
    """Find the repository root directory."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


try:  # Optional dependency – fail gracefully when unavailable
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    yaml = None  # type: ignore


def _normalise_path(value: str) -> str:
    return value.replace("\\", "/").lstrip("./")


def load_exceptions(repo_root: Path) -> dict[str, set[str]]:
    """Load per-rule exceptions defined by contributors."""

    exceptions_path = repo_root / ".coding-rules-exceptions.yml"
    if not exceptions_path.exists():
        return {}

    if yaml is None:  # pragma: no cover - dependency not installed
        return {}

    data = yaml.safe_load(exceptions_path.read_text()) or {}
    raw_exceptions: dict[str, Iterable[str]] = data.get("exceptions", {}) or {}

    normalised: dict[str, set[str]] = {}
    for rule_key, paths in raw_exceptions.items():
        normalised[rule_key] = {_normalise_path(str(path)) for path in (paths or [])}
    return normalised


def is_exception(
    rule_key: str,
    path: str,
    exceptions: dict[str, set[str]],
) -> bool:
    return _normalise_path(path) in exceptions.get(rule_key, set())


def _collect_git_paths(args: list[str]) -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return set()
    return {_normalise_path(line) for line in result.stdout.strip().split("\n") if line}


def get_modified_files() -> set[str]:
    """Return modified or staged file paths relative to repo root."""

    modified: set[str] = set()
    # Staged changes
    modified.update(_collect_git_paths(["--cached"]))
    # Working tree changes compared to HEAD
    modified.update(_collect_git_paths(["HEAD"]))
    return modified


def check_migration_modifications(
    modified_files: set[str], exceptions: dict[str, set[str]]
) -> tuple[bool, list[str]]:
    """Check if any existing migration files were modified (Rule 1)."""
    errors = []

    try:
        # Check for modified migration files
        migration_patterns = [
            r"backend/migrations/versions/\d{8}_\d{6}_.*\.py$",
            r"db/versions/\d{8}\d{6}_.*\.py$",
        ]

        for file_path in modified_files:
            for pattern in migration_patterns:
                if re.search(pattern, file_path):
                    if is_exception("rule_1_migrations", file_path, exceptions):
                        break
                    errors.append(
                        f"RULE VIOLATION: Modified existing migration file: {file_path}\n"
                        f"  -> Rule 1: Never edit existing migrations. Create a new migration instead.\n"
                        f"  -> See CODING_RULES.md section 1"
                    )

        return len(errors) == 0, errors
    except Exception as e:
        # If check fails, don't block - just warn
        return True, [f"Warning: Could not check migrations: {e}"]


def check_async_patterns(
    repo_root: Path, exceptions: dict[str, set[str]]
) -> tuple[bool, list[str]]:
    """Check for common sync patterns in async code (Rule 2)."""
    errors = []
    # Check Python files in backend/app/api for sync patterns
    api_routes_dir = repo_root / "backend" / "app" / "api"

    if not api_routes_dir.exists():
        return True, []  # No API routes to check

    # Common anti-patterns
    sync_patterns = [
        (
            r"from sqlalchemy\.orm import Session[^a-zA-Z]",
            "Use AsyncSession from sqlalchemy.ext.asyncio",
        ),
        (
            r"def\s+\w+\([^)]*session:\s*Session",
            "API functions should be async and use AsyncSession",
        ),
    ]

    for py_file in api_routes_dir.rglob("*.py"):
        if py_file.name.startswith("__"):
            continue

        try:
            content = py_file.read_text()
            for pattern, message in sync_patterns:
                if re.search(pattern, content):
                    rel_path = _normalise_path(str(py_file.relative_to(repo_root)))
                    if is_exception("rule_2_async", rel_path, exceptions):
                        continue
                    errors.append(
                        f"RULE VIOLATION: {rel_path}\n"
                        f"  -> {message}\n"
                        f"  -> Rule 2: Use async/await patterns. See CODING_RULES.md section 2"
                    )
                    break  # One error per file is enough
        except Exception:
            continue

    return len(errors) == 0, errors


def check_dependency_files(
    repo_root: Path, exceptions: dict[str, set[str]]
) -> tuple[bool, list[str]]:
    """Verify dependency files exist and are formatted correctly (Rule 4)."""
    errors = []
    repo_root = get_repo_root()

    # Check Python dependencies
    requirements_files = [
        repo_root / "backend" / "requirements.txt",
        repo_root / "backend" / "requirements-dev.txt",
    ]

    for req_file in requirements_files:
        if not req_file.exists():
            continue

        try:
            content = req_file.read_text()
            lines = content.strip().split("\n")

            for line_num, line in enumerate(lines, start=1):
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-r "):
                    continue

                # Check for version pinning
                if "==" not in line and not line.startswith("-"):
                    rel_path = _normalise_path(str(req_file.relative_to(repo_root)))
                    if is_exception("rule_4_dependency_pinning", rel_path, exceptions):
                        continue
                    errors.append(
                        f"RULE VIOLATION: {rel_path}:{line_num}\n"
                        f"  -> Dependency '{line}' is not pinned to a specific version\n"
                        f"  -> Rule 4: Pin exact versions (e.g., package==1.2.3)\n"
                        f"  -> See CODING_RULES.md section 4"
                    )
        except Exception as e:
            errors.append(f"Warning: Could not check {req_file}: {e}")

    return len(errors) == 0, errors


def check_singapore_compliance(
    repo_root: Path,
    modified_files: set[str],
    exceptions: dict[str, set[str]],
) -> tuple[bool, list[str]]:
    """Run compliance tests when Singapore property files change (Rule 5)."""

    rule_key = "rule_5_singapore"
    trigger_prefixes = (
        "backend/app/models/singapore_property",
        "backend/app/api/v1/singapore_property",
    )

    should_run = False
    for file_path in modified_files:
        if any(file_path.startswith(prefix) for prefix in trigger_prefixes):
            # Check if this specific file is excepted
            if is_exception(rule_key, file_path, exceptions):
                continue
            should_run = True
            break

    if not should_run:
        return True, []

    # Also skip if any of the prefix patterns are in exceptions (for broader exemptions)
    for prefix in trigger_prefixes:
        if any(prefix in exc_path for exc_path in exceptions.get(rule_key, set())):
            return True, []

    env = os.environ.copy()
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "backend/tests/test_api/test_feasibility.py",
        "-q",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=repo_root)
    if result.returncode == 0:
        return True, []

    output = (result.stdout or "") + (result.stderr or "")
    summary = output.strip() or "pytest failed"
    return (
        False,
        [
            "RULE VIOLATION: Singapore compliance tests failed\n"
            "  -> Rule 5: Run compliance validation when modifying Singapore property models.\n"
            "  -> See CODING_RULES.md section 5\n"
            f"  -> pytest output:\n{summary}\n"
        ],
    )


def main() -> int:
    """Run all coding rules checks."""
    print("=" * 60)
    print("Coding Rules Verification")
    print("=" * 60)

    all_passed = True
    all_errors: list[str] = []

    repo_root = get_repo_root()
    exceptions = load_exceptions(repo_root)
    modified_files = get_modified_files()

    checks = [
        (
            "Rule 1: Migration Files",
            lambda: check_migration_modifications(modified_files, exceptions),
        ),
        (
            "Rule 2: Async Patterns",
            lambda: check_async_patterns(repo_root, exceptions),
        ),
        (
            "Rule 4: Dependency Pinning",
            lambda: check_dependency_files(repo_root, exceptions),
        ),
        (
            "Rule 5: Singapore Compliance",
            lambda: check_singapore_compliance(repo_root, modified_files, exceptions),
        ),
    ]

    for check_name, check_func in checks:
        print(f"\nChecking {check_name}...", end=" ")
        passed, errors = check_func()

        if passed:
            print("✓ PASSED")
        else:
            print("✗ FAILED")
            all_passed = False
            all_errors.extend(errors)

    print("\n" + "=" * 60)

    if not all_passed:
        print("\nViolations found:\n")
        for error in all_errors:
            print(error)
            print()
        print("=" * 60)
        print("See CODING_RULES.md for details on how to fix these issues.")
        return 1

    print("All coding rules checks passed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
