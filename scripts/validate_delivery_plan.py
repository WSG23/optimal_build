#!/usr/bin/env python3
"""Validate docs/all_steps_to_product_completion.md for required structure."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ROADMAP_PATH = REPO_ROOT / "docs" / "all_steps_to_product_completion.md"


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing required documentation file: {path}")
    return path.read_text(encoding="utf-8")


def validate_roadmap(content: str) -> list[str]:
    errors: list[str] = []

    required_snippets = [
        "## 📊 Current Progress Snapshot",
        "### ✅ Phase Gate Checklist",
        "Phase 2D Gate:",
        "## 📋 PHASE 1:",
        "## 📋 PHASE 2:",
        "## 📋 PHASE 3:",
        "## 📋 PHASE 4:",
        "## 📋 PHASE 5:",
        "## 📋 PHASE 6:",
        "## 📊 ESTIMATED TIMELINE & EFFORT",
    ]

    for snippet in required_snippets:
        if snippet not in content:
            errors.append(
                "all_steps_to_product_completion.md is missing required content:\n"
                f"  -> '{snippet}'\n"
                "  -> Restore this section to keep stakeholders aligned."
            )

    # Backlog + deferred work now lives inside the roadmap file.
    backlog_markers = [
        "## 📌 Unified Execution Backlog & Deferred Work",
        "### 🚀 Active",
        "### 📋 Ready",
        "### ✅ Completed",
        "### 🧭 Operating Instructions for AI Agents",
        "### 🧱 Technical Debt Radar",
        "### ⚠️ Known Testing Issues",
    ]

    for marker in backlog_markers:
        if marker not in content:
            errors.append(
                "Unified backlog section is missing required content:\n"
                f"  -> '{marker}'\n"
                "  -> Restore the consolidated backlog before proceeding."
            )

    required_refs = [
        "development/testing/summary.md",
        "planning/ui-status.md",
        "docs/README.md",
    ]

    for ref in required_refs:
        if ref not in content:
            errors.append(
                "Unified backlog is missing required reference:\n"
                f"  -> '{ref}'\n"
                "  -> Ensure operating instructions point to canonical context docs."
            )

    return errors


def main() -> int:
    try:
        roadmap_content = _read(ROADMAP_PATH)
    except FileNotFoundError as exc:
        print(f"❌ Validation failed: {exc}")
        return 1

    errors = []
    errors.extend(validate_roadmap(roadmap_content))

    if errors:
        print("❌ Documentation validation failed:\n")
        for idx, error in enumerate(errors, start=1):
            print(f"{idx}. {error}\n")
        return 1

    print(
        "✅ Documentation validation passed! "
        "all_steps_to_product_completion.md looks healthy."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
