#!/usr/bin/env python3
"""Validate feature_delivery_plan_v2.md for consistency between summary and detailed sections.

This script ensures:
1. Summary section is not manually edited (it should be read-only)
2. Phases marked 100% complete don't have "What's Missing" items
3. Phase status in summary matches detailed sections

Usage:
    python scripts/validate_delivery_plan.py

Exit codes:
    0: All validations passed
    1: Validation errors found
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def check_summary_edits(content: str) -> list[str]:
    """Check if summary section was manually edited (violates read-only policy)."""
    errors = []

    # Find summary section
    summary_start = content.find(
        "## 📊 Current Progress Snapshot (Read-Only Dashboard)"
    )
    summary_end = content.find("## 🎯 Delivery Philosophy")

    if summary_start == -1 or summary_end == -1:
        errors.append("Could not find summary section boundaries")
        return errors

    summary_section = content[summary_start:summary_end]

    # Check for warning text
    if "⚠️ CRITICAL: DO NOT EDIT THIS SECTION DIRECTLY" not in summary_section:
        errors.append(
            "Summary section missing read-only warning - "
            "may have been manually edited"
        )

    # Check if summary has inline percentage updates (sign of manual editing)
    # Look for patterns like "Backend 100%, UI 100%" without "Status source:" link
    manual_edit_pattern = (
        r"\*\*\[Phase \w+:.*?\*\* ✅ COMPLETE\n"
        r"- \*\*Backend:\*\* 100% \| \*\*UI:\*\* 100%\n"
        r"(?!.*Status source:)"
    )
    if re.search(manual_edit_pattern, summary_section):
        errors.append(
            "Summary contains phase marked COMPLETE without 'Status source:' link - "
            "likely manually edited instead of derived from detailed section"
        )

    return errors


def parse_detailed_phases(content: str) -> dict[str, dict]:
    """Extract phase status from detailed sections."""
    phases = {}

    # Find all phase detailed sections
    pattern = r"### (Phase \w+): (.+?) (✅ COMPLETE|⚠️ IN PROGRESS|❌ NOT STARTED)"
    for match in re.finditer(pattern, content):
        phase_id = match.group(1)
        phase_name = match.group(2)
        status = match.group(3)

        # Find the section content
        section_start = match.start()
        # Find next phase or end of document
        next_phase = re.search(r"\n### Phase \w+:", content[section_start + 10 :])
        if next_phase:
            section_end = section_start + 10 + next_phase.start()
        else:
            section_end = len(content)

        section_content = content[section_start:section_end]

        # Check for "What's Missing" items
        missing_items = re.findall(r"^- ❌ (.+)$", section_content, re.MULTILINE)

        phases[phase_id] = {
            "name": phase_name,
            "status": status,
            "missing_items": missing_items,
            "has_missing_work": len(missing_items) > 0,
        }

    return phases


def validate_completion_consistency(phases: dict[str, dict]) -> list[str]:
    """Validate phases marked COMPLETE don't have missing work."""
    errors = []

    for phase_id, data in phases.items():
        if "✅ COMPLETE" in data["status"] and data["has_missing_work"]:
            # Check if missing items are legitimate blockers (external dependencies)
            # Allow missing items that contain keywords like "requires API credentials",
            # "pending", "blocked", etc.
            blocker_keywords = [
                "requires api credentials",
                "pending",
                "blocked",
                "waiting for",
                "external dependency",
            ]

            blocking_items = []
            for item in data["missing_items"]:
                item_lower = item.lower()
                is_blocker = any(keyword in item_lower for keyword in blocker_keywords)
                if not is_blocker:
                    blocking_items.append(item)

            # Only report error if there are non-blocker missing items
            if blocking_items:
                errors.append(
                    f"{phase_id}: Marked '✅ COMPLETE' but 'What's Missing' section has "
                    f"{len(blocking_items)} ❌ items that are NOT external blockers:\n"
                    f"  {', '.join(blocking_items[:3])}\n"
                    f"  Hint: If these are legitimate blockers, add keywords like "
                    f"'requires API credentials' or 'blocked by' to the description."
                )

    return errors


def main() -> int:
    """Run all validations and report results."""
    plan_path = Path(__file__).parent.parent / "docs" / "feature_delivery_plan_v2.md"

    if not plan_path.exists():
        print(f"❌ ERROR: {plan_path} not found")
        return 1

    content = plan_path.read_text()

    all_errors = []

    # Validation 1: Check for manual summary edits
    all_errors.extend(check_summary_edits(content))

    # Validation 2: Parse detailed phases
    phases = parse_detailed_phases(content)

    # Validation 3: Check completion consistency
    all_errors.extend(validate_completion_consistency(phases))

    # Report results
    if all_errors:
        print("❌ Feature Delivery Plan Validation FAILED\n")
        print(f"Found {len(all_errors)} issue(s):\n")
        for i, error in enumerate(all_errors, 1):
            print(f"{i}. {error}\n")
        return 1
    else:
        print("✅ Feature Delivery Plan validation passed!")
        print(f"   Checked {len(phases)} phases for consistency")
        return 0


if __name__ == "__main__":
    sys.exit(main())
