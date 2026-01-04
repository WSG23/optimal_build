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
import { Link } from '../../../../../router'
import type {
  ScenarioComparisonDatum,
  FeasibilitySignalEntry,
  ScenarioOption,
} from '../../types'
import { formatCategoryName } from '../../utils/formatters'

// ============================================================================
// Constants - Scenario-Coded System Markers
// ============================================================================

const SCENARIO_MARKERS: Record<string, string> = {
  raw_land: 'PATH_GROUND-UP',
  en_bloc: 'PATH_ENBLOC',
  condo_redevelopment: 'PATH_CONDO',
  mixed_use: 'PATH_MIXED',
  residential: 'PATH_RESI',
  commercial: 'PATH_COMM',
  industrial: 'PATH_INDUS',
  hospitality: 'PATH_HOSP',
  retail: 'PATH_RETAIL',
  office: 'PATH_OFFICE',
  all: 'PATH_ALL',
}

/**
 * Get scenario-coded system marker for display
 */
function getScenarioMarker(scenario: string): string {
  return (
    SCENARIO_MARKERS[scenario] ??
    `PATH_${scenario.toUpperCase().replace(/_/g, '')}`
  )
}

/**
 * Get signal ID for Intel Tape header
 */
function getSignalId(scenario: string): string {
  const marker = SCENARIO_MARKERS[scenario]
  if (marker) {
    return `FSG-${marker.replace('PATH_', '')}`
  }
  return `FSG-${scenario.toUpperCase().replace(/_/g, '').slice(0, 6)}`
}

/**
 * Calculate signal strength based on count of opportunities + risks (max 10)
 */
function calculateSignalStrength(opportunities: number, risks: number): number {
  return Math.min(opportunities + risks, 10)
}

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
  formatRecordedTimestamp: _formatRecordedTimestamp,
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
                const activeSegments = Math.round((progressPercent / 100) * 8)

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
                        <span className="multi-scenario__path-marker">
                          {getScenarioMarker(row.key)}
                        </span>
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
                      <div className="multi-scenario__diligence-gauge">
                        <div className="multi-scenario__diligence-gauge-header">
                          <span className="multi-scenario__diligence-gauge-label">
                            DILIGENCE GAUGE
                          </span>
                          <span className="multi-scenario__diligence-gauge-value">
                            {progressPercent}%
                          </span>
                        </div>
                        <div className="multi-scenario__diligence-gauge-segments">
                          {[...Array(8)].map((_, i) => (
                            <div
                              key={i}
                              className={`multi-scenario__diligence-gauge-segment ${
                                i < activeSegments
                                  ? 'multi-scenario__diligence-gauge-segment--active'
                                  : ''
                              }`}
                            />
                          ))}
                        </div>
                      </div>

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
                            width: 16,
                            height: 16,
                            ml: 'var(--ob-space-050)',
                          }}
                        />
                      </button>
                    </div>
                  </article>
                )
              })}
          </div>

          {/* Feasibility Highlights - Flat structure (no nested card wrapper) */}
          {feasibilitySignals.length > 0 && (
            <div className="multi-scenario__intel-feed">
              <div className="multi-scenario__intel-feed-header">
                <span className="multi-scenario__intel-feed-label">
                  FEASIBILITY_HIGHLIGHTS
                </span>
                {propertyId && (
                  <Link
                    to={`/app/asset-feasibility?propertyId=${encodeURIComponent(propertyId)}`}
                    style={{ textDecoration: 'none', marginLeft: 'auto' }}
                  >
                    <Button variant="primary" size="sm">
                      FEASIBILITY →
                    </Button>
                  </Link>
                )}
              </div>
              {/* Intel tapes are direct siblings of header (Flat Section Pattern) */}
              {feasibilitySignals.map((entry) => {
                const signalStrength = calculateSignalStrength(
                  entry.opportunities.length,
                  entry.risks.length,
                )
                const signalId = getSignalId(entry.scenario)
                const timestamp = new Date()
                  .toISOString()
                  .slice(0, 19)
                  .replace('T', ' ')

                return (
                  <div
                    key={entry.scenario}
                    className="multi-scenario__intel-tape"
                  >
                    {/* Telemetry Header */}
                    <div className="multi-scenario__intel-tape-header">
                      <div className="multi-scenario__intel-tape-signal">
                        {/* Signal Strength Bar */}
                        <div className="multi-scenario__intel-tape-strength-bar">
                          {[...Array(10)].map((_, i) => (
                            <div
                              key={i}
                              className={`multi-scenario__intel-tape-strength-segment ${
                                i < signalStrength
                                  ? 'multi-scenario__intel-tape-strength-segment--active'
                                  : ''
                              }`}
                            />
                          ))}
                        </div>
                        <span className="multi-scenario__intel-tape-strength-value">
                          STRENGTH: {signalStrength}/10
                        </span>
                      </div>
                      <div className="multi-scenario__intel-tape-meta">
                        <span className="multi-scenario__intel-tape-id">
                          SIGNAL_ID: {signalId}
                        </span>
                        <span className="multi-scenario__intel-tape-path">
                          PATH: {entry.label}
                        </span>
                        <span className="multi-scenario__intel-tape-ts">
                          TS: {timestamp}
                        </span>
                      </div>
                    </div>
                    <div className="multi-scenario__intel-tape-divider" />
                    {/* Signal Content */}
                    {entry.opportunities.length > 0 && (
                      <div className="multi-scenario__intel-tape-section">
                        <span className="multi-scenario__intel-tape-type multi-scenario__intel-tape-type--opportunity">
                          ● OPPORTUNITY
                        </span>
                        <ul className="multi-scenario__intel-tape-list">
                          {entry.opportunities.map((message, idx) => (
                            <li key={message}>
                              <span className="multi-scenario__intel-tape-tree">
                                {idx === entry.opportunities.length - 1
                                  ? '└─'
                                  : '├─'}
                              </span>
                              {message}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {entry.risks.length > 0 && (
                      <div className="multi-scenario__intel-tape-section">
                        <span className="multi-scenario__intel-tape-type multi-scenario__intel-tape-type--risk">
                          ● RISK
                        </span>
                        <ul className="multi-scenario__intel-tape-list">
                          {entry.risks.map((message, idx) => (
                            <li key={message}>
                              <span className="multi-scenario__intel-tape-tree">
                                {idx === entry.risks.length - 1 ? '└─' : '├─'}
                              </span>
                              {message}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {entry.opportunities.length === 0 &&
                      entry.risks.length === 0 && (
                        <p className="multi-scenario__intel-tape-empty">
                          No automated guidance produced. Review the scenario
                          notes for additional context.
                        </p>
                      )}
                  </div>
                )
              })}
            </div>
          )}

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

          {/* Matrix Summary Footer - Stats + Export Actions consolidated */}
          <footer className="multi-scenario__matrix-summary">
            {/* Stats Row */}
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

            {/* Export Actions Row */}
            {capturedProperty && (
              <div className="multi-scenario__matrix-actions">
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
            )}
          </footer>
        </>
      )}
    </section>
  )
}
