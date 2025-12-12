import { useTranslation } from '../../i18n'
import { RoiMetrics } from './types'
import { Box, Paper, Typography, Skeleton, styled } from '@mui/material'
import { keyframes } from '@emotion/react'

const pulse = keyframes`
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
`

// Updated StatCard to handle glass variant
const StatCard = styled(Paper, {
  shouldForwardProp: (prop) => prop !== 'glass',
})<{ glass?: boolean }>(({ theme, glass }) => ({
  background: glass ? 'var(--ob-surface-glass-1)' : 'var(--ob-neutral-900)', // Glass vs Solid
  backdropFilter: glass ? 'blur(12px)' : 'none',
  border: glass
    ? '1px solid var(--ob-border-fine)'
    : '1px solid var(--ob-border-fine)',
  borderRadius: 'var(--ob-radius-sm)',
  padding: theme.spacing(2, 3), // Slightly tighter padding for HUD feel
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'space-between',
  height: '100%',
  minHeight: glass ? '120px' : '160px', // Smaller for HUD
  position: 'relative',
  overflow: 'hidden',
  transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
  '&:hover': {
    transform: 'translateY(-4px)',
    boxShadow: 'var(--ob-shadow-lg)',
    borderColor: 'var(--ob-neutral-700)',
  },
}))

const NeonText = styled(Typography, {
  shouldForwardProp: (prop) => prop !== 'colorStart' && prop !== 'colorEnd',
})<{ colorStart: string; colorEnd: string }>(({ colorStart, colorEnd }) => ({
  background: `linear-gradient(135deg, ${colorStart}, ${colorEnd})`,
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  fontWeight: 800,
  fontSize: 'var(--ob-font-size-3xl)',
  lineHeight: 1.1,
  letterSpacing: '-0.02em',
  filter: 'drop-shadow(0 0 15px var(--ob-neutral-950))',
}))

// Circular Progress Custom Implementation
const CircleBackground = styled('circle')({
  fill: 'none',
  stroke: 'var(--ob-neutral-800)',
})

const CircleProgress = styled('circle')<{ color: string }>(({ color }) => ({
  fill: 'none',
  stroke: color,
  strokeLinecap: 'round',
  transition: 'stroke-dashoffset 1.5s ease-out',
}))

interface CircularGaugeProps {
  value: number
  label: string
  color: string
  size?: number
}

function CircularGauge({
  value,
  label: _label,
  color,
  size = 80,
}: CircularGaugeProps) {
  const strokeWidth = 6
  const center = size / 2
  const radius = center - strokeWidth
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (value / 100) * circumference

  return (
    <Box
      sx={{ position: 'relative', width: size, height: size, margin: '0 auto' }}
    >
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <CircleBackground
          cx={center}
          cy={center}
          r={radius}
          strokeWidth={strokeWidth}
        />
        <CircleProgress
          cx={center}
          cy={center}
          r={radius}
          strokeWidth={strokeWidth}
          color={color}
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column',
        }}
      >
        <Typography
          variant="h6"
          sx={{ fontWeight: 'bold', color: 'white', lineHeight: 1 }}
        >
          {value}%
        </Typography>
      </Box>
    </Box>
  )
}

interface RoiSummaryProps {
  metrics: RoiMetrics
  loading?: boolean
  isLive?: boolean
  variant?: 'default' | 'glass'
}

export function RoiSummary({
  metrics,
  loading,
  isLive,
  variant = 'default',
}: RoiSummaryProps) {
  const { t } = useTranslation()
  const isGlass = variant === 'glass'

  // Colors - using design tokens
  const scoreColor = 'var(--ob-success-500)' // Emerald
  const savingsColorStart = 'var(--ob-brand-400)' // Cyan-ish brand
  const savingsColorEnd = 'var(--ob-brand-500)' // Blue
  const hoursColorStart = 'var(--ob-warning-500)' // Amber
  const hoursColorEnd = 'var(--ob-brand-600)' // Purple-ish brand

  if (loading) {
    return (
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 2,
          mb: isGlass ? 0 : 4,
        }}
      >
        {[1, 2, 3, 4].map((i) => (
          <Skeleton
            key={i}
            variant="rectangular"
            height={isGlass ? 120 : 160}
            sx={{
              borderRadius: 'var(--ob-radius-sm)',
              bgcolor: 'var(--ob-neutral-800)',
            }}
          />
        ))}
      </Box>
    )
  }

  return (
    <Box sx={{ mb: isGlass ? 0 : 6 }}>
      {!isGlass && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <Typography variant="h5" sx={{ fontWeight: 700, color: 'white' }}>
            {t('panels.roiTitle')}
          </Typography>
          {isLive && (
            <Box
              sx={{
                background: 'var(--ob-success-muted)',
                color: 'var(--ob-success-400)',
                border: '1px solid var(--ob-success-600)',
                px: 1,
                py: 0.25,
                borderRadius: 'var(--ob-radius-xs)',
                fontSize: 'var(--ob-font-size-xs)',
                fontWeight: 'bold',
                letterSpacing: '0.05em',
                animation: `${pulse} 2s infinite`,
              }}
            >
              LIVE
            </Box>
          )}
        </Box>
      )}

      {/*
            For Glass variant (HUD), we might want a horizontal row with less gap?
            User requested "Horizontal Stat Deck".
            If Glass, let's make it compact.
        */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            md: isGlass ? 'repeat(4, 140px)' : 'repeat(4, 1fr)',
          }, // Compact width for glass HUD
          gap: 2,
        }}
      >
        {/* 1. Automation Score - Gauge */}
        <StatCard glass={isGlass}>
          <Typography
            variant="caption"
            sx={{
              color: 'text.secondary',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              fontSize: '0.65rem',
              mb: 1,
            }}
          >
            {t('pipelines.automationScore')}
          </Typography>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              flex: 1,
            }}
          >
            <CircularGauge
              value={Math.round(metrics.automationScore * 100)}
              label=""
              color={scoreColor}
              size={isGlass ? 70 : 100}
            />
          </Box>
        </StatCard>

        {/* 2. Estimated Savings - Big Number */}
        <StatCard glass={isGlass}>
          <Typography
            variant="caption"
            sx={{
              color: 'text.secondary',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              fontSize: '0.65rem',
            }}
          >
            {t('pipelines.savings')}
          </Typography>
          <Box sx={{ flex: 1, display: 'flex', alignItems: 'center' }}>
            <NeonText colorStart={savingsColorStart} colorEnd={savingsColorEnd}>
              {metrics.savingsPercent}%
            </NeonText>
          </Box>
          <Typography
            variant="caption"
            sx={{
              color: 'text.secondary',
              fontSize: '0.6rem',
              lineHeight: 1.2,
            }}
          >
            OpEx cut
          </Typography>
        </StatCard>

        {/* 3. Hours Saved - Big Number */}
        <StatCard glass={isGlass}>
          <Typography
            variant="caption"
            sx={{
              color: 'text.secondary',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              fontSize: '0.65rem',
            }}
          >
            {t('pipelines.reviewHours')}
          </Typography>
          <Box sx={{ flex: 1, display: 'flex', alignItems: 'center' }}>
            <NeonText colorStart={hoursColorStart} colorEnd={hoursColorEnd}>
              {metrics.reviewHoursSaved}h
            </NeonText>
          </Box>
          <Typography
            variant="caption"
            sx={{
              color: 'text.secondary',
              fontSize: '0.6rem',
              lineHeight: 1.2,
            }}
          >
            Time saved
          </Typography>
        </StatCard>

        {/* 4. Payback - Timeline */}
        <StatCard glass={isGlass}>
          <Typography
            variant="caption"
            sx={{
              color: 'text.secondary',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              fontSize: '0.65rem',
              mb: 1,
            }}
          >
            {t('pipelines.payback')}
          </Typography>
          <Box sx={{ mt: 'auto' }}>
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                mb: 0.5,
                alignItems: 'flex-end',
              }}
            >
              <Typography
                variant="h5"
                sx={{ color: 'white', fontWeight: 'bold' }}
              >
                {metrics.paybackWeeks}
                <span
                  style={{
                    fontSize: 'var(--ob-font-size-sm)',
                    color: 'var(--ob-neutral-400)',
                    fontWeight: 'normal',
                    marginLeft: '2px',
                  }}
                >
                  w
                </span>
              </Typography>
            </Box>

            {/* Custom Progress Bar */}
            <Box
              sx={{
                height: 4,
                background: 'var(--ob-neutral-800)',
                borderRadius: 'var(--ob-radius-xs)',
                overflow: 'hidden',
              }}
            >
              <Box
                sx={{
                  width: `${Math.min(100, Math.max(10, (1 - metrics.paybackWeeks / 26) * 100))}%`,
                  height: '100%',
                  background:
                    'linear-gradient(90deg, var(--ob-warning-500), var(--ob-success-500))',
                  borderRadius: 'var(--ob-radius-xs)',
                }}
              />
            </Box>
          </Box>
        </StatCard>
      </Box>
    </Box>
  )
}

export default RoiSummary
