import { Box, Typography, useTheme, alpha } from '@mui/material'
import TrendingUp from '@mui/icons-material/TrendingUp'
import TrendingDown from '@mui/icons-material/TrendingDown'

export interface HeroMetricProps {
  label: string
  value: string | number
  unit?: string
  trend?: {
    value: number
    direction: 'up' | 'down' | 'neutral'
  }
  trendLabel?: string
  icon?: React.ReactNode
  variant?: 'primary' | 'secondary' | 'glass'
  delay?: number
}

export function HeroMetric({
  label,
  value,
  unit,
  trend,
  trendLabel = 'vs last month',
  icon,
  variant = 'glass',
  delay = 0,
}: HeroMetricProps) {
  const theme = useTheme()

  const getBackground = () => {
    switch (variant) {
      case 'primary':
        return theme.palette.primary.dark
      case 'secondary':
        return theme.palette.background.paper
      case 'glass':
        return alpha(theme.palette.background.paper, 0.88)
    }
  }

  const getTextColor = () => {
    if (variant === 'primary') return theme.palette.primary.contrastText
    return theme.palette.text.primary
  }

  return (
    <Box
      sx={{
        background: getBackground(),
        border: `1px solid ${variant === 'primary' ? 'transparent' : theme.palette.divider}`,
        borderRadius: 'var(--ob-radius-sm)', // 4px - cards, panels, tiles
        padding: 'var(--ob-space-300)',
        boxShadow: variant === 'glass' ? theme.shadows[1] : theme.shadows[2],
        opacity: 0,
        animation: `slideUpFade 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards ${delay}ms`,
        '@media (prefers-reduced-motion: reduce)': {
          animation: 'none',
          opacity: 1,
        },
        minWidth: 0,
        position: 'relative',
        overflow: 'hidden',
        '@keyframes slideUpFade': {
          from: { opacity: 0, transform: 'translateY(20px)' },
          to: { opacity: 1, transform: 'translateY(0)' },
        },
      }}
    >
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          mb: 1,
        }}
      >
        <Typography
          variant="caption"
          sx={{
            textTransform: 'uppercase',
            letterSpacing: 'var(--ob-letter-spacing-widest)',
            fontWeight: 'var(--ob-font-weight-semibold)',
            color:
              variant === 'primary'
                ? alpha(theme.palette.primary.contrastText, 0.7)
                : theme.palette.text.secondary,
          }}
        >
          {label}
        </Typography>
        {icon && (
          <Box
            sx={{
              color:
                variant === 'primary'
                  ? alpha(theme.palette.primary.contrastText, 0.9)
                  : theme.palette.primary.main,
              opacity: 0.8,
            }}
          >
            {icon}
          </Box>
        )}
      </Box>

      <Box sx={{ display: 'flex', alignItems: 'baseline', mt: 1 }}>
        <Typography
          variant="h3"
          sx={{
            fontWeight: 'var(--ob-font-weight-bold)',
            lineHeight: 1,
            color: getTextColor(),
            letterSpacing: 'var(--ob-letter-spacing-tighter)',
          }}
        >
          {value}
        </Typography>
        {unit && (
          <Typography
            variant="h6"
            sx={{
              ml: 0.5,
              fontWeight: 'var(--ob-font-weight-regular)',
              color:
                variant === 'primary'
                  ? alpha(theme.palette.primary.contrastText, 0.6)
                  : theme.palette.text.secondary,
            }}
          >
            {unit}
          </Typography>
        )}
      </Box>

      {/* Trend Indicator */}
      {trend && (
        <Box sx={{ display: 'flex', alignItems: 'center', mt: 2, gap: 0.5 }}>
          {trend.direction === 'up' ? (
            <TrendingUp fontSize="small" color="success" />
          ) : (
            <TrendingDown
              fontSize="small"
              color={trend.direction === 'down' ? 'error' : 'action'}
            />
          )}
          <Typography
            variant="body2"
            sx={{
              fontWeight: 'var(--ob-font-weight-semibold)',
              color:
                trend.direction === 'up'
                  ? theme.palette.success.main
                  : trend.direction === 'down'
                    ? theme.palette.error.main
                    : theme.palette.text.secondary,
            }}
          >
            {Math.abs(trend.value)}%
          </Typography>
          <Typography
            variant="caption"
            sx={{
              color:
                variant === 'primary'
                  ? alpha(theme.palette.primary.contrastText, 0.5)
                  : theme.palette.text.disabled,
            }}
          >
            {trendLabel}
          </Typography>
        </Box>
      )}
    </Box>
  )
}
