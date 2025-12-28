import { Box, Typography, SxProps, Theme } from '@mui/material'
import { ReactNode } from 'react'

export interface StatusChipProps {
  /**
   * Status text
   */
  children: ReactNode
  /**
   * Status type determines color
   */
  status:
    | 'success'
    | 'warning'
    | 'error'
    | 'info'
    | 'neutral'
    | 'brand'
    | 'live'
  /**
   * Size variant
   */
  size?: 'sm' | 'md'
  /**
   * Leading icon
   */
  icon?: ReactNode
  /**
   * Pulsing dot indicator
   */
  pulse?: boolean
  /**
   * Additional styles
   */
  sx?: SxProps<Theme>
}

const statusColors = {
  success: {
    bg: 'var(--ob-color-success-soft)',
    text: 'var(--ob-color-status-success-text)',
    border: 'var(--ob-success-500)',
    dot: 'var(--ob-success-400)',
  },
  warning: {
    bg: 'var(--ob-color-warning-soft)',
    text: 'var(--ob-color-status-warning-text)',
    border: 'var(--ob-warning-500)',
    dot: 'var(--ob-warning-400)',
  },
  error: {
    bg: 'var(--ob-color-error-soft)',
    text: 'var(--ob-color-status-error-text)',
    border: 'var(--ob-error-500)',
    dot: 'var(--ob-error-400)',
  },
  info: {
    bg: 'var(--ob-color-info-soft)',
    text: 'var(--ob-color-status-info-text)',
    border: 'var(--ob-info-500)',
    dot: 'var(--ob-info-400)',
  },
  neutral: {
    bg: 'var(--ob-color-surface-strong)',
    text: 'var(--ob-color-text-secondary)',
    border: 'var(--ob-neutral-600)',
    dot: 'var(--ob-neutral-400)',
  },
  brand: {
    bg: 'var(--ob-color-brand-soft)',
    text: 'var(--ob-color-brand-primary)',
    border: 'var(--ob-brand-500)',
    dot: 'var(--ob-brand-400)',
  },
  live: {
    bg: 'rgba(0, 243, 255, 0.1)',
    text: 'var(--ob-color-neon-cyan)',
    border: 'rgba(0, 243, 255, 0.3)',
    dot: 'var(--ob-color-neon-cyan)',
  },
}

/**
 * StatusChip - Status Indicator Component
 *
 * Geometry: 2px border radius (--ob-radius-xs)
 * Height: 20px (sm), 24px (md)
 * Border: 1px colored based on status
 *
 * Used for showing status in tables, cards, and lists.
 */
export function StatusChip({
  children,
  status,
  size = 'md',
  icon,
  pulse = false,
  sx = {},
}: StatusChipProps) {
  const colors = statusColors[status]
  const height = size === 'sm' ? '20px' : '24px'
  const fontSize =
    size === 'sm' ? 'var(--ob-font-size-xs)' : 'var(--ob-font-size-sm)'
  const dotSize = size === 'sm' ? 6 : 8

  return (
    <Box
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        height,
        px: 'var(--ob-space-075)',
        gap: 'var(--ob-space-050)',
        borderRadius: 'var(--ob-radius-xs)', // 2px - ENFORCED
        background: colors.bg,
        border: `1px solid ${colors.border}`,
        ...sx,
      }}
    >
      {/* Pulsing dot or icon */}
      {(pulse || icon) && (
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {icon ? (
            <Box
              sx={{
                color: colors.text,
                display: 'flex',
                '& svg': { fontSize: size === 'sm' ? 12 : 14 },
              }}
            >
              {icon}
            </Box>
          ) : (
            <Box
              sx={{
                width: dotSize,
                height: dotSize,
                borderRadius: '50%',
                background: colors.dot,
                ...(pulse && {
                  animation: 'statusPulse 2s ease-in-out infinite',
                  '@keyframes statusPulse': {
                    '0%, 100%': { opacity: 1 },
                    '50%': { opacity: 0.4 },
                  },
                }),
              }}
            />
          )}
        </Box>
      )}
      <Typography
        component="span"
        sx={{
          color: colors.text,
          fontSize,
          fontWeight: 'var(--ob-font-weight-medium)',
          lineHeight: 1,
          whiteSpace: 'nowrap',
        }}
      >
        {children}
      </Typography>
    </Box>
  )
}
