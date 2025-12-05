/**
 * Yōsai Design Tokens
 * "Fortress" Aesthetic: Solid, High-Contrast, Technical.
 * Supports both dark and light modes.
 */

// Dark mode colors (original Yōsai)
export const darkColors = {
    // Sumi (Ink) - Backgrounds and dark surfaces
    sumi: {
        900: '#0a0a0a', // Main background (Void)
        800: '#111111', // Secondary background (Card)
        700: '#1a1a1a', // Tertiary background (Hover)
        600: '#262626', // Border / Divider
    },

    // Ishigaki (Stone) - UI Elements, Borders, Text
    ishigaki: {
        900: '#404040', // Disabled text
        700: '#737373', // Secondary text
        500: '#a3a3a3', // Primary text
        300: '#d4d4d4', // Bright text
        100: '#f5f5f5', // High-contrast text
    },

    // Kin (Gold) - Primary Actions, Highlights
    kin: {
        500: '#E6B422', // Primary Gold
        600: '#C49510', // Hover Gold
        900: '#4D3B00', // Dark Gold Background
    },

    // Akarn (Signal Red) - Errors, Alerts
    akarn: {
        500: '#cf222e',
        900: '#3c0609',
    },

    // Aon (Signal Blue) - Info, Selection
    aon: {
        500: '#0969da',
        900: '#031428',
    },
} as const;

// Light mode colors (Yōsai daylight variant)
export const lightColors = {
    // Shiro (White) - Backgrounds and light surfaces
    sumi: {
        900: '#ffffff', // Main background
        800: '#fafafa', // Secondary background (Card)
        700: '#f5f5f5', // Tertiary background (Hover)
        600: '#e5e5e5', // Border / Divider
    },

    // Ishigaki (Stone) - UI Elements, Borders, Text (inverted for light mode)
    ishigaki: {
        900: '#d4d4d4', // Disabled text
        700: '#a3a3a3', // Secondary text
        500: '#737373', // Primary text (muted)
        300: '#404040', // Standard text
        100: '#171717', // High-contrast text (near-black)
    },

    // Kin (Gold) - Primary Actions, Highlights (slightly deeper for light bg)
    kin: {
        500: '#D4A41A', // Primary Gold (darkened for light bg)
        600: '#B8890E', // Hover Gold
        900: '#FDF6E3', // Light Gold Background
    },

    // Akarn (Signal Red) - Errors, Alerts
    akarn: {
        500: '#dc2626',
        900: '#fef2f2',
    },

    // Aon (Signal Blue) - Info, Selection
    aon: {
        500: '#2563eb',
        900: '#eff6ff',
    },
} as const;

// Default export for backward compatibility (dark mode)
export const colors = darkColors;

// Get colors for a specific mode
export function getColors(mode: 'dark' | 'light') {
    return mode === 'dark' ? darkColors : lightColors;
}

export const typography = {
    fontFamily: {
        sans: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        mono: '"JetBrains Mono", "SF Mono", Consolas, "Liberation Mono", Courier, monospace',
    },
    weights: {
        regular: 400,
        medium: 500,
        bold: 700,
    },
    sizes: {
        xs: '0.75rem',    // 12px
        sm: '0.875rem',   // 14px
        base: '1rem',     // 16px
        lg: '1.125rem',   // 18px
        xl: '1.25rem',    // 20px
        '2xl': '1.5rem',  // 24px
    },
} as const;

export const spacing = {
    0: '0px',
    1: '4px',
    2: '8px',
    3: '12px',
    4: '16px',
    6: '24px',
    8: '32px',
    12: '48px',
    16: '64px',
} as const;

export const radii = {
    none: '0px',
    sm: '2px',   // Sharp/Technical feel
    md: '4px',
    lg: '8px',
    full: '9999px',
} as const;
