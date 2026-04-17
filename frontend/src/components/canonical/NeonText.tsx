import { Typography, TypographyProps, SxProps, Theme } from '@mui/material'
import { ReactNode } from 'react'

export interface NeonTextProps extends Omit<TypographyProps, 'sx'> {
  /**
   * Content to display
   */
  children: ReactNode
  /**
   * Glow intensity
   */
  intensity?: 'subtle' | 'medium' | 'strong'
  /**
   * Color variant
   */
  color?: 'cyan' | 'success' | 'warning' | 'error'
  /**
   * Whether to animate the glow
   */
  animate?: boolean
  /**
   * Additional styles
   */
  sx?: SxProps<Theme>
}

const colorConfig = {
  cyan: {
    color: 'var(--ob-color-neon-cyan)',
    glowSubtle: '0 0 4px var(--ob-glow-brand-color-30)',
    glowMedium: 'var(--ob-glow-neon-text)',
    glowStrong: 'var(--ob-glow-neon-cyan)',
  },
  success: {
    color: 'var(--ob-success-400)',
    glowSubtle: '0 0 4px var(--ob-glow-success-color-30)',
    glowMedium: '0 0 6px var(--ob-glow-success-color-40)',
    glowStrong: 'var(--ob-glow-status-success)',
  },
  warning: {
    color: 'var(--ob-warning-400)',
    glowSubtle: '0 0 4px var(--ob-glow-warning-color-30)',
    glowMedium: '0 0 6px var(--ob-glow-warning-color-40)',
    glowStrong: 'var(--ob-glow-status-warning)',
  },
  error: {
    color: 'var(--ob-error-400)',
    glowSubtle: '0 0 4px var(--ob-glow-error-color-30)',
    glowMedium: '0 0 6px var(--ob-glow-error-color-40)',
    glowStrong: 'var(--ob-glow-status-error)',
  },
}

/**
 * NeonText - Glowing Text Component
 *
 * Premium cyber aesthetic with neon glow effect.
 * Use for key metrics, highlighted values, and emphasis.
 *
 * Usage:
 * ```tsx
 * <NeonText variant="h3" intensity="strong">$1,234,567</NeonText>
 * <NeonText color="success" intensity="medium">+15.2%</NeonText>
 * <NeonText color="error">-5.3%</NeonText>
 * ```
 */
export function NeonText({
  children,
  intensity = 'medium',
  color = 'cyan',
  animate = false,
  variant = 'body1',
  sx = {},
  ...typographyProps
}: NeonTextProps) {
  const config = colorConfig[color]
  const glow =
    intensity === 'subtle'
      ? config.glowSubtle
      : intensity === 'strong'
        ? config.glowStrong
        : config.glowMedium

  return (
    <Typography
      variant={variant}
      {...typographyProps}
      sx={{
        color: config.color,
        textShadow: intensity === 'strong' ? glow : 'none',
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
