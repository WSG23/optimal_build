/**
 * FinanceCapitalStack - Capital stack visualization with Gemini-matching layout
 *
 * Layout (matching Gemini design):
 * 1. Page header with title/subtitle
 * 2. Split layout: Chart (2/3) | Scenario Cards (1/3)
 * 3. Scenario tabs below chart area
 * 4. Stats cards (4-column metrics grid)
 * 5. Enhanced tranche/facility table
 *
 * Follows UI_STANDARDS.md for design tokens.
 */

import { useMemo, useState } from 'react'

import { Box, Grid, Typography } from '@mui/material'

import type { FinanceScenarioSummary } from '../../../api/finance'
import { useTranslation } from '../../../i18n'
import { GlassCard } from '../../../components/canonical/GlassCard'
import { CapitalStackChart } from './CapitalStackChart'
import { CapitalStackHeader } from './CapitalStackHeader'
import { CapitalStackScenarioCards } from './CapitalStackScenarioCards'
import { CapitalStackScenarioTabs } from './CapitalStackScenarioTabs'
import { CapitalStackFacilityTable } from './CapitalStackFacilityTable'
import { FinanceMetricsGrid } from './FinanceMetricsGrid'

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

  const activeScenario = useMemo(() => {
    if (activeScenarioId === null) return null
    return validScenarios.find((s) => s.scenarioId === activeScenarioId) ?? null
  }, [validScenarios, activeScenarioId])

  // Show empty state with helpful message if no capital stack data
  if (validScenarios.length === 0) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          py: 'var(--ob-space-400)',
          textAlign: 'center',
        }}
      >
        <Typography
          variant="h5"
          sx={{
            fontWeight: 600,
            color: 'text.primary',
            mb: 'var(--ob-space-100)',
          }}
        >
          {t('finance.capitalStack.empty.title', {
            defaultValue: 'No Capital Stack Data',
          })}
        </Typography>
        <Typography
          sx={{
            color: 'text.secondary',
            maxWidth: 400,
          }}
        >
          {t('finance.capitalStack.empty.description', {
            defaultValue:
              'Run a feasibility scenario to generate capital stack analysis. The chart and metrics will appear here once data is available.',
          })}
        </Typography>
      </Box>
    )
  }

  const handleScenarioSelect = (scenarioId: number) => {
    setActiveScenarioId(scenarioId)
  }

  const handlePreview = (scenario: FinanceScenarioSummary) => {
    // TODO: Implement preview functionality
    console.log('Preview scenario:', scenario.scenarioId)
  }

  return (
    <section className="finance-capital">
      {/* Page Header */}
      <CapitalStackHeader />

      {/* Split Layout: Chart + Scenario Cards */}
      <Grid
        container
        spacing="var(--ob-space-150)"
        sx={{ mb: 'var(--ob-space-150)' }}
      >
        {/* Chart (2/3 width on large screens) */}
        <Grid item xs={12} lg={8}>
          <GlassCard sx={{ p: 'var(--ob-space-100)' }}>
            <CapitalStackChart scenarios={validScenarios} />
          </GlassCard>
        </Grid>

        {/* Scenario Cards (1/3 width on large screens) */}
        <Grid item xs={12} lg={4}>
          <CapitalStackScenarioCards
            scenarios={validScenarios}
            activeId={activeScenarioId}
            onSelect={handleScenarioSelect}
            onPreview={handlePreview}
          />
        </Grid>
      </Grid>

      {/* Scenario Tabs */}
      <CapitalStackScenarioTabs
        scenarios={validScenarios}
        activeId={activeScenarioId}
        onSelect={handleScenarioSelect}
      />

      {/* Stats Cards */}
      <FinanceMetricsGrid scenario={activeScenario} />

      {/* Tranche/Facility Table */}
      <CapitalStackFacilityTable scenario={activeScenario} />
    </section>
  )
}

export default FinanceCapitalStack
