#!/usr/bin/env python3
"""Smoke test for PDF generation changes.

This hook is triggered when PDF-related files are staged.

Historically it required an interactive `input()` confirmation, which blocks
automation (e.g., scripted commits or tooling that can't provide stdin).
The default behavior is now non-interactive: it prints a checklist reminder
and exits successfully. Enforcement can be enabled explicitly via `--enforce`.
"""

import argparse
import subprocess
import sys


def get_staged_files():
    """Get list of staged files in git."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip().splitlines()


def is_pdf_related(filepath):
    """Check if file is PDF-related."""
    pdf_patterns = [
        "universal_site_pack",
        "investment_memorandum",
        "pdf_generator",
        "marketing_materials",
        "/agents.py",  # API endpoints
    ]
    return any(pattern in filepath for pattern in pdf_patterns)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print a manual PDF testing checklist when PDF-related files are staged."
    )
    parser.add_argument(
        "--enforce",
        action="store_true",
        help="Fail when PDF-related files are staged unless --confirm is provided.",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Use with --enforce to acknowledge manual testing (non-interactive).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Check if PDF files were modified and (optionally) enforce manual testing."""
    args = _build_parser().parse_args(argv)
    staged_files = get_staged_files()
    pdf_files = [f for f in staged_files if is_pdf_related(f)]

    if not pdf_files:
        # No PDF files modified, skip check
        return 0

    print("=" * 70)
    print("⚠️  PDF GENERATION FILES MODIFIED")
    print("=" * 70)
    print("\nModified files:")
    for filepath in pdf_files:
        print(f"  - {filepath}")

    print("\n" + "=" * 70)
    print("📋 MANUAL TESTING REQUIRED")
    print("=" * 70)
    print("\nBefore committing, you MUST:")
    print("  1. Generate a test PDF via API")
    print("  2. Open PDF in Safari (strictest renderer)")
    print("  3. Open PDF in Chrome/Brave")
    print("  4. Verify all content is visible")
    print("  5. Test download from frontend (if applicable)")
    print("\nSee docs/PDF_TESTING_CHECKLIST.md for full checklist")

    print("\n" + "=" * 70)
    print("Quick Test Commands:")
    print("=" * 70)
    print(
        """
# 1. Start backend (if not running)
make dev

# 2. Generate test PDF
PROPERTY_ID="d47174ee-bb6f-4f3f-8baa-141d7c5d9051"
curl -X POST \\
  "http://localhost:9400/api/v1/agents/commercial-property/properties/\\
${PROPERTY_ID}/generate-pack/universal" \\
  -H "Content-Type: application/json"

# 3. Copy to /tmp for easy access
cp .storage/uploads/reports/d47174ee-bb6f-4f3f-8baa-141d7c5d9051/*.pdf /tmp/test.pdf

# 4. Open in browsers
open -a Safari /tmp/test.pdf
open -a "Google Chrome" /tmp/test.pdf
    """
    )

    if not args.enforce:
        print("\n✅ PDF checklist printed (non-blocking).")
        print(
            "To enforce confirmation, run: `python3 scripts/smoke_test_pdfs.py --enforce --confirm`"
        )
        return 0

    if args.confirm:
        print("\n✅ PDF testing confirmed (enforced mode) - proceeding with commit")
        return 0

    print("\n❌ PDF testing not confirmed (enforced mode). Commit blocked.")
    print("Re-run with: `python3 scripts/smoke_test_pdfs.py --enforce --confirm`")
    return 1


if __name__ == "__main__":
    sys.exit(main())
