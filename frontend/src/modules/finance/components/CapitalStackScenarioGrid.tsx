import { useMemo, useState } from 'react'

import {
  Box,
  CircularProgress,
  Grid,
  IconButton,
  InputBase,
  Tooltip,
  Typography,
} from '@mui/material'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline'
import SearchIcon from '@mui/icons-material/Search'
import StarIcon from '@mui/icons-material/Star'
import StarBorderIcon from '@mui/icons-material/StarBorder'

import type { FinanceScenarioSummary } from '../../../api/finance'
import { useTranslation } from '../../../i18n'
import { Card } from '../../../components/canonical/Card'
import { NeonText } from '../../../components/canonical/NeonText'
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

function formatDateTime(
  value: string | null | undefined,
  locale: string,
): string | null {
  if (!value) return null
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return null
  return new Intl.DateTimeFormat(locale, {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(date)
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
  const { t, i18n } = useTranslation()

  const currency = scenario.currency ?? 'SGD'
  const escalatedCost = toNumber(scenario.escalatedCost)
  const npv = getResultValue(scenario, 'NPV')
  const irr = getResultValue(scenario, 'IRR')
  const dscr = getLatestDscr(scenario)
  const lastUpdated = formatDateTime(scenario.updatedAt, i18n.language)

  const canManage = scenario.scenarioId > 0
  const makingPrimary = updatingScenarioId === scenario.scenarioId
  const deleting = deletingScenarioId === scenario.scenarioId

  return (
    <Card
      variant={active ? 'default' : 'default'}
      hover="lift"
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
          borderColor: 'var(--ob-color-brand-primary)',
        }),
        '&:focus-visible': {
          outline: '2px solid var(--ob-color-brand-primary)',
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
              fontWeight: 'var(--ob-font-weight-bold)',
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
                fontWeight: 'var(--ob-font-weight-bold)',
                letterSpacing: 'var(--ob-letter-spacing-wider)',
                color: 'var(--ob-color-brand-primary)',
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
          {lastUpdated && (
            <Typography
              sx={{
                mt: 'var(--ob-space-025)',
                fontSize: 'var(--ob-font-size-2xs)',
                color: 'text.disabled',
              }}
            >
              {t('finance.scenarios.lastUpdated', { defaultValue: 'Updated' })}:{' '}
              {lastUpdated}
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
                    // Gold color for primary scenario star
                    ...(scenario.isPrimary && {
                      color: 'var(--ob-gold-500, #C8A951)',
                      '&.Mui-disabled': {
                        color: 'var(--ob-gold-500, #C8A951)',
                      },
                    }),
                  }}
                >
                  {makingPrimary ? (
                    <CircularProgress size={14} />
                  ) : scenario.isPrimary ? (
                    <StarIcon
                      fontSize="small"
                      sx={{ color: 'var(--ob-gold-500, #C8A951)' }}
                    />
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

          {active && (
            <Box
              sx={{
                width: 6,
                height: 6,
                borderRadius: 'var(--ob-radius-xs)',
                bgcolor: 'var(--ob-color-brand-primary)',
                flexShrink: 0,
              }}
            />
          )}
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
  const [searchQuery, setSearchQuery] = useState('')
  const showSearch = scenarios.length > 4

  const filtered = useMemo(() => {
    if (!searchQuery.trim()) return scenarios
    const query = searchQuery.toLowerCase()
    return scenarios.filter(
      (s) =>
        s.scenarioName.toLowerCase().includes(query) ||
        (s.description && s.description.toLowerCase().includes(query)),
    )
  }, [scenarios, searchQuery])

  if (scenarios.length === 0) {
    return null
  }

  return (
    <Box sx={{ mb: 'var(--ob-space-150)' }}>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 'var(--ob-space-100)',
          mb: 'var(--ob-space-100)',
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'baseline',
            gap: 'var(--ob-space-075)',
          }}
        >
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-sm)',
              fontWeight: 'var(--ob-font-weight-bold)',
              color: 'text.primary',
            }}
          >
            {t('finance.scenarios.sectionTitle', {
              defaultValue: 'Scenarios',
            })}
          </Typography>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-xs)',
              color: 'text.secondary',
            }}
          >
            {scenarios.length}
          </Typography>
        </Box>

        {showSearch && (
          <Box
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              border: 1,
              borderColor: 'divider',
              borderRadius: 'var(--ob-radius-xs)',
              px: 'var(--ob-space-075)',
              py: 'var(--ob-space-025)',
              maxWidth: 220,
            }}
          >
            <SearchIcon
              fontSize="small"
              sx={{ color: 'text.disabled', mr: 'var(--ob-space-050)' }}
            />
            <InputBase
              placeholder="Filter scenarios..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              sx={{
                fontSize: 'var(--ob-font-size-sm)',
                '& input': { p: 0 },
              }}
            />
          </Box>
        )}
      </Box>

      {/* Horizontal scroll when 4+ scenarios to preserve vertical space */}
      <Box
        sx={{
          display: 'flex',
          gap: 'var(--ob-space-150)',
          overflowX: filtered.length >= 4 ? 'auto' : 'visible',
          flexWrap: filtered.length >= 4 ? 'nowrap' : 'wrap',
          pb: filtered.length >= 4 ? 'var(--ob-space-075)' : 0,
        }}
      >
        {filtered.map((scenario) => (
          <Box
            key={scenario.scenarioId}
            sx={{
              flex:
                filtered.length >= 4
                  ? '0 0 280px'
                  : {
                      xs: '1 1 100%',
                      md: '1 1 calc(33.333% - var(--ob-space-100))',
                    },
              minWidth: filtered.length >= 4 ? 280 : 0,
              display: 'flex',
            }}
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
          </Box>
        ))}
      </Box>

      {searchQuery && filtered.length === 0 && (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mt: 'var(--ob-space-100)', fontSize: 'var(--ob-font-size-sm)' }}
        >
          No scenarios match &ldquo;{searchQuery}&rdquo;
        </Typography>
      )}
    </Box>
  )
}

export default CapitalStackScenarioGrid
