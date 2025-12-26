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

import { useEffect, useMemo, useState } from 'react'

import { Box, Typography } from '@mui/material'

import type { FinanceScenarioSummary } from '../../../api/finance'
import { useTranslation } from '../../../i18n'
import { GlassCard } from '../../../components/canonical/GlassCard'
import { CapitalStackChart } from './CapitalStackChart'
import { CapitalStackFacilityTable } from './CapitalStackFacilityTable'
import { FinanceMetricsGrid } from './FinanceMetricsGrid'
import { CapitalStackScenarioGrid } from './CapitalStackScenarioGrid'
import { CapitalStackInsightBox } from './CapitalStackInsightBox'

interface FinanceCapitalStackProps {
  scenarios: FinanceScenarioSummary[]
  onMarkPrimary?: (scenarioId: number) => void
  updatingScenarioId?: number | null
  onRequestDelete?: (scenarioId: number, scenarioName: string) => void
  deletingScenarioId?: number | null
}

export function FinanceCapitalStack({
  scenarios,
  onMarkPrimary,
  updatingScenarioId = null,
  onRequestDelete,
  deletingScenarioId = null,
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

  const handleScenarioSelect = (scenarioId: number) => {
    setActiveScenarioId(scenarioId)
  }

  if (scenarioList.length === 0) {
    return (
      <GlassCard sx={{ p: 'var(--ob-space-200)' }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
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
      </GlassCard>
    )
  }

  return (
    <section className="finance-capital">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-200)',
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

        <Box>
          <Typography
            variant="h5"
            sx={{ mb: 'var(--ob-space-100)', fontWeight: 600 }}
          >
            {t('finance.capitalStack.title')}
          </Typography>
          <Typography
            variant="body2"
            sx={{ mb: 'var(--ob-space-100)', color: 'text.secondary' }}
          >
            {t('finance.capitalStack.overview.showingFor', {
              defaultValue: 'Visualizing data for',
            })}{' '}
            <Box
              component="span"
              sx={{ fontWeight: 700, color: 'text.primary' }}
            >
              {activeScenario?.scenarioName}
            </Box>
            .
          </Typography>
          <FinanceMetricsGrid scenario={activeScenario} />
        </Box>

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
            <GlassCard sx={{ p: 'var(--ob-space-100)', height: '100%' }}>
              <Typography
                variant="h6"
                sx={{ mb: 'var(--ob-space-100)', fontWeight: 600 }}
              >
                {t('finance.capitalStack.comparison.title', {
                  defaultValue: 'Scenario Comparison',
                })}
              </Typography>
              <CapitalStackChart scenarios={scenariosWithCapitalStack} />

              <Box sx={{ mt: 'var(--ob-space-100)' }}>
                <CapitalStackInsightBox
                  scenarios={scenariosWithCapitalStack}
                  activeScenarioId={activeScenarioId}
                />
              </Box>
            </GlassCard>
          </Box>
        </Box>
      </Box>
    </section>
  )
}

export default FinanceCapitalStack
