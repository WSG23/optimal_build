import { Box, SxProps, Theme } from '@mui/material'

export interface PulsingStatusDotProps {
  /**
   * Status type determines color and glow
   */
  status: 'live' | 'success' | 'warning' | 'error' | 'inactive'
  /**
   * Size of the dot
   */
  size?: 'sm' | 'md' | 'lg'
  /**
   * Whether the dot pulses
   */
  pulse?: boolean
  /**
   * Additional styles
   */
  sx?: SxProps<Theme>
}

const statusColors = {
  live: {
    bg: 'var(--ob-color-neon-cyan)',
    glow: 'var(--ob-glow-status-live)',
  },
  success: {
    bg: 'var(--ob-success-500)',
    glow: 'var(--ob-glow-status-success)',
  },
  warning: {
    bg: 'var(--ob-warning-500)',
    glow: 'var(--ob-glow-status-warning)',
  },
  error: {
    bg: 'var(--ob-error-500)',
    glow: 'var(--ob-glow-status-error)',
  },
  inactive: {
    bg: 'var(--ob-neutral-600)',
    glow: 'none',
  },
}

const sizes = {
  sm: 'var(--ob-space-600)',
  md: 8,
  lg: 10,
}

/**
 * PulsingStatusDot - Animated Status Indicator
 *
 * Premium cyber aesthetic with pulsing glow animation.
 * Uses neon cyan for "live" status, semantic colors for others.
 *
 * Usage:
 * ```tsx
 * <PulsingStatusDot status="live" pulse />
 * <PulsingStatusDot status="success" />
 * <PulsingStatusDot status="error" size="lg" />
 * ```
 */
export function PulsingStatusDot({
  status,
  size = 'md',
  pulse = true,
  sx = {},
}: PulsingStatusDotProps) {
  const colors = statusColors[status]
  const dotSize = sizes[size]

  return (
    <Box
      className={pulse && status !== 'inactive' ? 'ob-status-pulse-glow' : ''}
      sx={{
        width: dotSize,
        height: dotSize,
        borderRadius: 'var(--ob-radius-xs)', // Square cyber-minimalism
        backgroundColor: colors.bg,
        boxShadow: pulse && status !== 'inactive' ? colors.glow : 'none',
        flexShrink: 0,
        ...sx,
      }}
    />
  )
}
