#!/usr/bin/env python3
"""UI Upgrade scorecard generator (brand-aware).

Scans frontend/src for canon deviations and Nielsen-heuristic signals, then
writes docs/ui_upgrade_scorecard.md.

Rubric (Nielsen 10 × 0-4 = 40 max):
  - H4 Consistency & Standards: anchored to brand canon (--ob-* tokens,
    canonical components, sharp radii, dual-mode parity)
  - H1/H5/H6/H7/H9: credited from detected state coverage + ARIA + canonical
    composition (parent context inheritance)
  - Leaf widgets (<200 lines) with 0 deviations + canonical/token usage: 38 baseline
  - Pages / large widgets: must earn each signal explicitly

Brand-aware false-positive exclusions:
  - var(--ob-token, #fallback) defensive patterns
  - borderRadius: 0 (sharp Square Cyber-Minimalism edges)
  - Structural micro-pixels in width/height/inset contexts (1-8px) — dots,
    indicators, dividers, hairlines
  - Domain table column widths (>=60px on min/maxWidth)
  - Mapbox/Google-Maps style configs
  - Lines marked `// canon-ok`
  - Canonical-component implementation files (they wrap Paper by design)

Usage:
    python3 scripts/ui_scorecard.py
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "frontend" / "src"
SCAN_DIRS = ["app/pages", "pages", "components", "modules", "features"]

RE_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
RE_FALLBACK_HEX = re.compile(r"var\(\s*--[\w-]+\s*,\s*#[0-9a-fA-F]{3,8}\s*\)")
RE_CANON_OK_LINE = re.compile(r".*//\s*canon-ok\b.*")
RE_MAPBOX_BLOCK = re.compile(
    r"\{\s*(elementType|featureType|stylers)[^{}]*\}", re.DOTALL
)

PAT_REAL_HEX = re.compile(r"(?<!['\"a-zA-Z0-9_&-])#[0-9a-fA-F]{3,8}\b(?!;)")
PAT_HARDCODED_PX = re.compile(r"['\"`](\d+)px['\"`]")
PAT_MUI_SPACING_INT = re.compile(r"spacing=\{\d+\}")
PAT_SX_BR_INT = re.compile(r"borderRadius:\s*([1-9]\d*)\s*[,}]")
PAT_RAW_PAPER = re.compile(r"<Paper[\s>]")

PAT_STRUCT_PX_LINE = re.compile(
    r"(width|height|minHeight|maxHeight|minWidth|maxWidth|top|bottom|left|right|inset):\s*['\"`](\d+)px['\"`]"
)
STRUCT_SMALL_OK_MAX = 8
STRUCT_LARGE_OK_MIN = 60

RE_CANONICAL = re.compile(r"from\s+['\"][^'\"]*components/canonical[^'\"]*['\"]")
RE_USE_OB_TOKEN = re.compile(r"var\(\s*--ob-[\w-]+\s*\)")
RE_HAS_LOADING = re.compile(
    r"isLoading|\bloading\b|Skeleton|<Skeleton|Placeholder|Loader|Spinner|CircularProgress|LinearProgress"
)
RE_HAS_EMPTY = re.compile(
    r"EmptyState|empty|noData|\b===\s*0\b|\.length\s*===\s*0|if\s*\(\s*!\w+(?:\.\w+)*\s*\)"
)
RE_HAS_ERROR = re.compile(r"AlertBlock|<Alert\b|error|Error\b|onError|catch\s*\(")
RE_HAS_FOCUS = re.compile(
    r"focus-visible|focusVisible|:focus|<Button|<IconButton|<TextField|<Select|<MenuItem|<Tab\b|<Tabs|<Switch|<Checkbox|<Radio|<Slider"
)
RE_HAS_ARIA = re.compile(
    r"aria-\w+=|<Button|<IconButton|<Tabs|<Tab\b|<Alert|<Tooltip|<Dialog|<Menu"
)
RE_BEM_CLASSNAME = re.compile(r'className=["\'`][\w-]+(?:__|--)[\w-]+')


def clean(txt: str) -> str:
    """Strip block comments / line comments (preserve canon-ok markers) and
    neutralize defensive fallback hex + Mapbox style blocks."""
    t = RE_BLOCK_COMMENT.sub(" ", txt)
    t = re.sub(r"//(?!\s*canon-ok\b).*", " ", t)
    t = RE_FALLBACK_HEX.sub("__OK__", t)
    t = RE_MAPBOX_BLOCK.sub("__OK__", t)
    return t


def line_has_structural_px(line: str) -> bool:
    for m in PAT_STRUCT_PX_LINE.finditer(line):
        n = int(m.group(2))
        if n <= STRUCT_SMALL_OK_MAX or n >= STRUCT_LARGE_OK_MIN:
            return True
    return False


def count_real_px(raw: str) -> int:
    c = clean(raw)
    count = 0
    for ln in c.splitlines():
        if RE_CANON_OK_LINE.match(ln):
            continue
        for m in PAT_HARDCODED_PX.finditer(ln):
            n = int(m.group(1))
            if line_has_structural_px(ln):
                continue
            if 1 <= n <= 4:
                continue
            count += 1
    return count


def scan_file(path: Path) -> dict | None:
    try:
        raw = path.read_text()
    except OSError:
        return None
    rel = str(path.relative_to(ROOT))
    is_canonical_impl = rel.startswith("components/canonical/")
    c = clean(raw)
    c_lines = [ln for ln in c.splitlines() if not RE_CANON_OK_LINE.match(ln)]
    c_no_marker = "\n".join(c_lines)
    deviations = (
        len(PAT_REAL_HEX.findall(c_no_marker))
        + count_real_px(raw)
        + len(PAT_MUI_SPACING_INT.findall(c_no_marker))
        + len(PAT_SX_BR_INT.findall(c_no_marker))
        + (0 if is_canonical_impl else len(PAT_RAW_PAPER.findall(c_no_marker)))
    )
    bem_count = len(RE_BEM_CLASSNAME.findall(raw))
    css_driven = bem_count >= 3
    signals = {
        "canonical_imports": len(RE_CANONICAL.findall(raw)),
        "ob_tokens": len(RE_USE_OB_TOKEN.findall(raw)),
        "bem_classes": bem_count,
        "css_driven": css_driven,
        "has_loading": bool(RE_HAS_LOADING.search(raw)),
        "has_empty": bool(RE_HAS_EMPTY.search(raw)),
        "has_error": bool(RE_HAS_ERROR.search(raw)),
        "has_focus": bool(RE_HAS_FOCUS.search(raw)),
        "has_aria": bool(RE_HAS_ARIA.search(raw)),
    }
    return {
        "file": rel,
        "deviations": deviations,
        "signals": signals,
        "lines": len(raw.splitlines()),
    }


def is_fixture_file(file_rel: str) -> bool:
    name = file_rel.rsplit("/", 1)[-1]
    return (
        name.startswith("Demo")
        or name.startswith("Mock")
        or name.startswith("Fixture")
        or "demo-" in name.lower()
        or "fixture" in name.lower()
    )


def score(rec: dict) -> int:
    dev = rec["deviations"]
    sig = rec["signals"]
    lines = rec["lines"]
    very_small = lines < 60
    is_leaf = lines < 200
    if is_fixture_file(rec["file"]) and dev == 0:
        return 38
    is_brand_aware = (
        sig["canonical_imports"] > 0
        or sig["ob_tokens"] >= 3
        or sig.get("css_driven", False)
    )

    if very_small and dev == 0:
        return 38 if is_brand_aware else 37

    if is_leaf and dev == 0 and is_brand_aware:
        s = 38 + (1 if sig["has_aria"] else 0)
        if sig["has_focus"] or sig["ob_tokens"] >= 10 or sig["canonical_imports"] >= 2:
            s += 1
        return min(40, s)

    if not is_leaf:
        s = 34 if (dev == 0 and is_brand_aware) else (33 if dev == 0 else 30)
        s += sum(
            1
            for k in ("has_loading", "has_empty", "has_error", "has_focus", "has_aria")
            if sig[k]
        )
        if sig["canonical_imports"] >= 2:
            s += 1
        if sig["ob_tokens"] >= 10 or sig.get("css_driven", False):
            s += 1
        s -= min(dev, 8)
        return min(40, max(0, s))

    s = 36 - min(dev * 2, 10)
    if is_brand_aware:
        s += 1
    return max(0, s)


AUTO_BEGIN = "<!-- ui-scorecard:auto:begin -->"
AUTO_END = "<!-- ui-scorecard:auto:end -->"


def _auto_block(rows: list[dict]) -> str:
    """Render only the auto-managed portion (roll-up + below-36 list).

    Everything outside the AUTO_BEGIN/AUTO_END markers is hand-maintained
    (per-surface Nielsen tables, iteration history, fix log) and preserved
    untouched across re-runs.
    """
    at = sum(1 for r in rows if r["score"] >= 36)
    below = len(rows) - at
    lines: list[str] = [AUTO_BEGIN, "", "## Roll-up (auto-generated)", ""]
    lines.append("| Metric | Count |")
    lines.append("|---|---|")
    lines.append(f"| Surfaces scanned | **{len(rows)}** |")
    lines.append(f"| At target (≥36/40) | **{at}** |")
    lines.append(f"| Below target (<36/40) | **{below}** |")
    lines.append(f"| % canonized | **{100 * at / len(rows):.1f}%** |")
    lines.append("")
    lines.append("## Surfaces below 36 (fix targets, auto-generated)")
    lines.append("")
    if below == 0:
        lines.append("_None — goal met._ 🎯")
    else:
        lines.append("| Score | dev | Lines | Surface |")
        lines.append("|---|---|---|---|")
        for r in rows:
            if r["score"] >= 36:
                continue
            lines.append(
                f"| **{r['score']}** | {r['deviations']} | {r['lines']} | `{r['file']}` |"
            )
    lines.append("")
    lines.append(AUTO_END)
    return "\n".join(lines)


def main() -> int:
    rows: list[dict] = []
    for d in SCAN_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for p in base.rglob("*.tsx"):
            if (
                "__tests__" in p.parts
                or p.name.endswith(".test.tsx")
                or ".stories." in p.name
            ):
                continue
            r = scan_file(p)
            if r:
                r["score"] = score(r)
                rows.append(r)
    rows.sort(key=lambda r: (r["score"], r["file"]))

    at = sum(1 for r in rows if r["score"] >= 36)
    below = len(rows) - at
    auto = _auto_block(rows)

    target = Path(__file__).resolve().parents[1] / "docs" / "ui_upgrade_scorecard.md"
    if target.exists():
        existing = target.read_text()
        if AUTO_BEGIN in existing and AUTO_END in existing:
            # Preserve hand-written sections: replace only the marked block.
            import re as _re

            new = _re.sub(
                _re.escape(AUTO_BEGIN) + r".*?" + _re.escape(AUTO_END),
                auto,
                existing,
                flags=_re.DOTALL,
                count=1,
            )
            target.write_text(new)
        else:
            # Existing file has no marker — append the auto block so hand-written
            # content above is never destroyed.
            target.write_text(existing.rstrip() + "\n\n" + auto + "\n")
    else:
        # First run: emit a minimal scaffold containing only the auto block.
        target.write_text(
            "# UI Upgrade Scorecard\n\n"
            "_Hand-written sections (rubric, per-surface scores, iteration history) "
            "go above the auto-managed block below. The block between the "
            "`ui-scorecard:auto:begin/end` HTML comments is rewritten by "
            "`python3 scripts/ui_scorecard.py` — everything else is preserved._\n\n"
            + auto
            + "\n"
        )
    print(
        f"Scorecard: {len(rows)} surfaces · {at} at ≥36 · {below} below ({100 * at / len(rows):.1f}% canonized)"
    )
    print(f"Updated auto-block in: {target}")
    return 0 if below == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
