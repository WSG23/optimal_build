#!/usr/bin/env python3
"""
Pre-commit hook to validate SQLAlchemy enum column patterns.

Ensures all SQLEnum/Enum columns include values_callable parameter
to serialize enum VALUES instead of NAMES.

Exit codes:
  0 - All enum patterns valid
  1 - Found enum columns missing values_callable
"""

import re
import sys
from pathlib import Path


ENUM_PATTERN = re.compile(r"(?:SQLEnum|Enum)\s*\(\s*(\w+)", re.MULTILINE)

VALUES_CALLABLE_PATTERN = re.compile(r"values_callable\s*=", re.MULTILINE)


def check_file(file_path: Path) -> list[tuple[int, str]]:
    """
    Check a Python file for enum patterns without values_callable.

    Returns list of (line_number, enum_class_name) tuples for violations.
    """
    violations = []

    try:
        content = file_path.read_text()
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)
        return violations

    lines = content.split("\n")

    for line_num, line in enumerate(lines, start=1):
        # Skip comments and docstrings
        stripped = line.strip()
        if (
            stripped.startswith("#")
            or stripped.startswith('"""')
            or stripped.startswith("'''")
        ):
            continue

        # Look for SQLEnum or Enum usage
        enum_match = ENUM_PATTERN.search(line)
        if not enum_match:
            continue

        enum_class = enum_match.group(1)

        # Check if values_callable appears in the same logical expression
        # (within the same column definition, which may span multiple lines)
        # For simplicity, check next 5 lines for values_callable
        context_lines = "\n".join(
            lines[max(0, line_num - 1) : min(len(lines), line_num + 5)]
        )

        if not VALUES_CALLABLE_PATTERN.search(context_lines):
            violations.append((line_num, enum_class))

    return violations


def main(file_paths: list[str]) -> int:
    """
    Main entry point for pre-commit hook.

    Args:
        file_paths: List of file paths to check (from pre-commit)

    Returns:
        0 if all files pass, 1 if violations found
    """
    all_violations = []

    for file_path_str in file_paths:
        file_path = Path(file_path_str)

        # Only check Python files in models directory
        if not file_path.name.endswith(".py"):
            continue
        if "models" not in file_path.parts and "app/models" not in str(file_path):
            continue

        violations = check_file(file_path)
        if violations:
            all_violations.append((file_path, violations))

    if all_violations:
        print(
            "\n❌ SQLAlchemy enum columns missing values_callable:\n", file=sys.stderr
        )
        for file_path, violations in all_violations:
            print(f"  {file_path}:", file=sys.stderr)
            for line_num, enum_class in violations:
                print(f"    Line {line_num}: {enum_class}", file=sys.stderr)

        print(
            "\n  💡 Fix: Add values_callable parameter to serialize enum VALUES:\n",
            file=sys.stderr,
        )
        print(
            "     SQLEnum(MyEnum, values_callable=lambda x: [e.value for e in x])",
            file=sys.stderr,
        )
        print("     OR use the _enum() helper function\n", file=sys.stderr)

        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
