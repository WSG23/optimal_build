import { Typography, TypographyProps, SxProps, Theme } from '@mui/material'
import { ReactNode } from 'react'

export interface NeonTextProps extends Omit<TypographyProps, 'sx'> {
  children: ReactNode
  /**
   * Color variant.
   * - 'default': inherits text.primary — use for data readout values
   * - 'brand': uses brand accent — use for highlighted/interactive values
   * - 'success' / 'warning' / 'error': semantic status colors
   */
  color?: 'default' | 'brand' | 'cyan' | 'success' | 'warning' | 'error'
  /** @deprecated No longer applies visual effect. Kept for API compat. */
  intensity?: 'subtle' | 'medium' | 'strong'
  animate?: boolean
  sx?: SxProps<Theme>
}

const colorConfig: Record<string, { color: string }> = {
  default: {
    color: 'var(--ob-color-text-primary, inherit)',
  },
  brand: {
    color: 'var(--ob-color-brand-primary)',
  },
  // 'cyan' kept as alias for 'brand' for backward compat
  cyan: {
    color: 'var(--ob-color-brand-primary)',
  },
  success: {
    color: 'var(--ob-success-400)',
  },
  warning: {
    color: 'var(--ob-warning-400)',
  },
  error: {
    color: 'var(--ob-error-400)',
  },
}

/**
 * AccentText — Colored text for metric values and status indicators.
 *
 * Use `color="default"` (the default) for data readout values.
 * Use `color="brand"` for highlighted or interactive values.
 * Use `color="success"` / `color="error"` for trend indicators.
 *
 * Exported as both `NeonText` (legacy) and `AccentText` (preferred).
 */
export function NeonText({
  children,
  intensity: _intensity = 'medium',
  color = 'default',
  animate = false,
  variant = 'body1',
  sx = {},
  ...typographyProps
}: NeonTextProps) {
  const config = colorConfig[color] ?? colorConfig.default

  return (
    <Typography
      variant={variant}
      {...typographyProps}
      sx={{
        color: config.color,
        fontWeight: 'var(--ob-font-weight-bold)',
        ...(animate && {
          animation:
            'ob-fade-in var(--ob-motion-duration-moderate) ease-out both',
        }),
        '@media (prefers-reduced-motion: reduce)': {
          animation: 'none',
        },
        ...sx,
      }}
    >
      {children}
    </Typography>
  )
}

/** Preferred name for NeonText */
export const AccentText = NeonText
