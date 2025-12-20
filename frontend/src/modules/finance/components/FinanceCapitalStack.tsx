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
}

export function FinanceCapitalStack({ scenarios }: FinanceCapitalStackProps) {
  const { t } = useTranslation()

  // Filter scenarios that have capital stack data
  const validScenarios = useMemo(
    () => scenarios.filter((s) => Boolean(s.capitalStack)),
    [scenarios],
  )

  // Active scenario selection
  const [activeScenarioId, setActiveScenarioId] = useState<number | null>(
    () => {
      // Default to primary scenario or first one
      const primary = validScenarios.find((s) => s.isPrimary)
      return primary?.scenarioId ?? validScenarios[0]?.scenarioId ?? null
    },
  )

  useEffect(() => {
    if (validScenarios.length === 0) {
      if (activeScenarioId !== null) {
        setActiveScenarioId(null)
      }
      return
    }
    if (
      activeScenarioId !== null &&
      validScenarios.some((s) => s.scenarioId === activeScenarioId)
    ) {
      return
    }
    const primary = validScenarios.find((s) => s.isPrimary)
    setActiveScenarioId(primary?.scenarioId ?? validScenarios[0].scenarioId)
  }, [activeScenarioId, validScenarios])

  const activeScenario = useMemo(() => {
    if (activeScenarioId === null) return null
    return validScenarios.find((s) => s.scenarioId === activeScenarioId) ?? null
  }, [validScenarios, activeScenarioId])

  const handleScenarioSelect = (scenarioId: number) => {
    setActiveScenarioId(scenarioId)
  }

  if (validScenarios.length === 0) {
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
          scenarios={validScenarios}
          activeScenarioId={activeScenarioId}
          onSelect={handleScenarioSelect}
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
            gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' },
            gap: 'var(--ob-space-150)',
          }}
        >
          <Box>
            <CapitalStackFacilityTable scenario={activeScenario} />
          </Box>
          <Box>
            <GlassCard sx={{ p: 'var(--ob-space-100)', height: '100%' }}>
              <Typography
                variant="h6"
                sx={{ mb: 'var(--ob-space-100)', fontWeight: 600 }}
              >
                {t('finance.capitalStack.comparison.title', {
                  defaultValue: 'Scenario Comparison',
                })}
              </Typography>
              <CapitalStackChart scenarios={validScenarios} />

              <Box sx={{ mt: 'var(--ob-space-100)' }}>
                <CapitalStackInsightBox
                  scenarios={validScenarios}
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
