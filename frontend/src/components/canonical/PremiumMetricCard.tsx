import { Box, Skeleton, Typography, SxProps, Theme } from '@mui/material'
import { ReactNode } from 'react'
import { Card } from './Card'
import { NeonText } from './NeonText'
import { PulsingStatusDot } from './PulsingStatusDot'

export interface PremiumMetricCardProps {
  /**
   * Metric label (e.g., "Total Revenue")
   */
  label: string
  /**
   * Metric value (can be formatted string or ReactNode)
   */
  value: ReactNode
  /**
   * Optional trend percentage (positive = green, negative = red)
   */
  trend?: number
  /**
   * Trend label (e.g., "vs last month")
   */
  trendLabel?: string
  /**
   * Loading state
   */
  loading?: boolean
  /**
   * Icon to display
   */
  icon?: ReactNode
  /**
   * Status indicator
   */
  status?: 'live' | 'success' | 'warning' | 'error' | 'inactive'
  /**
   * Whether this is a featured/highlighted metric
   */
  featured?: boolean
  /**
   * Progress value (0-100) for circular progress ring
   */
  progress?: number
  /**
   * Compact mode for smaller spaces
   */
  compact?: boolean
  /**
   * Click handler
   */
  onClick?: () => void
  /**
   * Additional styles
   */
  sx?: SxProps<Theme>
}

/**
 * PremiumMetricCard - Cyber Aesthetic Metric Display
 *
 * Premium version with:
 * - Glassmorphism background
 * - Neon glow on value
 * - Optional progress ring
 * - Pulsing status indicator
 * - Holographic shine on featured state
 *
 * Usage:
 * ```tsx
 * <PremiumMetricCard
 *   label="Total NPV"
 *   value="$1,234,567"
 *   trend={15.2}
 *   status="live"
 *   featured
 * />
 * ```
 */
export function PremiumMetricCard({
  label,
  value,
  trend,
  trendLabel,
  loading = false,
  icon,
  status,
  featured = false,
  progress,
  compact = false,
  onClick,
  sx = {},
}: PremiumMetricCardProps) {
  const getTrendColor = (t: number) => {
    if (t > 0) return 'success' as const
    if (t < 0) return 'error' as const
    return 'cyan' as const
  }

  const formatTrend = (t: number) => {
    const sign = t > 0 ? '+' : ''
    return `${sign}${t.toFixed(1)}%`
  }

  return (
    <Card
      variant="premium"
      hover={onClick ? 'glow' : 'subtle'}
      accent={featured}
      animated={!loading}
      onClick={onClick}
      sx={{
        p: compact ? 'var(--ob-space-150)' : 'var(--ob-space-200)',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-100)',
        position: 'relative',
        overflow: 'hidden',
        // Holographic shine effect on featured cards
        ...(featured && {
          '&::after': {
            content: '""',
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(120deg, transparent 30%, var(--ob-color-table-row-hover) 50%, transparent 70%)',
            backgroundSize: '200% 100%',
            animation:
              'ob-holographic-shine var(--ob-motion-shine-duration) ease-in-out infinite',
            pointerEvents: 'none',
          },
          '@keyframes ob-holographic-shine': {
            '0%': { backgroundPosition: '-200% center' },
            '100%': { backgroundPosition: '200% center' },
          },
          '@media (prefers-reduced-motion: reduce)': {
            '&::after': { animation: 'none' },
          },
        }),
        ...sx,
      }}
    >
      {/* Header Row */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--ob-space-075)',
          }}
        >
          {status && <PulsingStatusDot status={status} size="sm" />}
          <Typography
            variant="overline"
            sx={{
              color: 'var(--ob-text-dim)',
              fontWeight: 'var(--ob-font-weight-semibold)',
              fontSize: 'var(--ob-font-size-xs)',
              letterSpacing: 'var(--ob-letter-spacing-wider)',
              textTransform: 'uppercase',
            }}
          >
            {label}
          </Typography>
        </Box>
        {icon && (
          <Box
            sx={{
              color: 'var(--ob-color-neon-cyan)',
              opacity: 0.7,
              display: 'flex',
            }}
          >
            {icon}
          </Box>
        )}
      </Box>

      {/* Value Section */}
      <Box sx={{ flex: 1, display: 'flex', alignItems: 'center' }}>
        {loading ? (
          <Skeleton
            width="70%"
            height={compact ? 36 : 48}
            animation="wave"
            sx={{
              transform: 'none',
              borderRadius: 'var(--ob-radius-sm)',
              bgcolor: 'var(--ob-overlay-light)',
            }}
          />
        ) : progress !== undefined ? (
          /* Layout with progress ring */
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--ob-space-150)',
              width: '100%',
            }}
          >
            {/* Progress Ring */}
            <Box
              sx={{
                position: 'relative',
                width: compact ? 48 : 64,
                height: compact ? 48 : 64,
                flexShrink: 0,
              }}
            >
              <svg
                viewBox="0 0 36 36"
                style={{
                  width: '100%',
                  height: '100%',
                  transform: 'rotate(-90deg)',
                }}
              >
                {/* Background circle */}
                <circle
                  cx="18"
                  cy="18"
                  r="15.5"
                  fill="none"
                  stroke="var(--ob-overlay-medium)"
                  strokeWidth="3"
                />
                {/* Progress circle */}
                <circle
                  cx="18"
                  cy="18"
                  r="15.5"
                  fill="none"
                  stroke="var(--ob-color-neon-cyan)"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeDasharray={`${progress} 100`}
                  style={{
                    filter: 'drop-shadow(0 0 4px rgba(0, 243, 255, 0.5))',
                  }}
                />
              </svg>
              <Typography
                sx={{
                  position: 'absolute',
                  inset: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 'var(--ob-font-size-xs)',
                  fontWeight: 'var(--ob-font-weight-bold)',
                  color: 'var(--ob-color-neon-cyan)',
                }}
              >
                {Math.round(progress)}%
              </Typography>
            </Box>
            {/* Value next to ring */}
            <NeonText
              variant={compact ? 'h5' : 'h4'}
              intensity={featured ? 'strong' : 'medium'}
            >
              {value}
            </NeonText>
          </Box>
        ) : (
          /* Standard value display */
          <NeonText
            variant={compact ? 'h4' : 'h3'}
            intensity={featured ? 'strong' : 'medium'}
            sx={{
              fontSize: compact
                ? 'var(--ob-font-size-2xl)'
                : 'var(--ob-font-size-3xl)',
              lineHeight: 1.1,
            }}
          >
            {value}
          </NeonText>
        )}
      </Box>

      {/* Trend Row */}
      {(trend !== undefined || loading) && (
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--ob-space-075)',
          }}
        >
          {loading ? (
            <Skeleton
              width="30%"
              height={20}
              animation="wave"
              sx={{ borderRadius: 'var(--ob-radius-xs)' }}
            />
          ) : (
            <>
              <NeonText
                variant="caption"
                color={getTrendColor(trend!)}
                intensity="subtle"
                sx={{
                  fontWeight: 'var(--ob-font-weight-semibold)',
                  px: 'var(--ob-space-050)',
                  py: '2px',
                  borderRadius: 'var(--ob-radius-xs)',
                  bgcolor:
                    trend! > 0
                      ? 'rgba(0, 255, 157, 0.1)'
                      : trend! < 0
                        ? 'rgba(255, 51, 102, 0.1)'
                        : 'var(--ob-overlay-subtle)',
                }}
              >
                {formatTrend(trend!)}
              </NeonText>
              {trendLabel && (
                <Typography
                  variant="caption"
                  sx={{
                    color: 'var(--ob-text-dim)',
                    fontSize: 'var(--ob-font-size-xs)',
                  }}
                >
                  {trendLabel}
                </Typography>
              )}
            </>
          )}
        </Box>
      )}
    </Card>
  )
}
