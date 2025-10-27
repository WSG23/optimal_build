#!/usr/bin/env python3
"""Automated coding rules verification for optimal_build.

This script checks compliance with CODING_RULES.md:
1. No modified migration files (only new ones allowed)
2. Async patterns in API routes
3. Dependency files are properly formatted
4. Singapore compliance tests run when critical files change
5. Core expectations from CONTRIBUTING.md remain documented

Exceptions to individual rules can be declared in
``.coding-rules-exceptions.yml``.
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Callable, Iterable
from pathlib import Path


def get_repo_root() -> Path:
    """Find the repository root directory."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def get_venv_python() -> str:
    """Find the venv Python interpreter.

    Returns the path to the venv Python if it exists, otherwise falls back
    to sys.executable. This ensures we use the venv with all dependencies
    installed, rather than system Python.
    """
    repo_root = get_repo_root()
    venv_python = repo_root / ".venv" / "bin" / "python"

    if venv_python.exists():
        return str(venv_python)

    # Fallback to current Python (might be system Python)
    return sys.executable


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
                        f"  -> Rule 1: Do not edit existing migrations; create a new one instead.\n"
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

    # Check black version synchronization (CRITICAL for formatting consistency)
    black_versions = {}
    try:
        # Check requirements.txt
        req_txt = repo_root / "backend" / "requirements.txt"
        if req_txt.exists():
            for line in req_txt.read_text().splitlines():
                if line.strip().startswith("black=="):
                    black_versions["requirements.txt"] = line.strip().split("==")[1]

        # Check requirements-dev.txt
        req_dev = repo_root / "backend" / "requirements-dev.txt"
        if req_dev.exists():
            for line in req_dev.read_text().splitlines():
                if line.strip().startswith("black=="):
                    black_versions["requirements-dev.txt"] = line.strip().split("==")[1]

        # Check .pre-commit-config.yaml
        precommit_yaml = repo_root / ".pre-commit-config.yaml"
        if precommit_yaml.exists():
            content = precommit_yaml.read_text()
            # Look for black repo rev
            lines = content.splitlines()
            for i, line in enumerate(lines):
                if "github.com/psf/black" in line:
                    # Next few lines should have rev:
                    for j in range(i + 1, min(i + 5, len(lines))):
                        if "rev:" in lines[j]:
                            rev = lines[j].split("rev:")[1].strip()
                            # Strip comments
                            if "#" in rev:
                                rev = rev.split("#")[0].strip()
                            black_versions[".pre-commit-config.yaml"] = rev.strip("\"'")
                            break
                    break

        # Check if all black versions match
        if len(black_versions) > 1:
            versions_list = list(black_versions.values())
            if not all(v == versions_list[0] for v in versions_list):
                errors.append(
                    "RULE VIOLATION: Black version mismatch across configuration files\n"
                    f"  -> Found versions: {black_versions}\n"
                    "  -> Rule 4: Black versions MUST match in requirements.txt, "
                    "requirements-dev.txt, and .pre-commit-config.yaml\n"
                    "  -> This causes 'make format' to produce different output "
                    "than pre-commit hooks\n"
                    "  -> See CODING_RULES.md section 4"
                )
    except Exception as e:
        errors.append(f"Warning: Could not check black version synchronization: {e}")

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

    python_exe = get_venv_python()
    cmd = [
        python_exe,
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


def check_formatting(repo_root: Path) -> tuple[bool, list[str]]:
    """Check if code needs formatting (Rule 3)."""
    errors = []

    # Run black in check mode (use venv Python to ensure black is available)
    python_exe = get_venv_python()
    result = subprocess.run(
        [python_exe, "-m", "black", "--check", "--quiet", "backend/", "scripts/"],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    if result.returncode != 0:
        errors.append(
            "RULE VIOLATION: Code needs formatting (black)\n"
            "  -> Rule 3: Run 'make format' before committing\n"
            "  -> See CODING_RULES.md section 3\n"
            f"  -> Files need formatting:\n{result.stderr or result.stdout}"
        )

    # Note: Import ordering is checked by ruff (with the I rule), not isort
    # This avoids conflicts between ruff and isort when they disagree on formatting

    return len(errors) == 0, errors


def check_code_quality(
    repo_root: Path, exceptions: dict[str, set[str]]
) -> tuple[bool, list[str]]:
    """Check for code quality issues like unused variables (Rule 7)."""
    errors = []

    # Run ruff in check mode (use venv Python to ensure ruff is available)
    python_exe = get_venv_python()
    result = subprocess.run(
        [python_exe, "-m", "ruff", "check", "backend/", "scripts/"],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    if result.returncode != 0:
        # Parse output to filter exceptions
        output = result.stdout or result.stderr

        # Split output by error blocks (separated by blank lines)
        error_blocks = []
        current_block = []

        for line in output.split("\n"):
            if line.strip():
                current_block.append(line)
            elif current_block:
                error_blocks.append(current_block)
                current_block = []

        if current_block:
            error_blocks.append(current_block)

        # Filter out blocks from excepted files
        excepted_files = exceptions.get("rule_7_code_quality", set())
        filtered_blocks = []

        for block in error_blocks:
            # Check if any line in this block references an excepted file
            is_excepted = False
            block_text = "\n".join(block)

            for excepted_path in excepted_files:
                if excepted_path in block_text:
                    is_excepted = True
                    break

            if not is_excepted:
                filtered_blocks.append(block)

        # Reconstruct filtered output
        filtered_output = "\n\n".join(
            ["\n".join(block) for block in filtered_blocks]
        ).strip()

        # Only report error if there are non-excepted violations
        if filtered_output:
            errors.append(
                "RULE VIOLATION: Code quality issues found (ruff)\n"
                "  -> Rule 7: Fix unused variables, exception chaining, etc.\n"
                "  -> See CODING_RULES.md section 7\n"
                f"  -> Issues found:\n{filtered_output[:500]}"  # Limit output
            )

    return len(errors) == 0, errors


def check_ai_guidance_references(repo_root: Path) -> tuple[bool, list[str]]:
    """Ensure AI planning docs reference the mandatory testing guides (Rule 8)."""

    errors: list[str] = []

    guidance_file = repo_root / "docs" / "NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md"
    plan_file = repo_root / "docs" / "feature_delivery_plan_v2.md"

    required_refs = [
        "TESTING_KNOWN_ISSUES.md",
        "UI_STATUS.md",
        "TESTING_DOCUMENTATION_SUMMARY.md",
        "README.md",
    ]

    # NEW: Required content sections (Rule 8.1)
    required_content_sections = [
        (
            "MANDATORY TESTING CHECKLIST",
            "docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md",
        ),
        ("Backend tests:", "docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md"),
        ("Frontend tests", "docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md"),
        ("Manual UI testing:", "docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md"),
    ]

    def _read(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:  # pragma: no cover - surface unexpected IO issues
            errors.append(
                f"RULE VIOLATION: Unable to read {path} while enforcing Rule 8.\n"
                f"  -> {exc}"
            )
            return ""

    guidance_content = _read(guidance_file)
    plan_content = _read(plan_file)

    if not guidance_content or not plan_content:
        return len(errors) == 0, errors

    # Check for file references
    for ref in required_refs:
        if ref not in guidance_content:
            errors.append(
                "RULE VIOLATION: docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md "
                f"must reference '{ref}'.\n"
                "  -> Rule 8.2: AI agents must read canonical testing guides.\n"
                "  -> See CODING_RULES.md section 8.2"
            )
        if ref not in plan_content:
            errors.append(
                "RULE VIOLATION: docs/feature_delivery_plan_v2.md must reference "
                f"'{ref}' within relevant phase guidance.\n"
                "  -> Rule 8.2: AI agents must read canonical testing guides.\n"
                "  -> See CODING_RULES.md section 8.2"
            )

    # NEW: Check for required content sections (Rule 8.1)
    for section, doc_path in required_content_sections:
        content = guidance_content if "NEXT_STEPS" in doc_path else plan_content
        if section not in content:
            errors.append(
                f"RULE VIOLATION: {doc_path} must contain '{section}' section.\n"
                "  -> Rule 8.1: MANDATORY Testing Checklist must be present.\n"
                "  -> AI agents MUST provide backend, frontend, and UI manual test instructions.\n"
                "  -> See CODING_RULES.md section 8.1"
            )

    return len(errors) == 0, errors


def check_contributing_guidelines(repo_root: Path) -> tuple[bool, list[str]]:
    """Validate key expectations documented in CONTRIBUTING.md."""

    errors: list[str] = []
    contributing_path = repo_root / "CONTRIBUTING.md"

    if not contributing_path.exists():
        errors.append(
            "GUIDELINE VIOLATION: CONTRIBUTING.md is missing.\n"
            "  -> Restore the contributing guide at the repository root."
        )
        return False, errors

    try:
        content = contributing_path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - surface unexpected IO issues
        errors.append(
            "GUIDELINE VIOLATION: CONTRIBUTING.md could not be read.\n" f"  -> {exc}"
        )
        return False, errors

    content_lower = content.lower()
    required_snippets = {
        "pre-commit install": (
            "GUIDELINE VIOLATION: CONTRIBUTING.md must instruct contributors to install "
            "pre-commit hooks (missing 'pre-commit install')."
        ),
        "make verify": (
            "GUIDELINE VIOLATION: CONTRIBUTING.md must reference the 'make verify' quality gate."
        ),
        "coding_rules.md": (
            "GUIDELINE VIOLATION: CONTRIBUTING.md should link to CODING_RULES.md."
        ),
    }

    for snippet, error_message in required_snippets.items():
        if snippet not in content_lower:
            errors.append(error_message)

    return len(errors) == 0, errors


def run_section(
    title: str, checks: list[tuple[str, Callable[[], tuple[bool, list[str]]]]]
) -> tuple[bool, list[str]]:
    """Run a group of checks and report their results."""

    print("=" * 60)
    print(title)
    print("=" * 60)

    section_passed = True
    section_errors: list[str] = []

    for check_name, check_func in checks:
        print(f"\nChecking {check_name}...", end=" ")
        passed, errors = check_func()

        if passed:
            print("✓ PASSED")
        else:
            print("✗ FAILED")
            section_passed = False
            section_errors.extend(errors)

    print("\n" + "=" * 60)
    return section_passed, section_errors


def main() -> int:
    """Run all coding rules checks."""
    repo_root = get_repo_root()
    exceptions = load_exceptions(repo_root)
    modified_files = get_modified_files()

    coding_checks = [
        (
            "Rule 1: Migration Files",
            lambda: check_migration_modifications(modified_files, exceptions),
        ),
        (
            "Rule 2: Async Patterns",
            lambda: check_async_patterns(repo_root, exceptions),
        ),
        (
            "Rule 3: Code Formatting",
            lambda: check_formatting(repo_root),
        ),
        (
            "Rule 4: Dependency Pinning",
            lambda: check_dependency_files(repo_root, exceptions),
        ),
        (
            "Rule 5: Singapore Compliance",
            lambda: check_singapore_compliance(repo_root, modified_files, exceptions),
        ),
        (
            "Rule 7: Code Quality",
            lambda: check_code_quality(repo_root, exceptions),
        ),
        (
            "Rule 8: AI Planning References",
            lambda: check_ai_guidance_references(repo_root),
        ),
    ]

    contributing_checks = [
        ("Contributor Documentation", lambda: check_contributing_guidelines(repo_root)),
    ]

    all_passed = True
    all_errors: list[str] = []

    for title, checks in [
        ("Coding Rules Verification", coding_checks),
        ("Contributing Guidelines Verification", contributing_checks),
    ]:
        section_passed, section_errors = run_section(title, checks)
        if not section_passed:
            all_passed = False
            all_errors.extend(section_errors)

    if not all_passed:
        print("\nViolations found:\n")
        for error in all_errors:
            print(error)
            print()
        print("=" * 60)
        print(
            "See CODING_RULES.md and CONTRIBUTING.md for details on how to fix these issues."
        )
        return 1

    print("All coding rules and contributing guideline checks passed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
