/**
 * Multi-Scenario Comparison Section Component
 *
 * "Differential Analysis Matrix" - Tactical transformation of scenario comparison.
 *
 * Design Principles (AI Studio):
 * - Information Density vs Visual Noise: Strict visual hierarchy with typography tokens
 * - Responsive Resilience: Fluid grid with graceful degradation
 * - Functional Color Language: Cyan (Primary), Red (Critical), Indigo (AI Intelligence), Slate (Neutral)
 * - Progressive Disclosure: AI insights behind expandable buttons
 * - Summary Footer: Aggregate stats at bottom
 *
 * Phase 5 Transformation:
 * - "Asset Path Modules" with vertical glow-bar for focus indicator
 * - Scenario-coded system markers (PATH_RAW, PATH_ENBLOC, etc.)
 * - "Diligence Gauge" with 8 segmented blocks (machined edge style)
 * - "Intel Tapes" for Feasibility Signals with telemetry headers + signal strength
 * - "Data Export Console" at bottom for export actions
 * - "Matrix Summary" footer with tactical labels
 */

import { useMemo } from 'react'

import { ArrowForward as ArrowRight } from '@mui/icons-material'

import type {
  DevelopmentScenario,
  CapturedProperty,
} from '../../../../../api/siteAcquisition'
import { Button } from '../../../../../components/canonical/Button'
import { SegmentedGauge } from '../../../../../components/canonical/SegmentedGauge'
import { SystemMarker } from '../../../../../components/canonical/SystemMarker'
import { Link } from '../../../../../router'
import type {
  ScenarioComparisonDatum,
  FeasibilitySignalEntry,
  ScenarioOption,
} from '../../types'
import { formatCategoryName } from '../../utils/formatters'
import { FeasibilityIntelTape } from './FeasibilityIntelTape'
import {
  calculateSignalStrength,
  getScenarioMarker,
  getSignalId,
} from './telemetry'

// ============================================================================
// Types
// ============================================================================

interface SummaryStats {
  avgCondition: number | null
  totalRisks: number
  totalOpportunities: number
  scenariosTracked: number
}

export interface MultiScenarioComparisonSectionProps {
  // Data
  capturedProperty: CapturedProperty | null
  quickAnalysisScenariosCount: number
  scenarioComparisonData: ScenarioComparisonDatum[]
  feasibilitySignals: FeasibilitySignalEntry[]
  comparisonScenariosCount: number
  activeScenario: 'all' | DevelopmentScenario
  scenarioLookup: Map<DevelopmentScenario, ScenarioOption>
  propertyId: string | null

  // Export state
  isExportingReport: boolean
  reportExportMessage: string | null

  // Callbacks
  setActiveScenario: (scenario: 'all' | DevelopmentScenario) => void
  handleReportExport: (format: 'json' | 'pdf') => void
  formatRecordedTimestamp: (timestamp: string | null | undefined) => string
}

// ============================================================================
// Component
// ============================================================================

export function MultiScenarioComparisonSection({
  capturedProperty,
  quickAnalysisScenariosCount,
  scenarioComparisonData,
  feasibilitySignals,
  comparisonScenariosCount,
  activeScenario,
  scenarioLookup,
  propertyId,
  isExportingReport,
  reportExportMessage,
  setActiveScenario,
  handleReportExport,
  formatRecordedTimestamp,
}: MultiScenarioComparisonSectionProps) {
  // Calculate summary stats for footer (AI Studio: Summary Footer pattern)
  const summaryStats = useMemo((): SummaryStats => {
    const scenarioData = scenarioComparisonData.filter(
      (row) => row.key !== 'all',
    )
    const conditionScores = scenarioData
      .map((row) => row.conditionScore)
      .filter((score): score is number => score !== null)
    const avgCondition =
      conditionScores.length > 0
        ? Math.round(
            conditionScores.reduce((a, b) => a + b, 0) / conditionScores.length,
          )
        : null

    const totalRisks = feasibilitySignals.reduce(
      (sum, entry) => sum + entry.risks.length,
      0,
    )
    const totalOpportunities = feasibilitySignals.reduce(
      (sum, entry) => sum + entry.opportunities.length,
      0,
    )

    return {
      avgCondition,
      totalRisks,
      totalOpportunities,
      scenariosTracked: scenarioData.length,
    }
  }, [scenarioComparisonData, feasibilitySignals])

  const quickAnalysisTimestamp = useMemo(() => {
    if (!capturedProperty) {
      return null
    }
    return formatRecordedTimestamp(capturedProperty.quickAnalysis?.generatedAt)
  }, [capturedProperty, formatRecordedTimestamp])

  return (
    <section className="multi-scenario">
      {/* Header on background - Content vs Context pattern */}
      <h2 className="multi-scenario__title">Multi-Scenario Comparison</h2>
      {/* Content - direct children (Flat Section Pattern) */}
      {!capturedProperty ? (
        <div className="site-acquisition__empty-state site-acquisition__empty-state--prominent">
          <div className="multi-scenario__empty-icon">📊</div>
          <p className="multi-scenario__empty-title">
            Capture a property to review scenario economics and development
            posture
          </p>
          <p className="multi-scenario__empty-subtitle">
            Financial and planning metrics for each developer scenario appear
            here.
          </p>
        </div>
      ) : quickAnalysisScenariosCount === 0 ? (
        <div className="site-acquisition__empty-state">
          <p>
            Quick analysis metrics unavailable for this capture. Try
            regenerating the scenarios.
          </p>
        </div>
      ) : (
        <>
          {/* Asset Path Modules - Differential Analysis Matrix */}
          <div className="multi-scenario__path-grid">
            {scenarioComparisonData
              .filter((row) => row.key !== 'all') // Skip aggregate row for path modules
              .map((row) => {
                const isActive = activeScenario === row.key
                const progressPercent = row.checklistPercent ?? 0

                // Extract revenue from quickMetrics or use placeholder
                const revenueMetric = row.quickMetrics.find(
                  (m) =>
                    m.label.toLowerCase().includes('revenue') ||
                    m.label.toLowerCase().includes('rev'),
                )
                const revenueDisplay = revenueMetric?.value ?? '—'

                // Risk profile from riskLevel
                const riskDisplay = row.riskLevel
                  ? row.riskLevel.toUpperCase()
                  : '—'

                return (
                  <article
                    key={row.key}
                    className={`multi-scenario__path-module ${isActive ? 'multi-scenario__path-module--focus' : ''}`}
                  >
                    {/* Vertical Glow-Bar (focus indicator) */}
                    <div className="multi-scenario__path-glow-bar" />

                    {/* Module Content */}
                    <div className="multi-scenario__path-content">
                      {/* Header: System Marker */}
                      <div className="multi-scenario__path-header">
                        <SystemMarker active={isActive}>
                          {getScenarioMarker(row.key)}
                        </SystemMarker>
                        <div className="multi-scenario__path-timestamp">
                          <span className="multi-scenario__path-timestamp-label">
                            RECORDED
                          </span>
                          <span className="multi-scenario__path-timestamp-value">
                            {row.recordedAt
                              ? formatRecordedTimestamp(row.recordedAt)
                              : '—'}
                          </span>
                        </div>
                      </div>

                      {/* Metrics Grid: Yield + Risk Vector */}
                      <div className="multi-scenario__path-metrics">
                        <div className="multi-scenario__path-metric">
                          <span className="multi-scenario__path-metric-label">
                            EST. YIELD
                          </span>
                          <span className="multi-scenario__path-metric-value multi-scenario__path-metric-value--cyan">
                            {revenueDisplay}
                          </span>
                        </div>
                        <div className="multi-scenario__path-metric">
                          <span className="multi-scenario__path-metric-label">
                            RISK VECTOR
                          </span>
                          <span className="multi-scenario__path-metric-value">
                            {riskDisplay}
                          </span>
                        </div>
                      </div>

                      {/* Diligence Gauge - Segmented */}
                      <SegmentedGauge
                        label="DILIGENCE GAUGE"
                        value={progressPercent}
                        valueLabel={`${progressPercent}%`}
                        segments={8}
                      />

                      {/* Enter Matrix CTA */}
                      <button
                        type="button"
                        onClick={() =>
                          setActiveScenario(row.key as DevelopmentScenario)
                        }
                        className="multi-scenario__path-cta"
                      >
                        {isActive ? 'VIEWING MATRIX' : 'ENTER MATRIX'}
                        <ArrowRight
                          sx={{
                            width: 'var(--ob-space-100)',
                            height: 'var(--ob-space-100)',
                            ml: 'var(--ob-space-050)',
                          }}
                        />
                      </button>
                    </div>
                  </article>
                )
              })}
          </div>

          {/* Feasibility Highlights - Header on background, surfaces below */}
          <div className="multi-scenario__feasibility">
            <div className="multi-scenario__intel-feed-header">
              <span className="multi-scenario__intel-feed-label">
                FEASIBILITY_HIGHLIGHTS
              </span>
              {propertyId && (
                <Link
                  to={`/app/asset-feasibility?propertyId=${encodeURIComponent(propertyId)}`}
                  className="multi-scenario__full-feasibility-link"
                >
                  <Button variant="primary" size="sm">
                    FULL FEASIBILITY →
                  </Button>
                </Link>
              )}
            </div>

            {/* Summary stats moved above intel feed */}
            <div className="multi-scenario__matrix-summary">
              <div className="multi-scenario__matrix-stats">
                <div className="multi-scenario__matrix-stat">
                  <span className="multi-scenario__matrix-value">
                    {summaryStats.scenariosTracked}
                  </span>
                  <span className="multi-scenario__matrix-label">
                    PATHS_TRACKED
                  </span>
                </div>
                <div className="multi-scenario__matrix-stat">
                  <span className="multi-scenario__matrix-value">
                    {summaryStats.avgCondition !== null
                      ? `${summaryStats.avgCondition}/100`
                      : '—'}
                  </span>
                  <span className="multi-scenario__matrix-label">
                    AVG_CONDITION
                  </span>
                </div>
                <div className="multi-scenario__matrix-stat multi-scenario__matrix-stat--opportunity">
                  <span className="multi-scenario__matrix-value">
                    {summaryStats.totalOpportunities}
                  </span>
                  <span className="multi-scenario__matrix-label">
                    OPPORTUNITIES
                  </span>
                </div>
                <div className="multi-scenario__matrix-stat multi-scenario__matrix-stat--risk">
                  <span className="multi-scenario__matrix-value">
                    {summaryStats.totalRisks}
                  </span>
                  <span className="multi-scenario__matrix-label">
                    RISKS_FLAGGED
                  </span>
                </div>
              </div>
            </div>

            <div className="multi-scenario__intel-feed">
              <div className="multi-scenario__intel-feed-subheader">
                <span className="multi-scenario__intel-feed-subtitle">
                  DETAILED_INSIGHTS ({feasibilitySignals.length})
                </span>
                <div className="multi-scenario__intel-feed-actions">
                  {reportExportMessage && (
                    <span className="multi-scenario__matrix-status">
                      {reportExportMessage}
                    </span>
                  )}
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleReportExport('json')}
                    disabled={isExportingReport}
                  >
                    {isExportingReport ? 'PREPARING…' : 'JSON'}
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleReportExport('pdf')}
                    disabled={isExportingReport}
                  >
                    {isExportingReport ? 'PREPARING…' : 'PDF'}
                  </Button>
                </div>
              </div>

              {feasibilitySignals.length > 0 ? (
                feasibilitySignals.map((entry) => {
                  const signalStrength = calculateSignalStrength(
                    entry.opportunities.length,
                    entry.risks.length,
                  )
                  const signalId = getSignalId(entry.scenario)

                  return (
                    <FeasibilityIntelTape
                      key={entry.scenario}
                      signalStrength={signalStrength}
                      signalId={signalId}
                      pathLabel={entry.label}
                      timestamp={quickAnalysisTimestamp ?? '—'}
                      opportunities={entry.opportunities}
                      risks={entry.risks}
                    />
                  )
                })
              ) : (
                <p className="multi-scenario__intel-feed-empty">
                  No automated feasibility highlights available yet.
                </p>
              )}
            </div>
          </div>

          {/* Path Focus Notice */}
          {activeScenario !== 'all' && comparisonScenariosCount > 0 && (
            <div className="multi-scenario__focus-notice">
              <strong>PATH FOCUS:</strong> Viewing{' '}
              {getScenarioMarker(activeScenario)} (
              {scenarioLookup.get(activeScenario)?.label ??
                formatCategoryName(activeScenario)}
              ). Switch back to "All scenarios" to compare paths side-by-side.
            </div>
          )}
        </>
      )}
    </section>
  )
}
