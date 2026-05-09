/**
 * FinanceCapitalStack
 *
 * Renders the Capital Stack "detail" portion of the Finance workspace:
 * - Scenario selection grid
 * - Overview metrics
 * - Facility table + comparison chart + insight box
 *
 * Note: The FinanceWorkspace owns the page-level header and top tabs.
 */

import { Suspense, lazy, useEffect, useMemo, useState } from 'react'

import { Box, Typography } from '@mui/material'

import type { FinanceScenarioSummary } from '../../../api/finance'
import { useTranslation } from '../../../i18n'
import { Card } from '../../../components/canonical/Card'
import { CapitalStackFacilityTable } from './CapitalStackFacilityTable'
import { CapitalStackScenarioGrid } from './CapitalStackScenarioGrid'
import { CapitalStackInsightBox } from './CapitalStackInsightBox'

const CapitalStackChart = lazy(() =>
  import('./CapitalStackChart').then((module) => ({
    default: module.CapitalStackChart,
  })),
)

function CapitalStackChartFallback() {
  return (
    <Box
      sx={{
        height: 'var(--ob-max-height-panel)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        borderRadius: 'var(--ob-radius-sm)',
        border: '1px solid var(--ob-color-border-subtle)',
        bgcolor: 'var(--ob-color-surface-subtle)',
      }}
    >
      <Typography color="text.secondary">Loading comparison chart…</Typography>
    </Box>
  )
}

interface FinanceCapitalStackProps {
  scenarios: FinanceScenarioSummary[]
  onMarkPrimary?: (scenarioId: number) => void
  updatingScenarioId?: number | null
  onRequestDelete?: (scenarioId: number, scenarioName: string) => void
  deletingScenarioId?: number | null
  onActiveScenarioChange?: (scenario: FinanceScenarioSummary | null) => void
}

export function FinanceCapitalStack({
  scenarios,
  onMarkPrimary,
  updatingScenarioId = null,
  onRequestDelete,
  deletingScenarioId = null,
  onActiveScenarioChange,
}: FinanceCapitalStackProps) {
  const { t } = useTranslation()

  const scenarioList = useMemo(() => {
    const ordered = [...scenarios]
    ordered.sort((a, b) => {
      if (a.isPrimary !== b.isPrimary) {
        return a.isPrimary ? -1 : 1
      }
      return a.scenarioId - b.scenarioId
    })
    return ordered
  }, [scenarios])

  const scenariosWithCapitalStack = useMemo(
    () => scenarioList.filter((scenario) => Boolean(scenario.capitalStack)),
    [scenarioList],
  )

  // Active scenario selection
  const [activeScenarioId, setActiveScenarioId] = useState<number | null>(
    () => {
      // Default to primary scenario or first one
      const primary = scenarioList.find((s) => s.isPrimary)
      return primary?.scenarioId ?? scenarioList[0]?.scenarioId ?? null
    },
  )

  useEffect(() => {
    if (scenarioList.length === 0) {
      if (activeScenarioId !== null) {
        setActiveScenarioId(null)
      }
      return
    }
    if (
      activeScenarioId !== null &&
      scenarioList.some((s) => s.scenarioId === activeScenarioId)
    ) {
      return
    }
    const primary = scenarioList.find((s) => s.isPrimary)
    setActiveScenarioId(primary?.scenarioId ?? scenarioList[0].scenarioId)
  }, [activeScenarioId, scenarioList])

  const activeScenario = useMemo(() => {
    if (activeScenarioId === null) return null
    return scenarioList.find((s) => s.scenarioId === activeScenarioId) ?? null
  }, [scenarioList, activeScenarioId])

  // Notify parent when the viewed scenario changes
  useEffect(() => {
    onActiveScenarioChange?.(activeScenario)
  }, [activeScenario, onActiveScenarioChange])

  const handleScenarioSelect = (scenarioId: number) => {
    setActiveScenarioId(scenarioId)
  }

  if (scenarioList.length === 0) {
    return (
      <Card sx={{ p: 'var(--ob-space-200)' }}>
        <Typography
          variant="h6"
          sx={{ fontWeight: 'var(--ob-font-weight-semibold)' }}
        >
          {t('finance.capitalStack.empty.title', {
            defaultValue: 'Capital stack details',
          })}
        </Typography>
        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
          {t('finance.capitalStack.empty.subtitle', {
            defaultValue:
              'Run a feasibility scenario to see the capital stack breakdown.',
          })}
        </Typography>
      </Card>
    )
  }

  return (
    <section className="finance-capital">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-150)',
        }}
      >
        <CapitalStackScenarioGrid
          scenarios={scenarioList}
          activeScenarioId={activeScenarioId}
          onSelect={handleScenarioSelect}
          onMarkPrimary={onMarkPrimary}
          updatingScenarioId={updatingScenarioId}
          onRequestDelete={onRequestDelete}
          deletingScenarioId={deletingScenarioId}
        />

        <Typography
          variant="body2"
          sx={{ color: 'text.secondary', fontSize: 'var(--ob-font-size-sm)' }}
        >
          {t('finance.capitalStack.overview.showingFor', {
            defaultValue: 'Visualizing data for',
          })}{' '}
          <Box
            component="span"
            sx={{
              fontWeight: 'var(--ob-font-weight-bold)',
              color: 'text.primary',
            }}
          >
            {activeScenario?.scenarioName}
          </Box>
        </Typography>

        <Box
          sx={{
            display: 'grid',
            // Ensure the facility table can shrink (and scroll internally) so the
            // comparison panel is always visible.
            gridTemplateColumns: {
              xs: '1fr',
              lg: 'minmax(0, 2fr) minmax(0, 1fr)',
            },
            gap: 'var(--ob-space-150)',
            alignItems: 'start',
            '& > *': { minWidth: 0 },
          }}
        >
          <Box sx={{ minWidth: 0 }}>
            <CapitalStackFacilityTable scenario={activeScenario} />
          </Box>
          <Box sx={{ minWidth: 0 }}>
            <Card sx={{ p: 'var(--ob-space-100)', height: '100%' }}>
              <Typography
                variant="h6"
                sx={{
                  mb: 'var(--ob-space-100)',
                  fontWeight: 'var(--ob-font-weight-semibold)',
                }}
              >
                {t('finance.capitalStack.comparison.title', {
                  defaultValue: 'Scenario Comparison',
                })}
              </Typography>
              <Suspense fallback={<CapitalStackChartFallback />}>
                <CapitalStackChart scenarios={scenariosWithCapitalStack} />
              </Suspense>

              <Box sx={{ mt: 'var(--ob-space-100)' }}>
                <CapitalStackInsightBox
                  scenarios={scenariosWithCapitalStack}
                  activeScenarioId={activeScenarioId}
                />
              </Box>
            </Card>
          </Box>
        </Box>
      </Box>
    </section>
  )
}

export default FinanceCapitalStack
