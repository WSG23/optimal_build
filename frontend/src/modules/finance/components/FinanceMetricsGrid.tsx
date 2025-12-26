/**
 * FinanceMetricsGrid - 4-column responsive metrics grid
 *
 * Follows UI_STANDARDS.md Metrics Grid Pattern:
 * - Uses PremiumMetricCard for cyber aesthetic
 * - Grid uses xs={6} md={3} for responsive 2/4 columns
 * - Neon glow on key metrics
 */

import { useMemo } from 'react'
import { Box, Grid } from '@mui/material'
import {
  AttachMoney as MoneyIcon,
  TrendingUp as TrendingIcon,
  AccountBalance as BankIcon,
  PieChart as PieIcon,
} from '@mui/icons-material'

import { useTranslation } from '../../../i18n'
import { PremiumMetricCard } from '../../../components/canonical/PremiumMetricCard'
import type { FinanceScenarioSummary } from '../../../api/finance'
import { formatCurrencyFull, formatPercent } from '../utils/chartTheme'

interface FinanceMetricsGridProps {
  scenario: FinanceScenarioSummary | null
}

interface MetricItem {
  key: string
  label: string
  value: string
  icon: React.ReactNode
  featured?: boolean
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
        }),
        value:
          total !== null
            ? formatCurrencyFull(total, currency, locale)
            : fallback,
        icon: <MoneyIcon />,
        featured: true,
      },
      {
        key: 'weightedRate',
        label: t('finance.metrics.weightedRate', {
          defaultValue: 'Weighted Debt Rate',
        }),
        value: weightedRate !== null ? formatPercent(weightedRate) : fallback,
        icon: <TrendingIcon />,
      },
      {
        key: 'loanToCost',
        label: t('finance.metrics.loanToCost', { defaultValue: 'LTC' }),
        value: loanToCost !== null ? formatPercent(loanToCost) : fallback,
        icon: <BankIcon />,
      },
      {
        key: 'equityShare',
        label: t('finance.metrics.equityShare', {
          defaultValue: 'Equity Share',
        }),
        value: equityRatio !== null ? formatPercent(equityRatio) : fallback,
        icon: <PieIcon />,
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
            <PremiumMetricCard
              label={metric.label}
              value={metric.value}
              icon={metric.icon}
              featured={metric.featured}
              status="live"
              compact
            />
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}

export default FinanceMetricsGrid
