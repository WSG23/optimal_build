import { Box, Skeleton, Typography, SxProps, Theme } from '@mui/material'
import { ReactNode } from 'react'
import { Card } from './Card'

export interface MetricTileProps {
  /**
   * Metric label (e.g., "Total Revenue", "Active Users")
   */
  label: string
  /**
   * Metric value (can be string or ReactNode for formatted values)
   */
  value: ReactNode
  /**
   * Trend indicator - number shows percentage, string shows custom text
   */
  trend?: number | string
  /**
   * Trend context (e.g., "vs last month", "YoY")
   */
  trendLabel?: string
  /**
   * Icon displayed in top-right corner
   */
  icon?: ReactNode
  /**
   * Loading state - shows skeleton
   */
  loading?: boolean
  /**
   * Tile variant:
   * - 'default': Standard 88px height
   * - 'hero': Larger hero metric display
   * - 'compact': Smaller for tight spaces
   */
  variant?: 'default' | 'hero' | 'compact'
  /**
   * Enable entrance animation
   */
  animated?: boolean
  /**
   * Click handler - makes tile interactive
   */
  onClick?: () => void
  /**
   * Additional styles
   */
  sx?: SxProps<Theme>
}

/**
 * MetricTile - Standardized KPI Display
 *
 * Geometry: 4px border radius (--ob-radius-sm)
 * Height: Fixed 88px (default), 120px (hero), 72px (compact)
 * Border: 1px fine line
 *
 * Used for displaying high-level metrics in dashboards.
 */
export function MetricTile({
  label,
  value,
  trend,
  trendLabel,
  icon,
  loading = false,
  variant = 'default',
  animated = true,
  onClick,
  sx = {},
}: MetricTileProps) {
  // Height based on variant
  const heightMap = {
    compact: '72px',
    default: '88px',
    hero: '120px',
  }

  // Font sizes based on variant
  const valueSizeMap = {
    compact: 'var(--ob-font-size-xl)',
    default: 'var(--ob-font-size-2xl)',
    hero: 'var(--ob-font-size-4xl)',
  }

  const getTrendColor = (t: number | string): string => {
    if (typeof t === 'number') {
      if (t > 0) return 'var(--ob-color-status-success-text)'
      if (t < 0) return 'var(--ob-color-status-error-text)'
    }
    return 'var(--ob-color-text-secondary)'
  }

  const getTrendBg = (t: number | string): string => {
    if (typeof t === 'number') {
      if (t > 0) return 'var(--ob-color-success-soft)'
      if (t < 0) return 'var(--ob-color-error-soft)'
    }
    return 'var(--ob-color-surface-strong)'
  }

  const formatTrend = (t: number | string): string => {
    if (typeof t === 'number') {
      const sign = t > 0 ? '+' : ''
      return `${sign}${t}%`
    }
    return t
  }

  return (
    <Card
      variant="glass"
      hover={onClick ? 'lift' : 'subtle'}
      animated={animated && !loading}
      onClick={onClick}
      sx={{
        height: heightMap[variant],
        p:
          variant === 'compact' ? 'var(--ob-space-075)' : 'var(--ob-space-100)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        ...sx,
      }}
    >
      {/* Header row: label + icon */}
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
            fontSize: 'var(--ob-font-size-xs)',
            lineHeight: 1.2,
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
          }}
        >
          {label}
        </Typography>
        {icon && (
          <Box
            sx={{
              color: 'var(--ob-color-brand-primary)',
              opacity: 0.7,
              display: 'flex',
              '& svg': { fontSize: variant === 'hero' ? 28 : 20 },
            }}
          >
            {icon}
          </Box>
        )}
      </Box>

      {/* Value row */}
      <Box>
        {loading ? (
          <Skeleton
            width="60%"
            height={variant === 'hero' ? 48 : 32}
            animation="wave"
            sx={{
              transform: 'none',
              borderRadius: 'var(--ob-radius-xs)',
            }}
          />
        ) : (
          <Typography
            sx={{
              color: 'var(--ob-color-text-primary)',
              fontWeight: 'var(--ob-font-weight-bold)',
              fontSize: valueSizeMap[variant],
              lineHeight: 1.1,
              letterSpacing: '-0.02em',
            }}
          >
            {value}
          </Typography>
        )}

        {/* Trend indicator */}
        {(trend !== undefined || loading) && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--ob-space-050)',
              mt: 'var(--ob-space-050)',
            }}
          >
            {loading ? (
              <Skeleton
                width="40%"
                height={16}
                animation="wave"
                sx={{ borderRadius: 'var(--ob-radius-xs)' }}
              />
            ) : (
              <>
                <Typography
                  variant="caption"
                  sx={{
                    color: getTrendColor(trend!),
                    fontWeight: 'var(--ob-font-weight-semibold)',
                    fontSize: 'var(--ob-font-size-xs)',
                    bgcolor: getTrendBg(trend!),
                    px: 'var(--ob-space-050)',
                    py: '2px',
                    borderRadius: 'var(--ob-radius-xs)', // 2px
                  }}
                >
                  {formatTrend(trend!)}
                </Typography>
                {trendLabel && (
                  <Typography
                    variant="caption"
                    sx={{
                      color: 'var(--ob-color-text-muted)',
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
      </Box>
    </Card>
  )
}
