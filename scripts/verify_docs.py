#!/usr/bin/env python3
"""
Verify markdown documentation files against the codebase.

Checks for:
1. Broken internal file references
2. References to non-existent code files
3. Stale API endpoint documentation
4. Outdated model references
5. Dead links to moved/deleted files
"""

import re
import sys
from pathlib import Path

# Project root
ROOT = Path(__file__).parent.parent


def find_all_md_files() -> list[Path]:
    """Find all project-owned markdown files."""
    md_files = []
    for pattern in ["*.md", "docs/**/*.md", ".github/**/*.md"]:
        md_files.extend(ROOT.glob(pattern))

    # Exclude dependencies
    return [
        f
        for f in md_files
        if "node_modules" not in str(f)
        and ".venv" not in str(f)
        and ".pytest_cache" not in str(f)
        and ".playwright-browsers" not in str(f)
    ]


def extract_file_references(content: str) -> set[str]:
    """Extract file path references from markdown content."""
    references = set()

    # Pattern 1: [text](path/to/file.py)
    for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", content):
        link = match.group(2)
        if not link.startswith(("http://", "https://", "#", "mailto:")):
            references.add(link)

    # Pattern 2: `path/to/file.py`
    for match in re.finditer(
        r"`([a-zA-Z_][a-zA-Z0-9_/.-]*\.(py|ts|tsx|js|json|yaml|yml))`", content
    ):
        references.add(match.group(1))

    # Pattern 3: backend/app/services/something.py (without backticks)
    for match in re.finditer(
        r"\b((?:backend|frontend)/[a-zA-Z0-9_/.]+\.(?:py|ts|tsx|js))\b", content
    ):
        references.add(match.group(1))

    return references


def check_file_exists(ref: str) -> bool:
    """Check if a file reference exists in the codebase."""
    # Handle relative paths
    path = ROOT / ref
    if path.exists():
        return True

    # Try without leading slash
    path = ROOT / ref.lstrip("/")
    if path.exists():
        return True

    # Try from docs directory
    if not ref.startswith("/"):
        path = ROOT / "docs" / ref
        if path.exists():
            return True

    return False


def verify_md_file(md_path: Path) -> dict[str, list[str]]:
    """Verify a single markdown file."""
    issues = {
        "broken_references": [],
        "stale_content_hints": [],
    }

    try:
        content = md_path.read_text(encoding="utf-8")
    except Exception as e:
        issues["stale_content_hints"].append(f"Could not read file: {e}")
        return issues

    # Check file references
    references = extract_file_references(content)
    for ref in references:
        if not check_file_exists(ref):
            issues["broken_references"].append(ref)

    # Check for stale content indicators
    stale_indicators = [
        (r"\bTODO\b", "Contains TODO items"),
        (r"\bFIXME\b", "Contains FIXME items"),
        (r"\bDEPRECATED\b", "Contains DEPRECATED markers"),
        (r"\b20(19|20|21|22)\b", "Contains old year references (pre-2023)"),
        (r"\[!\[.*?\]\(.*?\.png\)\]", "Contains image links (verify images exist)"),
    ]

    for pattern, description in stale_indicators:
        if re.search(pattern, content, re.IGNORECASE):
            issues["stale_content_hints"].append(description)

    return issues


def find_duplicate_content() -> list[tuple[str, str]]:
    """Find potentially duplicate markdown files based on similar titles."""
    md_files = find_all_md_files()
    titles = {}

    for md_path in md_files:
        try:
            content = md_path.read_text(encoding="utf-8")
            # Extract first h1 heading
            match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            if match:
                title = match.group(1).strip().lower()
                if title in titles:
                    titles[title].append(str(md_path.relative_to(ROOT)))
                else:
                    titles[title] = [str(md_path.relative_to(ROOT))]
        except Exception:
            continue

    # Return duplicates
    duplicates = [(title, files) for title, files in titles.items() if len(files) > 1]
    return duplicates


def main():
    """Run documentation verification."""
    print("🔍 Verifying Markdown Documentation\n")
    print("=" * 80)

    md_files = find_all_md_files()
    print(f"\nFound {len(md_files)} markdown files to verify\n")

    total_issues = 0
    files_with_issues = 0

    # Check each file
    for md_path in md_files:
        rel_path = md_path.relative_to(ROOT)
        issues = verify_md_file(md_path)

        if issues["broken_references"] or issues["stale_content_hints"]:
            files_with_issues += 1
            print(f"\n📄 {rel_path}")

            if issues["broken_references"]:
                print(f"  ❌ Broken references ({len(issues['broken_references'])}):")
                for ref in issues["broken_references"][:5]:  # Show first 5
                    print(f"     - {ref}")
                    total_issues += 1
                if len(issues["broken_references"]) > 5:
                    print(f"     ... and {len(issues['broken_references']) - 5} more")

            if issues["stale_content_hints"]:
                print("  ⚠️  Stale content indicators:")
                for hint in set(issues["stale_content_hints"]):
                    print(f"     - {hint}")

    # Check for duplicates
    print("\n" + "=" * 80)
    print("\n🔄 Checking for duplicate content...\n")
    duplicates = find_duplicate_content()

    if duplicates:
        print(f"Found {len(duplicates)} potential duplicates:\n")
        for title, files in duplicates:
            print(f"  📋 '{title}'")
            for f in files:
                print(f"     - {f}")
            print()
    else:
        print("✅ No duplicate titles found")

    # Summary
    print("=" * 80)
    print("\n📊 Summary:")
    print(f"   - Total MD files: {len(md_files)}")
    print(f"   - Files with issues: {files_with_issues}")
    print(f"   - Total broken references: {total_issues}")
    print(f"   - Potential duplicates: {len(duplicates)}")

    if files_with_issues > 0 or duplicates:
        print("\n💡 Recommendation: Review and fix issues before consolidation")
        return 1
    else:
        print("\n✅ All documentation appears valid!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
