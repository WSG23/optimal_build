#!/usr/bin/env python3
"""Smoke test for PDF generation changes.

This script runs when PDF-related files are modified to ensure
developers perform manual testing before committing.
"""

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


def main():
    """Check if PDF files were modified and prompt for manual testing."""
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
curl -X POST "http://localhost:9400/api/v1/agents/commercial-property/properties/d47174ee-bb6f-4f3f-8baa-141d7c5d9051/generate-pack/universal" \\
  -H "Content-Type: application/json"

# 3. Copy to /tmp for easy access
cp .storage/uploads/reports/d47174ee-bb6f-4f3f-8baa-141d7c5d9051/*.pdf /tmp/test.pdf

# 4. Open in browsers
open -a Safari /tmp/test.pdf
open -a "Google Chrome" /tmp/test.pdf
    """
    )

    print("\n" + "=" * 70)
    print("Have you completed manual PDF testing?")
    print("=" * 70)
    print("  - Tested in Safari: PDF displays correctly")
    print("  - Tested in Chrome/Brave: PDF displays correctly")
    print("  - All text content visible (not blank)")
    print("  - Download works from frontend")
    print("\n✅ Type 'yes' to confirm testing is complete:")
    print("❌ Type anything else to cancel commit")
    print("=" * 70)

    try:
        response = input("> ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\n\n❌ PDF testing not confirmed. Commit blocked.")
        return 1

    if response == "yes":
        print("\n✅ PDF smoke test passed - proceeding with commit")
        return 0
    else:
        print(f"\n❌ Response '{response}' is not 'yes'. Commit blocked.")
        print("Please complete manual PDF testing before committing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
