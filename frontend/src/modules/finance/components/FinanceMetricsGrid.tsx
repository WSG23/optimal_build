/**
 * FinanceMetricsGrid - 4-column responsive metrics grid
 *
 * - Uses PremiumMetricCard with tooltips explaining each metric
 * - Grid uses xs={6} md={3} for responsive 2/4 columns
 */

import { useMemo } from 'react'
import { Box, Grid, Tooltip } from '@mui/material'
import MoneyIcon from '@mui/icons-material/AttachMoney'
import TrendingIcon from '@mui/icons-material/TrendingUp'
import BankIcon from '@mui/icons-material/AccountBalance'
import PieIcon from '@mui/icons-material/PieChart'

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
  tooltip?: string
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
        tooltip: 'Blended interest rate across all debt facilities',
        value: weightedRate !== null ? formatPercent(weightedRate) : fallback,
        icon: <TrendingIcon />,
      },
      {
        key: 'loanToCost',
        label: t('finance.metrics.loanToCost', { defaultValue: 'LTC' }),
        tooltip:
          'Loan-to-cost ratio — total debt as a percentage of project cost',
        value: loanToCost !== null ? formatPercent(loanToCost) : fallback,
        icon: <BankIcon />,
      },
      {
        key: 'equityShare',
        label: t('finance.metrics.equityShare', {
          defaultValue: 'Equity Share',
        }),
        tooltip: 'Equity contribution as a percentage of total project cost',
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
            <Tooltip title={metric.tooltip ?? ''} placement="bottom" arrow>
              <Box sx={{ height: '100%' }}>
                <PremiumMetricCard
                  label={metric.label}
                  value={metric.value}
                  icon={metric.icon}
                  featured={metric.featured}
                  compact
                />
              </Box>
            </Tooltip>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}

export default FinanceMetricsGrid
