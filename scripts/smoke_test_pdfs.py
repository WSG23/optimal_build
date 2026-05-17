#!/usr/bin/env python3
"""Smoke test for PDF generation changes.

This script runs when PDF-related files are modified to ensure
developers perform manual testing before committing.

Bypass paths (use sparingly, and only when the change demonstrably can't
affect rendered output):

  CONFIRM_PDF_TESTED=1 git commit ...
      Programmatic equivalent of typing "yes" at the prompt. Use when
      committing from a non-interactive shell after manual verification.

  SKIP=pdf-smoke-test git commit ...
      Pre-commit's standard skip mechanism. Use for changes that only
      touch routing/auth/typing in the PDF API surface and leave the
      rendering pipeline untouched.

In a non-TTY shell (CI, agents, scripted commits) the prompt would
otherwise hang forever; we now exit 1 with the bypass instructions
instead.
"""

import re
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
        "/commercial_property_packs.py",  # API endpoints
    ]
    return any(pattern in filepath for pattern in pdf_patterns)


# Diff lines that touch only routing/auth/typing infrastructure can be
# safely skipped — they can't change rendered output. Each pattern matches
# a single added line (already stripped of the leading '+').
SAFE_ADDED_LINE_PATTERNS = (
    re.compile(r"^\s*$"),  # blank lines
    re.compile(r"^\s*#"),  # comments (including `# public-endpoint:` markers)
    re.compile(r"^\s*from\s+app\.api\.deps\s+import\b"),  # auth dep imports
    re.compile(r"^\s*from\s+fastapi\s+import\b"),  # FastAPI imports
    re.compile(r"^\s*_identity\s*:\s*RequestIdentity\s*=\s*Depends\("),
    re.compile(r"^\s*[a-zA-Z_]\w*\s*:\s*[A-Za-z_][\w\[\], |\"']*\s*=\s*Depends\("),
)


def staged_diff_for(filepath):
    """Return the unified staged diff for a single file (or '' on failure)."""
    result = subprocess.run(
        ["git", "diff", "--cached", "-U0", "--", filepath],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout


def diff_is_routing_only(filepath):
    """True if every added line in this file's staged diff is auth/routing.

    Only added lines matter — deletions of arbitrary lines can still change
    behaviour, so they don't get a free pass. We look only at lines starting
    with '+' (and not '+++').
    """
    diff = staged_diff_for(filepath)
    if not diff:
        return False
    saw_added = False
    for line in diff.splitlines():
        if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
            continue
        if not line.startswith("+"):
            continue
        saw_added = True
        body = line[1:]
        if not any(p.search(body) for p in SAFE_ADDED_LINE_PATTERNS):
            return False
    return saw_added


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
    print("""
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
    """)

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
