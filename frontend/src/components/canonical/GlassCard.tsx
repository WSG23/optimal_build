import { Paper, type PaperProps, useTheme, SxProps, Theme } from '@mui/material'
import type { ReactNode } from 'react'

export interface GlassCardProps extends Omit<
  PaperProps,
  'children' | 'sx' | 'variant'
> {
  children: ReactNode
  className?: string
  elevation?: number
  /** @deprecated Use variant='seamless' instead for new code */
  blur?: number
  /** @deprecated Use variant='seamless' instead for new code */
  opacity?: number
  hoverEffect?: boolean
  /**
   * Card variant:
   * - 'default': Original glass card with MUI Paper background
   * - 'seamless': Zero-card architecture using design tokens (--ob-surface-glass-1)
   */
  variant?: 'default' | 'seamless'
  sx?: SxProps<Theme>
}

export function GlassCard({
  children,
  className,
  elevation = 0,
  blur = 20,
  opacity = 0.85,
  hoverEffect = false,
  variant = 'seamless', // Default to seamless for Zero-Card architecture
  sx = {},
  onClick,
  ...paperProps
}: GlassCardProps) {
  const theme = useTheme()

  // Seamless variant: uses design tokens directly
  // NOTE: No backdrop-filter here to avoid scroll jank from nested blur layers.
  // Blur should only be applied at top-level page containers, not individual cards.
  const seamlessSx: SxProps<Theme> = {
    background: 'var(--ob-surface-glass-1)',
    border: '1px solid var(--ob-color-border-subtle)',
    borderRadius: 0, // Edge-to-edge tile
    transition: 'border-color 0.15s ease',
    overflow: 'hidden',
    cursor: onClick ? 'pointer' : 'default',
    ...(hoverEffect && {
      '&:hover': {
        borderColor: 'var(--ob-color-neon-cyan)',
      },
    }),
  }

  // Default variant: original MUI-based styling (deprecated)
  const defaultSx: SxProps<Theme> = {
    background: `rgba(255, 255, 255, ${opacity * 0.5})`,
    backdropFilter: `blur(${blur}px)`,
    WebkitBackdropFilter: `blur(${blur}px)`,
    border: `1px solid ${theme.palette.divider}`,
    borderRadius: 'var(--ob-radius-sm)',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    overflow: 'hidden',
    cursor: onClick ? 'pointer' : 'default',
    ...(hoverEffect && {
      '&:hover': {
        transform: 'translateY(-4px)',
        boxShadow: theme.shadows[4],
        borderColor: theme.palette.primary.main,
      },
    }),
  }

  const baseSx = variant === 'seamless' ? seamlessSx : defaultSx
  const resolvedSx = Array.isArray(sx) ? sx : [sx]

  return (
    <Paper
      className={className}
      elevation={elevation}
      onClick={onClick}
      {...paperProps}
      sx={[baseSx, ...resolvedSx]}
    >
      {children}
    </Paper>
  )
}
