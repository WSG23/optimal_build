/**
 * FinanceDrawdownSchedule - Complete drawdown schedule view
 *
 * Features (matching Gemini design):
 * - Page header with Export Report / Save Scenario buttons
 * - Scenario selector tabs
 * - Stats cards (3 columns) with icons
 * - Split layout: Details table (left) | Chart + Analysis box (right)
 * - Chart/Table view toggle for the chart section
 *
 * Follows UI_STANDARDS.md for design tokens and canonical components.
 */

import { Suspense, lazy, useMemo, useState } from 'react'

import { Box, Grid, ToggleButton, ToggleButtonGroup } from '@mui/material'
import BarChartIcon from '@mui/icons-material/BarChart'
import TableChartIcon from '@mui/icons-material/TableChart'

import type { FinanceScenarioSummary } from '../../../api/finance'
import { useTranslation } from '../../../i18n'
import { DrawdownHeader } from './DrawdownHeader'
import { DrawdownStatsCards } from './DrawdownStatsCards'
import { DrawdownDetailsPanel } from './DrawdownDetailsPanel'
import { DrawdownInsightBox } from './DrawdownInsightBox'
import { ScenarioSelector } from './ScenarioSelector'
import { Card } from '../../../components/canonical/Card'

const DrawdownChart = lazy(() =>
  import('./DrawdownChart').then((module) => ({
    default: module.DrawdownChart,
  })),
)

function DrawdownChartFallback() {
  return (
    <Card
      sx={{
        height: 'var(--ob-max-height-panel)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <Box color="text.secondary">Loading funding chart…</Box>
    </Card>
  )
}

interface FinanceDrawdownScheduleProps {
  scenarios: FinanceScenarioSummary[]
  maxRows?: number
}

type ChartViewMode = 'chart' | 'table'

export function FinanceDrawdownSchedule({
  scenarios,
}: FinanceDrawdownScheduleProps) {
  const { t } = useTranslation()

  // Filter scenarios that have drawdown data
  const validScenarios = useMemo(
    () => scenarios.filter((s) => Boolean(s.drawdownSchedule)),
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

  // Chart view mode toggle
  const [chartViewMode, setChartViewMode] = useState<ChartViewMode>('chart')

  const activeScenario = useMemo(() => {
    if (activeScenarioId === null) return null
    return validScenarios.find((s) => s.scenarioId === activeScenarioId) ?? null
  }, [validScenarios, activeScenarioId])

  if (validScenarios.length === 0) {
    return null
  }

  const handleScenarioSelect = (scenarioId: number) => {
    setActiveScenarioId(scenarioId)
  }

  const handleChartViewChange = (
    _: React.MouseEvent<HTMLElement>,
    newView: ChartViewMode | null,
  ) => {
    if (newView !== null) {
      setChartViewMode(newView)
    }
  }

  const handleExportReport = () => {
    // TODO: Implement export report functionality
  }

  const handleSaveScenario = () => {
    // TODO: Implement save scenario functionality
  }

  const handleViewFullForecast = () => {
    // TODO: Navigate to full forecast view
  }

  return (
    <section className="finance-drawdown">
      {/* Page Header with Actions */}
      <DrawdownHeader
        onExportReport={handleExportReport}
        onSaveScenario={handleSaveScenario}
      />

      {/* Scenario Selector */}
      <ScenarioSelector
        scenarios={validScenarios}
        activeId={activeScenarioId}
        onSelect={handleScenarioSelect}
      />

      {/* Stats Cards - 3 columns */}
      <DrawdownStatsCards scenario={activeScenario} />

      {/* Split Layout: Table (left) | Chart + Analysis (right) */}
      <Grid container spacing="var(--ob-space-200)">
        {/* Left Column: Details Table */}
        <Grid item xs={12} xl={6}>
          <DrawdownDetailsPanel
            scenario={activeScenario}
            onViewFullForecast={handleViewFullForecast}
          />
        </Grid>

        {/* Right Column: Chart + Analysis */}
        <Grid item xs={12} xl={6}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {/* Chart/Table Toggle */}
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'flex-end',
                mb: 'var(--ob-space-100)',
              }}
            >
              <ToggleButtonGroup
                value={chartViewMode}
                exclusive
                onChange={handleChartViewChange}
                size="small"
                sx={{
                  '& .MuiToggleButton-root': {
                    borderRadius: 'var(--ob-radius-xs)',
                    px: 'var(--ob-space-075)',
                    py: 'var(--ob-space-025)',
                    fontSize: 'var(--ob-font-size-sm)',
                    textTransform: 'none',
                  },
                }}
              >
                <ToggleButton
                  value="chart"
                  aria-label={t('finance.charts.viewChart')}
                >
                  <BarChartIcon
                    fontSize="small"
                    sx={{ mr: 'var(--ob-space-025)' }}
                  />
                  {t('finance.charts.viewChart')}
                </ToggleButton>
                <ToggleButton
                  value="table"
                  aria-label={t('finance.charts.viewTable')}
                >
                  <TableChartIcon
                    fontSize="small"
                    sx={{ mr: 'var(--ob-space-025)' }}
                  />
                  {t('finance.charts.viewTable')}
                </ToggleButton>
              </ToggleButtonGroup>
            </Box>

            {/* Chart View */}
            {chartViewMode === 'chart' && activeScenario && (
              <Suspense fallback={<DrawdownChartFallback />}>
                <DrawdownChart scenarios={[activeScenario]} />
              </Suspense>
            )}

            {/* Table View - legacy table for the selected scenario */}
            {chartViewMode === 'table' && activeScenario && (
              <LegacyDrawdownTable scenario={activeScenario} />
            )}

            {/* Analysis Insight Box */}
            <DrawdownInsightBox scenario={activeScenario} />
          </Box>
        </Grid>
      </Grid>
    </section>
  )
}

/**
 * LegacyDrawdownTable - Simple table view for drawdown entries
 * Used in the table view toggle mode
 */
function LegacyDrawdownTable({
  scenario,
}: {
  scenario: FinanceScenarioSummary
}) {
  const { t, i18n } = useTranslation()
  const locale = i18n.language
  const fallback = t('common.fallback.dash')
  const currency = scenario.currency ?? 'SGD'

  const entries = scenario.drawdownSchedule?.entries ?? []

  function toNumber(value: string | undefined): number | null {
    if (typeof value !== 'string') return null
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }

  function formatCurrency(amount: string): string {
    const numeric = toNumber(amount)
    if (numeric === null) return fallback
    try {
      return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency,
        maximumFractionDigits: 0,
      }).format(numeric)
    } catch {
      return `${numeric.toLocaleString(locale)} ${currency}`
    }
  }

  return (
    <Card
      sx={{
        maxHeight: 'var(--ob-max-height-panel)',
        overflow: 'auto',
      }}
    >
      <div className="finance-drawdown__table-wrapper">
        <table className="finance-drawdown__table">
          <caption className="finance-drawdown__table-caption">
            {t('finance.drawdown.caption')}
          </caption>
          <thead>
            <tr>
              <th scope="col">{t('finance.drawdown.headers.period')}</th>
              <th scope="col">{t('finance.drawdown.headers.equity')}</th>
              <th scope="col">{t('finance.drawdown.headers.debt')}</th>
              <th scope="col">{t('finance.drawdown.headers.outstanding')}</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => (
              <tr key={entry.period}>
                <th scope="row">{entry.period}</th>
                <td>{formatCurrency(entry.equityDraw)}</td>
                <td>{formatCurrency(entry.debtDraw)}</td>
                <td>{formatCurrency(entry.outstandingDebt)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  )
}

export default FinanceDrawdownSchedule
