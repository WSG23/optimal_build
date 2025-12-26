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
import { Box, Grid } from '@mui/material'

import { useTranslation } from '../../../i18n'
import { MetricCard } from '../../../components/canonical/MetricCard'
import type { FinanceScenarioSummary } from '../../../api/finance'
import { formatCurrencyFull, formatPercent } from '../utils/chartTheme'

interface FinanceMetricsGridProps {
  scenario: FinanceScenarioSummary | null
}

interface MetricItem {
  key: string
  label: string
  value: string
  trend?: number
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
        label: t('finance.metrics.totalCost', {
          defaultValue: 'Total Project Cost',
        }), // Use explicit default to match screenshot
        value:
          total !== null
            ? formatCurrencyFull(total, currency, locale)
            : fallback,
      },
      {
        key: 'weightedRate',
        label: t('finance.metrics.weightedRate', {
          defaultValue: 'Weighted Debt Rate',
        }),
        value: weightedRate !== null ? formatPercent(weightedRate) : fallback,
      },
      {
        key: 'loanToCost',
        label: t('finance.metrics.loanToCost', { defaultValue: 'LTC' }),
        value: loanToCost !== null ? formatPercent(loanToCost) : fallback,
      },
      {
        key: 'equityShare',
        label: t('finance.metrics.equityShare', {
          defaultValue: 'Equity Share',
        }),
        value: equityRatio !== null ? formatPercent(equityRatio) : fallback,
      },
    ]
  }, [scenario, t, locale, fallback])

  if (metrics.length === 0) {
    return null
  }

  return (
    <Box sx={{ mb: 'var(--ob-space-150)' }}>
      <Grid container spacing="var(--ob-space-100)">
        {metrics.map((metric) => (
          <Grid item xs={6} md={3} key={metric.key}>
            <MetricCard
              label={metric.label}
              value={metric.value}
              compact
              // We could add trends if available in data
            />
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}

export default FinanceMetricsGrid
