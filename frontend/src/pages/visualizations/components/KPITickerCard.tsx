import { Box, Typography, Stack, useTheme, alpha } from '@mui/material'

export interface KPITickerCardProps {
  label: string
  value: string | number
  trend: number // Percentage, e.g. 44.7
  data: number[] // Array of numbers for the sparkline
  active?: boolean
}

export function KPITickerCard({
  label,
  value,
  trend,
  data,
  active,
}: KPITickerCardProps) {
  const theme = useTheme()

  const isPositive = trend >= 0
  const trendColor = isPositive
    ? theme.palette.success.main
    : theme.palette.error.main
  const safeData = data.length > 1 ? data : [0, ...(data.length ? data : [0])]
  const min = Math.min(...safeData)
  const max = Math.max(...safeData)
  const range = max - min || 1
  const width = 100
  const height = 60
  const points = safeData.map((point, index) => {
    const x = (index / (safeData.length - 1)) * width
    const y = height - ((point - min) / range) * (height - 8) - 4
    return `${x},${y}`
  })
  const linePath = `M ${points.join(' L ')}`
  const areaPath = `${linePath} L ${width},${height} L 0,${height} Z`
  const gradientId = `gradient-${label.replace(/[^a-z0-9]+/gi, '-').toLowerCase()}`

  return (
    <Box
      sx={{
        position: 'relative',
        p: 3,
        borderRadius: '4px', // Square Cyber-Minimalism: sm for cards
        overflow: 'hidden',
        bgcolor: alpha(theme.palette.background.paper, 0.6), // Glassmorphic base
        backdropFilter: 'blur(var(--ob-blur-lg))',
        border: '1px solid',
        borderColor: active
          ? theme.palette.primary.main
          : alpha(theme.palette.divider, 0.1),
        boxShadow: active
          ? `0 0 20px -5px ${alpha(theme.palette.primary.main, 0.5)}`
          : '0 4px 24px -1px rgba(0, 0, 0, 0.05)',
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: '0 8px 30px -5px rgba(0, 0, 0, 0.1)',
        },
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}
    >
      <Box mb={2}>
        <Typography
          variant="overline"
          sx={{
            color: 'text.secondary',
            fontWeight: 600,
            letterSpacing: '0.1em',
          }}
        >
          {label}
        </Typography>
        <Stack
          direction="row"
          alignItems="baseline"
          spacing={1}
          sx={{ mt: 0.5 }}
        >
          <Typography
            variant="h3"
            sx={{
              fontWeight: 800,
              color: 'text.primary',
              letterSpacing: '-0.02em',
            }}
          >
            {value}
          </Typography>
          <Box
            sx={{
              bgcolor: alpha(trendColor, 0.1),
              color: trendColor,
              px: 1,
              py: 0.25,
              borderRadius: '2px', // Square Cyber-Minimalism: xs for badges
              fontSize: '0.75rem',
              fontWeight: 700,
            }}
          >
            {isPositive ? '+' : ''}
            {trend.toFixed(1)}%
          </Box>
        </Stack>
      </Box>

      <Box sx={{ height: 60, width: '100%', opacity: 0.8 }}>
        <Box
          component="svg"
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="none"
          sx={{ display: 'block', width: '100%', height: '100%' }}
        >
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop
                offset="5%"
                stopColor={theme.palette.primary.main}
                stopOpacity={0.3}
              />
              <stop
                offset="95%"
                stopColor={theme.palette.primary.main}
                stopOpacity={0}
              />
            </linearGradient>
          </defs>
          <path d={areaPath} fill={`url(#${gradientId})`} />
          <path
            d={linePath}
            fill="none"
            stroke={theme.palette.primary.main}
            strokeWidth="2"
            vectorEffect="non-scaling-stroke"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </Box>
      </Box>
    </Box>
  )
}
