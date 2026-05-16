#!/usr/bin/env python3
"""Auth-required endpoint scanner.

Scans backend/app/api/v1/ for FastAPI route handlers (@router.{get,post,
put,patch,delete}) and verifies each one declares an authentication
dependency: get_identity, require_viewer, require_reviewer, or
get_request_role.

Why: the #1 way auth bugs ship is someone copies an endpoint, forgets the
Depends(), and merges it. This script catches that before commit.

Public endpoints (signup/login/health) must opt out explicitly with a
trailing comment on the decorator line:

    @router.post("/login")  # public-endpoint: login flow
    async def login(...): ...

Exit codes:
  0 — every endpoint either declares auth or is explicitly public
  1 — at least one endpoint is missing auth
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
API_DIR = REPO_ROOT / "backend" / "app" / "api" / "v1"
BASELINE_FILE = REPO_ROOT / ".auth-required-baseline.txt"

AUTH_DEPS = (
    "get_identity",
    "require_viewer",
    "require_reviewer",
    "get_request_role",
    "get_current_user",  # future-proofing if codebase migrates to JWT
)

ROUTER_DECORATOR_RE = re.compile(r"^\s*@router\.(get|post|put|patch|delete)\b")
PUBLIC_OPT_OUT_RE = re.compile(r"#\s*public-endpoint\b")
FUNCTION_DEF_RE = re.compile(r"^\s*(?:async\s+)?def\s+(\w+)\s*\(")


# Function body end: dedented line not in parens
def find_function_block(lines: list[str], start: int) -> tuple[int, int]:
    """Given a line index pointing at `async def name(`, return (body_start,
    body_end) line indexes covering the function signature + body."""
    # Walk forward until we find the closing `)` of the signature, balancing parens
    paren = 0
    sig_end = start
    for i in range(start, len(lines)):
        for ch in lines[i]:
            if ch == "(":
                paren += 1
            elif ch == ")":
                paren -= 1
                if paren == 0:
                    sig_end = i
                    return start, sig_end
    return start, sig_end


def check_file(path: Path) -> list[str]:
    """Return violation lines for one router file."""
    violations: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return violations
    lines = text.splitlines()
    rel = path.relative_to(REPO_ROOT)

    i = 0
    while i < len(lines):
        line = lines[i]
        m = ROUTER_DECORATOR_RE.match(line)
        if not m:
            i += 1
            continue

        # Collect contiguous decorator block (router decorator may span
        # multiple lines for multi-arg @router.post(... "/x", response_model=...))
        decorator_start = i
        # Walk forward over balanced parens to consume the full decorator,
        # then any additional decorators, then find the function def.
        paren = 0
        j = i
        # Consume @router.X(...) signature
        consumed_paren = False
        while j < len(lines):
            for ch in lines[j]:
                if ch == "(":
                    paren += 1
                    consumed_paren = True
                elif ch == ")":
                    paren -= 1
            j += 1
            if consumed_paren and paren == 0:
                break
        # Now j points just past the decorator's closing line. Allow more
        # decorators on subsequent lines.
        decorator_block_end = j
        while j < len(lines) and lines[j].lstrip().startswith("@"):
            # Skip additional decorator (may itself span lines)
            paren = 0
            consumed_paren = False
            while j < len(lines):
                for ch in lines[j]:
                    if ch == "(":
                        paren += 1
                        consumed_paren = True
                    elif ch == ")":
                        paren -= 1
                j += 1
                if not consumed_paren or paren == 0:
                    break
            decorator_block_end = j

        # j should now point at the function definition
        if j >= len(lines):
            i = j
            continue
        func_match = FUNCTION_DEF_RE.match(lines[j])
        if not func_match:
            # Decorator without a function — unusual, skip
            i = j
            continue
        func_name = func_match.group(1)

        # Check decorator block for public-endpoint opt-out
        decorator_text = "\n".join(lines[decorator_start:decorator_block_end])
        is_public = bool(PUBLIC_OPT_OUT_RE.search(decorator_text))

        # Find function signature (might span multiple lines)
        _, sig_end = find_function_block(lines, j)
        signature_text = "\n".join(lines[j : sig_end + 1])

        # Auth can be declared in the decorator (`dependencies=[Depends(...)]`)
        # or as a function parameter. Check both.
        has_auth = any(
            dep in signature_text or dep in decorator_text for dep in AUTH_DEPS
        )

        if not has_auth and not is_public:
            method = m.group(1).upper()
            violations.append(
                f"{rel}:{decorator_start + 1}: {method} endpoint "
                f"`{func_name}` missing auth dependency "
                "(add Depends(require_viewer/reviewer/get_identity) or "
                "annotate decorator with `# public-endpoint: <reason>`)"
            )

        i = sig_end + 1

    return violations


def load_baseline() -> set[str]:
    """Load grandfathered violations as `path:funcname` keys."""
    if not BASELINE_FILE.exists():
        return set()
    baseline: set[str] = set()
    for raw in BASELINE_FILE.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        baseline.add(line)
    return baseline


def violation_key(v: str) -> str:
    """Extract `path:funcname` from a violation string for baseline matching.

    Line numbers are deliberately excluded — endpoints shift line numbers
    as files are edited, but the (file, function name) pair is stable.
    """
    # Format: "path:LINE: METHOD endpoint `funcname` missing..."
    m = re.match(r"^([^:]+):\d+:\s+\w+ endpoint `(\w+)`", v)
    if not m:
        return v
    return f"{m.group(1)}::{m.group(2)}"


def main() -> int:
    if not API_DIR.exists():
        print(f"ERROR: api dir not found at {API_DIR}", file=sys.stderr)
        return 2

    write_baseline = "--write-baseline" in sys.argv

    all_violations: list[str] = []
    files_scanned = 0
    for py_file in sorted(API_DIR.rglob("*.py")):
        if py_file.name == "__init__.py":
            continue
        files_scanned += 1
        all_violations.extend(check_file(py_file))

    if write_baseline:
        keys = sorted({violation_key(v) for v in all_violations})
        BASELINE_FILE.write_text(
            "# Auth-required baseline. Auto-generated by:\n"
            "#   python3 scripts/check_auth_required.py --write-baseline\n"
            "# Format: <relative_path>::<function_name>\n"
            "# Entries here are grandfathered — new endpoints missing auth\n"
            "# will still fail the check. To remove an entry, add proper\n"
            "# auth to that endpoint, then re-generate this file.\n"
            + "\n".join(keys)
            + "\n"
        )
        print(f"Wrote {len(keys)} entries to {BASELINE_FILE.relative_to(REPO_ROOT)}")
        return 0

    baseline = load_baseline()
    new_violations = [v for v in all_violations if violation_key(v) not in baseline]
    grandfathered = len(all_violations) - len(new_violations)

    if not new_violations:
        suffix = f" ({grandfathered} grandfathered)" if grandfathered else ""
        print(f"✓ Auth required ({files_scanned} router files scanned){suffix}")
        return 0

    print("\n" + "=" * 70)
    print(f"NEW ENDPOINTS MISSING AUTH ({len(new_violations)})")
    print("=" * 70)
    print("Each FastAPI route handler must either:")
    print("  1) Declare an auth dep: Depends(require_viewer/reviewer/get_identity)")
    print("  2) Opt out with `# public-endpoint: <reason>` on the decorator")
    print()
    for v in new_violations:
        print(f"  {v}")
    print(
        f"\nTotal: {len(new_violations)} NEW endpoints "
        f"({grandfathered} grandfathered). "
        "See backend/app/api/deps.py for available auth dependencies."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
