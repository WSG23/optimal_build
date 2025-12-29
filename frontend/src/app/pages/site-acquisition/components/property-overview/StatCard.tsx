/**
 * StatCard - Atomic Card Architecture Component
 *
 * Implements UX Friction Solution #1: Cognitive Overload & Data Density
 * - One metric per card (atomic design)
 * - Hierarchical typography: tiny uppercase label + large bold value
 * - Optional trend indicator and sparkline/progress
 *
 * @see frontend/UX_ARCHITECTURE.md - Problem 1: Cognitive Overload & Data Density
 */

import { Box, Typography, SxProps, Theme } from '@mui/material'
import { ReactNode } from 'react'
import { GlassCard } from '../../../../../components/canonical/GlassCard'
import { PulsingStatusDot } from '../../../../../components/canonical/PulsingStatusDot'

export interface StatCardProps {
  /** Tiny uppercase label (e.g., "EST. REVENUE") */
  label: string
  /** Large bold value (e.g., "S$16.9M") */
  value: ReactNode
  /** Optional subtitle/secondary info below value */
  subtitle?: string
  /** Optional trend percentage (positive = green, negative = red) */
  trend?: number
  /** Optional status indicator */
  status?: 'live' | 'success' | 'warning' | 'error' | 'inactive'
  /** Optional progress value (0-100) */
  progress?: number
  /** Optional icon */
  icon?: ReactNode
  /** Compact mode for smaller spaces */
  compact?: boolean
  /** Additional styles */
  sx?: SxProps<Theme>
}

export function StatCard({
  label,
  value,
  subtitle,
  trend,
  status,
  progress,
  icon,
  compact = false,
  sx = {},
}: StatCardProps) {
  const getTrendColor = (t: number) => {
    if (t > 0) return 'var(--ob-success-500)'
    if (t < 0) return 'var(--ob-error-500)'
    return 'var(--ob-text-secondary)'
  }

  const formatTrend = (t: number) => {
    const sign = t > 0 ? '+' : ''
    return `${sign}${t.toFixed(1)}%`
  }

  return (
    <GlassCard
      sx={{
        p: compact ? 'var(--ob-space-100)' : 'var(--ob-space-150)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-050)',
        height: '100%',
        ...sx,
      }}
    >
      {/* Header: Status + Label + Icon */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 'var(--ob-space-050)',
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--ob-space-050)',
          }}
        >
          {status && <PulsingStatusDot status={status} size="sm" />}
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-2xs)',
              fontWeight: 600,
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              color: 'var(--ob-text-secondary)',
            }}
          >
            {label}
          </Typography>
        </Box>
        {icon && (
          <Box sx={{ color: 'var(--ob-text-tertiary)', display: 'flex' }}>
            {icon}
          </Box>
        )}
      </Box>

      {/* Value - Large bold text */}
      <Typography
        sx={{
          fontSize: compact
            ? 'var(--ob-font-size-2xl)'
            : 'var(--ob-font-size-3xl)',
          fontWeight: 700,
          color: 'var(--ob-color-text-primary)',
          lineHeight: 1.1,
        }}
      >
        {value}
      </Typography>

      {/* Optional subtitle */}
      {subtitle && (
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-xs)',
            color: 'var(--ob-text-secondary)',
          }}
        >
          {subtitle}
        </Typography>
      )}

      {/* Optional trend indicator */}
      {trend !== undefined && (
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-xs)',
            fontWeight: 600,
            color: getTrendColor(trend),
          }}
        >
          {formatTrend(trend)}
        </Typography>
      )}

      {/* Optional progress bar */}
      {progress !== undefined && (
        <Box
          sx={{
            mt: 'var(--ob-space-050)',
            height: 4,
            bgcolor: 'var(--ob-surface-glass-subtle)',
            borderRadius: 'var(--ob-radius-xs)',
            overflow: 'hidden',
          }}
        >
          <Box
            sx={{
              height: '100%',
              width: `${Math.min(100, Math.max(0, progress))}%`,
              bgcolor:
                status === 'success'
                  ? 'var(--ob-success-500)'
                  : status === 'warning'
                    ? 'var(--ob-warning-500)'
                    : status === 'error'
                      ? 'var(--ob-error-500)'
                      : 'var(--ob-color-neon-cyan)',
              transition: 'width 0.3s ease',
            }}
          />
        </Box>
      )}
    </GlassCard>
  )
}
