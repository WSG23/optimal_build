export const colors = {
  surface: {
    default: '#ffffff',
    alt: '#f8fafc',
    inverse: '#0f172a',
  },
  border: {
    subtle: '#cbd5f5',
    neutral: '#e2e8f0',
  },
  text: {
    primary: '#1e293b',
    muted: '#475569',
    inverse: '#ffffff',
  },
  brand: {
    primary: '#2563eb',
    primaryEmphasis: '#1d4ed8',
    soft: '#bfdbfe',
  },
  info: {
    strong: '#1e3a8a',
  },
  success: {
    strong: '#15803d',
  },
  warning: {
    strong: '#b45309',
    soft: '#f1f5f9',
  },
  error: {
    strong: '#b91c1c',
    muted: '#991b1b',
    soft: '#fee2e2',
  },
} as const

export const spacing = {
  '025': '0.25rem',
  '035': '0.35rem',
  '050': '0.5rem',
  '065': '0.65rem',
  '075': '0.75rem',
  '085': '0.85rem',
  '090': '0.9rem',
  '095': '0.95rem',
  '100': '1rem',
  '125': '1.25rem',
  '130': '1.3rem',
  '150': '1.5rem',
  '175': '1.75rem',
  '200': '2rem',
  '250': '2.5rem',
  '300': '3rem',
  '400': '4rem',
} as const

export const radii = {
  sm: '0.65rem',
  md: '0.75rem',
  mdPlus: '0.85rem',
  lg: '1rem',
  xl: '1.25rem',
  '2xl': '1.5rem',
  pill: '9999px',
} as const

export const typography = {
  family: {
    base: "'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  },
  weight: {
    regular: 400,
    semibold: 600,
    bold: 700,
  },
} as const

export type CssTokenName =
  | 'color-surface-default'
  | 'color-surface-alt'
  | 'color-surface-inverse'
  | 'color-border-subtle'
  | 'color-border-neutral'
  | 'color-text-primary'
  | 'color-text-muted'
  | 'color-text-inverse'
  | 'color-brand-primary'
  | 'color-brand-primary-emphasis'
  | 'color-brand-soft'
  | 'color-info-strong'
  | 'color-success-strong'
  | 'color-warning-strong'
  | 'color-warning-soft'
  | 'color-error-strong'
  | 'color-error-muted'
  | 'color-error-soft'
  | 'space-025'
  | 'space-035'
  | 'space-050'
  | 'space-065'
  | 'space-075'
  | 'space-085'
  | 'space-090'
  | 'space-095'
  | 'space-100'
  | 'space-125'
  | 'space-130'
  | 'space-150'
  | 'space-175'
  | 'space-200'
  | 'space-250'
  | 'space-300'
  | 'space-400'
  | 'radius-sm'
  | 'radius-md'
  | 'radius-md-plus'
  | 'radius-lg'
  | 'radius-xl'
  | 'radius-2xl'
  | 'radius-pill'
  | 'font-weight-regular'
  | 'font-weight-semibold'
  | 'font-weight-bold'
  | 'font-family-base'

export type CssRgbTokenName =
  | 'color-surface-default-rgb'
  | 'color-surface-alt-rgb'
  | 'color-surface-inverse-rgb'
  | 'color-border-subtle-rgb'
  | 'color-border-neutral-rgb'
  | 'color-text-inverse-muted-rgb'
  | 'color-brand-primary-rgb'
  | 'color-brand-primary-emphasis-rgb'
  | 'color-brand-soft-rgb'

export const cssVar = (token: CssTokenName) => `var(--ob-${token})`

export const cssRgb = (token: CssRgbTokenName) => `var(--ob-${token})`

export type TokenExports = {
  colors: typeof colors
  spacing: typeof spacing
  radii: typeof radii
  typography: typeof typography
}

export const tokens: TokenExports = {
  colors,
  spacing,
  radii,
  typography,
}
