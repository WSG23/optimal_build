/**
 * DrawdownStatsCards - 3-column stats grid with icons
 *
 * Premium cyber aesthetic - all icons use cyan for visual consistency.
 * Displays: Equity Deployed, Debt Deployed, Peak Debt Balance
 *
 * Follows UI_STANDARDS.md for design tokens and GlassCard usage.
 */

import { Box, Grid, Typography } from '@mui/material'
import {
  AccountBalanceWallet as WalletIcon,
  AccountBalance as BankIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material'

import { GlassCard } from '../../../components/canonical/GlassCard'
import { useTranslation } from '../../../i18n'
import type { FinanceScenarioSummary } from '../../../api/finance'
import { formatCurrencyFull } from '../utils/chartTheme'

interface DrawdownStatsCardsProps {
  scenario: FinanceScenarioSummary | null
}

interface StatsCardProps {
  label: string
  value: string
  subtext: string
  icon: React.ElementType
}

/**
 * StatsCard - Uses consistent cyan styling for premium cyber aesthetic.
 */
function StatsCard({ label, value, subtext, icon: Icon }: StatsCardProps) {
  return (
    <GlassCard
      sx={{
        p: 'var(--ob-space-150)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        height: '100%',
      }}
    >
      <Box>
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-sm)',
            fontWeight: 500,
            color: 'text.secondary',
            mb: 'var(--ob-space-025)',
          }}
        >
          {label}
        </Typography>
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-2xl)',
            fontWeight: 700,
            color: 'var(--ob-color-neon-cyan)',
            textShadow: 'var(--ob-glow-neon-text)',
            letterSpacing: '-0.02em',
          }}
        >
          {value}
        </Typography>
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-xs)',
            color: 'text.disabled',
            mt: 'var(--ob-space-025)',
          }}
        >
          {subtext}
        </Typography>
      </Box>
      <Box
        sx={{
          p: 'var(--ob-space-075)',
          borderRadius: 'var(--ob-radius-sm)',
          bgcolor: 'rgba(0, 243, 255, 0.1)',
          color: 'var(--ob-color-neon-cyan)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Icon sx={{ fontSize: 20 }} />
      </Box>
    </GlassCard>
  )
}

function toNumber(value: string | null | undefined): number | null {
  if (typeof value !== 'string') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

export function DrawdownStatsCards({ scenario }: DrawdownStatsCardsProps) {
  const { t, i18n } = useTranslation()
  const fallback = t('common.fallback.dash')
  const locale = i18n.language

  if (!scenario?.drawdownSchedule) {
    return null
  }

  const { drawdownSchedule } = scenario
  const currency = scenario.currency ?? 'SGD'

  const totalEquity = toNumber(drawdownSchedule.totalEquity)
  const totalDebt = toNumber(drawdownSchedule.totalDebt)
  const peakDebt = toNumber(drawdownSchedule.peakDebtBalance)

  const stats = [
    {
      key: 'equityDeployed',
      label: t('finance.drawdown.stats.equityDeployed'),
      value:
        totalEquity !== null
          ? formatCurrencyFull(totalEquity, currency, locale)
          : fallback,
      subtext: t('finance.drawdown.stats.sponsorContribution'),
      icon: WalletIcon,
    },
    {
      key: 'debtDeployed',
      label: t('finance.drawdown.stats.debtDeployed'),
      value:
        totalDebt !== null
          ? formatCurrencyFull(totalDebt, currency, locale)
          : fallback,
      subtext: t('finance.drawdown.stats.lenderContribution'),
      icon: BankIcon,
    },
    {
      key: 'peakDebtBalance',
      label: t('finance.drawdown.stats.peakDebtBalance'),
      value:
        peakDebt !== null
          ? formatCurrencyFull(peakDebt, currency, locale)
          : fallback,
      subtext: t('finance.drawdown.stats.maxExposure'),
      icon: TrendingUpIcon,
    },
  ]

  return (
    <Grid
      container
      spacing="var(--ob-space-150)"
      sx={{ mb: 'var(--ob-space-200)' }}
    >
      {stats.map((stat) => (
        <Grid item xs={12} md={4} key={stat.key}>
          <StatsCard
            label={stat.label}
            value={stat.value}
            subtext={stat.subtext}
            icon={stat.icon}
          />
        </Grid>
      ))}
    </Grid>
  )
}

export default DrawdownStatsCards
