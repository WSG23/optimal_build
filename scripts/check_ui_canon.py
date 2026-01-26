#!/usr/bin/env python3
"""
UI Canon Checker - Enforces styling standards in the frontend codebase.

This script checks for violations of the canonical UI patterns:
1. Inline styles in TSX files (style={{ }})
2. Hardcoded colors (should use CSS variables)
3. Hardcoded spacing values in CSS and MUI sx props
4. Non-canonical font declarations
5. MUI numeric spacing props (mb={2}, spacing={3}, etc.)
6. MUI sx prop hardcoded values (p: 16, borderRadius: 2, etc.)

Run as: python scripts/check_ui_canon.py
Or via pre-commit hook.

Canonical CSS architecture:
  core/design-tokens/tokens.css    <- SINGLE SOURCE OF TRUTH
          |
  styles/page-layout.css           <- Shared page patterns
          |
  styles/[feature].css             <- Feature-specific styles

Design tokens that MUST be used:
  Spacing: var(--ob-space-50|100|150|200|300|400|500|600|800)
  Radius:  var(--ob-radius-xs|sm|md|lg|xl|full)
  Colors:  theme.palette.* or var(--ob-color-*)
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

# Grandfathered files - existing inline styles allowed, enforce on NEW files only
# These files were created before UI canon enforcement
# Migrate incrementally when touching these files
INLINE_STYLE_GRANDFATHERED = {
    # App entry point
    "frontend/src/App.tsx",
    # Navigation
    "frontend/src/app/components/AppNavigation.tsx",
    # Site acquisition (complex 3D/canvas components)
    "frontend/src/app/components/site-acquisition/Preview3DViewer.tsx",
    "frontend/src/app/pages/site-acquisition/DeveloperPreviewStandalone.tsx",
    "frontend/src/app/pages/site-acquisition/components/capture-form/VoiceNoteList.tsx",
    "frontend/src/app/pages/site-acquisition/components/capture-form/VoiceNoteRecorder.tsx",
    "frontend/src/app/pages/site-acquisition/components/condition-assessment/ConditionAssessmentEditor.tsx",
    "frontend/src/app/pages/site-acquisition/components/condition-assessment/InsightCard.tsx",
    "frontend/src/app/pages/site-acquisition/components/condition-assessment/ManualInspectionControls.tsx",
    "frontend/src/app/pages/site-acquisition/components/condition-assessment/OverallAssessmentCard.tsx",
    "frontend/src/app/pages/site-acquisition/components/condition-assessment/ScenarioComparisonCard.tsx",
    "frontend/src/app/pages/site-acquisition/components/condition-assessment/SystemRatingCard.tsx",
    "frontend/src/app/pages/site-acquisition/components/inspection-history/HistoryCompareView.tsx",
    "frontend/src/app/pages/site-acquisition/components/inspection-history/HistoryTimelineView.tsx",
    "frontend/src/app/pages/site-acquisition/components/inspection-history/InspectionHistoryContent.tsx",
    "frontend/src/app/pages/site-acquisition/components/modals/InspectionHistoryModal.tsx",
    "frontend/src/app/pages/site-acquisition/components/modals/QuickAnalysisHistoryModal.tsx",
    "frontend/src/app/pages/site-acquisition/components/photos/PhotoCapture.tsx",
    "frontend/src/app/pages/site-acquisition/components/photos/PhotoDocumentation.tsx",
    "frontend/src/app/pages/site-acquisition/components/photos/PhotoGallery.tsx",
    "frontend/src/app/pages/site-acquisition/components/property-overview/AssetMixChart.tsx",
    "frontend/src/app/pages/site-acquisition/components/property-overview/ColorLegendEditor.tsx",
    "frontend/src/app/pages/site-acquisition/components/property-overview/LayerBreakdownCards.tsx",
    # Capture/GPS
    "frontend/src/app/pages/capture/components/MissionLog.tsx",
    "frontend/src/app/pages/gps-capture/GpsCapturePage.tsx",
    # Integrations
    "frontend/src/app/pages/integrations/IntegrationsPage.tsx",
    # Phase management (Gantt chart needs inline positioning)
    "frontend/src/app/pages/phase-management/components/GanttChart.tsx",
    # Canonical components (dynamic styling from props)
    "frontend/src/components/canonical/PremiumMetricCard.tsx",
    "frontend/src/components/agents/widgets/MarketCycleIndicator.tsx",
    "frontend/src/components/agents/widgets/MarketHeatmap.tsx",
    # CAD module (canvas/SVG positioning)
    "frontend/src/modules/cad/CadDetectionPreview.tsx",
    "frontend/src/modules/cad/CadUploader.tsx",
    "frontend/src/modules/cad/InteractiveFloorplate.tsx",
    "frontend/src/modules/cad/RoiSummary.tsx",
    # Feasibility module
    "frontend/src/modules/feasibility/FeasibilityWizard.tsx",
    "frontend/src/modules/feasibility/components/AIAssistantSidebar.tsx",
    "frontend/src/modules/feasibility/components/AddressForm.tsx",
    "frontend/src/modules/feasibility/components/FeasibilityOutputPanel.tsx",
    "frontend/src/modules/feasibility/components/FinancialSettingsPanel.tsx",
    "frontend/src/modules/feasibility/components/GenerativeDesignPanel.tsx",
    "frontend/src/modules/feasibility/components/ImmersiveMap.tsx",
    "frontend/src/modules/feasibility/components/PackGenerationPanel.tsx",
    "frontend/src/modules/feasibility/components/ResultsPanel.tsx",
    "frontend/src/modules/feasibility/components/ScenarioHistorySidebar.tsx",
    "frontend/src/modules/feasibility/components/SmartIntelligenceField.tsx",
    # Finance module
    "frontend/src/modules/finance/FinanceWorkspace.tsx",
    "frontend/src/modules/finance/components/AllocationRing.tsx",
    "frontend/src/modules/finance/components/FinanceAssetBreakdown.tsx",
    "frontend/src/modules/finance/components/FinanceProjectSelector.tsx",
    "frontend/src/modules/finance/components/FinanceScenarioTable.tsx",
    "frontend/src/modules/finance/components/FinanceSensitivitySummary.tsx",
    # Advisory/visualizations
    "frontend/src/pages/advisory/components/AbsorptionChart.tsx",
    "frontend/src/pages/advisory/components/AssetMixPanel.tsx",
    "frontend/src/pages/visualizations/AdvancedIntelligence.tsx",
    "frontend/src/pages/visualizations/components/RelationshipGraph.tsx",
}

# Color patterns that are intentionally allowed (not violations)
ALLOWED_COLOR_PATTERNS = [
    r"rgba\([^)]+,\s*0\)",  # Animation endpoints (alpha=0) - intentional
    r"linear-gradient\(",  # CSS gradients require explicit colors
    r"rgb\(\s*\d+\s+\d+\s+\d+\s*/",  # CSS Color Level 4 syntax (rgb(255 255 255 / 0.4))
]

# Files with intentionally hardcoded colors (e.g., Google Maps API requires hex colors)
COLOR_EXCEPTIONS = {
    # Google Maps components - API requires direct color values, CSS variables not supported
    "frontend/src/app/pages/gps-capture/GpsCapturePage.tsx",
    "frontend/src/components/agents/widgets/MarketHeatmap.tsx",
    "frontend/src/modules/feasibility/components/ImmersiveMap.tsx",
}

# Known exceptions (files allowed to have specific violations)
EXCEPTIONS = {
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

# Hardcoded spacing values in CSS (should use CSS variables)
# Note: 1px values are allowed (borders, hairlines, etc.)
HARDCODED_SPACING_CSS = [
    r"padding:\s*['\"]?[2-9]\d*(?:px|rem|em)",  # 2px+ only (1px allowed)
    r"margin:\s*['\"]?[2-9]\d*(?:px|rem|em)",  # 2px+ only
    r"gap:\s*['\"]?[2-9]\d*(?:px|rem|em)",  # 2px+ only (1px hairlines allowed)
]

# Hardcoded font families
HARDCODED_FONTS = [
    r"fontFamily:\s*['\"].*(?:Inter|system-ui|sans-serif).*['\"]",
    r"font-family:\s*['\"].*(?:Inter|system-ui|sans-serif).*['\"]",
]

# MUI spacing props that should use design tokens instead of numbers
# These props accept numeric values that multiply by theme.spacing (8px default)
MUI_SPACING_PROPS = [
    # Margin props
    r"\bm=\{[\d.]+\}",  # m={2}
    r"\bmt=\{[\d.]+\}",  # mt={2}
    r"\bmb=\{[\d.]+\}",  # mb={2}
    r"\bml=\{[\d.]+\}",  # ml={2}
    r"\bmr=\{[\d.]+\}",  # mr={2}
    r"\bmx=\{[\d.]+\}",  # mx={2}
    r"\bmy=\{[\d.]+\}",  # my={2}
    # Padding props
    r"\bp=\{[\d.]+\}",  # p={2}
    r"\bpt=\{[\d.]+\}",  # pt={2}
    r"\bpb=\{[\d.]+\}",  # pb={2}
    r"\bpl=\{[\d.]+\}",  # pl={2}
    r"\bpr=\{[\d.]+\}",  # pr={2}
    r"\bpx=\{[\d.]+\}",  # px={2}
    r"\bpy=\{[\d.]+\}",  # py={2}
    # Gap/spacing props
    r"\bspacing=\{[\d.]+\}",  # spacing={2}
    r"\bgap=\{[\d.]+\}",  # gap={2}
    r"\browsGap=\{[\d.]+\}",  # rowsGap={2}
    r"\bcolumnGap=\{[\d.]+\}",  # columnGap={2}
]

# MUI sx prop hardcoded values (inside sx={{ ... }})
# These should use design tokens instead
MUI_SX_HARDCODED_SPACING = [
    # Spacing with numeric values (not strings with var())
    r"['\"]?(?:p|pt|pb|pl|pr|px|py|m|mt|mb|ml|mr|mx|my)['\"]?\s*:\s*[\d.]+(?!\s*['\"])",
    # Padding/margin with px values
    r"['\"]?(?:padding|margin)['\"]?\s*:\s*['\"]?\d+(?:px)?['\"]?",
    # Gap with numeric values
    r"['\"]?gap['\"]?\s*:\s*[\d.]+(?!\s*['\"])",
]

MUI_SX_HARDCODED_RADIUS = [
    # borderRadius with numeric values (should use var(--ob-radius-*))
    r"['\"]?borderRadius['\"]?\s*:\s*[\d.]+(?!\s*['\"])",
    r"['\"]?borderRadius['\"]?\s*:\s*['\"]?\d+px['\"]?",
]

# Allowed patterns in sx props (these are legitimate)
SX_ALLOWED_PATTERNS = [
    r"var\(--ob-",  # Design tokens
    r"theme\.",  # Theme references
    r"'[a-z]+\.[a-z]+'",  # Palette references like 'primary.main'
    r'"[a-z]+\.[a-z]+"',  # Palette references like "text.secondary"
    r"inherit",  # Inherit keyword
    r"auto",  # Auto keyword
    r"none",  # None keyword
    r"100%",  # Percentage values (often needed)
    r"'100%'",
    r'"100%"',
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


def is_inline_style_grandfathered(file_path: str) -> bool:
    """Check if file is grandfathered for inline styles."""
    for grandfathered_path in INLINE_STYLE_GRANDFATHERED:
        if grandfathered_path in file_path:
            return True
    return False


def is_allowed_color_pattern(line: str) -> bool:
    """Check if line uses an intentionally allowed color pattern."""
    for pattern in ALLOWED_COLOR_PATTERNS:
        if re.search(pattern, line):
            return True
    return False


def is_color_exception(file_path: str) -> bool:
    """Check if file is excepted from color checks (e.g., Google Maps components)."""
    for exc_path in COLOR_EXCEPTIONS:
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


def is_allowed_sx_value(line: str) -> bool:
    """Check if the sx value uses allowed patterns (design tokens, theme, etc.)."""
    for pattern in SX_ALLOWED_PATTERNS:
        if re.search(pattern, line):
            return True
    return False


def check_mui_spacing_props(line: str, line_num: int, rel_path: str) -> list[Violation]:
    """Check for MUI numeric spacing props like mb={2}, spacing={3}."""
    violations = []

    for pattern in MUI_SPACING_PROPS:
        match = re.search(pattern, line)
        if match:
            violations.append(
                Violation(
                    file=rel_path,
                    line=line_num,
                    rule="no-mui-numeric-spacing",
                    message=(
                        f"MUI numeric spacing prop '{match.group()}' detected. "
                        'Use design token: spacing="var(--ob-space-*)" instead.'
                    ),
                    snippet=line.strip()[:80],
                )
            )

    return violations


def check_mui_sx_prop(line: str, line_num: int, rel_path: str) -> list[Violation]:
    """Check for hardcoded values inside MUI sx={{ }} props."""
    violations = []

    # Only check lines with sx prop
    if "sx={{" not in line and "sx={" not in line:
        return violations

    # Skip if using allowed patterns (design tokens, theme references)
    if is_allowed_sx_value(line):
        return violations

    # Check for hardcoded spacing in sx
    for pattern in MUI_SX_HARDCODED_SPACING:
        match = re.search(pattern, line)
        if match:
            # Double-check it's not using a design token
            matched_text = match.group()
            if "var(--ob-" not in matched_text:
                # Skip 0 values - they don't need design tokens
                if re.search(r":\s*['\"]?0['\"]?\s*$", matched_text):
                    continue
                violations.append(
                    Violation(
                        file=rel_path,
                        line=line_num,
                        rule="no-sx-hardcoded-spacing",
                        message=(
                            f"Hardcoded spacing in sx prop: '{matched_text}'. "
                            "Use design token: 'var(--ob-space-*)' instead."
                        ),
                        snippet=line.strip()[:80],
                    )
                )
                break  # One violation per line for spacing

    # Check for hardcoded border radius in sx
    for pattern in MUI_SX_HARDCODED_RADIUS:
        match = re.search(pattern, line)
        if match:
            matched_text = match.group()
            if "var(--ob-" not in matched_text:
                violations.append(
                    Violation(
                        file=rel_path,
                        line=line_num,
                        rule="no-sx-hardcoded-radius",
                        message=(
                            f"Hardcoded borderRadius in sx prop: '{matched_text}'. "
                            "Use design token: 'var(--ob-radius-*)' instead."
                        ),
                        snippet=line.strip()[:80],
                    )
                )
                break  # One violation per line for radius

    return violations


def check_hardcoded_spacing_css(
    line: str, line_num: int, rel_path: str, file_suffix: str
) -> list[Violation]:
    """Check for hardcoded spacing values in CSS."""
    violations = []

    # Only check CSS files and style blocks
    if file_suffix != ".css" and "style" not in line.lower():
        return violations

    # Skip lines with design tokens
    if "var(--ob-" in line:
        return violations

    for pattern in HARDCODED_SPACING_CSS:
        match = re.search(pattern, line)
        if match:
            violations.append(
                Violation(
                    file=rel_path,
                    line=line_num,
                    rule="no-hardcoded-spacing",
                    message=(
                        f"Hardcoded spacing '{match.group()}' detected. "
                        "Use design token: var(--ob-space-*) instead."
                    ),
                    snippet=line.strip()[:80],
                )
            )
            break

    return violations


def check_hardcoded_fonts(line: str, line_num: int, rel_path: str) -> list[Violation]:
    """Check for hardcoded font family declarations."""
    violations = []

    # Skip lines with design tokens
    if "var(--ob-" in line:
        return violations

    for pattern in HARDCODED_FONTS:
        match = re.search(pattern, line)
        if match:
            violations.append(
                Violation(
                    file=rel_path,
                    line=line_num,
                    rule="no-hardcoded-fonts",
                    message=(
                        "Hardcoded font-family detected. "
                        "Use theme typography or var(--ob-font-*) instead."
                    ),
                    snippet=line.strip()[:80],
                )
            )
            break

    return violations


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

        # Check for inline styles in TSX (but not sx props)
        if file_path.suffix in (".tsx", ".jsx"):
            # Check MUI spacing props (mb={2}, spacing={3}, etc.)
            violations.extend(check_mui_spacing_props(line, line_num, rel_path))

            # Check MUI sx prop for hardcoded values
            violations.extend(check_mui_sx_prop(line, line_num, rel_path))

            # Check inline style={{ }} patterns (skip grandfathered files)
            if not is_inline_style_grandfathered(rel_path):
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
                                    "page-layout.css or MUI sx prop with design tokens."
                                ),
                                snippet=line.strip()[:80],
                            )
                        )
                        break

            # Check hardcoded fonts in TSX
            violations.extend(check_hardcoded_fonts(line, line_num, rel_path))

        # Check for hardcoded colors in style objects and CSS
        if "style" in line.lower() or file_path.suffix == ".css":
            # Skip files with intentional color exceptions (e.g., Google Maps)
            if is_color_exception(rel_path):
                continue

            # Skip intentionally allowed color patterns
            if is_allowed_color_pattern(line):
                continue

            for pattern in HARDCODED_COLORS:
                # Skip CSS variable definitions and usage
                if "var(--" in line or "--ob-" in line:
                    continue

                match = re.search(pattern, line)
                if match:
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
                                "Use CSS variable or theme.palette instead."
                            ),
                            snippet=line.strip()[:80],
                        )
                    )
                    break

        # Check for hardcoded spacing in CSS
        violations.extend(
            check_hardcoded_spacing_css(line, line_num, rel_path, file_path.suffix)
        )

        # Check hardcoded fonts in CSS
        if file_path.suffix == ".css":
            violations.extend(check_hardcoded_fonts(line, line_num, rel_path))

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
        print("")
        print("FIX GUIDE:")
        print("  Spacing: Use var(--ob-space-50|100|150|200|300|400|500|600|800)")
        print("  Radius:  Use var(--ob-radius-xs|sm|md|lg|xl|full)")
        print("  Colors:  Use theme.palette.* or var(--ob-color-*)")
        print("")
        print("See frontend/UI_STANDARDS.md for design token values.")
        print("=" * 80 + "\n")

        # BLOCKING MODE: Fail the build when violations are detected
        return 1

    print("✓ No UI canon violations detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
