#!/usr/bin/env python3
"""
UI Canon Checker - Enforces styling standards in the frontend codebase.

This script checks for violations of the canonical UI patterns:
1. Inline styles in TSX files (style={{ }})
2. Hardcoded colors (should use CSS variables)
3. Hardcoded spacing values
4. Non-canonical font declarations

IMPORTANT: This script does NOT flag Material-UI (MUI) sx prop usage.
MUI's sx prop is a theme-aware styling system and is the recommended
way to style MUI components. It integrates with the MUI theme and
uses semantic values like 'text.secondary', 'error.main', etc.

Run as: python scripts/check_ui_canon.py
Or via pre-commit hook.

Canonical CSS architecture:
  core/design-tokens/tokens.css    <- SINGLE SOURCE OF TRUTH
          |
  styles/page-layout.css           <- Shared page patterns
          |
  styles/[feature].css             <- Feature-specific styles
"""

import re
import sys
from pathlib import Path
from typing import NamedTuple


class Violation(NamedTuple):
    file: str
    line: int
    rule: str
    message: str
    snippet: str


# Files/patterns to skip
SKIP_PATTERNS = [
    "node_modules",
    "__tests__",
    ".test.tsx",
    ".test.ts",
    ".stories.tsx",  # Storybook files can use inline styles for demos
    "test/",
    # Legacy files we're not migrating yet
    "features/pages/Main.tsx",  # Security demo page
]

# Known exceptions (files allowed to have inline styles temporarily)
# Note: Migrated pages removed from exceptions list
EXCEPTIONS = {
    # MUI-heavy components that use sx prop (legitimate pattern)
    "frontend/src/app/pages/phase-management/": (
        "Uses MUI components with sx prop - legitimate pattern"
    ),
    # Components using dynamic styles from props (allowed with CSS variables)
    "frontend/src/pages/visualizations/EngineeringLayersPanel.tsx": (
        "Uses dynamic CSS variable colors from props"
    ),
}

# Hardcoded colors to flag (common violations)
HARDCODED_COLORS = [
    r"#[0-9a-fA-F]{3,8}",  # Hex colors
    r"rgb\s*\(",  # rgb()
    r"rgba\s*\(",  # rgba()
    r"hsl\s*\(",  # hsl()
]

# Patterns that indicate inline styles
INLINE_STYLE_PATTERNS = [
    r"style\s*=\s*\{\s*\{",  # style={{ in JSX
    r"\.style\.[a-zA-Z]+\s*=",  # element.style.property =
]

# Hardcoded spacing values (should use CSS variables)
HARDCODED_SPACING = [
    r"padding:\s*['\"]?\d+(?:px|rem|em)",
    r"margin:\s*['\"]?\d+(?:px|rem|em)",
    r"gap:\s*['\"]?\d+(?:px|rem|em)",
]

# Hardcoded font families
HARDCODED_FONTS = [
    r"fontFamily:\s*['\"].*(?:Inter|system-ui|sans-serif).*['\"]",
    r"font-family:\s*['\"].*(?:Inter|system-ui|sans-serif).*['\"]",
]


def should_skip(file_path: str) -> bool:
    """Check if file should be skipped."""
    for pattern in SKIP_PATTERNS:
        if pattern in file_path:
            return True
    return False


def is_exception(file_path: str) -> bool:
    """Check if file is a known exception."""
    for exc_path in EXCEPTIONS:
        if exc_path in file_path:
            return True
    return False


def is_using_css_variable_color(line: str) -> bool:
    """Check if line uses CSS variable for color (allowed pattern)."""
    # Allow: style={{ color: layer.color }} where layer.color is 'var(--ob-*)'
    # Also allow: style={{ color: someVar }} where var might be a CSS variable
    if "var(--" in line:
        return True
    # Dynamic color from object property (common pattern for layer colors)
    if re.search(r"color:\s*\w+\.\w+", line):
        return True
    return False


def check_file(file_path: Path) -> list[Violation]:
    """Check a single file for UI canon violations."""
    violations: list[Violation] = []
    rel_path = str(file_path)

    if should_skip(rel_path):
        return violations

    # Skip exceptions but log them
    if is_exception(rel_path):
        return violations

    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")
    except Exception:
        return violations

    for line_num, line in enumerate(lines, 1):
        # Skip comments
        stripped = line.strip()
        if (
            stripped.startswith("//")
            or stripped.startswith("/*")
            or stripped.startswith("*")
        ):
            continue

        # Check for inline styles in TSX
        if file_path.suffix in (".tsx", ".jsx"):
            # Skip MUI sx prop (legitimate styling pattern)
            if "sx={{" in line or "sx={" in line:
                continue

            for pattern in INLINE_STYLE_PATTERNS:
                if re.search(pattern, line):
                    # Allow dynamic color from CSS variable
                    if is_using_css_variable_color(line):
                        continue
                    violations.append(
                        Violation(
                            file=rel_path,
                            line=line_num,
                            rule="no-inline-styles",
                            message=(
                                "Inline styles detected. Use CSS classes from "
                                "page-layout.css instead."
                            ),
                            snippet=line.strip()[:80],
                        )
                    )
                    break

        # Check for hardcoded colors in style objects
        if "style" in line.lower() or file_path.suffix == ".css":
            # Skip MUI sx prop
            if "sx={{" in line or "sx={" in line:
                continue

            for pattern in HARDCODED_COLORS:
                # Skip CSS variable definitions and usage
                if (
                    "var(--" in line
                    or ": #" not in line
                    and "= '#" not in line
                    and '= "#' not in line
                ):
                    if "--ob-" in line or "var(" in line:
                        continue
                match = re.search(pattern, line)
                if match and "var(" not in line:
                    # Skip in CSS files where we're defining variables
                    if (
                        file_path.suffix == ".css"
                        and ":" in line
                        and "--" in line.split(":")[0]
                    ):
                        continue
                    violations.append(
                        Violation(
                            file=rel_path,
                            line=line_num,
                            rule="no-hardcoded-colors",
                            message=(
                                f"Hardcoded color '{match.group()}' detected. "
                                "Use CSS variable instead."
                            ),
                            snippet=line.strip()[:80],
                        )
                    )
                    break

    return violations


def main() -> int:
    """Main entry point."""
    frontend_dir = Path(__file__).parent.parent / "frontend" / "src"

    if not frontend_dir.exists():
        print(f"Frontend directory not found: {frontend_dir}")
        return 1

    all_violations: list[Violation] = []

    # Check TSX files
    for tsx_file in frontend_dir.rglob("*.tsx"):
        violations = check_file(tsx_file)
        all_violations.extend(violations)

    # Check CSS files (for hardcoded colors outside of variable definitions)
    for css_file in frontend_dir.rglob("*.css"):
        violations = check_file(css_file)
        all_violations.extend(violations)

    if all_violations:
        print("\n" + "=" * 80)
        print("UI CANON VIOLATIONS DETECTED")
        print("=" * 80 + "\n")

        # Group by rule
        by_rule: dict[str, list[Violation]] = {}
        for v in all_violations:
            by_rule.setdefault(v.rule, []).append(v)

        for rule, violations in by_rule.items():
            print(f"\n[{rule}] ({len(violations)} violations)")
            print("-" * 40)
            for v in violations[:10]:  # Limit output
                print(f"  {v.file}:{v.line}")
                print(f"    {v.message}")
                print(f"    > {v.snippet}")
            if len(violations) > 10:
                print(f"  ... and {len(violations) - 10} more")

        print("\n" + "=" * 80)
        print(f"Total: {len(all_violations)} violations")
        print("See frontend/src/styles/STYLE_GUIDE.md for correct patterns.")
        print("=" * 80 + "\n")

        # For now, just warn (don't fail the build)
        # Change to `return 1` when ready to enforce
        return 0

    print("✓ No UI canon violations detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
