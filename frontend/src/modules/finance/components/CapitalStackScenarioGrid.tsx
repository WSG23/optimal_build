import { Box, Grid, Typography, alpha, useTheme } from '@mui/material'

import type { FinanceScenarioSummary } from '../../../api/finance'
import { useTranslation } from '../../../i18n'
import { GlassCard } from '../../../components/canonical/GlassCard'
import { formatCurrencyShort, formatPercent } from '../utils/chartTheme'
import { CapitalStackMiniBar } from './CapitalStackMiniBar'

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

function getLatestDscr(scenario: FinanceScenarioSummary): number | null {
  if (!scenario.dscrTimeline || scenario.dscrTimeline.length === 0) {
    return null
  }
  for (let index = scenario.dscrTimeline.length - 1; index >= 0; index -= 1) {
    const entry = scenario.dscrTimeline[index]
    const dscr = toNumber(entry.dscr ?? null)
    if (dscr !== null) {
      return dscr
    }
  }
  return null
}

function formatNumber(value: number, decimals = 2): string {
  return value.toFixed(decimals).replace(/\.00$/, '')
}

interface ScenarioCardProps {
  scenario: FinanceScenarioSummary
  active: boolean
  onSelect: (scenarioId: number) => void
}

function ScenarioCard({ scenario, active, onSelect }: ScenarioCardProps) {
  const { t } = useTranslation()
  const theme = useTheme()

  const currency = scenario.currency ?? 'SGD'
  const escalatedCost = toNumber(scenario.escalatedCost)
  const npv = getResultValue(scenario, 'NPV')
  const irr = getResultValue(scenario, 'IRR')
  const dscr = getLatestDscr(scenario)

  const activeBorder = alpha(theme.palette.primary.main, 0.4)
  const activeBg = alpha(theme.palette.primary.main, 0.06)

  return (
    <Box
      component="button"
      type="button"
      onClick={() => onSelect(scenario.scenarioId)}
      sx={{
        width: '100%',
        textAlign: 'left',
        border: 'none',
        background: 'transparent',
        padding: 0,
        cursor: 'pointer',
        '&:focus-visible .capital-stack-scenario-card': {
          outline: `2px solid ${theme.palette.primary.main}`,
          outlineOffset: 2,
        },
      }}
    >
      <GlassCard
        className="capital-stack-scenario-card"
        sx={{
          textAlign: 'left',
          width: '100%',
          border: 1,
          borderColor: active ? activeBorder : 'divider',
          bgcolor: active ? activeBg : 'background.paper',
          p: 'var(--ob-space-150)',
          '&:hover': {
            borderColor: 'primary.main',
            boxShadow: 2,
          },
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 'var(--ob-space-100)',
            mb: 'var(--ob-space-075)',
          }}
        >
          <Box sx={{ minWidth: 0 }}>
            <Typography
              sx={{
                fontWeight: 800,
                fontSize: 'var(--ob-font-size-lg)',
                color: 'text.primary',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {scenario.scenarioName}
            </Typography>
            {scenario.isPrimary ? (
              <Typography
                sx={{
                  mt: 'var(--ob-space-025)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 'var(--ob-space-050)',
                  fontSize: 'var(--ob-font-size-xs)',
                  fontWeight: 800,
                  letterSpacing: 'var(--ob-letter-spacing-wider)',
                  color: 'primary.main',
                  textTransform: 'uppercase',
                }}
              >
                {t('finance.scenarios.primary', { defaultValue: 'Primary' })}
              </Typography>
            ) : (
              <Typography
                sx={{
                  mt: 'var(--ob-space-025)',
                  fontSize: 'var(--ob-font-size-xs)',
                  color: 'text.secondary',
                }}
              >
                {scenario.description || t('finance.capitalStack.baseCase')}
              </Typography>
            )}
          </Box>
          {active ? (
            <Box
              sx={{
                width: 'var(--ob-space-050)',
                height: 'var(--ob-space-050)',
                borderRadius: '50%',
                bgcolor: 'primary.main',
                flexShrink: 0,
              }}
            />
          ) : null}
        </Box>

        <Grid container spacing="var(--ob-space-100)">
          <Grid item xs={6}>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-2xs)',
                color: 'text.secondary',
              }}
            >
              {t('finance.scenarios.metrics.escalatedCost', {
                defaultValue: 'Escalated cost',
              })}
            </Typography>
            <Typography
              sx={{
                fontWeight: 700,
                color: 'text.primary',
                fontFamily: 'var(--ob-font-family-mono)',
              }}
            >
              {escalatedCost !== null
                ? formatCurrencyShort(escalatedCost, currency)
                : t('common.fallback.dash')}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-2xs)',
                color: 'text.secondary',
              }}
            >
              {t('finance.scenarios.metrics.npv', { defaultValue: 'NPV' })}
            </Typography>
            <Typography
              sx={{
                fontWeight: 700,
                color: 'text.primary',
                fontFamily: 'var(--ob-font-family-mono)',
              }}
            >
              {npv !== null
                ? formatCurrencyShort(npv, currency)
                : t('common.fallback.dash')}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-2xs)',
                color: 'text.secondary',
              }}
            >
              {t('finance.scenarios.metrics.irr', { defaultValue: 'IRR' })}
            </Typography>
            <Typography
              sx={{
                fontWeight: 700,
                color: 'success.main',
                fontFamily: 'var(--ob-font-family-mono)',
              }}
            >
              {irr !== null ? formatPercent(irr, 2) : t('common.fallback.dash')}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-2xs)',
                color: 'text.secondary',
              }}
            >
              {t('finance.scenarios.metrics.dscr', { defaultValue: 'DSCR' })}
            </Typography>
            <Typography
              sx={{
                fontWeight: 700,
                color:
                  dscr !== null && dscr < 1 ? 'error.main' : 'text.primary',
                fontFamily: 'var(--ob-font-family-mono)',
              }}
            >
              {dscr !== null ? formatNumber(dscr) : t('common.fallback.dash')}
            </Typography>
          </Grid>
        </Grid>

        {scenario.capitalStack ? (
          <Box sx={{ mt: 'var(--ob-space-125)' }}>
            <CapitalStackMiniBar stack={scenario.capitalStack} />
          </Box>
        ) : null}
      </GlassCard>
    </Box>
  )
}

interface CapitalStackScenarioGridProps {
  scenarios: FinanceScenarioSummary[]
  activeScenarioId: number | null
  onSelect: (scenarioId: number) => void
}

export function CapitalStackScenarioGrid({
  scenarios,
  activeScenarioId,
  onSelect,
}: CapitalStackScenarioGridProps) {
  const { t } = useTranslation()

  if (scenarios.length === 0) {
    return null
  }

  return (
    <Box sx={{ mb: 'var(--ob-space-150)' }}>
      <Typography
        sx={{
          fontSize: 'var(--ob-font-size-sm)',
          fontWeight: 700,
          color: 'text.primary',
          mb: 'var(--ob-space-075)',
        }}
      >
        {t('finance.scenarios.sectionTitle', {
          defaultValue: 'Scenarios',
        })}
      </Typography>
      <Grid container spacing="var(--ob-space-150)">
        {scenarios.map((scenario) => (
          <Grid item xs={12} md={4} key={scenario.scenarioId}>
            <ScenarioCard
              scenario={scenario}
              active={scenario.scenarioId === activeScenarioId}
              onSelect={onSelect}
            />
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}

export default CapitalStackScenarioGrid
