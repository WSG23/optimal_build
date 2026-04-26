import { Box, Skeleton as MuiSkeleton, SxProps, Theme } from '@mui/material'

export interface SkeletonProps {
  /**
   * Skeleton variant
   */
  variant?: 'text' | 'rectangular' | 'circular' | 'rounded'
  /**
   * Width
   */
  width?: string | number
  /**
   * Height
   */
  height?: string | number
  /**
   * Animation type
   */
  animation?: 'pulse' | 'wave' | false
  /**
   * Additional styles
   */
  sx?: SxProps<Theme>
}

/**
 * Skeleton - Loading Placeholder
 *
 * Geometry: 2px border radius (--ob-radius-xs) for rounded variant
 *
 * Consistent loading state indicator.
 */
export function Skeleton({
  variant = 'rounded',
  width,
  height,
  animation = 'wave',
  sx = {},
}: SkeletonProps) {
  return (
    <MuiSkeleton
      variant={variant === 'rounded' ? 'rectangular' : variant}
      width={width}
      height={height}
      animation={animation}
      sx={{
        bgcolor: 'var(--ob-color-surface-strong)',
        borderRadius:
          variant === 'rounded'
            ? 'var(--ob-radius-xs)' // 2px
            : variant === 'circular'
              ? '50%'
              : 0,
        transform: 'none', // Prevent MUI transform
        ...sx,
      }}
    />
  )
}

/**
 * SkeletonText - Text placeholder with multiple lines
 */
export interface SkeletonTextProps {
  /**
   * Number of lines
   */
  lines?: number
  /**
   * Width of last line (percentage)
   */
  lastLineWidth?: string
  /**
   * Gap between lines
   */
  gap?: string
  /**
   * Additional styles
   */
  sx?: SxProps<Theme>
}

export function SkeletonText({
  lines = 3,
  lastLineWidth = '60%',
  gap = 'var(--ob-space-050)',
  sx = {},
}: SkeletonTextProps) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap, ...sx }}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          variant="rounded"
          width={i === lines - 1 ? lastLineWidth : '100%'}
          height={16}
        />
      ))}
    </Box>
  )
}

/**
 * SkeletonCard - Card placeholder
 */
export interface SkeletonCardProps {
  /**
   * Include header
   */
  hasHeader?: boolean
  /**
   * Number of content lines
   */
  contentLines?: number
  /**
   * Card height
   */
  height?: string | number
  /**
   * Additional styles
   */
  sx?: SxProps<Theme>
}

export function SkeletonCard({
  hasHeader = true,
  contentLines = 3,
  height,
  sx = {},
}: SkeletonCardProps) {
  return (
    <Box
      sx={{
        borderRadius: 'var(--ob-radius-sm)', // 4px - matches Card
        border: 'var(--ob-border-fine)',
        background: 'var(--ob-color-bg-surface)',
        p: 'var(--ob-space-100)',
        height,
        ...sx,
      }}
    >
      {hasHeader && (
        <Box sx={{ mb: 'var(--ob-space-100)' }}>
          <Skeleton variant="rounded" width="40%" height={20} />
        </Box>
      )}
      <SkeletonText lines={contentLines} />
    </Box>
  )
}

/**
 * SkeletonMetric - Metric tile placeholder
 */
export function SkeletonMetric({ sx = {} }: { sx?: SxProps<Theme> }) {
  return (
    <Box
      sx={{
        borderRadius: 'var(--ob-radius-sm)', // 4px - matches MetricTile
        border: 'var(--ob-border-fine)',
        background: 'var(--ob-surface-glass-1)',
        p: 'var(--ob-space-100)',
        height: '88px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        ...sx,
      }}
    >
      <Skeleton variant="rounded" width="50%" height={14} />
      <Box>
        <Skeleton
          variant="rounded"
          width="70%"
          height={28}
          sx={{ mb: 'var(--ob-space-100)' }}
        />
        <Skeleton variant="rounded" width="30%" height={16} />
      </Box>
    </Box>
  )
}
