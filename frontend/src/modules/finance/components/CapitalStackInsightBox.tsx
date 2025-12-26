import { Box, Typography } from '@mui/material'

import type { FinanceScenarioSummary } from '../../../api/finance'
import { useTranslation } from '../../../i18n'
import { GlassCard } from '../../../components/canonical/GlassCard'
import { formatCurrencyShort, formatPercent } from '../utils/chartTheme'

function toNumber(value: string | null | undefined): number | null {
  if (typeof value !== 'string') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function getResultValue(
  scenario: FinanceScenarioSummary,
  key: string,
): number | null {
  const target = key.trim().toLowerCase()
  const match = scenario.results.find(
    (entry) => entry.name.trim().toLowerCase() === target,
  )
  return toNumber(match?.value ?? null)
}

interface CapitalStackInsightBoxProps {
  scenarios: FinanceScenarioSummary[]
  activeScenarioId: number | null
}

export function CapitalStackInsightBox({
  scenarios,
  activeScenarioId,
}: CapitalStackInsightBoxProps) {
  const { t } = useTranslation()

  const withCapitalStack = scenarios.filter((scenario) =>
    Boolean(scenario.capitalStack),
  )
  if (withCapitalStack.length < 2) {
    return null
  }

  const baseScenario =
    withCapitalStack.find((scenario) => scenario.isPrimary) ??
    withCapitalStack[0]
  const npvRanked = [...withCapitalStack].sort((a, b) => {
    const aNpv = getResultValue(a, 'NPV') ?? -Infinity
    const bNpv = getResultValue(b, 'NPV') ?? -Infinity
    return bNpv - aNpv
  })
  const bestScenario = npvRanked[0]
  const bestNpv = getResultValue(bestScenario, 'NPV')
  const baseDebtRate = toNumber(
    baseScenario.capitalStack?.weightedAverageDebtRate,
  )
  const bestDebtRate = toNumber(
    bestScenario.capitalStack?.weightedAverageDebtRate,
  )
  const debtRateDelta =
    baseDebtRate !== null && bestDebtRate !== null
      ? bestDebtRate - baseDebtRate
      : null

  const currency = bestScenario.currency ?? baseScenario.currency ?? 'SGD'
  const bestLabel =
    activeScenarioId && bestScenario.scenarioId === activeScenarioId
      ? t('finance.insight.thisScenario', { defaultValue: 'This scenario' })
      : bestScenario.scenarioName

  const headline =
    bestNpv !== null
      ? t('finance.insight.headline', {
          defaultValue:
            '{{name}} offers the highest NPV ({{npv}}) due to optimized leverage.',
          name: bestLabel,
          npv: formatCurrencyShort(bestNpv, currency),
        })
      : t('finance.insight.headlineFallback', {
          defaultValue:
            '{{name}} appears to offer the strongest value based on current metrics.',
          name: bestLabel,
        })

  const detail =
    debtRateDelta !== null
      ? t('finance.insight.detail', {
          defaultValue:
            'However, the weighted debt rate is {{delta}} vs the base case.',
          delta:
            debtRateDelta >= 0
              ? `+${formatPercent(debtRateDelta, 2)}`
              : formatPercent(debtRateDelta, 2),
        })
      : t('finance.insight.detailFallback', {
          defaultValue:
            'Review debt costs and cash-flow resilience to confirm the recommendation.',
        })

  const recommendation = t('finance.insight.recommendation', {
    defaultValue: 'Consider negotiating mezzanine fees.',
  })

  return (
    <GlassCard
      sx={{
        p: 'var(--ob-space-150)',
        border: 1,
        borderColor: 'var(--ob-color-brand-soft)',
        bgcolor: 'var(--ob-color-brand-soft)',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-050)',
        }}
      >
        <Typography
          sx={{
            fontWeight: 700,
            fontSize: 'var(--ob-font-size-md)',
            color: 'text.primary',
          }}
        >
          {t('finance.insight.title', { defaultValue: 'AI Financial Insight' })}
        </Typography>
        <Typography sx={{ color: 'text.primary' }}>{headline}</Typography>
        <Typography sx={{ color: 'text.secondary' }}>{detail}</Typography>
        <Typography
          sx={{
            mt: 'var(--ob-space-050)',
            display: 'flex',
            justifyContent: 'space-between',
            gap: 'var(--ob-space-100)',
            color: 'text.primary',
            fontWeight: 600,
          }}
        >
          <span>
            {t('finance.insight.recommendationLabel', {
              defaultValue: 'Recommendation:',
            })}
          </span>
          <span>{recommendation}</span>
        </Typography>
      </Box>
    </GlassCard>
  )
}

export default CapitalStackInsightBox
