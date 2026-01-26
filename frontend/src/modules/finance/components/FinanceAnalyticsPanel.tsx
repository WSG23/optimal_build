import { Box, Grid, Typography } from '@mui/material'
import { ShowChart, AccountBalanceWallet, Paid } from '@mui/icons-material'

import type {
  FinanceAnalyticsBucket,
  FinanceAnalyticsMetadata,
} from '../../../api/finance'
import { Card } from '../../../components/canonical/Card'
import { NeonText } from '../../../components/canonical/NeonText'
import { PremiumMetricCard } from '../../../components/canonical/PremiumMetricCard'

interface FinanceAnalyticsPanelProps {
  analytics: FinanceAnalyticsMetadata
  currency: string
}

function formatCurrencyValue(
  value: string | null | undefined,
  currency: string,
): string {
  if (value === null || value === undefined || value === '') {
    return '—'
  }
  const amount = Number(value)
  if (!Number.isFinite(amount)) {
    return value
  }
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency,
      maximumFractionDigits: 0,
    }).format(amount)
  } catch {
    return `${value} ${currency}`
  }
}

function formatRatio(value: string | null | undefined): string {
  if (!value) {
    return '—'
  }
  return `${value}x`
}

/**
 * DSCR bucket bar color gradients - all within cyan family for visual consistency.
 * Reference: optimal-build-v2-dashboard uses ['#00f3ff', '#0096cc', '#1e293b']
 * Semantic colors (orange/green) reserved for status badges and alert banners only.
 */
const BUCKET_COLORS: Record<string, string> = {
  lt_1: 'var(--ob-color-primary)', // Darker cyan for DSCR < 1 (still in cyan family)
  '1_to_1_25': 'var(--ob-color-neon-cyan)', // Bright cyan
  gt_1_25: 'var(--ob-color-neon-cyan)', // Bright cyan
}

function BucketBar({
  bucket,
  total,
}: {
  bucket: FinanceAnalyticsBucket
  total: number
}): JSX.Element {
  const percentage = total > 0 ? Math.round((bucket.count / total) * 100) : 0
  const barColor = BUCKET_COLORS[bucket.key] ?? 'var(--ob-color-neon-cyan)'

  return (
    <Box
      key={bucket.key}
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--ob-space-100)',
        mb: 'var(--ob-space-075)',
      }}
    >
      <Typography
        sx={{
          width: '120px',
          fontWeight: 'var(--ob-font-weight-semibold)',
          fontSize: 'var(--ob-font-size-sm)',
          color: 'text.primary',
        }}
      >
        {bucket.label}
      </Typography>
      <Box
        sx={{
          flex: 1,
          background: 'var(--ob-overlay-medium)',
          borderRadius: 'var(--ob-radius-xs)',
          height: '8px',
          overflow: 'hidden',
        }}
      >
        <Box
          sx={{
            width: `${Math.max(percentage, 2)}%`,
            background: barColor,
            height: '100%',
            boxShadow: 'var(--ob-glow-neon-cyan)',
            transition: 'width 0.5s ease-out',
          }}
        />
      </Box>
      <NeonText
        variant="caption"
        intensity="subtle"
        color="cyan"
        sx={{ width: '40px', textAlign: 'right' }}
      >
        {bucket.count}
      </NeonText>
    </Box>
  )
}

export function FinanceAnalyticsPanel({
  analytics,
  currency,
}: FinanceAnalyticsPanelProps) {
  const cashSummary = analytics.cash_flow_summary ?? {}
  const buckets = analytics.dscr_heatmap?.buckets ?? []
  const totalPeriods = buckets.reduce((sum, bucket) => sum + bucket.count, 0)

  return (
    <Card
      variant="premium"
      accent
      sx={{
        mt: 'var(--ob-space-200)',
        p: 'var(--ob-space-200)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-150)',
      }}
    >
      {/* Header */}
      <Box>
        <Typography
          variant="h6"
          sx={{
            fontWeight: 'var(--ob-font-weight-bold)',
            color: 'text.primary',
            mb: 'var(--ob-space-025)',
          }}
        >
          Advanced Analytics
        </Typography>
        <Typography
          variant="body2"
          sx={{ color: 'text.secondary', fontSize: 'var(--ob-font-size-sm)' }}
        >
          MOIC, equity multiples, and DSCR health derived from the current
          scenario.
        </Typography>
      </Box>

      {/* Metrics Grid */}
      <Grid container spacing="var(--ob-space-100)">
        <Grid item xs={12} sm={4}>
          <PremiumMetricCard
            label="MOIC"
            value={formatRatio(analytics.moic)}
            icon={<ShowChart />}
            featured
            status="live"
            compact
          />
        </Grid>
        <Grid item xs={12} sm={4}>
          <PremiumMetricCard
            label="Equity Multiple"
            value={formatRatio(analytics.equity_multiple)}
            icon={<AccountBalanceWallet />}
            status="live"
            compact
          />
        </Grid>
        <Grid item xs={12} sm={4}>
          <PremiumMetricCard
            label="Equity Invested"
            value={formatCurrencyValue(cashSummary.invested_equity, currency)}
            icon={<Paid />}
            status="live"
            compact
          />
        </Grid>
      </Grid>

      {/* Net Cash sub-metric */}
      <Box sx={{ mt: 'var(--ob-space-050)' }}>
        <Typography
          variant="caption"
          sx={{ color: 'text.secondary', fontSize: 'var(--ob-font-size-xs)' }}
        >
          Net cash:{' '}
          <NeonText
            variant="caption"
            intensity="subtle"
            sx={{ display: 'inline' }}
          >
            {formatCurrencyValue(cashSummary.net_cash, currency)}
          </NeonText>
        </Typography>
      </Box>

      {/* DSCR Heat Map */}
      <Box>
        <Typography
          variant="subtitle1"
          sx={{
            fontWeight: 'var(--ob-font-weight-semibold)',
            color: 'text.primary',
            mb: 'var(--ob-space-100)',
          }}
        >
          DSCR Heat Map{' '}
          <Typography
            component="span"
            sx={{ color: 'text.secondary', fontSize: 'var(--ob-font-size-sm)' }}
          >
            ({totalPeriods} periods)
          </Typography>
        </Typography>
        {buckets.length === 0 ? (
          <Typography variant="body2" sx={{ color: 'text.secondary' }}>
            DSCR data not available.
          </Typography>
        ) : (
          <Box>
            {buckets.map((bucket) => (
              <BucketBar
                key={bucket.key}
                bucket={bucket}
                total={totalPeriods}
              />
            ))}
          </Box>
        )}
      </Box>
    </Card>
  )
}
