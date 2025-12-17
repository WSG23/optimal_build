/**
 * DrawdownStatsCards - 3-column stats grid with icons
 *
 * Displays: Equity Deployed, Debt Deployed, Peak Debt Balance
 * Each card has:
 * - Icon on right side
 * - Label, large value, and subtext
 *
 * Follows UI_STANDARDS.md for design tokens and GlassCard usage.
 */

import { Box, Grid, Typography, useTheme, alpha } from '@mui/material'
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
  iconColor?: 'primary' | 'success' | 'warning' | 'error' | 'info'
}

function StatsCard({
  label,
  value,
  subtext,
  icon: Icon,
  iconColor = 'primary',
}: StatsCardProps) {
  const theme = useTheme()

  const getIconBgColor = () => {
    switch (iconColor) {
      case 'success':
        return alpha(theme.palette.success.main, 0.1)
      case 'warning':
        return alpha(theme.palette.warning.main, 0.1)
      case 'error':
        return alpha(theme.palette.error.main, 0.1)
      case 'info':
        return alpha(theme.palette.info.main, 0.1)
      default:
        return alpha(theme.palette.primary.main, 0.1)
    }
  }

  const getIconColor = () => {
    switch (iconColor) {
      case 'success':
        return 'success.main'
      case 'warning':
        return 'warning.main'
      case 'error':
        return 'error.main'
      case 'info':
        return 'info.main'
      default:
        return 'primary.main'
    }
  }

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
            color: 'text.primary',
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
          bgcolor: getIconBgColor(),
          color: getIconColor(),
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
      iconColor: 'primary' as const,
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
      iconColor: 'info' as const,
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
      iconColor: 'success' as const,
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
            iconColor={stat.iconColor}
          />
        </Grid>
      ))}
    </Grid>
  )
}

export default DrawdownStatsCards
