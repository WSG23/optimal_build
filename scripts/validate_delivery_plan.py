#!/usr/bin/env python3
"""Validate ROADMAP.MD and WORK_QUEUE.MD for required structure."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ROADMAP_PATH = REPO_ROOT / "docs" / "ROADMAP.MD"
WORK_QUEUE_PATH = REPO_ROOT / "docs" / "WORK_QUEUE.MD"


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing required documentation file: {path}")
    return path.read_text(encoding="utf-8")


def validate_roadmap(content: str) -> list[str]:
    errors: list[str] = []

    required_snippets = [
        "## 📈 Phase Overview",
        "## ✅ Phase Gate Checklist",
        "Phase 2D Gate: Pre-Phase",
        "docs/WORK_QUEUE.MD",
        "## Phase Summaries",
    ]

    for snippet in required_snippets:
        if snippet not in content:
            errors.append(
                "ROADMAP.MD is missing required content:\n"
                f"  -> '{snippet}'\n"
                "  -> Restore this section to keep stakeholders aligned."
            )

    return errors


def validate_work_queue(content: str) -> list[str]:
    errors: list[str] = []

    required_snippets = [
        "# Work Queue (AI Agent Task List)",
        "## 🚀 Active",
        "## 📋 Ready",
        "## ✅ Completed",
        "docs/development/testing/known-issues.md",
        "docs/planning/ui-status.md",
        "docs/development/testing/summary.md",
        "README.md",
    ]

    for snippet in required_snippets:
        if snippet not in content:
            errors.append(
                "WORK_QUEUE.MD is missing required content:\n"
                f"  -> '{snippet}'\n"
                "  -> Update the queue to include the full operating instructions."
            )

    return errors


def main() -> int:
    try:
        roadmap_content = _read(ROADMAP_PATH)
        work_queue_content = _read(WORK_QUEUE_PATH)
    except FileNotFoundError as exc:
        print(f"❌ Validation failed: {exc}")
        return 1

    errors = []
    errors.extend(validate_roadmap(roadmap_content))
    errors.extend(validate_work_queue(work_queue_content))

    if errors:
        print("❌ Documentation validation failed:\n")
        for idx, error in enumerate(errors, start=1):
            print(f"{idx}. {error}\n")
        return 1

    print(
        "✅ Documentation validation passed! ROADMAP.MD and WORK_QUEUE.MD look healthy."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
