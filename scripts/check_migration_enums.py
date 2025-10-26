#!/usr/bin/env python3
"""Check for problematic sa.Enum patterns in Alembic migrations.

This script enforces CODING_RULES.md Section 1.2:
- Never use sa.Enum(..., create_type=False) in migrations
- Use sa.String() columns instead to avoid "type already exists" errors

This is a READ-ONLY validator that prevents migration issues before they
reach production. It does not modify any files.

Exit codes:
  0 - All migrations use correct ENUM patterns
  1 - One or more migrations have forbidden patterns
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def get_repo_root() -> Path:
    """Find the repository root directory."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def _normalise_path(path: Path) -> str:
    """Normalize path for comparison with exceptions."""
    return str(path).replace("\\", "/").lstrip("./")


def load_exceptions() -> set[str]:
    """Load migration files excepted from ENUM pattern checks.

    Uses the same exception loading mechanism as audit_migrations.py.
    Returns a set of normalized file paths that should be skipped.
    """
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError:
        yaml = None  # type: ignore

    repo_root = get_repo_root()
    cfg = repo_root / ".coding-rules-exceptions.yml"

    if not cfg.exists():
        return set()

    if yaml is not None:
        data = yaml.safe_load(cfg.read_text()) or {}
        exceptions = data.get("exceptions", {}) or {}
        # Use rule_1_2_enum_pattern for this specific check
        rule_entries = exceptions.get("rule_1_2_enum_pattern", []) or []
        return {_normalise_path(Path(entry)) for entry in rule_entries}

    # Fallback parser for simple YAML structures when PyYAML is unavailable
    entries: set[str] = set()
    current_rule: str | None = None
    in_exceptions = False

    for raw_line in cfg.read_text().splitlines():
        no_comment = raw_line.split("#", 1)[0].rstrip()
        if not no_comment.strip():
            continue
        stripped = no_comment.strip()

        if not no_comment.startswith(" "):
            in_exceptions = stripped == "exceptions:"
            current_rule = None
            continue

        if not in_exceptions:
            continue

        if not stripped.startswith("- ") and stripped.endswith(":"):
            current_rule = stripped.rstrip(":")
            continue

        if current_rule == "rule_1_2_enum_pattern" and stripped.startswith("- "):
            path = stripped[2:].strip()
            if path:
                entries.add(_normalise_path(Path(path)))

    return entries


def check_migration_file(file_path: Path) -> list[str]:
    """Check a single migration file for problematic ENUM patterns.

    Returns a list of issues found (empty list if no issues).
    """
    issues = []

    try:
        content = file_path.read_text()
    except Exception as e:
        issues.append(f"Could not read file: {e}")
        return issues

    # Pattern 1: sa.Enum(..., create_type=False)
    # This is the most common problematic pattern
    if re.search(r"sa\.Enum\([^)]*create_type\s*=\s*False", content):
        issues.append(
            "Found forbidden pattern: sa.Enum(..., create_type=False)\n"
            "  → This pattern causes 'type already exists' errors\n"
            "  → Use sa.String() for ENUM columns instead\n"
            "  → See CODING_RULES.md Section 1.2 for correct pattern"
        )

    # Pattern 2: SOME_ENUM = sa.Enum(...) variable definitions
    # These variables often get reused in ways that trigger type creation
    enum_var_pattern = re.compile(r"^([A-Z_]+_ENUM)\s*=\s*sa\.Enum\(", re.MULTILINE)
    if enum_var_pattern.search(content):
        matches = enum_var_pattern.findall(content)
        issues.append(
            f"Found ENUM variable definition(s): {', '.join(matches)}\n"
            "  → ENUM variables can cause type creation issues\n"
            "  → Use sa.String() directly in op.add_column() instead\n"
            "  → See CODING_RULES.md Section 1.2 for correct pattern"
        )

    # Pattern 3: postgresql.ENUM(...) without proper guards
    # Less common but can also cause issues
    if re.search(r"postgresql\.ENUM\s*\(", content):
        # Check if there's a proper guard in upgrade()
        has_upgrade = re.search(r"def\s+upgrade\s*\(\s*\)\s*:", content)
        has_guard = re.search(
            r"SELECT\s+1\s+FROM\s+pg_type\s+WHERE\s+typname", content, re.IGNORECASE
        )

        if has_upgrade and not has_guard:
            issues.append(
                "Found postgresql.ENUM() without idempotent type creation guard\n"
                "  → Use DO $$ IF NOT EXISTS block to create ENUM types\n"
                "  → See CODING_RULES.md Section 1.2 for correct pattern"
            )

    return issues


def main() -> int:
    """Run ENUM pattern checks on all migration files."""
    repo_root = get_repo_root()

    # Find migrations directory (try both backend/migrations and migrations)
    migrations_dir = repo_root / "backend" / "migrations" / "versions"
    if not migrations_dir.exists():
        migrations_dir = repo_root / "migrations" / "versions"

    if not migrations_dir.exists():
        print("✓ No migrations directory found (skipping check)")
        return 0

    # Load exceptions
    exceptions = load_exceptions()

    # Check all migration files
    migration_files = sorted(migrations_dir.glob("*.py"))
    if not migration_files:
        print("✓ No migration files found (skipping check)")
        return 0

    failed_files: list[tuple[Path, list[str]]] = []
    checked_count = 0
    skipped_count = 0

    for migration_file in migration_files:
        if migration_file.name == "__init__.py":
            continue

        # Check if file is in exceptions
        rel_path = _normalise_path(migration_file.relative_to(repo_root))
        if rel_path in exceptions:
            skipped_count += 1
            continue

        # Check the file
        issues = check_migration_file(migration_file)
        checked_count += 1

        if issues:
            failed_files.append((migration_file, issues))

    # Report results
    print("=" * 70)
    print("Migration ENUM Pattern Check")
    print("=" * 70)
    print(f"Checked: {checked_count} files")
    print(f"Skipped: {skipped_count} files (in exceptions)")
    print(f"Failed:  {len(failed_files)} files")
    print("=" * 70)

    if failed_files:
        print("\n❌ VIOLATIONS FOUND:\n")
        for file_path, issues in failed_files:
            print(f"File: {file_path.name}")
            print(f"Path: {_normalise_path(file_path.relative_to(repo_root))}")
            for issue in issues:
                print(f"\n  {issue}")
            print("\n" + "-" * 70)

        print("\n" + "=" * 70)
        print("CODING_RULES.md Section 1.2: PostgreSQL ENUM Types in Migrations")
        print("=" * 70)
        print("\n✅ CORRECT PATTERN:")
        print(
            """
def upgrade() -> None:
    # Optional: Create ENUM type if you want DB-level validation
    op.execute('''
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'deal_status') THEN
                CREATE TYPE deal_status AS ENUM ('open', 'closed_won', 'closed_lost');
            END IF;
        END$$;
    ''')

    op.create_table(
        "deals",
        sa.Column("status", sa.String(), nullable=False),  # ← Use String, not Enum
    )

    # Optional: Convert to ENUM type after table creation
    op.execute(
        "ALTER TABLE deals ALTER COLUMN status TYPE deal_status USING status::deal_status"
    )
"""
        )
        print("\n" + "=" * 70)
        print(
            "\nTo bypass this check temporarily, add files to .coding-rules-exceptions.yml:"
        )
        print("exceptions:")
        print("  rule_1_2_enum_pattern:")
        for file_path, _ in failed_files:
            rel_path = _normalise_path(file_path.relative_to(repo_root))
            print(f"    - {rel_path}")
        print("=" * 70)

        return 1

    print("\n✅ All migrations use correct ENUM patterns!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
