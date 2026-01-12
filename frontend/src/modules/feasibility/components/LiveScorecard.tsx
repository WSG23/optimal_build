import { Box, Typography } from '@mui/material'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import SquareFootIcon from '@mui/icons-material/SquareFoot'
import AccountBalanceIcon from '@mui/icons-material/AccountBalance'
import SpeedIcon from '@mui/icons-material/Speed'

interface LiveScorecardProps {
  siteArea?: number
  efficiencyRatio?: number
  floorToFloor?: number
  plotRatio?: number
  visible?: boolean
}

export function LiveScorecard({
  siteArea = 0,
  efficiencyRatio = 0.8,
  floorToFloor = 3.4,
  plotRatio = 2.8,
  visible = true,
}: LiveScorecardProps) {
  if (!visible || siteArea <= 0) return null

  // Calculate live metrics
  const maxGFA = Math.round(siteArea * plotRatio)
  const netSaleableArea = Math.round(maxGFA * efficiencyRatio)
  const estimatedFloors = Math.floor(40 / floorToFloor) // Assuming 40m height limit
  const estimatedYield = ((netSaleableArea * 2500) / 1000000).toFixed(1) // Rough SGD yield estimate

  const metrics = [
    {
      label: 'Projected GFA',
      value: maxGFA.toLocaleString(),
      unit: 'm²',
      icon: <SquareFootIcon sx={{ fontSize: 'var(--ob-font-size-base)' }} />,
      colorClass: 'live-scorecard__icon--cyan',
      change: `+${String(Math.round((efficiencyRatio - 0.8) * 100))}%`,
    },
    {
      label: 'Net Saleable',
      value: netSaleableArea.toLocaleString(),
      unit: 'm²',
      icon: <TrendingUpIcon sx={{ fontSize: 'var(--ob-font-size-base)' }} />,
      colorClass: 'live-scorecard__icon--green',
    },
    {
      label: 'Est. Floors',
      value: estimatedFloors.toString(),
      unit: 'floors',
      icon: (
        <AccountBalanceIcon sx={{ fontSize: 'var(--ob-font-size-base)' }} />
      ),
      colorClass: 'live-scorecard__icon--purple',
    },
    {
      label: 'Est. Yield',
      value: estimatedYield,
      unit: 'M SGD',
      icon: <SpeedIcon sx={{ fontSize: 'var(--ob-font-size-base)' }} />,
      colorClass: 'live-scorecard__icon--amber',
    },
  ]

  return (
    <Box className="live-scorecard">
      {/* Header */}
      <Box className="live-scorecard__header">
        <Box className="live-scorecard__pulse-dot" />
        <Typography className="live-scorecard__title">
          Live Feasibility
        </Typography>
      </Box>

      {/* Metrics */}
      <Box className="live-scorecard__metrics">
        {metrics.map((metric) => (
          <Box key={metric.label} className="live-scorecard__metric">
            <Box className="live-scorecard__metric-left">
              <Box className={`live-scorecard__icon ${metric.colorClass}`}>
                {metric.icon}
              </Box>
              <Typography className="live-scorecard__label">
                {metric.label}
              </Typography>
            </Box>
            <Box className="live-scorecard__metric-right">
              <Typography className="live-scorecard__value">
                {metric.value}
              </Typography>
              <Typography className="live-scorecard__unit">
                {metric.unit}
              </Typography>
            </Box>
          </Box>
        ))}
      </Box>

      {/* Efficiency indicator bar */}
      <Box className="live-scorecard__efficiency">
        <Box className="live-scorecard__efficiency-header">
          <Typography className="live-scorecard__efficiency-label">
            Efficiency Score
          </Typography>
          <Typography className="live-scorecard__efficiency-value">
            {Math.round(efficiencyRatio * 100)}%
          </Typography>
        </Box>
        <Box className="live-scorecard__progress-track">
          <Box
            className="live-scorecard__progress-fill"
            sx={{ width: `${String(efficiencyRatio * 100)}%` }}
          />
        </Box>
      </Box>
    </Box>
  )
}
