import React from 'react'
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
} from '@mui/material'
import SpeedIcon from '@mui/icons-material/Speed'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import TrendingDownIcon from '@mui/icons-material/TrendingDown'
import { AbsorptionTrends } from '../../../types/market'
import { PropertyType } from '../../../types/property'

interface AbsorptionTrendsChartProps {
  absorptionTrends?: AbsorptionTrends | null
  propertyType: PropertyType
}

const formatPercent = (value?: number | null, fractionDigits = 1) => {
  if (value === undefined || value === null || Number.isNaN(value)) return '—'
  const percentValue = Math.abs(value) <= 1 ? value * 100 : value
  return `${percentValue.toFixed(fractionDigits)}%`
}

const formatNumber = (value?: number | null) => {
  if (value === undefined || value === null || Number.isNaN(value)) return '—'
  return new Intl.NumberFormat('en-SG', { maximumFractionDigits: 0 }).format(
    value,
  )
}

const AbsorptionTrendsChart: React.FC<AbsorptionTrendsChartProps> = ({
  absorptionTrends,
  propertyType,
}) => {
  const velocityTrend = absorptionTrends?.velocity_trend

  const velocityChip = () => {
    if (!velocityTrend) {
      return (
        <Chip
          size="small"
          label="Velocity: N/A"
          variant="outlined"
          icon={<SpeedIcon fontSize="small" />}
        />
      )
    }

    if (velocityTrend === 'accelerating') {
      return (
        <Chip
          size="small"
          color="success"
          icon={<TrendingUpIcon fontSize="small" />}
          label="Velocity: Accelerating"
        />
      )
    }

    if (velocityTrend === 'decelerating') {
      return (
        <Chip
          size="small"
          color="error"
          icon={<TrendingDownIcon fontSize="small" />}
          label="Velocity: Decelerating"
        />
      )
    }

    return (
      <Chip
        size="small"
        icon={<SpeedIcon fontSize="small" />}
        label="Velocity: Stable"
        variant="outlined"
      />
    )
  }

  return (
    <Box>
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb="var(--ob-space-200)"
      >
        <Typography variant="h6">Absorption & Demand</Typography>
        <Typography variant="caption" color="textSecondary">
          {propertyType.replace(/_/g, ' ').toUpperCase()}
        </Typography>
      </Box>

      {!absorptionTrends ? (
        <Paper sx={{ p: 'var(--ob-space-300)' }}>
          <Typography color="textSecondary">
            No absorption analytics available.
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing="var(--ob-space-200)">
          <Grid item xs={12} md={6} lg={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Current Sales Absorption
                </Typography>
                <Typography variant="h5">
                  {formatPercent(
                    absorptionTrends.current_metrics.sales_absorption_rate,
                  )}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Avg{' '}
                  {formatPercent(
                    absorptionTrends.period_averages.avg_sales_absorption,
                  )}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6} lg={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Current Leasing Absorption
                </Typography>
                <Typography variant="h5">
                  {formatPercent(
                    absorptionTrends.current_metrics.leasing_absorption_rate,
                  )}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Avg{' '}
                  {formatPercent(
                    absorptionTrends.period_averages.avg_leasing_absorption,
                  )}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6} lg={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Days to Sell / Lease
                </Typography>
                <Typography variant="h6">
                  {formatNumber(
                    absorptionTrends.current_metrics.avg_days_to_sale,
                  )}{' '}
                  days sell
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  {formatNumber(
                    absorptionTrends.current_metrics.avg_days_to_lease,
                  )}{' '}
                  days lease
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6} lg={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Market Comparison
                </Typography>
                <Typography variant="h5">
                  {formatPercent(
                    absorptionTrends.market_comparison.vs_market_average,
                  )}{' '}
                  vs market
                </Typography>
                {velocityChip()}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 'var(--ob-space-200)' }}>
              <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
                Forecast (6 months)
              </Typography>
              {absorptionTrends.forecast.message ? (
                <Typography color="textSecondary">
                  {absorptionTrends.forecast.message}
                </Typography>
              ) : (
                <>
                  <Typography variant="body2">
                    Current absorption:{' '}
                    {formatPercent(
                      absorptionTrends.forecast.current_absorption,
                    )}
                  </Typography>
                  <Typography variant="body2">
                    Projected absorption:{' '}
                    {formatPercent(
                      absorptionTrends.forecast.projected_absorption_6m,
                    )}
                  </Typography>
                  <Typography variant="body2">
                    Avg monthly absorption:{' '}
                    {formatPercent(
                      absorptionTrends.forecast.avg_monthly_absorption,
                    )}
                  </Typography>
                  <Typography variant="body2">
                    Estimated sellout:{' '}
                    {formatNumber(
                      absorptionTrends.forecast.estimated_sellout_months,
                    )}{' '}
                    months
                  </Typography>
                </>
              )}
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 'var(--ob-space-200)' }}>
              <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
                Seasonality Snapshot
              </Typography>
              {absorptionTrends.seasonal_patterns?.message ? (
                <Typography color="textSecondary">
                  {absorptionTrends.seasonal_patterns.message}
                </Typography>
              ) : absorptionTrends.seasonal_patterns ? (
                <>
                  <Typography variant="body2">
                    Peak month: {absorptionTrends.seasonal_patterns.peak_month}
                  </Typography>
                  <Typography variant="body2">
                    Low month: {absorptionTrends.seasonal_patterns.low_month}
                  </Typography>
                  <Typography variant="body2">
                    Seasonality strength:{' '}
                    {formatPercent(
                      absorptionTrends.seasonal_patterns.seasonality_strength,
                      1,
                    )}
                  </Typography>
                </>
              ) : (
                <Typography color="textSecondary">
                  No seasonal patterns detected.
                </Typography>
              )}
            </Paper>
          </Grid>
        </Grid>
      )}
    </Box>
  )
}

export default AbsorptionTrendsChart
