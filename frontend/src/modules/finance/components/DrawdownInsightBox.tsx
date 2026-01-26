/**
 * DrawdownInsightBox - Analysis callout with cyan border
 *
 * Displays dynamic insight text about peak debt exposure.
 * Premium cyber aesthetic with cyan accents for visual consistency.
 *
 * Follows UI_STANDARDS.md for design tokens.
 */

import { Box, Typography } from '@mui/material'

import { useTranslation } from '../../../i18n'
import type { FinanceScenarioSummary } from '../../../api/finance'
import { formatCurrencyFull } from '../utils/chartTheme'

interface DrawdownInsightBoxProps {
  scenario: FinanceScenarioSummary | null
}

function toNumber(value: string | null | undefined): number | null {
  if (typeof value !== 'string') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

export function DrawdownInsightBox({ scenario }: DrawdownInsightBoxProps) {
  const { t, i18n } = useTranslation()
  const locale = i18n.language

  if (!scenario?.drawdownSchedule) {
    return null
  }

  const { drawdownSchedule } = scenario
  const currency = scenario.currency ?? 'SGD'
  const peakDebt = toNumber(drawdownSchedule.peakDebtBalance)
  const periodCount = drawdownSchedule.entries?.length ?? 0

  // Find the period where peak debt occurs (last period typically)
  const peakPeriod =
    drawdownSchedule.entries?.[periodCount - 1]?.period ?? `M${periodCount}`

  return (
    <Box
      sx={{
        bgcolor: 'var(--ob-color-table-row-selected)',
        border: 2,
        borderColor: 'var(--ob-color-neon-cyan-muted)',
        borderRadius: 'var(--ob-radius-sm)',
        p: 'var(--ob-space-150)',
        mt: 'var(--ob-space-150)',
      }}
    >
      <Typography
        sx={{
          fontSize: 'var(--ob-font-size-sm)',
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: 'var(--ob-letter-spacing-wider)',
          color: 'var(--ob-color-neon-cyan)',
          textShadow: 'var(--ob-glow-neon-text)',
          mb: 'var(--ob-space-050)',
        }}
      >
        {t('finance.drawdown.analysis.title')}
      </Typography>
      <Typography
        sx={{
          fontSize: 'var(--ob-font-size-sm)',
          color: 'text.primary',
          lineHeight: 1.6,
          '& strong': {
            fontWeight: 600,
            color: 'var(--ob-color-neon-cyan)',
          },
        }}
      >
        {t('finance.drawdown.analysis.text', {
          scenario: scenario.scenarioName,
          peakDebt:
            peakDebt !== null
              ? formatCurrencyFull(peakDebt, currency, locale)
              : '--',
          peakPeriod,
        })}
      </Typography>
    </Box>
  )
}

export default DrawdownInsightBox
