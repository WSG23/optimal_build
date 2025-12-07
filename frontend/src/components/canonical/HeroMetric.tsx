import { Box, Typography, useTheme, alpha } from '@mui/material'
import { TrendingUp, TrendingDown } from '@mui/icons-material'

interface HeroMetricProps {
  label: string
  value: string | number
  unit?: string
  trend?: {
    value: number
    direction: 'up' | 'down' | 'neutral'
  }
  icon?: React.ReactNode
  variant?: 'primary' | 'secondary' | 'glass'
  delay?: number
}

export function HeroMetric({
  label,
  value,
  unit,
  trend,
  icon,
  variant = 'glass',
  delay = 0
}: HeroMetricProps) {
  const theme = useTheme()

  const getBackground = () => {
    switch (variant) {
      case 'primary': return 'linear-gradient(135deg, #1F2937 0%, #111827 100%)'
      case 'secondary': return 'white'
      case 'glass': return alpha(theme.palette.background.paper, 0.6)
    }
  }

  const getTextColor = () => {
     if (variant === 'primary') return 'white'
     return theme.palette.text.primary
  }

  return (
    <Box
      sx={{
        background: getBackground(),
        backdropFilter: variant === 'glass' ? 'blur(12px)' : 'none',
        border: `1px solid ${variant === 'primary' ? 'transparent' : theme.palette.divider}`,
        borderRadius: 4, // var(--ob-radius-lg) which is usually 16px
        padding: 3,
        boxShadow: variant === 'glass' ? '0 8px 32px rgba(0,0,0,0.05)' : theme.shadows[2],
        opacity: 0,
        animation: `slideUpFade 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards ${delay}ms`,
        minWidth: 200,
        position: 'relative',
        overflow: 'hidden',
        '@keyframes slideUpFade': {
            from: { opacity: 0, transform: 'translateY(20px)' },
            to: { opacity: 1, transform: 'translateY(0)' }
        }
      }}
    >
        {/* Background Decoration for Primary */}
        {variant === 'primary' && (
            <Box sx={{
                position: 'absolute',
                top: -20,
                right: -20,
                width: 100,
                height: 100,
                background: 'radial-gradient(circle, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 70%)',
                borderRadius: '50%'
            }} />
        )}

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
            <Typography variant="caption" sx={{
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                fontWeight: 600,
                color: variant === 'primary' ? alpha('#fff', 0.7) : theme.palette.text.secondary
            }}>
                {label}
            </Typography>
            {icon && (
                <Box sx={{
                    color: variant === 'primary' ? alpha('#fff', 0.9) : theme.palette.primary.main,
                    opacity: 0.8
                }}>
                    {icon}
                </Box>
            )}
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'baseline', mt: 1 }}>
            <Typography variant="h3" sx={{
                fontWeight: 700,
                lineHeight: 1,
                color: getTextColor(),
                letterSpacing: '-0.02em'
            }}>
                {value}
            </Typography>
            {unit && (
                <Typography variant="h6" sx={{
                    ml: 0.5,
                    fontWeight: 400,
                    color: variant === 'primary' ? alpha('#fff', 0.6) : theme.palette.text.secondary
                }}>
                    {unit}
                </Typography>
            )}
        </Box>

        {/* Trend Indicator */}
        {trend && (
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 2, gap: 0.5 }}>
                {trend.direction === 'up' ?
                    <TrendingUp fontSize="small" color="success" /> :
                    <TrendingDown fontSize="small" color={trend.direction === 'down' ? 'error' : 'action'} />
                }
                <Typography variant="body2" sx={{
                    fontWeight: 600,
                    color: trend.direction === 'up' ? theme.palette.success.main :
                           (trend.direction === 'down' ? theme.palette.error.main : theme.palette.text.secondary)
                }}>
                    {Math.abs(trend.value)}%
                </Typography>
                <Typography variant="caption" sx={{ color: variant === 'primary' ? alpha('#fff', 0.5) : theme.palette.text.disabled }}>
                    vs last month
                </Typography>
            </Box>
        )}
    </Box>
  )
}
