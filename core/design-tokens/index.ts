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
  // Border Radius
  | 'radius-sm'
  | 'radius-md'
  | 'radius-lg'
  | 'radius-xl'
  | 'radius-2xl'
  | 'radius-pill'
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
 * Color palette values - mirrors tokens.css :root values
 * Use cssVar() in CSS contexts, these values for JS/MUI contexts
 */
export const colors = {
  neutral: {
    950: '#121212',
    900: '#1e293b',
    800: '#334155',
    700: '#475569',
    600: '#64748b',
    500: '#94a3b8',
    400: '#cbd5e1',
    300: '#e2e8f0',
    200: '#f1f5f9',
    100: '#f8fafc',
    50: '#ffffff',
  },
  brand: {
    700: '#1d4ed8',
    600: '#2563eb',
    500: '#3b82f6',
    400: '#60a5fa',
    300: '#93c5fd',
    200: '#bfdbfe',
    100: '#dbeafe',
  },
  accent: {
    600: '#059669',
    500: '#10b981',
    400: '#34d399',
    300: '#6ee7b7',
    200: '#d1fae5',
  },
  success: {
    700: '#047857',
    600: '#059669',
    500: '#10b981',
    400: '#34d399',
  },
  warning: {
    700: '#b45309',
    600: '#d97706',
    500: '#f59e0b',
    400: '#fbbf24',
  },
  error: {
    700: '#b91c1c',
    600: '#dc2626',
    500: '#ef4444',
    400: '#f87171',
  },
  info: {
    700: '#1d4ed8',
    600: '#2563eb',
    500: '#3b82f6',
    400: '#60a5fa',
  },
} as const

/**
 * Spacing scale values - mirrors tokens.css
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
 * Border radius values - mirrors tokens.css
 */
export const radii = {
  sm: '0.375rem',
  md: '0.5rem',
  lg: '0.75rem',
  xl: '1rem',
  '2xl': '1.5rem',
  pill: '9999px',
} as const

/**
 * Typography values - mirrors tokens.css
 */
export const typography = {
  family: {
    base: "'Inter', system-ui, -apple-system, sans-serif",
    mono: "'JetBrains Mono', 'Roboto Mono', monospace",
  },
  size: {
    xs: '0.75rem',
    sm: '0.875rem',
    base: '1rem',
    lg: '1.125rem',
    xl: '1.25rem',
    '2xl': '1.5rem',
    '3xl': '1.875rem',
    '4xl': '2.25rem',
  },
  weight: {
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  lineHeight: {
    tight: 1.2,
    normal: 1.5,
    relaxed: 1.6,
  },
} as const

/**
 * Shadow values - mirrors tokens.css (dark mode defaults)
 */
export const shadows = {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.3)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.3)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.3)',
  glass: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
  glassLg: '0 12px 40px 0 rgba(0, 0, 0, 0.4)',
} as const

/**
 * Z-index scale - mirrors tokens.css
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
  typography: typeof typography
  shadows: typeof shadows
  zIndex: typeof zIndex
}

export const tokens: TokenExports = {
  colors,
  spacing,
  radii,
  typography,
  shadows,
  zIndex,
}
