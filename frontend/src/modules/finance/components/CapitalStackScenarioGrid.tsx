import type { KeyboardEvent as ReactKeyboardEvent } from 'react'

import {
  Box,
  CircularProgress,
  Grid,
  IconButton,
  Tooltip,
  Typography,
  useTheme,
} from '@mui/material'
import {
  DeleteOutline as DeleteOutlineIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
} from '@mui/icons-material'

import type { FinanceScenarioSummary } from '../../../api/finance'
import { useTranslation } from '../../../i18n'
import { Card } from '../../../components/canonical/Card'
import { NeonText } from '../../../components/canonical/NeonText'
import { PulsingStatusDot } from '../../../components/canonical/PulsingStatusDot'
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
  onMarkPrimary?: (scenarioId: number) => void
  updatingScenarioId?: number | null
  onRequestDelete?: (scenarioId: number, scenarioName: string) => void
  deletingScenarioId?: number | null
}

function ScenarioCard({
  scenario,
  active,
  onSelect,
  onMarkPrimary,
  updatingScenarioId = null,
  onRequestDelete,
  deletingScenarioId = null,
}: ScenarioCardProps) {
  const { t } = useTranslation()
  const theme = useTheme()

  const currency = scenario.currency ?? 'SGD'
  const escalatedCost = toNumber(scenario.escalatedCost)
  const npv = getResultValue(scenario, 'NPV')
  const irr = getResultValue(scenario, 'IRR')
  const dscr = getLatestDscr(scenario)

  const canManage = scenario.scenarioId > 0
  const makingPrimary = updatingScenarioId === scenario.scenarioId
  const deleting = deletingScenarioId === scenario.scenarioId

  return (
    <Card
      variant={active ? 'premium' : 'glass'}
      hover="glow"
      accent={active || scenario.isPrimary}
      onClick={() => onSelect(scenario.scenarioId)}
      className="capital-stack-scenario-card"
      sx={{
        display: 'flex',
        flexDirection: 'column',
        textAlign: 'left',
        width: '100%',
        height: '100%',
        minHeight: 'var(--ob-size-finance-scenario-card-min)',
        p: 'var(--ob-space-150)',
        cursor: 'pointer',
        // Active state neon glow
        ...(active && {
          borderColor: 'var(--ob-color-neon-cyan)',
          boxShadow: 'var(--ob-glow-neon-cyan)',
        }),
        '&:focus-visible': {
          outline: '2px solid var(--ob-color-neon-cyan)',
          outlineOffset: 2,
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
                color: 'var(--ob-color-neon-cyan)',
                textShadow: 'var(--ob-glow-neon-text)',
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
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--ob-space-050)',
          }}
        >
          {onMarkPrimary ? (
            <Tooltip
              title={
                !canManage
                  ? t('finance.scenarios.actions.unavailableOffline', {
                      defaultValue: 'Unavailable offline',
                    })
                  : scenario.isPrimary
                    ? t('finance.scenarios.actions.primary', {
                        defaultValue: 'Primary scenario',
                      })
                    : t('finance.scenarios.actions.makePrimary', {
                        defaultValue: 'Make primary',
                      })
              }
            >
              <span>
                <IconButton
                  size="small"
                  onClick={(event) => {
                    event.stopPropagation()
                    if (!canManage || scenario.isPrimary || !onMarkPrimary)
                      return
                    onMarkPrimary(scenario.scenarioId)
                  }}
                  disabled={
                    !canManage ||
                    scenario.isPrimary ||
                    makingPrimary ||
                    deleting
                  }
                  aria-label={
                    scenario.isPrimary
                      ? t('finance.scenarios.actions.primary', {
                          defaultValue: 'Primary scenario',
                        })
                      : t('finance.scenarios.actions.makePrimary', {
                          defaultValue: 'Make primary',
                        })
                  }
                  sx={{
                    borderRadius: 'var(--ob-radius-xs)',
                    border: 'var(--ob-border-fine)',
                  }}
                >
                  {makingPrimary ? (
                    <CircularProgress size={14} />
                  ) : scenario.isPrimary ? (
                    <StarIcon fontSize="small" />
                  ) : (
                    <StarBorderIcon fontSize="small" />
                  )}
                </IconButton>
              </span>
            </Tooltip>
          ) : null}

          {onRequestDelete ? (
            <Tooltip
              title={
                !canManage
                  ? t('finance.scenarios.actions.unavailableOffline', {
                      defaultValue: 'Unavailable offline',
                    })
                  : t('finance.scenarios.actions.delete', {
                      defaultValue: 'Delete scenario',
                    })
              }
            >
              <span>
                <IconButton
                  size="small"
                  onClick={(event) => {
                    event.stopPropagation()
                    if (!canManage || !onRequestDelete) return
                    onRequestDelete(scenario.scenarioId, scenario.scenarioName)
                  }}
                  disabled={!canManage || deleting || makingPrimary}
                  aria-label={t('finance.scenarios.actions.delete', {
                    defaultValue: 'Delete scenario',
                  })}
                  sx={{
                    borderRadius: 'var(--ob-radius-xs)',
                    border: 'var(--ob-border-fine)',
                  }}
                >
                  {deleting ? (
                    <CircularProgress size={14} />
                  ) : (
                    <DeleteOutlineIcon fontSize="small" />
                  )}
                </IconButton>
              </span>
            </Tooltip>
          ) : null}

          {active ? <PulsingStatusDot status="live" size="sm" /> : null}
        </Box>
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
          <NeonText
            variant="body2"
            intensity="subtle"
            sx={{ fontFamily: 'var(--ob-font-family-mono)' }}
          >
            {escalatedCost !== null
              ? formatCurrencyShort(escalatedCost, currency)
              : t('common.fallback.dash')}
          </NeonText>
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
          <NeonText
            variant="body2"
            intensity={active ? 'medium' : 'subtle'}
            sx={{ fontFamily: 'var(--ob-font-family-mono)' }}
          >
            {npv !== null
              ? formatCurrencyShort(npv, currency)
              : t('common.fallback.dash')}
          </NeonText>
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
          <NeonText
            variant="body2"
            intensity="subtle"
            sx={{ fontFamily: 'var(--ob-font-family-mono)' }}
          >
            {irr !== null ? formatPercent(irr, 2) : t('common.fallback.dash')}
          </NeonText>
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
          <NeonText
            variant="body2"
            intensity="subtle"
            color="cyan"
            sx={{ fontFamily: 'var(--ob-font-family-mono)' }}
          >
            {dscr !== null ? formatNumber(dscr) : t('common.fallback.dash')}
          </NeonText>
        </Grid>
      </Grid>

      <Box sx={{ mt: 'auto', pt: 'var(--ob-space-125)' }}>
        {scenario.capitalStack ? (
          <CapitalStackMiniBar stack={scenario.capitalStack} />
        ) : (
          <Box
            aria-hidden
            sx={{
              height: 'var(--ob-space-050)',
              width: '100%',
              borderRadius: 'var(--ob-radius-sm)',
              opacity: 0,
            }}
          />
        )}
      </Box>
    </Card>
  )
}

interface CapitalStackScenarioGridProps {
  scenarios: FinanceScenarioSummary[]
  activeScenarioId: number | null
  onSelect: (scenarioId: number) => void
  onMarkPrimary?: (scenarioId: number) => void
  updatingScenarioId?: number | null
  onRequestDelete?: (scenarioId: number, scenarioName: string) => void
  deletingScenarioId?: number | null
}

export function CapitalStackScenarioGrid({
  scenarios,
  activeScenarioId,
  onSelect,
  onMarkPrimary,
  updatingScenarioId = null,
  onRequestDelete,
  deletingScenarioId = null,
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
          <Grid
            item
            xs={12}
            md={4}
            key={scenario.scenarioId}
            sx={{ display: 'flex' }}
          >
            <ScenarioCard
              scenario={scenario}
              active={scenario.scenarioId === activeScenarioId}
              onSelect={onSelect}
              onMarkPrimary={onMarkPrimary}
              updatingScenarioId={updatingScenarioId}
              onRequestDelete={onRequestDelete}
              deletingScenarioId={deletingScenarioId}
            />
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}

export default CapitalStackScenarioGrid
