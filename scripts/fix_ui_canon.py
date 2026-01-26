#!/usr/bin/env python3
"""
UI Canon Auto-Fixer - Automatically fixes common UI canon violations.

This script applies automated fixes for:
1. MUI numeric spacing props (mb={2} → mb="var(--ob-space-200)")
2. MUI sx hardcoded spacing (p: 3 → p: 'var(--ob-space-300)')
3. MUI sx hardcoded radius (borderRadius: 2 → borderRadius: 'var(--ob-radius-sm)')
4. CSS hardcoded spacing (padding: 1rem → padding: var(--ob-space-200))
5. Inline style hardcoded spacing (gap: '16px' → gap: 'var(--ob-space-200)')

Run as: python scripts/fix_ui_canon.py [--dry-run]
"""

import argparse
import re
import sys
from pathlib import Path

# MUI spacing unit is 8px by default
# Map numeric values to design tokens
SPACING_MAP = {
    0: "0",
    0.5: "var(--ob-space-50)",  # 4px
    1: "var(--ob-space-100)",  # 8px
    1.5: "var(--ob-space-150)",  # 12px
    2: "var(--ob-space-200)",  # 16px
    3: "var(--ob-space-300)",  # 24px
    4: "var(--ob-space-400)",  # 32px
    5: "var(--ob-space-500)",  # 40px
    6: "var(--ob-space-600)",  # 48px
    8: "var(--ob-space-800)",  # 64px
}

# Map pixel values to design tokens
PX_SPACING_MAP = {
    0: "0",
    1: "1px",  # Keep 1px as-is (border widths)
    2: "var(--ob-space-50)",  # 2px → 4px
    4: "var(--ob-space-50)",  # 4px
    6: "var(--ob-space-100)",  # 6px → 8px
    8: "var(--ob-space-100)",  # 8px
    10: "var(--ob-space-100)",  # 10px → 8px
    12: "var(--ob-space-150)",  # 12px
    16: "var(--ob-space-200)",  # 16px
    20: "var(--ob-space-200)",  # 20px → 16px
    24: "var(--ob-space-300)",  # 24px
    32: "var(--ob-space-400)",  # 32px
    40: "var(--ob-space-500)",  # 40px
    48: "var(--ob-space-600)",  # 48px
    64: "var(--ob-space-800)",  # 64px
}

# Map rem values to design tokens (1rem = 16px typically)
REM_SPACING_MAP = {
    0.25: "var(--ob-space-50)",  # 4px
    0.5: "var(--ob-space-100)",  # 8px
    0.75: "var(--ob-space-150)",  # 12px
    1: "var(--ob-space-200)",  # 16px
    1.25: "var(--ob-space-200)",  # 20px → 16px
    1.5: "var(--ob-space-300)",  # 24px
    2: "var(--ob-space-400)",  # 32px
    2.5: "var(--ob-space-500)",  # 40px
    3: "var(--ob-space-600)",  # 48px
    4: "var(--ob-space-800)",  # 64px
}

# borderRadius map (MUI default shape.borderRadius = 4px)
RADIUS_MAP = {
    0: "var(--ob-radius-none)",  # 0px
    0.5: "var(--ob-radius-xs)",  # 2px
    1: "var(--ob-radius-sm)",  # 4px
    2: "var(--ob-radius-sm)",  # 8px → use sm for consistency
    3: "var(--ob-radius-md)",  # 12px → use md
    4: "var(--ob-radius-sm)",  # 16px → too large, use sm
}

# Color mapping: hex colors to theme.palette or CSS variables
# Format: hex_color (lowercase) -> replacement
COLOR_MAP = {
    # White/light backgrounds
    "#fff": "var(--ob-color-bg-default)",
    "#ffffff": "var(--ob-color-bg-default)",
    "#f9fafb": "var(--ob-color-bg-muted)",
    "#f5f5f7": "var(--ob-color-bg-muted)",
    "#f4f4f8": "var(--ob-color-bg-muted)",
    # Gray text colors (secondary text)
    "#6b7280": "var(--ob-color-text-secondary)",  # gray-500
    "#6e6e73": "var(--ob-color-text-secondary)",
    "#64748b": "var(--ob-color-text-secondary)",  # slate-500
    "#9ca3af": "var(--ob-color-text-tertiary)",  # gray-400
    "#94a3b8": "var(--ob-color-text-tertiary)",  # slate-400
    # Darker grays (for stronger secondary text)
    "#4b5563": "var(--ob-color-text-secondary)",  # gray-600
    "#374151": "var(--ob-color-text-primary)",  # gray-700
    # Border colors
    "#e5e7eb": "var(--ob-color-border-subtle)",  # gray-200
    "#d1d5db": "var(--ob-color-border-default)",  # gray-300
    "#d2d2d7": "var(--ob-color-border-default)",
    "#e5e5e7": "var(--ob-color-border-subtle)",
    # Dark backgrounds
    "#1d1d1f": "var(--ob-color-bg-inverse)",
    "#111827": "var(--ob-color-bg-inverse)",  # gray-900
    "#0a1628": "var(--ob-color-bg-inverse)",
    "#3a3a3c": "var(--ob-color-bg-elevated)",
    # Primary/brand colors
    "#0096cc": "var(--ob-color-primary)",
    "#00f3ff": "var(--ob-color-neon-cyan)",
    "#3b82f6": "var(--ob-color-primary)",  # blue-500
    # Status colors
    "#10b981": "var(--ob-color-success)",  # green-500
    "#f59e0b": "var(--ob-color-warning)",  # amber-500
    "#dc2626": "var(--ob-color-error)",  # red-600
    "#f87171": "var(--ob-color-error-light)",  # red-400 (lighter error)
    "#b45309": "var(--ob-color-warning-dark)",  # amber-600 (darker warning)
    "#b91c1c": "var(--ob-color-error-dark)",  # red-700 (darker error)
    # Additional gray colors
    "#ccc": "var(--ob-color-text-tertiary)",  # light gray
    "#cccccc": "var(--ob-color-text-tertiary)",  # light gray (full hex)
    # Additional brand/primary colors
    "#0a84ff": "var(--ob-color-primary)",  # iOS blue
    # Slate grays - Note: #94a3b8 (slate-400) mapped to text-tertiary above
    # Black
    "#000": "var(--ob-color-bg-inverse)",
    "#000000": "var(--ob-color-bg-inverse)",
    # Blue accent colors
    "#1d4ed8": "var(--ob-color-primary)",  # blue-700
    # Red/error colors
    "#fee2e2": "var(--ob-color-error-muted)",  # red-100 (error background)
    "#991b1b": "var(--ob-color-error-dark)",  # red-800 (error text)
    # Green/success colors
    "#166534": "var(--ob-color-success-dark)",  # green-800 (success text)
}

# RGBA color mappings based on UI_STANDARDS.md design tokens
# Note: These map common rgba() patterns to semantic design tokens
RGBA_MAP = {
    # Action states (dark mode values)
    "rgba(255, 255, 255, 0.08)": "var(--ob-color-action-hover)",
    "rgba(255,255,255,0.08)": "var(--ob-color-action-hover)",
    "rgba(255, 255, 255, 0.12)": "var(--ob-color-action-active)",
    "rgba(255,255,255,0.12)": "var(--ob-color-action-active)",
    # Selection states (cyan brand color)
    "rgba(0, 243, 255, 0.1)": "var(--ob-color-action-selected)",
    "rgba(0,243,255,0.1)": "var(--ob-color-action-selected)",
    "rgba(0, 243, 255, 0.15)": "var(--ob-color-action-selected-strong)",
    "rgba(0,243,255,0.15)": "var(--ob-color-action-selected-strong)",
    # Table states
    "rgba(255, 255, 255, 0.02)": "var(--ob-color-table-row-alt)",
    "rgba(255,255,255,0.02)": "var(--ob-color-table-row-alt)",
    "rgba(255, 255, 255, 0.03)": "var(--ob-color-table-header)",
    "rgba(255,255,255,0.03)": "var(--ob-color-table-header)",
    "rgba(0, 243, 255, 0.05)": "var(--ob-color-table-row-hover)",
    "rgba(0,243,255,0.05)": "var(--ob-color-table-row-hover)",
    "rgba(0, 243, 255, 0.08)": "var(--ob-color-table-row-selected)",
    "rgba(0,243,255,0.08)": "var(--ob-color-table-row-selected)",
    # Input/surface states
    "rgba(255, 255, 255, 0.04)": "var(--ob-color-surface-input)",
    "rgba(255,255,255,0.04)": "var(--ob-color-surface-input)",
    "rgba(255, 255, 255, 0.06)": "var(--ob-color-surface-input-hover)",
    "rgba(255,255,255,0.06)": "var(--ob-color-surface-input-hover)",
    # Common overlays
    "rgba(255, 255, 255, 0.05)": "var(--ob-color-surface-overlay-light)",
    "rgba(255,255,255,0.05)": "var(--ob-color-surface-overlay-light)",
    "rgba(255, 255, 255, 0.1)": "var(--ob-color-surface-overlay)",
    "rgba(255,255,255,0.1)": "var(--ob-color-surface-overlay)",
    # Light mode action states
    "rgba(0, 0, 0, 0.05)": "var(--ob-color-action-hover-light)",
    "rgba(0,0,0,0.05)": "var(--ob-color-action-hover-light)",
    "rgba(0, 0, 0, 0.1)": "var(--ob-color-action-active-light)",
    "rgba(0,0,0,0.1)": "var(--ob-color-action-active-light)",
    # Additional white overlays (stronger opacity)
    "rgba(255, 255, 255, 0.2)": "var(--ob-color-surface-overlay-medium)",
    "rgba(255,255,255,0.2)": "var(--ob-color-surface-overlay-medium)",
    "rgba(255, 255, 255, 0.3)": "var(--ob-color-surface-overlay-strong)",
    "rgba(255,255,255,0.3)": "var(--ob-color-surface-overlay-strong)",
    "rgba(255, 255, 255, 0.15)": "var(--ob-color-action-active)",
    "rgba(255,255,255,0.15)": "var(--ob-color-action-active)",
    # Modal/backdrop overlays
    "rgba(0, 0, 0, 0.5)": "var(--ob-color-overlay-backdrop)",
    "rgba(0,0,0,0.5)": "var(--ob-color-overlay-backdrop)",
    "rgba(0, 0, 0, 0.4)": "var(--ob-color-overlay-backdrop)",
    "rgba(0,0,0,0.4)": "var(--ob-color-overlay-backdrop)",
    "rgba(0, 0, 0, 0.6)": "var(--ob-color-overlay-backdrop-strong)",
    "rgba(0,0,0,0.6)": "var(--ob-color-overlay-backdrop-strong)",
    # Blue selection states (light mode)
    "rgba(59, 130, 246, 0.2)": "var(--ob-color-action-selected)",
    "rgba(59,130,246,0.2)": "var(--ob-color-action-selected)",
    "rgba(59, 130, 246, 0.1)": "var(--ob-color-action-selected)",
    "rgba(59,130,246,0.1)": "var(--ob-color-action-selected)",
    "rgba(59, 130, 246, 0.5)": "var(--ob-color-action-focus-ring)",
    "rgba(59,130,246,0.5)": "var(--ob-color-action-focus-ring)",
    # Cyan brand glow effects
    "rgba(6, 182, 212, 0.3)": "var(--ob-color-neon-cyan-muted)",
    "rgba(6,182,212,0.3)": "var(--ob-color-neon-cyan-muted)",
    "rgba(6, 182, 212, 0.2)": "var(--ob-color-neon-cyan-muted)",
    "rgba(6,182,212,0.2)": "var(--ob-color-neon-cyan-muted)",
    "rgba(6, 182, 212, 0.8)": "var(--ob-color-neon-cyan)",
    "rgba(6,182,212,0.8)": "var(--ob-color-neon-cyan)",
    "rgba(0, 243, 255, 0.2)": "var(--ob-color-action-selected-strong)",
    "rgba(0,243,255,0.2)": "var(--ob-color-action-selected-strong)",
    "rgba(0, 243, 255, 0.3)": "var(--ob-color-neon-cyan-muted)",
    "rgba(0,243,255,0.3)": "var(--ob-color-neon-cyan-muted)",
    # Additional light-mode shadow/border colors
    "rgba(0, 0, 0, 0.04)": "var(--ob-color-border-subtle)",
    "rgba(0,0,0,0.04)": "var(--ob-color-border-subtle)",
    "rgba(0, 0, 0, 0.08)": "var(--ob-color-action-hover-light)",
    "rgba(0,0,0,0.08)": "var(--ob-color-action-hover-light)",
    "rgba(37, 99, 235, 0.05)": "var(--ob-color-table-row-hover)",
    "rgba(37,99,235,0.05)": "var(--ob-color-table-row-hover)",
    # Semi-transparent white text
    "rgba(255, 255, 255, 0.7)": "var(--ob-color-text-secondary)",
    "rgba(255,255,255,0.7)": "var(--ob-color-text-secondary)",
    "rgba(255, 255, 255, 0.85)": "var(--ob-color-text-primary)",
    "rgba(255,255,255,0.85)": "var(--ob-color-text-primary)",
    # Light gray backgrounds (light mode surfaces)
    "rgba(248, 250, 252, 0.92)": "var(--ob-color-bg-default)",
    "rgba(248,250,252,0.92)": "var(--ob-color-bg-default)",
    "rgba(148, 163, 184, 0.18)": "var(--ob-color-border-subtle)",
    "rgba(148,163,184,0.18)": "var(--ob-color-border-subtle)",
    # Additional high-opacity white overlays
    "rgba(255, 255, 255, 0.9)": "var(--ob-color-bg-default)",
    "rgba(255,255,255,0.9)": "var(--ob-color-bg-default)",
    "rgba(255, 255, 255, 0.5)": "var(--ob-color-border-default)",
    "rgba(255,255,255,0.5)": "var(--ob-color-border-default)",
    # Subtle black overlays
    "rgba(0, 0, 0, 0.02)": "var(--ob-color-table-row-alt)",
    "rgba(0,0,0,0.02)": "var(--ob-color-table-row-alt)",
    # Blue shadow/glow effects
    "rgba(0, 118, 255, 0.39)": "var(--ob-color-primary-muted)",
    "rgba(0,118,255,0.39)": "var(--ob-color-primary-muted)",
    # Stronger black shadows/overlays
    "rgba(0, 0, 0, 0.2)": "var(--ob-color-overlay-backdrop-light)",
    "rgba(0,0,0,0.2)": "var(--ob-color-overlay-backdrop-light)",
    "rgba(0, 0, 0, 0.12)": "var(--ob-color-action-active-light)",
    "rgba(0,0,0,0.12)": "var(--ob-color-action-active-light)",
    # Cyan brand variants
    "rgba(6, 182, 212, 0.1)": "var(--ob-color-action-selected)",
    "rgba(6,182,212,0.1)": "var(--ob-color-action-selected)",
    "rgba(6, 182, 212, 0.7)": "var(--ob-color-neon-cyan)",
    "rgba(6,182,212,0.7)": "var(--ob-color-neon-cyan)",
    # Slate/neutral border colors
    "rgba(148, 163, 184, 0.35)": "var(--ob-color-border-subtle)",
    "rgba(148,163,184,0.35)": "var(--ob-color-border-subtle)",
    "rgba(148, 163, 184, 0.25)": "var(--ob-color-border-subtle)",
    "rgba(148,163,184,0.25)": "var(--ob-color-border-subtle)",
    "rgba(15, 23, 42, 0.15)": "var(--ob-color-border-subtle)",
    "rgba(15,23,42,0.15)": "var(--ob-color-border-subtle)",
    # Semi-transparent white borders/glass effects
    "rgba(255, 255, 255, 0.25)": "var(--ob-color-border-subtle)",
    "rgba(255,255,255,0.25)": "var(--ob-color-border-subtle)",
    # Neon cyan animation/glow colors
    "rgba(0, 243, 255, 0.6)": "var(--ob-color-neon-cyan)",
    "rgba(0,243,255,0.6)": "var(--ob-color-neon-cyan)",
    "rgba(0, 243, 255, 0.02)": "var(--ob-color-table-row-alt)",
    "rgba(0,243,255,0.02)": "var(--ob-color-table-row-alt)",
    "rgba(0, 243, 255, 0.04)": "var(--ob-color-action-selected)",
    "rgba(0,243,255,0.04)": "var(--ob-color-action-selected)",
    # Subtle black shadows/backgrounds
    "rgba(0, 0, 0, 0.03)": "var(--ob-color-table-header)",
    "rgba(0,0,0,0.03)": "var(--ob-color-table-header)",
    "rgba(0, 0, 0, 0.06)": "var(--ob-color-action-hover-light)",
    "rgba(0,0,0,0.06)": "var(--ob-color-action-hover-light)",
    "rgba(0, 0, 0, 0.3)": "var(--ob-color-overlay-backdrop-light)",
    "rgba(0,0,0,0.3)": "var(--ob-color-overlay-backdrop-light)",
    # Slate shadows
    "rgba(15, 23, 42, 0.12)": "var(--ob-color-action-active-light)",
    "rgba(15,23,42,0.12)": "var(--ob-color-action-active-light)",
    # Alternative cyan (0, 229, 255) - close to neon cyan
    "rgba(0, 229, 255, 0.1)": "var(--ob-color-action-selected)",
    "rgba(0,229,255,0.1)": "var(--ob-color-action-selected)",
    "rgba(0, 229, 255, 0.3)": "var(--ob-color-neon-cyan-muted)",
    "rgba(0,229,255,0.3)": "var(--ob-color-neon-cyan-muted)",
    # Semi-transparent white text/elements
    "rgba(255, 255, 255, 0.4)": "var(--ob-color-text-tertiary)",
    "rgba(255,255,255,0.4)": "var(--ob-color-text-tertiary)",
    # Dark overlays for cockpit/modal backgrounds
    "rgba(20, 20, 20, 0.75)": "var(--ob-color-overlay-backdrop-strong)",
    "rgba(20,20,20,0.75)": "var(--ob-color-overlay-backdrop-strong)",
    "rgba(20, 20, 20, 0.6)": "var(--ob-color-overlay-backdrop)",
    "rgba(20,20,20,0.6)": "var(--ob-color-overlay-backdrop)",
    "rgba(0, 0, 0, 0.8)": "var(--ob-color-overlay-backdrop-strong)",
    "rgba(0,0,0,0.8)": "var(--ob-color-overlay-backdrop-strong)",
    # Indigo accent colors
    "rgba(99, 102, 241, 0.1)": "var(--ob-color-action-selected)",
    "rgba(99,102,241,0.1)": "var(--ob-color-action-selected)",
    "rgba(99, 102, 241, 0.3)": "var(--ob-color-primary-muted)",
    "rgba(99,102,241,0.3)": "var(--ob-color-primary-muted)",
    # Deep slate shadows
    "rgba(15, 23, 42, 0.35)": "var(--ob-color-overlay-backdrop-light)",
    "rgba(15,23,42,0.35)": "var(--ob-color-overlay-backdrop-light)",
    "rgba(15, 23, 42, 0.08)": "var(--ob-color-action-hover-light)",
    "rgba(15,23,42,0.08)": "var(--ob-color-action-hover-light)",
    # Slate borders with various opacities
    "rgba(148, 163, 184, 0.24)": "var(--ob-color-border-subtle)",
    "rgba(148,163,184,0.24)": "var(--ob-color-border-subtle)",
    "rgba(148, 163, 184, 0.45)": "var(--ob-color-border-default)",
    "rgba(148,163,184,0.45)": "var(--ob-color-border-default)",
    "rgba(148, 163, 184, 0.12)": "var(--ob-color-action-hover-light)",
    "rgba(148,163,184,0.12)": "var(--ob-color-action-hover-light)",
    # Blue accent backgrounds
    "rgba(37, 99, 235, 0.12)": "var(--ob-color-action-selected)",
    "rgba(37,99,235,0.12)": "var(--ob-color-action-selected)",
    # Status color backgrounds (for indicators)
    "rgba(220, 38, 38, 0.12)": "var(--ob-color-error-muted)",  # red-600 12% - error bg
    "rgba(220,38,38,0.12)": "var(--ob-color-error-muted)",
    "rgba(22, 163, 74, 0.15)": "var(--ob-color-success-muted)",  # green-600 15% - success bg
    "rgba(22,163,74,0.15)": "var(--ob-color-success-muted)",
    # Note: rgba(..., 0) values are intentionally used for animation endpoints
    # Keep them as-is since they represent "fully transparent"
}

# Files to skip
SKIP_PATTERNS = [
    "node_modules",
    "__tests__",
    ".test.tsx",
    ".test.ts",
    ".stories.tsx",
    "test/",
]


def should_skip(file_path: str) -> bool:
    """Check if file should be skipped."""
    for pattern in SKIP_PATTERNS:
        if pattern in file_path:
            return True
    return False


def get_spacing_token(value: float) -> str:
    """Get the closest spacing token for a numeric value."""
    if value in SPACING_MAP:
        return SPACING_MAP[value]
    # Find closest match
    closest = min(SPACING_MAP.keys(), key=lambda x: abs(x - value))
    return SPACING_MAP[closest]


def get_px_spacing_token(px_value: int) -> str:
    """Get the spacing token for a pixel value."""
    if px_value in PX_SPACING_MAP:
        return PX_SPACING_MAP[px_value]
    # Find closest match
    closest = min(PX_SPACING_MAP.keys(), key=lambda x: abs(x - px_value))
    return PX_SPACING_MAP[closest]


def get_rem_spacing_token(rem_value: float) -> str:
    """Get the spacing token for a rem value."""
    if rem_value in REM_SPACING_MAP:
        return REM_SPACING_MAP[rem_value]
    # Find closest match
    closest = min(REM_SPACING_MAP.keys(), key=lambda x: abs(x - rem_value))
    return REM_SPACING_MAP[closest]


def get_radius_token(value: float) -> str:
    """Get the radius token for a numeric value."""
    if value in RADIUS_MAP:
        return RADIUS_MAP[value]
    return "var(--ob-radius-sm)"


def fix_mui_spacing_props(content: str) -> tuple[str, int]:
    """Fix MUI numeric spacing props like mb={2} → mb="var(--ob-space-200)"."""
    count = 0
    props = [
        "m",
        "mt",
        "mb",
        "ml",
        "mr",
        "mx",
        "my",
        "p",
        "pt",
        "pb",
        "pl",
        "pr",
        "px",
        "py",
        "spacing",
        "gap",
        "rowGap",
        "columnGap",
    ]

    for prop in props:
        pattern = rf"\b{prop}=\{{([\d.]+)\}}"

        def replacer(match, _prop=prop):
            nonlocal count
            value = float(match.group(1))
            token = get_spacing_token(value)
            count += 1
            return f'{_prop}="{token}"'

        content = re.sub(pattern, replacer, content)

    return content, count


def fix_sx_spacing(content: str) -> tuple[str, int]:
    """Fix hardcoded spacing in sx props like p: 3 → p: 'var(--ob-space-300)'."""
    count = 0
    props = [
        "p",
        "pt",
        "pb",
        "pl",
        "pr",
        "px",
        "py",
        "m",
        "mt",
        "mb",
        "ml",
        "mr",
        "mx",
        "my",
        "gap",
    ]

    for prop in props:
        pattern = rf"(['\"]?{prop}['\"]?\s*:\s*)([\d.]+)(\s*[,}}\n])"

        def replacer(match):
            nonlocal count
            prefix = match.group(1)
            value = float(match.group(2))
            suffix = match.group(3)
            token = get_spacing_token(value)
            count += 1
            return f"{prefix}'{token}'{suffix}"

        content = re.sub(pattern, replacer, content)

    return content, count


def fix_sx_radius(content: str) -> tuple[str, int]:
    """Fix hardcoded borderRadius in sx props."""
    count = 0

    pattern = r"(['\"]?borderRadius['\"]?\s*:\s*)([\d.]+)(\s*[,}}\n])"

    def replacer(match):
        nonlocal count
        prefix = match.group(1)
        value = float(match.group(2))
        suffix = match.group(3)
        token = get_radius_token(value)
        count += 1
        return f"{prefix}'{token}'{suffix}"

    content = re.sub(pattern, replacer, content)

    # Also fix borderRadius: 'Npx' patterns
    pattern2 = r"(['\"]?borderRadius['\"]?\s*:\s*)['\"](\d+)px['\"](\s*[,}}\n])"

    def replacer2(match):
        nonlocal count
        prefix = match.group(1)
        px_value = int(match.group(2))
        suffix = match.group(3)
        if px_value <= 2:
            token = "var(--ob-radius-xs)"
        elif px_value <= 4:
            token = "var(--ob-radius-sm)"
        elif px_value <= 6:
            token = "var(--ob-radius-md)"
        else:
            token = "var(--ob-radius-lg)"
        count += 1
        return f"{prefix}'{token}'{suffix}"

    content = re.sub(pattern2, replacer2, content)

    return content, count


def fix_css_spacing(content: str, is_css_file: bool = False) -> tuple[str, int]:
    """Fix hardcoded spacing in CSS and inline styles."""
    count = 0
    props = ["padding", "margin", "gap"]

    # Fix pixel values: padding: 16px → padding: var(--ob-space-200)
    for prop in props:
        # CSS file pattern: property: Npx
        if is_css_file:
            pattern = rf"({prop}:\s*)(\d+)(px)(\s*[;,\n])"
        else:
            # Inline style pattern: property: 'Npx' or property: "Npx"
            pattern = rf"({prop}:\s*)['\"](\d+)(px)['\"]"

        def replacer_px(match):
            nonlocal count
            prefix = match.group(1)
            px_value = int(match.group(2))
            if is_css_file:
                suffix = match.group(4)
                token = get_px_spacing_token(px_value)
                count += 1
                return f"{prefix}{token}{suffix}"
            else:
                token = get_px_spacing_token(px_value)
                count += 1
                return f"{prefix}'{token}'"

        content = re.sub(pattern, replacer_px, content)

    # Fix rem values: padding: 1rem → padding: var(--ob-space-200)
    for prop in props:
        if is_css_file:
            pattern = rf"({prop}:\s*)([\d.]+)(rem)(\s*[;,\n])"
        else:
            pattern = rf"({prop}:\s*)['\"]?([\d.]+)(rem)['\"]?"

        def replacer_rem(match):
            nonlocal count
            prefix = match.group(1)
            rem_value = float(match.group(2))
            if is_css_file:
                suffix = match.group(4)
                token = get_rem_spacing_token(rem_value)
                count += 1
                return f"{prefix}{token}{suffix}"
            else:
                token = get_rem_spacing_token(rem_value)
                count += 1
                return f"{prefix}'{token}'"

        content = re.sub(pattern, replacer_rem, content)

    return content, count


def fix_colors(content: str) -> tuple[str, int]:
    """Fix hardcoded hex colors with design tokens."""
    count = 0

    for hex_color, token in COLOR_MAP.items():
        # Pattern 1: color: '#fff' or color: "#fff" (direct color property)
        pattern1 = rf"(:\s*)['\"]({re.escape(hex_color)})['\"]"

        def replacer1(match, _token=token):
            nonlocal count
            prefix = match.group(1)
            count += 1
            return f"{prefix}'{_token}'"

        content = re.sub(pattern1, replacer1, content, flags=re.IGNORECASE)

        # Pattern 2: color: '#fff', (with comma/end) in sx props
        pattern2 = (
            rf"(color|backgroundColor|background|borderColor|fill|stroke)"
            rf":\s*['\"]({re.escape(hex_color)})['\"]"
        )

        def replacer2(match, _token=token):
            nonlocal count
            prop = match.group(1)
            count += 1
            return f"{prop}: '{_token}'"

        content = re.sub(pattern2, replacer2, content, flags=re.IGNORECASE)

        # Pattern 3: border: '1px solid #hex' - replace the hex within the border value
        pattern3 = (
            rf"(border[a-zA-Z]*:\s*['\"][^'\"]*?)({re.escape(hex_color)})([^'\"]*['\"])"
        )

        def replacer3(match, _token=token):
            nonlocal count
            prefix = match.group(1)
            suffix = match.group(3)
            count += 1
            return f"{prefix}{_token}{suffix}"

        content = re.sub(pattern3, replacer3, content, flags=re.IGNORECASE)

        # Pattern 4: DOM style property assignment: .style.background = '#hex'
        pattern4 = rf"(\.style\.[a-zA-Z]+\s*=\s*)['\"]({re.escape(hex_color)})['\"]"

        def replacer4(match, _token=token):
            nonlocal count
            prefix = match.group(1)
            count += 1
            return f"{prefix}'{_token}'"

        content = re.sub(pattern4, replacer4, content, flags=re.IGNORECASE)

    return content, count


def fix_css_colors(content: str) -> tuple[str, int]:
    """Fix hardcoded hex colors in CSS files."""
    count = 0

    for hex_color, token in COLOR_MAP.items():
        # Pattern 1: color: #fff; or background: #ffffff; or #fff !important;
        pattern = rf"(:\s*)({re.escape(hex_color)})(\s*(?:[;,\n\}}\)]|!important))"

        def replacer(match, _token=token):
            nonlocal count
            prefix = match.group(1)
            suffix = match.group(3)
            count += 1
            return f"{prefix}{_token}{suffix}"

        content = re.sub(pattern, replacer, content, flags=re.IGNORECASE)

        # Pattern 2: Gradient stops like #0096cc 0%, or #0096cc 100%
        pattern2 = rf"({re.escape(hex_color)})(\s+\d+%)"

        def replacer2(match, _token=token):
            nonlocal count
            suffix = match.group(2)
            count += 1
            return f"{_token}{suffix}"

        content = re.sub(pattern2, replacer2, content, flags=re.IGNORECASE)

        # Pattern 3: border: 1px solid #hex (hex in CSS border property)
        pattern3 = rf"(border[^:]*:\s*[^;]*?)({re.escape(hex_color)})([^;]*;)"

        def replacer3(match, _token=token):
            nonlocal count
            prefix = match.group(1)
            suffix = match.group(3)
            count += 1
            return f"{prefix}{_token}{suffix}"

        content = re.sub(pattern3, replacer3, content, flags=re.IGNORECASE)

    return content, count


def fix_rgba_colors(content: str) -> tuple[str, int]:
    """Fix common rgba() patterns with design tokens from UI_STANDARDS.md."""
    count = 0

    for rgba_value, token in RGBA_MAP.items():
        # Escape the rgba value for regex (parentheses, etc.)
        escaped = re.escape(rgba_value)

        # Pattern 1: 'rgba(...)' or "rgba(...)" as the entire quoted value
        pattern = rf"['\"]({escaped})['\"]"

        def replacer(match, _token=token):
            nonlocal count
            count += 1
            return f"'{_token}'"

        content = re.sub(pattern, replacer, content, flags=re.IGNORECASE)

        # Pattern 2: rgba(...) embedded within a quoted string
        # (e.g., textShadow: '0 0 10px rgba(...)')
        pattern_embedded = rf"(['\"][^'\"]*?)({escaped})([^'\"]*['\"])"

        def replacer_embedded(match, _token=token):
            nonlocal count
            prefix = match.group(1)
            suffix = match.group(3)
            count += 1
            return f"{prefix}{_token}{suffix}"

        content = re.sub(
            pattern_embedded, replacer_embedded, content, flags=re.IGNORECASE
        )

        # Pattern 3: CSS - rgba(...) followed by ; , or } or ) or !important
        pattern_css = rf"({escaped})(\s*(?:[;,\}}\)]|!important))"

        def replacer_css(match, _token=token):
            nonlocal count
            suffix = match.group(2)
            count += 1
            return f"{_token}{suffix}"

        content = re.sub(pattern_css, replacer_css, content, flags=re.IGNORECASE)

        # Pattern 4: rgba(...) followed by space (e.g., in box-shadow values)
        pattern_space = rf"({escaped})(\s+[^;,\}}\)'\"])"

        def replacer_space(match, _token=token):
            nonlocal count
            suffix = match.group(2)
            count += 1
            return f"{_token}{suffix}"

        content = re.sub(pattern_space, replacer_space, content, flags=re.IGNORECASE)

    return content, count


def fix_inline_style_spacing(content: str) -> tuple[str, int]:
    """Fix hardcoded spacing in inline style={{ }} props."""
    count = 0

    # Fix gap: 'Npx' patterns in inline styles
    pattern = r"(gap:\s*)['\"](\d+)(px)['\"]"

    def replacer(match):
        nonlocal count
        prefix = match.group(1)
        px_value = int(match.group(2))
        token = get_px_spacing_token(px_value)
        count += 1
        return f"{prefix}'{token}'"

    content = re.sub(pattern, replacer, content)

    # Fix gap: 'Nrem' patterns
    pattern2 = r"(gap:\s*)['\"]?([\d.]+)(rem)['\"]?"

    def replacer2(match):
        nonlocal count
        prefix = match.group(1)
        rem_value = float(match.group(2))
        token = get_rem_spacing_token(rem_value)
        count += 1
        return f"{prefix}'{token}'"

    content = re.sub(pattern2, replacer2, content)

    # Fix marginTop: 'Npx' etc
    margin_props = ["marginTop", "marginBottom", "marginLeft", "marginRight", "margin"]
    padding_props = [
        "paddingTop",
        "paddingBottom",
        "paddingLeft",
        "paddingRight",
        "padding",
    ]

    for prop in margin_props + padding_props:
        pattern = rf"({prop}:\s*)['\"](\d+)(px)['\"]"

        def replacer_prop(match):
            nonlocal count
            prefix = match.group(1)
            px_value = int(match.group(2))
            token = get_px_spacing_token(px_value)
            count += 1
            return f"{prefix}'{token}'"

        content = re.sub(pattern, replacer_prop, content)

        # rem version
        pattern_rem = rf"({prop}:\s*)['\"]?([\d.]+)(rem)['\"]?"

        def replacer_prop_rem(match):
            nonlocal count
            prefix = match.group(1)
            rem_value = float(match.group(2))
            token = get_rem_spacing_token(rem_value)
            count += 1
            return f"{prefix}'{token}'"

        content = re.sub(pattern_rem, replacer_prop_rem, content)

    return content, count


def process_tsx_file(file_path: Path, dry_run: bool = False) -> dict:
    """Process a TSX file and apply fixes."""
    if should_skip(str(file_path)):
        return {"skipped": True}

    try:
        original = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return {"error": str(e)}

    content = original
    fixes = {
        "spacing_props": 0,
        "sx_spacing": 0,
        "sx_radius": 0,
        "inline_spacing": 0,
        "colors": 0,
        "rgba_colors": 0,
    }

    content, count = fix_mui_spacing_props(content)
    fixes["spacing_props"] = count

    content, count = fix_sx_spacing(content)
    fixes["sx_spacing"] = count

    content, count = fix_sx_radius(content)
    fixes["sx_radius"] = count

    content, count = fix_inline_style_spacing(content)
    fixes["inline_spacing"] = count

    content, count = fix_colors(content)
    fixes["colors"] = count

    content, count = fix_rgba_colors(content)
    fixes["rgba_colors"] = count

    total = sum(fixes.values())

    if total > 0 and content != original:
        if not dry_run:
            file_path.write_text(content, encoding="utf-8")
        return {"fixes": fixes, "total": total, "modified": not dry_run}

    return {"fixes": fixes, "total": 0}


def process_css_file(file_path: Path, dry_run: bool = False) -> dict:
    """Process a CSS file and apply fixes."""
    if should_skip(str(file_path)):
        return {"skipped": True}

    try:
        original = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return {"error": str(e)}

    content = original
    fixes = {"css_spacing": 0, "css_colors": 0, "css_rgba_colors": 0}

    content, count = fix_css_spacing(content, is_css_file=True)
    fixes["css_spacing"] = count

    content, count = fix_css_colors(content)
    fixes["css_colors"] = count

    content, count = fix_rgba_colors(content)
    fixes["css_rgba_colors"] = count

    total = sum(fixes.values())

    if total > 0 and content != original:
        if not dry_run:
            file_path.write_text(content, encoding="utf-8")
        return {"fixes": fixes, "total": total, "modified": not dry_run}

    return {"fixes": fixes, "total": 0}


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Auto-fix UI canon violations")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without making changes",
    )
    args = parser.parse_args()

    frontend_dir = Path(__file__).parent.parent / "frontend" / "src"

    if not frontend_dir.exists():
        print(f"Frontend directory not found: {frontend_dir}")
        return 1

    total_fixes = {
        "spacing_props": 0,
        "sx_spacing": 0,
        "sx_radius": 0,
        "inline_spacing": 0,
        "colors": 0,
        "rgba_colors": 0,
        "css_spacing": 0,
        "css_colors": 0,
        "css_rgba_colors": 0,
    }
    files_modified = 0

    print("=" * 60)
    if args.dry_run:
        print("DRY RUN - No files will be modified")
    print("Scanning for UI canon violations to fix...")
    print("=" * 60)

    # Process TSX files
    for tsx_file in frontend_dir.rglob("*.tsx"):
        result = process_tsx_file(tsx_file, dry_run=args.dry_run)

        if result.get("total", 0) > 0:
            fixes = result["fixes"]
            print(f"\n{tsx_file.relative_to(frontend_dir.parent)}")
            if fixes.get("spacing_props"):
                print(f"  - MUI spacing props: {fixes['spacing_props']}")
            if fixes.get("sx_spacing"):
                print(f"  - sx spacing: {fixes['sx_spacing']}")
            if fixes.get("sx_radius"):
                print(f"  - sx radius: {fixes['sx_radius']}")
            if fixes.get("inline_spacing"):
                print(f"  - inline spacing: {fixes['inline_spacing']}")
            if fixes.get("colors"):
                print(f"  - colors: {fixes['colors']}")
            if fixes.get("rgba_colors"):
                print(f"  - rgba colors: {fixes['rgba_colors']}")

            for key in fixes:
                if key in total_fixes:
                    total_fixes[key] += fixes[key]

            if result.get("modified"):
                files_modified += 1

    # Process CSS files
    for css_file in frontend_dir.rglob("*.css"):
        result = process_css_file(css_file, dry_run=args.dry_run)

        if result.get("total", 0) > 0:
            fixes = result["fixes"]
            print(f"\n{css_file.relative_to(frontend_dir.parent)}")
            if fixes.get("css_spacing"):
                print(f"  - CSS spacing: {fixes['css_spacing']}")
            if fixes.get("css_colors"):
                print(f"  - CSS colors: {fixes['css_colors']}")
            if fixes.get("css_rgba_colors"):
                print(f"  - CSS rgba colors: {fixes['css_rgba_colors']}")

            for key in fixes:
                if key in total_fixes:
                    total_fixes[key] += fixes[key]

            if result.get("modified"):
                files_modified += 1

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"MUI spacing props fixed: {total_fixes['spacing_props']}")
    print(f"sx spacing fixed: {total_fixes['sx_spacing']}")
    print(f"sx radius fixed: {total_fixes['sx_radius']}")
    print(f"Inline spacing fixed: {total_fixes['inline_spacing']}")
    print(f"Colors (TSX) fixed: {total_fixes['colors']}")
    print(f"RGBA colors (TSX) fixed: {total_fixes['rgba_colors']}")
    print(f"CSS spacing fixed: {total_fixes['css_spacing']}")
    print(f"CSS colors fixed: {total_fixes['css_colors']}")
    print(f"CSS rgba colors fixed: {total_fixes['css_rgba_colors']}")
    print(f"Total fixes: {sum(total_fixes.values())}")
    print(f"Files modified: {files_modified}")

    if args.dry_run:
        print("\nRun without --dry-run to apply fixes")

    return 0


if __name__ == "__main__":
    sys.exit(main())
