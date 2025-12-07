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
      icon: <SquareFootIcon sx={{ fontSize: 16 }} />,
      color: '#06b6d4',
      change: `+${String(Math.round((efficiencyRatio - 0.8) * 100))}%`,
    },
    {
      label: 'Net Saleable',
      value: netSaleableArea.toLocaleString(),
      unit: 'm²',
      icon: <TrendingUpIcon sx={{ fontSize: 16 }} />,
      color: '#10b981',
    },
    {
      label: 'Est. Floors',
      value: estimatedFloors.toString(),
      unit: 'floors',
      icon: <AccountBalanceIcon sx={{ fontSize: 16 }} />,
      color: '#8b5cf6',
    },
    {
      label: 'Est. Yield',
      value: estimatedYield,
      unit: 'M SGD',
      icon: <SpeedIcon sx={{ fontSize: 16 }} />,
      color: '#f59e0b',
    },
  ]

  return (
    <Box
      sx={{
        position: 'absolute',
        top: '24px',
        right: '80px', // Offset from layer controls
        zIndex: 20,
        background: 'rgba(15, 23, 42, 0.9)',
        backdropFilter: 'blur(16px)',
        border: '1px solid rgba(6, 182, 212, 0.2)',
        borderRadius: '16px',
        padding: '16px',
        minWidth: '200px',
        animation: 'slideInRight 0.4s ease-out',
      }}
    >
      <style>
        {`
          @keyframes slideInRight {
            from { transform: translateX(20px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
          }
          @keyframes pulse-value {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
          }
        `}
      </style>

      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginBottom: '12px',
          paddingBottom: '8px',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        <Box
          sx={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: '#10b981',
            animation: 'pulse-value 2s infinite',
          }}
        />
        <Typography
          sx={{
            fontSize: '0.7rem',
            fontWeight: 600,
            color: 'rgba(255,255,255,0.7)',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
          }}
        >
          Live Feasibility
        </Typography>
      </Box>

      {/* Metrics */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {metrics.map((metric) => (
          <Box
            key={metric.label}
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Box sx={{ color: metric.color, opacity: 0.8 }}>
                {metric.icon}
              </Box>
              <Typography
                sx={{
                  fontSize: '0.7rem',
                  color: 'rgba(255,255,255,0.6)',
                }}
              >
                {metric.label}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
              <Typography
                sx={{
                  fontSize: '0.9rem',
                  fontWeight: 700,
                  color: 'white',
                  fontFamily: 'monospace',
                }}
              >
                {metric.value}
              </Typography>
              <Typography
                sx={{
                  fontSize: '0.6rem',
                  color: 'rgba(255,255,255,0.4)',
                }}
              >
                {metric.unit}
              </Typography>
            </Box>
          </Box>
        ))}
      </Box>

      {/* Efficiency indicator bar */}
      <Box
        sx={{
          marginTop: '12px',
          paddingTop: '12px',
          borderTop: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            marginBottom: '4px',
          }}
        >
          <Typography
            sx={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.5)' }}
          >
            Efficiency Score
          </Typography>
          <Typography
            sx={{ fontSize: '0.65rem', color: '#06b6d4', fontWeight: 600 }}
          >
            {Math.round(efficiencyRatio * 100)}%
          </Typography>
        </Box>
        <Box
          sx={{
            height: '4px',
            borderRadius: '2px',
            background: 'rgba(255,255,255,0.1)',
            overflow: 'hidden',
          }}
        >
          <Box
            sx={{
              height: '100%',
              width: `${String(efficiencyRatio * 100)}%`,
              background: 'linear-gradient(90deg, #06b6d4, #3b82f6)',
              borderRadius: '2px',
              transition: 'width 0.3s ease-out',
            }}
          />
        </Box>
      </Box>
    </Box>
  )
}
