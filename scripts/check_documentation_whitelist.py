#!/usr/bin/env python3
"""
Documentation Whitelist Enforcement (Rule 14.2)

Prevents AI agents from creating unauthorized .md files in docs/ directory
after the 2025-11-12 documentation consolidation.

POLICY: New documentation must be added to existing files (feature_delivery_plan_v2.md,
WORK_QUEUE.MD) unless explicitly approved by user and whitelisted.

This script runs as a pre-commit hook to enforce the whitelist.
"""

import json
import subprocess
import sys
from pathlib import Path


def get_repo_root() -> Path:
    """Get the repository root directory."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(result.stdout.strip())


def get_staged_files() -> list[str]:
    """Get list of files staged for commit."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=A"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [f for f in result.stdout.strip().split("\n") if f]


def load_whitelist(repo_root: Path) -> dict:
    """Load the documentation whitelist configuration."""
    # Try YAML first (preferred), fallback to JSON
    yaml_path = repo_root / ".documentation-whitelist.yaml"
    json_path = repo_root / ".documentation-whitelist.json"

    if yaml_path.exists():
        # Simple YAML parser (only works for simple key: value structure)
        whitelist = {
            "allowed_files": [],
            "automatic_allow": [],
            "allowed_archive_patterns": [],
            "exceptions": [],
            "enforcement": {},
        }
        with open(yaml_path) as f:
            current_key = None
            for line in f:
                line = line.rstrip()
                if not line or line.strip().startswith("#"):
                    continue
                if line and not line[0].isspace():
                    if ":" in line:
                        key = line.split(":")[0].strip()
                        current_key = key
                        if key not in whitelist:
                            whitelist[key] = []
                elif current_key and line.strip().startswith("-"):
                    value = line.strip()[1:].strip().strip('"')
                    if isinstance(whitelist[current_key], list):
                        whitelist[current_key].append(value)
        return whitelist
    elif json_path.exists():
        with open(json_path) as f:
            return json.load(f)
    else:
        print(
            "ERROR: Neither .documentation-whitelist.yaml nor .documentation-whitelist.json found. "
            "This file is required for documentation enforcement."
        )
        sys.exit(1)


def is_whitelisted(file_path: str, whitelist: dict) -> bool:
    """Check if a file is whitelisted."""
    # Check exact matches
    if file_path in whitelist.get("allowed_files", []):
        return True

    # Check automatic allowances (README.md in any directory)
    for pattern in whitelist.get("automatic_allow", []):
        if pattern == "**/README.md" and file_path.endswith("/README.md"):
            return True
        if pattern == "docs/generated/**/*.md" and file_path.startswith(
            "docs/generated/"
        ):
            return True

    # Check archive patterns (docs/archive/**/*.md)
    for pattern in whitelist.get("allowed_archive_patterns", []):
        if pattern == "docs/archive/**/*.md" and file_path.startswith("docs/archive/"):
            return True

    # Check exceptions (temporary allowances with expiry dates)
    for exception in whitelist.get("exceptions", []):
        if file_path in exception:
            return True

    return False


def check_new_documentation_files() -> int:
    """Check for unauthorized new .md files in docs/ directory."""
    repo_root = get_repo_root()
    whitelist = load_whitelist(repo_root)

    # Get staged files that are new .md files in docs/
    staged_files = get_staged_files()
    new_md_files = [
        f for f in staged_files if f.startswith("docs/") and f.endswith(".md")
    ]

    if not new_md_files:
        # No new .md files being added, check passes
        return 0

    # Check each new file against whitelist
    unauthorized_files = []
    for file_path in new_md_files:
        if not is_whitelisted(file_path, whitelist):
            unauthorized_files.append(file_path)

    if unauthorized_files:
        # Print error message from whitelist configuration
        error_msg = whitelist.get("enforcement", {}).get(
            "error_message",
            "Unauthorized .md file creation detected. "
            "See .documentation-whitelist.yaml",
        )

        print("\n" + "=" * 70)
        print(error_msg)
        print("=" * 70)
        print("\nUnauthorized files:")
        for f in unauthorized_files:
            print(f"  - {f}")
        print("\nWhitelisted files are listed in .documentation-whitelist.yaml")
        print("=" * 70 + "\n")
        return 1

    # All new .md files are whitelisted
    return 0


if __name__ == "__main__":
    sys.exit(check_new_documentation_files())
