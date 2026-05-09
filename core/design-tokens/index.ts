/**
 * Design Token TypeScript Exports
 * =============================================================================
 * This file provides type-safe access to CSS variables defined in tokens.css.
 * tokens.css is the SINGLE SOURCE OF TRUTH - this file provides TS types and helpers.
 *
 * Usage:
 *   import { cssVar, cssRgb } from '@ob/tokens';
 *   const style = { background: cssVar('color-bg-surface') };
 * =============================================================================
 */

// =============================================================================
// CSS Variable Helper Functions
// =============================================================================

/**
 * Returns a CSS var() reference for the given token name.
 * @example cssVar('color-bg-surface') => 'var(--ob-color-bg-surface)'
 */
export const cssVar = (token: CssTokenName): string => `var(--ob-${token})`

/**
 * Returns a CSS var() reference for RGB tokens (for use with rgba()).
 * @example cssRgb('color-surface-default-rgb') => 'var(--ob-color-surface-default-rgb)'
 */
export const cssRgb = (token: CssRgbTokenName): string => `var(--ob-${token})`

// =============================================================================
// Token Name Types (Generated from tokens.css)
// =============================================================================

export type CssTokenName =
  // Core Palette - Neutrals
  | 'neutral-950'
  | 'neutral-900'
  | 'neutral-800'
  | 'neutral-700'
  | 'neutral-600'
  | 'neutral-500'
  | 'neutral-400'
  | 'neutral-300'
  | 'neutral-200'
  | 'neutral-100'
  | 'neutral-50'
  // Core Palette - Brand
  | 'brand-700'
  | 'brand-600'
  | 'brand-500'
  | 'brand-400'
  | 'brand-300'
  | 'brand-200'
  | 'brand-100'
  | 'brand-glow'
  // Core Palette - Accent
  | 'accent-600'
  | 'accent-500'
  | 'accent-400'
  | 'accent-300'
  | 'accent-200'
  // Core Palette - Status
  | 'success-700'
  | 'success-600'
  | 'success-500'
  | 'success-400'
  | 'success-bg'
  | 'success-text'
  | 'warning-700'
  | 'warning-600'
  | 'warning-500'
  | 'warning-400'
  | 'warning-bg'
  | 'warning-text'
  | 'error-700'
  | 'error-600'
  | 'error-500'
  | 'error-400'
  | 'error-bg'
  | 'error-text'
  | 'info-700'
  | 'info-600'
  | 'info-500'
  | 'info-400'
  | 'info-bg'
  | 'info-text'
  // Semantic - Surfaces
  | 'color-bg-root'
  | 'color-bg-surface'
  | 'color-bg-surface-elevated'
  | 'surface-glass-1'
  | 'surface-glass-2'
  | 'color-surface-default'
  | 'color-surface-alt'
  | 'color-surface-strong'
  | 'color-surface-inverse'
  // Semantic - Text
  | 'color-text-primary'
  | 'color-text-secondary'
  | 'color-text-muted'
  | 'color-text-subtle'
  | 'color-text-strong'
  | 'color-text-inverse'
  | 'color-text-accent'
  // Semantic - Borders
  | 'color-border-subtle'
  | 'color-border-neutral'
  | 'color-border-strong'
  | 'color-border-focus'
  | 'color-border-brand'
  | 'color-border-warning'
  | 'color-border-error'
  | 'color-border-success'
  | 'border-glass'
  | 'border-glass-strong'
  // Semantic - Brand & Actions
  | 'color-brand-primary'
  | 'color-brand-primary-emphasis'
  | 'color-brand-primary-glow'
  | 'color-brand-accent'
  | 'color-brand-soft'
  | 'color-brand-muted'
  | 'color-brand-strong'
  | 'color-action-hover'
  // Semantic - Status variants
  | 'color-success-soft'
  | 'color-success-strong'
  | 'color-success-muted'
  | 'color-warning-soft'
  | 'color-warning-strong'
  | 'color-warning-muted'
  | 'color-error-soft'
  | 'color-error-strong'
  | 'color-error-muted'
  | 'color-danger-strong'
  | 'color-info-soft'
  | 'color-info-strong'
  | 'color-info-muted'
  // Typography
  | 'font-family-display'
  | 'font-family-base'
  | 'font-family-mono'
  | 'font-size-xs'
  | 'font-size-sm'
  | 'font-size-base'
  | 'font-size-lg'
  | 'font-size-xl'
  | 'font-size-2xl'
  | 'font-size-3xl'
  | 'font-size-4xl'
  | 'font-weight-regular'
  | 'font-weight-medium'
  | 'font-weight-semibold'
  | 'font-weight-bold'
  | 'line-height-tight'
  | 'line-height-normal'
  | 'line-height-relaxed'
  // Spacing
  | 'space-025'
  | 'space-050'
  | 'space-075'
  | 'space-100'
  | 'space-125'
  | 'space-150'
  | 'space-175'
  | 'space-200'
  | 'space-250'
  | 'space-300'
  | 'space-400'
  // Border Radius - Square Cyber-Minimalism
  | 'radius-none'
  | 'radius-xs'
  | 'radius-sm'
  | 'radius-md'
  | 'radius-lg'
  | 'radius-xl'      // DEPRECATED - maps to lg
  | 'radius-2xl'     // DEPRECATED - maps to lg
  | 'radius-md-plus' // DEPRECATED - maps to sm
  | 'radius-pill'
  // Elegant Fine Lines
  | 'border-fine'
  | 'border-fine-strong'
  | 'border-fine-hover'
  | 'divider'
  | 'divider-strong'
  // Glow Effects
  | 'glow-brand-subtle'
  | 'glow-brand-medium'
  | 'glow-brand-strong'
  | 'glow-gold'
  | 'glow-success'
  | 'glow-error'
  | 'glow-warning'
  // Shadows
  | 'shadow-sm'
  | 'shadow-md'
  | 'shadow-lg'
  | 'shadow-xl'
  | 'shadow-glass'
  | 'shadow-glass-lg'
  // Z-Index
  | 'z-dropdown'
  | 'z-sticky'
  | 'z-fixed'
  | 'z-modal-backdrop'
  | 'z-modal'
  | 'z-popover'
  | 'z-tooltip'

export type CssRgbTokenName =
  | 'color-surface-default-rgb'
  | 'color-surface-inverse-rgb'

// =============================================================================
// Static Token Values (for use in non-CSS contexts like MUI theme)
// =============================================================================

/**
 * Color palette values — mirrors tokens.css :root values
 * Use cssVar() in CSS contexts, these values for JS/MUI contexts
 *
 * Color Purposes:
 * - brand: Institutional Slate Blue — Primary brand, interactive states, analytical precision
 * - info: Soft Violet — Informational content, AI insights, metadata
 * - success: Emerald Green — Completed, approved, positive outcomes
 * - warning: Burnt Orange — Pending, attention needed, high priority
 * - error: Soft Red — Failed, rejected, urgent, destructive actions
 */
export const colors = {
  neutral: {
    950: '#0c0a09',
    900: '#151311',
    800: '#1c1917',
    700: '#292524',
    600: '#44403c',
    500: '#78716c',
    400: '#a8a29e',
    300: '#d6d3d1',
    200: '#e7e5e3',
    100: '#f5f5f4',
    50: '#fafaf9',
  },
  /** Institutional Slate Blue — Brand identity, interactive states, analytical precision */
  brand: {
    700: '#1e4f7a',
    600: '#2d6697',
    500: '#3B7CB8',
    400: '#5a9ad4',
    300: '#85b8e4',
    200: '#b3d4f0',
    100: '#e0eefa',
  },
  accent: {
    600: '#059669',
    500: '#10b981',
    400: '#34d399',
    300: '#6ee7b7',
    200: '#d1fae5',
  },
  /** Emerald Green — Completed, approved, positive outcomes */
  success: {
    700: '#047857',
    600: '#059669',
    500: '#10b981',
    400: '#34d399',
  },
  /** Burnt Orange — Pending, attention needed, high priority */
  warning: {
    700: '#b45309',
    600: '#d97706',
    500: '#f59e0b',
    400: '#fbbf24',
  },
  /** Soft Red — Failed, rejected, urgent, destructive actions */
  error: {
    700: '#b91c1c',
    600: '#dc2626',
    500: '#ef4444',
    400: '#f87171',
  },
  /** Soft Violet — Informational states, AI insights, metadata */
  info: {
    700: '#7c3aed',
    600: '#8b5cf6',
    500: '#a78bfa',
    400: '#c4b5fd',
  },
} as const

/**
 * Spacing scale values — mirrors tokens.css
 */
export const spacing = {
  '025': '0.25rem',
  '050': '0.5rem',
  '075': '0.75rem',
  '100': '1rem',
  '125': '1.25rem',
  '150': '1.5rem',
  '175': '1.75rem',
  '200': '2rem',
  '250': '2.5rem',
  '300': '3rem',
  '400': '4rem',
} as const

/**
 * Border radius values — Square Cyber-Minimalism scale
 * Sharp, geometric aesthetic for architect/designer appeal
 */
export const radii = {
  none: '0',           // 0px - tables, data grids
  xs: '0.125rem',      // 2px - buttons, tags, chips
  sm: '0.25rem',       // 4px - cards, panels, tiles
  md: '0.375rem',      // 6px - inputs, select boxes
  lg: '0.5rem',        // 8px - modals, windows ONLY
  pill: '9999px',      // Avatars, circular icons ONLY
  // DEPRECATED - kept for backward compatibility
  xl: '0.5rem',        // Maps to lg
  '2xl': '0.5rem',     // Maps to lg
  'md-plus': '0.25rem', // Maps to sm
} as const

/**
 * Elegant fine line borders — cream-tinted for warmth (dark mode)
 */
export const borders = {
  fine: '1px solid rgba(245, 235, 220, 0.08)',
  fineStrong: '1px solid rgba(245, 235, 220, 0.12)',
  fineHover: '1px solid rgba(245, 235, 220, 0.18)',
  divider: '1px solid rgba(245, 235, 220, 0.06)',
  dividerStrong: '1px solid rgba(245, 235, 220, 0.10)',
} as const

/**
 * Glow effects — brand glows (blue) + gold accent for financial highlights
 */
export const glows = {
  brandSubtle: '0 0 8px rgba(59, 124, 184, 0.15)',
  brandMedium: '0 0 12px rgba(59, 124, 184, 0.25)',
  brandStrong: '0 0 20px rgba(59, 124, 184, 0.4)',
  gold: '0 0 12px rgba(200, 169, 81, 0.25)', // Gold kept for financial highlights
  success: '0 0 10px rgba(34, 197, 94, 0.2)',
  error: '0 0 10px rgba(239, 68, 68, 0.2)',
  warning: '0 0 10px rgba(234, 179, 8, 0.2)',
} as const

/**
 * Typography values — Founders-OS canonical typography
 */
export const typography = {
  family: {
    display: "'Zilla Slab', Georgia, serif",
    base: "'Hanken Grotesk', 'Helvetica Neue', -apple-system, sans-serif",
    mono: "'JetBrains Mono', 'Roboto Mono', monospace",
  },
  size: {
    '2xs': '0.6875rem',
    xs: '0.75rem',
    'sm-minus': '0.8125rem',
    sm: '0.875rem',
    md: '0.9375rem',
    base: '1rem',
    lg: '1.125rem',
    xl: '1.25rem',
    '2xl': '1.5rem',
    '3xl': '1.875rem',
    '4xl': '2.25rem',
    '5xl': '3rem',
  },
  weight: {
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  lineHeight: {
    none: 1,
    tight: 1.2,
    snug: 1.4,
    normal: 1.5,
    relaxed: 1.6,
    loose: 1.75,
  },
  letterSpacing: {
    tighter: '-0.02em',
    tight: '-0.01em',
    normal: '0',
    wide: '0.01em',
    wider: '0.02em',
    widest: '0.05em',
    caps: '0.1em',
  },
} as const

/**
 * Shadow values — mirrors tokens.css (dark mode defaults)
 */
export const shadows = {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.5)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.5)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.5)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.5)',
  glass: '0 8px 32px 0 rgba(0, 0, 0, 0.5)',
  glassLg: '0 12px 40px 0 rgba(0, 0, 0, 0.6)',
} as const

/**
 * Z-index scale — mirrors tokens.css
 */
export const zIndex = {
  dropdown: 1000,
  sticky: 1020,
  fixed: 1030,
  modalBackdrop: 1040,
  modal: 1050,
  popover: 1060,
  tooltip: 1070,
} as const

// =============================================================================
// Bundled Exports
// =============================================================================

export type TokenExports = {
  colors: typeof colors
  spacing: typeof spacing
  radii: typeof radii
  borders: typeof borders
  glows: typeof glows
  typography: typeof typography
  shadows: typeof shadows
  zIndex: typeof zIndex
}

export const tokens: TokenExports = {
  colors,
  spacing,
  radii,
  borders,
  glows,
  typography,
  shadows,
  zIndex,
}
