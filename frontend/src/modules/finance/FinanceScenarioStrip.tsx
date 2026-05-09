import { Box, Stack, Tooltip, Typography } from '@mui/material'

import type { FinanceScenarioSummary } from '../../api/finance'
import { formatCurrencyFull, formatPercent } from './utils/chartTheme'

interface FinanceScenarioStripProps {
  scenario: FinanceScenarioSummary
  /** Whether this is the primary scenario or just being viewed */
  isPrimary?: boolean
  locale?: string
}

function toNumber(value: string | null | undefined): number | null {
  if (typeof value !== 'string') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

const METRIC_TOOLTIPS: Record<string, string> = {
  Cost: 'Total escalated project cost',
  LTC: 'Loan-to-cost ratio — total debt as a percentage of project cost',
  NPV: 'Net present value — the present-day value of all future cash flows',
  IRR: 'Internal rate of return — annualized effective compounded return rate',
}

export function FinanceScenarioStrip({
  scenario,
  isPrimary = true,
  locale = 'en',
}: FinanceScenarioStripProps) {
  const currency = scenario.currency ?? 'SGD'
  const stack = scenario.capitalStack
  const total = toNumber(stack?.total)
  const loanToCost = toNumber(stack?.loanToCost)

  const npvResult = scenario.results.find((r) => r.name === 'npv')
  const npvValue = npvResult?.value ? toNumber(String(npvResult.value)) : null

  const irrResult = scenario.results.find((r) => r.name === 'irr')
  const irrValue = irrResult?.value ? toNumber(String(irrResult.value)) : null

  const statusLabel = isPrimary ? 'Primary' : 'Viewing'

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--ob-space-200)',
        px: 'var(--ob-space-150)',
        py: 'var(--ob-space-075)',
        borderBottom: 1,
        borderColor: 'divider',
        fontSize: 'var(--ob-font-size-xs)',
        overflowX: 'auto',
        whiteSpace: 'nowrap',
        minHeight: 'var(--ob-space-250)',
      }}
    >
      <Stack direction="row" spacing="var(--ob-space-050)" alignItems="center">
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-2xs)',
            fontWeight: 'var(--ob-font-weight-bold)',
            letterSpacing: 'var(--ob-letter-spacing-wider)',
            textTransform: 'uppercase',
            color: isPrimary
              ? 'text.secondary'
              : 'var(--ob-color-brand-primary)',
          }}
        >
          {statusLabel}
        </Typography>
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-sm)',
            fontWeight: 'var(--ob-font-weight-bold)',
            color: 'text.primary',
          }}
        >
          {scenario.scenarioName}
        </Typography>
      </Stack>

      <Divider />

      {total !== null && (
        <MetricChip
          label="Cost"
          value={formatCurrencyFull(total, currency, locale)}
        />
      )}
      {loanToCost !== null && (
        <MetricChip label="LTC" value={formatPercent(loanToCost)} />
      )}
      {npvValue !== null && (
        <MetricChip
          label="NPV"
          value={formatCurrencyFull(npvValue, currency, locale)}
        />
      )}
      {irrValue !== null && (
        <MetricChip label="IRR" value={formatPercent(irrValue)} />
      )}
    </Box>
  )
}

function Divider() {
  return (
    <Box
      sx={{
        height: 'var(--ob-space-150)',
        width: 1,
        bgcolor: 'divider',
        flexShrink: 0,
      }}
    />
  )
}

function MetricChip({ label, value }: { label: string; value: string }) {
  const tooltip = METRIC_TOOLTIPS[label]
  return (
    <Tooltip title={tooltip ?? ''} placement="bottom" arrow>
      <Stack
        direction="row"
        spacing="var(--ob-space-050)"
        alignItems="baseline"
      >
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-2xs)',
            fontWeight: 'var(--ob-font-weight-semibold)',
            color: 'text.secondary',
            textTransform: 'uppercase',
            letterSpacing: 'var(--ob-letter-spacing-wider)',
          }}
        >
          {label}
        </Typography>
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-sm)',
            fontWeight: 'var(--ob-font-weight-bold)',
            fontFamily: 'var(--ob-font-family-mono)',
            color: 'text.primary',
          }}
        >
          {value}
        </Typography>
      </Stack>
    </Tooltip>
  )
}
