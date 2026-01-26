import React from 'react'
import {
  Alert,
  Box,
  Chip,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  Typography,
} from '@mui/material'
import InfoIcon from '@mui/icons-material/Info'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import TrendingDownIcon from '@mui/icons-material/TrendingDown'
import WarningAmberIcon from '@mui/icons-material/WarningAmber'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import {
  MarketReport,
  ComparablesAnalysis,
  SupplyDynamics,
  YieldBenchmarks,
  AbsorptionTrends,
} from '../../../types/market'

interface QuickInsightsProps {
  marketReport: MarketReport
  comparables?: ComparablesAnalysis | null
  supplyDynamics?: SupplyDynamics | null
  yieldBenchmarks?: YieldBenchmarks | null
  absorptionTrends?: AbsorptionTrends | null
}

const QuickInsights: React.FC<QuickInsightsProps> = ({
  marketReport,
  comparables,
  supplyDynamics,
  yieldBenchmarks,
  absorptionTrends,
}) => {
  const comparablesData = comparables ?? marketReport.comparables_analysis
  const supplyData = supplyDynamics ?? marketReport.supply_dynamics
  const yieldData = yieldBenchmarks ?? marketReport.yield_benchmarks
  const absorptionData = absorptionTrends ?? marketReport.absorption_trends

  const formatCurrency = (value?: number | null) => {
    if (value === undefined || value === null) return '—'
    return new Intl.NumberFormat('en-SG', {
      style: 'currency',
      currency: 'SGD',
      maximumFractionDigits: 0,
    }).format(value)
  }

  const formatNumber = (value?: number | null) => {
    if (value === undefined || value === null) return '—'
    return new Intl.NumberFormat('en-SG', {
      maximumFractionDigits: 0,
    }).format(value)
  }

  const formatDate = (value?: string | null) => {
    if (!value) return '—'
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) {
      return value
    }
    return date.toLocaleDateString('en-SG', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const formatPercentSmart = (value?: number | null, fractionDigits = 1) => {
    if (value === undefined || value === null || Number.isNaN(value)) {
      return '—'
    }
    const percentValue = Math.abs(value) <= 1 ? value * 100 : value
    return `${percentValue.toFixed(fractionDigits)}%`
  }

  const determineSentiment = () => {
    const priceTrend = comparablesData?.price_trend ?? 'stable'
    const supplyPressure = supplyData?.supply_pressure ?? 'moderate'
    const velocity = absorptionData?.velocity_trend ?? 'stable'

    if (priceTrend === 'upward' && supplyPressure === 'low') {
      return {
        label: 'Positive momentum with limited new supply',
        severity: 'success' as const,
        icon: <TrendingUpIcon />,
      }
    }

    if (priceTrend === 'downward' || supplyPressure === 'high') {
      return {
        label: 'Market facing headwinds from pricing or supply',
        severity: 'error' as const,
        icon: <TrendingDownIcon />,
      }
    }

    if (velocity === 'decelerating') {
      return {
        label: 'Absorption velocity slowing - monitor leasing traction',
        severity: 'warning' as const,
        icon: <WarningAmberIcon />,
      }
    }

    return {
      label: 'Market conditions stable',
      severity: 'info' as const,
      icon: <InfoIcon />,
    }
  }

  const sentiment = determineSentiment()
  const formattedPropertyType = marketReport.property_type.replace(/_/g, ' ')

  return (
    <Box sx={{ mb: 'var(--ob-space-300)' }}>
      <Alert
        severity={sentiment.severity}
        icon={sentiment.icon}
        sx={{ mb: 'var(--ob-space-200)' }}
      >
        <Typography variant="subtitle1" fontWeight="medium">
          {formattedPropertyType.toUpperCase()} •{' '}
          {marketReport.location.toUpperCase()} •{' '}
          {formatDate(marketReport.period.start)} →{' '}
          {formatDate(marketReport.period.end)}
        </Typography>
        <Typography variant="body2" color="inherit">
          {sentiment.label}
        </Typography>
      </Alert>

      <Grid
        container
        spacing="var(--ob-space-200)"
        sx={{ mb: 'var(--ob-space-300)' }}
      >
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 'var(--ob-space-200)' }}>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Transactions (period)
            </Typography>
            <Typography variant="h5">
              {formatNumber(comparablesData?.transaction_count)}
            </Typography>
            <Typography variant="caption" color="textSecondary">
              Total volume {formatCurrency(comparablesData?.total_volume)}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 'var(--ob-space-200)' }}>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Average PSF
            </Typography>
            <Typography variant="h5">
              ${formatNumber(comparablesData?.average_psf)}
            </Typography>
            <Typography variant="caption" color="textSecondary">
              Median ${formatNumber(comparablesData?.median_psf)}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 'var(--ob-space-200)' }}>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Cap Rate (median)
            </Typography>
            <Typography variant="h5">
              {formatPercentSmart(
                yieldData?.current_metrics.cap_rate.median,
                2,
              )}
            </Typography>
            <Typography variant="caption" color="textSecondary">
              Range{' '}
              {formatPercentSmart(
                yieldData?.current_metrics.cap_rate.range.p25,
                2,
              )}{' '}
              -{' '}
              {formatPercentSmart(
                yieldData?.current_metrics.cap_rate.range.p75,
                2,
              )}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 'var(--ob-space-200)' }}>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Supply Pressure
            </Typography>
            <Chip
              label={
                supplyData?.supply_pressure
                  ? supplyData.supply_pressure.replace('_', ' ')
                  : 'N/A'
              }
              color={
                supplyData?.supply_pressure === 'high'
                  ? 'error'
                  : supplyData?.supply_pressure === 'low'
                    ? 'success'
                    : 'default'
              }
              size="small"
            />
            <Typography
              variant="caption"
              color="textSecondary"
              display="block"
              sx={{ mt: 'var(--ob-space-100)' }}
            >
              Upcoming GFA {formatNumber(supplyData?.total_upcoming_gfa)} sqm
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      <Grid
        container
        spacing="var(--ob-space-200)"
        sx={{ mb: 'var(--ob-space-300)' }}
      >
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 'var(--ob-space-200)', height: '100%' }}>
            <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
              Absorption Snapshot
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Sales absorption:{' '}
              {formatPercentSmart(
                absorptionData?.current_metrics.sales_absorption_rate,
              )}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Leasing absorption:{' '}
              {formatPercentSmart(
                absorptionData?.current_metrics.leasing_absorption_rate,
              )}
            </Typography>
            <Typography
              variant="caption"
              color="textSecondary"
              display="block"
              sx={{ mt: 'var(--ob-space-100)' }}
            >
              Velocity trend:{' '}
              {absorptionData?.velocity_trend?.replace('_', ' ') ?? 'N/A'}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 'var(--ob-space-200)', height: '100%' }}>
            <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
              Yield Outlook
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Rental median: $
              {formatNumber(yieldData?.current_metrics.rental_rates.median_psf)}{' '}
              psf/month
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Occupancy:{' '}
              {formatPercentSmart(
                yieldData?.current_metrics.rental_rates.occupancy,
              )}
            </Typography>
            <Typography
              variant="caption"
              color="textSecondary"
              display="block"
              sx={{ mt: 'var(--ob-space-100)' }}
            >
              {yieldData?.market_position?.replace('_', ' ') ??
                'No yield position available'}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 'var(--ob-space-200)', height: '100%' }}>
            <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
              Supply Impact
            </Typography>
            <Typography variant="body2" color="textSecondary">
              {supplyData?.market_impact ??
                'No supply impact assessment available'}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {marketReport.recommendations.length > 0 && (
        <Paper sx={{ p: 'var(--ob-space-200)' }}>
          <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
            Recommendations
          </Typography>
          <List dense>
            {marketReport.recommendations
              .slice(0, 5)
              .map((recommendation, index) => (
                <ListItem key={index}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <CheckCircleIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary={recommendation} />
                </ListItem>
              ))}
          </List>
        </Paper>
      )}
    </Box>
  )
}

export default QuickInsights
