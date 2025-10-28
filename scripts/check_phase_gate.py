#!/usr/bin/env python3
"""Guardrail to block Phase 2D work until prerequisite checkboxes are complete.

🤖 ARCHIVAL INSTRUCTIONS (For AI Agents)
========================================

⚠️ DO NOT DELETE THIS SCRIPT

This script enforces phase gate prerequisites. Even after Phase 2D prerequisites
are complete, keep this file for:

1. Audit trail - shows what enforcement existed
2. Future reference - may be adapted for Phase 3/4/5 gates
3. Documentation - demonstrates how phase gates work

When Phase 2D Gate Is Complete:
- Keep this script in scripts/ (do NOT delete)
- Optionally disable the pre-commit hook in .pre-commit-config.yaml by commenting out:
  ```yaml
  # - id: phase-gate
  #   name: Phase 2D gate enforcement
  #   entry: python3 scripts/check_phase_gate.py
  #   language: system
  #   pass_filenames: false
  ```
- Add comment explaining hook was disabled after Phase 2D prerequisites met

Why Keep The Script:
- Historical record of enforcement mechanism
- Template for future phase gates (Phase 3D, 4D, etc.)
- Shows how pre-commit hooks can enforce project workflow
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

PHASE_GATE_DOC = Path("docs/feature_delivery_plan_v2.md")
REQUIRED_MARKERS = {
    "Phase 2D Gate: Pre-Phase": (
        r"- \[x\] Phase 2D Gate: Pre-Phase\u202f?2D Infrastructure Audit"
    ),
    "Phase 2D Gate: Phase 1D": (
        r"- \[x\] Phase 2D Gate: Phase\u202f?1D Business Performance UI backlog delivered"
    ),
    "Phase 2D Gate: Phase 2B": (
        r"- \[x\] Phase 2D Gate: Phase\u202f?2B visualisation residual work delivered"
    ),
    "Phase 2D Gate: Expansion": r"- \[x\] Phase 2D Gate: Expansion Window\u202f?1",
}

# File/path patterns that indicate new Phase 2D work.
PHASE2D_PATH_PATTERNS = (
    "phase2d",
    "developer_phase",
    "dev_project_phase",
    "multi_phase_development",
)


def _get_staged_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _touches_phase2d(files: list[str]) -> bool:
    for path in files:
        lower = path.lower()
        if any(pattern in lower for pattern in PHASE2D_PATH_PATTERNS):
            return True
    return False


def _markers_complete(doc: Path) -> tuple[bool, list[str]]:
    try:
        content = doc.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False, [f"Required document missing: {doc}"]

    missing: list[str] = []
    for label, pattern in REQUIRED_MARKERS.items():
        if not re.search(pattern, content):
            missing.append(label)
    return not missing, missing


def main() -> int:
    staged = _get_staged_files()
    if not staged:
        return 0

    if not _touches_phase2d(staged):
        return 0

    ok, missing = _markers_complete(PHASE_GATE_DOC)
    if ok:
        return 0

    print(
        "Phase 2D work detected, but prerequisite checklist items are incomplete:",
        file=sys.stderr,
    )
    for item in missing:
        print(f"  • {item}", file=sys.stderr)
    print(
        "\nUpdate docs/feature_delivery_plan_v2.md once the prerequisite work is done.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
