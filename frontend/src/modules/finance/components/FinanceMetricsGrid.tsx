/**
 * FinanceMetricsGrid - 4-column responsive metrics grid
 *
 * Follows UI_STANDARDS.md Metrics Grid Pattern:
 * - Uses GlassCard for metric containers
 * - Grid uses xs={6} md={3} for responsive 2/4 columns
 * - Label uses --ob-font-size-sm, text.secondary
 * - Value uses --ob-font-size-2xl, fontWeight: 700
 */

import { useMemo } from 'react'

import { Box, Grid, Typography } from '@mui/material'

import { useTranslation } from '../../../i18n'
import { GlassCard } from '../../../components/canonical/GlassCard'
import type { FinanceScenarioSummary } from '../../../api/finance'
import { formatCurrencyFull, formatPercent } from '../utils/chartTheme'

interface FinanceMetricsGridProps {
  scenario: FinanceScenarioSummary | null
}

interface MetricItem {
  key: string
  label: string
  value: string
  color?: 'primary' | 'success' | 'warning' | 'error' | 'default'
}

function toNumber(value: string | null | undefined): number | null {
  if (typeof value !== 'string') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

export function FinanceMetricsGrid({ scenario }: FinanceMetricsGridProps) {
  const { t, i18n } = useTranslation()
  const locale = i18n.language
  const fallback = t('common.fallback.dash')

  const metrics = useMemo<MetricItem[]>(() => {
    if (!scenario?.capitalStack) return []

    const stack = scenario.capitalStack
    const currency = scenario.currency ?? 'SGD'

    const total = toNumber(stack.total)
    const loanToCost = toNumber(stack.loanToCost)
    const equityRatio = toNumber(stack.equityRatio)
    const weightedRate = toNumber(stack.weightedAverageDebtRate)

    return [
      {
        key: 'totalCost',
        label: t('finance.metrics.totalCost'),
        value:
          total !== null
            ? formatCurrencyFull(total, currency, locale)
            : fallback,
      },
      {
        key: 'weightedRate',
        label: t('finance.metrics.weightedRate'),
        value: weightedRate !== null ? formatPercent(weightedRate) : fallback,
      },
      {
        key: 'loanToCost',
        label: t('finance.metrics.loanToCost'),
        value: loanToCost !== null ? formatPercent(loanToCost) : fallback,
        color: 'primary',
      },
      {
        key: 'equityShare',
        label: t('finance.metrics.equityShare'),
        value: equityRatio !== null ? formatPercent(equityRatio) : fallback,
        color: 'success',
      },
    ]
  }, [scenario, t, locale, fallback])

  if (metrics.length === 0) {
    return null
  }

  const getValueColor = (color?: MetricItem['color']) => {
    switch (color) {
      case 'primary':
        return 'primary.main'
      case 'success':
        return 'success.main'
      case 'warning':
        return 'warning.main'
      case 'error':
        return 'error.main'
      default:
        return 'text.primary'
    }
  }

  return (
    <Box sx={{ mb: 'var(--ob-space-150)' }}>
      <Grid container spacing="var(--ob-space-100)">
        {metrics.map((metric) => (
          <Grid item xs={6} md={3} key={metric.key}>
            <GlassCard
              sx={{
                p: 'var(--ob-space-100)',
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
              }}
            >
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-sm)',
                  color: 'text.secondary',
                  mb: 'var(--ob-space-025)',
                  lineHeight: 1.3,
                }}
              >
                {metric.label}
              </Typography>
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-2xl)',
                  fontWeight: 700,
                  color: getValueColor(metric.color),
                  lineHeight: 1.2,
                }}
              >
                {metric.value}
              </Typography>
            </GlassCard>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}

export default FinanceMetricsGrid
