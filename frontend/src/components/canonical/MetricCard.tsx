import { Box, Skeleton, Typography } from '@mui/material'
import { ReactNode } from 'react'
import { Card } from './Card'

export interface MetricCardProps {
  label: string
  value: ReactNode
  /**
   * Trend percentage or text.
   * If number, positive is green, negative is red.
   */
  trend?: number | string
  /**
   * Optional trend label (e.g., "vs last month")
   */
  trendLabel?: string
  loading?: boolean
  icon?: ReactNode
  /**
   * Simplified variant for smaller spaces
   */
  compact?: boolean
  /**
   * Apply entrance animation
   */
  animated?: boolean
  onClick?: () => void
}

/**
 * MetricCard - Standardized KPI Display
 *
 * Used for displaying high-level metrics in dashboards.
 * Strictly uses design tokens for typography and spacing.
 */
export function MetricCard({
  label,
  value,
  trend,
  trendLabel,
  loading = false,
  icon,
  compact = false,
  onClick,
  animated = true,
}: MetricCardProps) {
  const getTrendColor = (t: number | string) => {
    if (typeof t === 'number') {
      if (t > 0) return 'var(--ob-color-success-text)'
      if (t < 0) return 'var(--ob-color-error-text)'
    }
    return 'var(--ob-color-text-secondary)'
  }

  const formatTrend = (t: number | string) => {
    if (typeof t === 'number') {
      const sign = t > 0 ? '+' : ''
      return `${sign}${t}%`
    }
    return t
  }

  return (
    <Card
      variant="glass" // Always use premium glass for metrics
      hover={onClick ? 'lift' : 'subtle'}
      animated={animated && !loading} // Animate entrance unless loading initial skeleton
      onClick={onClick}
      sx={{
        p: compact ? 'var(--ob-space-100)' : 'var(--ob-space-150)', // 16px vs 24px
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        gap: 'var(--ob-space-100)',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
        }}
      >
        <Typography
          variant="overline"
          sx={{
            color: 'var(--ob-color-text-secondary)',
            fontWeight: 'var(--ob-font-weight-medium)',
            lineHeight: 1.2,
            letterSpacing: 'var(--ob-letter-spacing-wider)',
          }}
        >
          {label}
        </Typography>
        {icon && (
          <Box
            sx={{
              color: 'var(--ob-color-brand-primary)',
              opacity: 0.8,
              display: 'flex',
            }}
          >
            {icon}
          </Box>
        )}
      </Box>

      <Box>
        {loading ? (
          <Skeleton
            width="60%"
            height={compact ? 40 : 56}
            animation="wave"
            sx={{
              transform: 'none',
              mb: 'var(--ob-space-100)',
              borderRadius: 'var(--ob-radius-sm)',
            }}
          />
        ) : (
          <Typography
            variant={compact ? 'h4' : 'h3'}
            sx={{
              color: 'var(--ob-color-text-primary)',
              fontWeight: 'var(--ob-font-weight-bold)',
              // Use fluid typography or standard token sizes
              fontSize: compact
                ? 'var(--ob-font-size-2xl)'
                : 'var(--ob-font-size-4xl)',
              lineHeight: 1.1,
              letterSpacing: '-0.02em',
            }}
          >
            {value}
          </Typography>
        )}

        {(trend !== undefined || loading) && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--ob-space-100)',
              mt: 'var(--ob-space-100)',
            }}
          >
            {loading ? (
              <Skeleton width="40%" height={20} animation="wave" />
            ) : (
              <>
                <Typography
                  variant="caption"
                  sx={{
                    color: getTrendColor(trend!),
                    fontWeight: 'var(--ob-font-weight-semibold)',
                    bgcolor:
                      typeof trend === 'number' && trend > 0
                        ? 'var(--ob-color-success-bg)'
                        : typeof trend === 'number' && trend < 0
                          ? 'var(--ob-color-error-bg)'
                          : 'var(--ob-color-surface-elevated)',
                    px: 'var(--ob-space-50)',
                    py: '0',
                    borderRadius: 'var(--ob-radius-sm)',
                  }}
                >
                  {formatTrend(trend!)}
                </Typography>
                {trendLabel && (
                  <Typography
                    variant="caption"
                    sx={{ color: 'var(--ob-color-text-muted)' }}
                  >
                    {trendLabel}
                  </Typography>
                )}
              </>
            )}
          </Box>
        )}
      </Box>
    </Card>
  )
}
