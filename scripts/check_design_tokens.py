#!/usr/bin/env python3
"""Design token enforcement.

Two checks:
1. UNDEFINED REFERENCES — every `var(--ob-*)` reference must resolve to a
   token defined in core/design-tokens/tokens.css. Catches typos like
   `--ob-space-6` that silently fall back to inherited/default values.

2. NEW HARDCODES — newly-introduced hardcoded pixel/color values in CSS
   and TSX style props are blocked. Existing violations are grandfathered
   via .design-token-exceptions.txt to allow incremental migration.

Exit codes:
  0 — no violations
  1 — violations found (blocks commit)
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOKENS_FILE = REPO_ROOT / "core" / "design-tokens" / "tokens.css"
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"
EXCEPTIONS_FILE = REPO_ROOT / ".design-token-exceptions.txt"

# Patterns
TOKEN_DEF_RE = re.compile(r"^\s*(--ob-[a-z0-9-]+)\s*:", re.MULTILINE)
TOKEN_REF_RE = re.compile(r"var\(\s*(--ob-[a-z0-9-]+)")
HARDCODED_PX_TSX_RE = re.compile(r"""['"](\d{1,4})px['"]""")
HARDCODED_HEX_TSX_RE = re.compile(r"""['"](#[0-9a-fA-F]{3,8})['"]""")
HARDCODED_PX_CSS_RE = re.compile(
    r"^\s*(?:padding|margin|gap|width|height|min-width|max-width|"
    r"min-height|max-height|border-radius):\s*(\d{1,4})px",
    re.MULTILINE,
)

# Files/paths to skip for hardcode check (test files, design system itself)
SKIP_HARDCODE = (
    "/__tests__/",
    ".test.",
    ".spec.",
    ".stories.",
    "/design-tokens/",
    "/theme/tokens.ts",  # The theme constants file defines the tokens
    "/components/canonical/",  # Canonical components allowed bespoke sizes (small set)
)


def load_defined_tokens() -> set[str]:
    """Return all defined --ob-* names.

    Scans the canonical tokens.css plus any component-scoped CSS file under
    frontend/src/styles (some legacy files define their own scoped tokens
    like --ob-depth-* or --ob-color-border-premium in feasibility.css).
    """
    if not TOKENS_FILE.exists():
        print(f"ERROR: tokens.css not found at {TOKENS_FILE}", file=sys.stderr)
        sys.exit(2)
    defined: set[str] = set()
    defined.update(TOKEN_DEF_RE.findall(TOKENS_FILE.read_text()))
    styles_dir = REPO_ROOT / "frontend" / "src" / "styles"
    if styles_dir.exists():
        for css_file in styles_dir.rglob("*.css"):
            try:
                defined.update(TOKEN_DEF_RE.findall(css_file.read_text()))
            except OSError:
                continue
    return defined


def load_exceptions() -> set[str]:
    """Load grandfathered violations from .design-token-exceptions.txt.

    Format: one `path:line_excerpt` per line. Comments start with #.
    """
    if not EXCEPTIONS_FILE.exists():
        return set()
    exceptions: set[str] = set()
    for raw in EXCEPTIONS_FILE.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        exceptions.add(line)
    return exceptions


def iter_files(extensions: tuple[str, ...]) -> list[Path]:
    """Yield files under frontend/src matching extensions."""
    files: list[Path] = []
    for ext in extensions:
        files.extend(FRONTEND_SRC.rglob(f"*{ext}"))
    return files


def check_undefined_references(defined: set[str]) -> list[str]:
    """Find `var(--ob-*)` references that don't resolve to a defined token."""
    violations: list[str] = []
    search_roots = [FRONTEND_SRC, REPO_ROOT / "core" / "design-tokens"]
    extensions = (".css", ".tsx", ".ts")
    for root in search_roots:
        if not root.exists():
            continue
        for ext in extensions:
            for path in root.rglob(f"*{ext}"):
                if "/node_modules/" in str(path):
                    continue
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                for line_no, line in enumerate(text.splitlines(), 1):
                    for ref in TOKEN_REF_RE.findall(line):
                        if ref not in defined:
                            rel = path.relative_to(REPO_ROOT)
                            violations.append(
                                f"{rel}:{line_no}: undefined token reference {ref}"
                            )
    return violations


def get_staged_files() -> list[Path]:
    """Return files staged for commit (for incremental hardcode check)."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=AM"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    files = []
    for name in result.stdout.splitlines():
        path = REPO_ROOT / name
        if path.exists() and path.suffix in (".tsx", ".ts", ".css"):
            files.append(path)
    return files


def should_skip_hardcode(path: Path) -> bool:
    s = str(path)
    return any(skip in s for skip in SKIP_HARDCODE)


def check_new_hardcodes(files: list[Path], exceptions: set[str]) -> list[str]:
    """Block new hardcoded px/hex values, allowing grandfathered exceptions."""
    violations: list[str] = []
    for path in files:
        if should_skip_hardcode(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = path.relative_to(REPO_ROOT)

        if path.suffix in (".tsx", ".ts"):
            for match in HARDCODED_PX_TSX_RE.finditer(text):
                line_no = text.count("\n", 0, match.start()) + 1
                key = f"{rel}:{line_no}"
                if key in exceptions:
                    continue
                excerpt = match.group(0)
                violations.append(
                    f"{rel}:{line_no}: hardcoded px string {excerpt} "
                    f"(use var(--ob-space-*) or var(--ob-size-*))"
                )
            for match in HARDCODED_HEX_TSX_RE.finditer(text):
                line_no = text.count("\n", 0, match.start()) + 1
                key = f"{rel}:{line_no}"
                if key in exceptions:
                    continue
                excerpt = match.group(0)
                violations.append(
                    f"{rel}:{line_no}: hardcoded hex color {excerpt} "
                    f"(use var(--ob-color-*))"
                )

        elif path.suffix == ".css":
            for match in HARDCODED_PX_CSS_RE.finditer(text):
                line_no = text.count("\n", 0, match.start()) + 1
                key = f"{rel}:{line_no}"
                if key in exceptions:
                    continue
                px = match.group(1)
                # 1px and 2px are legitimate (borders, outlines)
                if px in ("1", "2"):
                    continue
                violations.append(
                    f"{rel}:{line_no}: hardcoded {px}px in CSS property "
                    f"(use var(--ob-space-*) or var(--ob-size-*))"
                )
    return violations


def main() -> int:
    if "--full-audit" in sys.argv:
        # Scan ALL files (used in CI / one-time audits)
        files_to_check = []
        for ext in (".tsx", ".ts", ".css"):
            files_to_check.extend(FRONTEND_SRC.rglob(f"*{ext}"))
    else:
        # Default: incremental check on staged files only
        files_to_check = get_staged_files()

    defined = load_defined_tokens()
    exceptions = load_exceptions()

    undefined = check_undefined_references(defined)
    hardcodes = check_new_hardcodes(files_to_check, exceptions)

    if not undefined and not hardcodes:
        print(f"✓ Design tokens OK ({len(defined)} tokens defined)")
        return 0

    if undefined:
        print("\n" + "=" * 70)
        print(f"UNDEFINED TOKEN REFERENCES ({len(undefined)})")
        print("=" * 70)
        print("These var(--ob-*) references don't resolve — they silently")
        print("fall back to defaults. Define them in tokens.css or fix the name.\n")
        for v in undefined[:30]:
            print(f"  {v}")
        if len(undefined) > 30:
            print(f"  ... and {len(undefined) - 30} more")

    if hardcodes:
        print("\n" + "=" * 70)
        print(f"NEW HARDCODED VALUES ({len(hardcodes)})")
        print("=" * 70)
        print("Use design tokens. Existing violations are grandfathered in")
        print(".design-token-exceptions.txt — only NEW hardcodes are blocked.\n")
        for v in hardcodes[:30]:
            print(f"  {v}")
        if len(hardcodes) > 30:
            print(f"  ... and {len(hardcodes) - 30} more")

    print(
        f"\nTotal: {len(undefined) + len(hardcodes)} violations. "
        "See core/design-tokens/tokens.css for available tokens."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
