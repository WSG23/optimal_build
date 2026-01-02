/**
 * Multi-Scenario Comparison Section Component
 *
 * Displays scenario comparison cards with condition ratings, checklist progress,
 * quick metrics, insights, and feasibility signals. Includes export functionality.
 *
 * Design Principles (AI Studio):
 * - Information Density vs Visual Noise: Strict visual hierarchy with typography tokens
 * - Responsive Resilience: Fluid grid with graceful degradation
 * - Functional Color Language: Cyan (Primary), Red (Critical), Indigo (AI Intelligence), Slate (Neutral)
 * - Progressive Disclosure: AI insights behind expandable buttons
 * - Summary Footer: Aggregate stats at bottom
 *
 * Updated: Workspace-style cards with simplified layout
 * - "SCENARIO PATH" label, title, Est. Revenue (cyan), Risk Profile
 * - Diligence Progress bar with percentage
 * - "Enter Workspace" CTA button
 * - Focus card has cyan border + badge
 */

import { useMemo } from 'react'
import { Link } from '../../../../../router'
import { ArrowForward as ArrowRight } from '@mui/icons-material'
import type {
  DevelopmentScenario,
  CapturedProperty,
} from '../../../../../api/siteAcquisition'
import type {
  ScenarioComparisonDatum,
  FeasibilitySignalEntry,
  ScenarioOption,
} from '../../types'
import { formatCategoryName } from '../../utils/formatters'

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
      {/* Content - seamless glass surface */}
      <div className="ob-seamless-panel ob-seamless-panel--glass multi-scenario__surface">
        {!capturedProperty ? (
          <div className="multi-scenario__empty-state multi-scenario__empty-state--prominent">
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
          <div className="multi-scenario__empty-state">
            <p>
              Quick analysis metrics unavailable for this capture. Try
              regenerating the scenarios.
            </p>
          </div>
        ) : (
          <div className="multi-scenario__content">
            {/* Workspace-Style Scenario Cards */}
            <div className="multi-scenario__workspace-grid">
              {scenarioComparisonData
                .filter((row) => row.key !== 'all') // Skip aggregate row for workspace cards
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
                    ? `${row.riskLevel.charAt(0).toUpperCase()}${row.riskLevel.slice(1)}`
                    : '—'

                  return (
                    <article
                      key={row.key}
                      className={`multi-scenario__workspace-card ${isActive ? 'multi-scenario__workspace-card--focus' : ''}`}
                    >
                      {/* Focus Badge */}
                      {isActive && (
                        <span className="multi-scenario__workspace-focus-badge">
                          Focus
                        </span>
                      )}

                      {/* Card Content */}
                      <div className="multi-scenario__workspace-content">
                        {/* Header: Label + Title */}
                        <div className="multi-scenario__workspace-header">
                          <span className="multi-scenario__workspace-label">
                            Scenario Path
                          </span>
                          <h4 className="multi-scenario__workspace-title">
                            {row.label}
                          </h4>
                        </div>

                        {/* Metrics Grid: Revenue + Risk */}
                        <div className="multi-scenario__workspace-metrics">
                          <div className="multi-scenario__workspace-metric">
                            <span className="multi-scenario__workspace-metric-label">
                              Est. Revenue
                            </span>
                            <span className="multi-scenario__workspace-metric-value multi-scenario__workspace-metric-value--cyan">
                              {revenueDisplay}
                            </span>
                          </div>
                          <div className="multi-scenario__workspace-metric">
                            <span className="multi-scenario__workspace-metric-label">
                              Risk Profile
                            </span>
                            <span className="multi-scenario__workspace-metric-value">
                              {riskDisplay}
                            </span>
                          </div>
                        </div>

                        {/* Diligence Progress */}
                        <div className="multi-scenario__workspace-progress">
                          <div className="multi-scenario__workspace-progress-header">
                            <span className="multi-scenario__workspace-progress-label">
                              Diligence Progress
                            </span>
                            <span className="multi-scenario__workspace-progress-value">
                              {progressPercent}%
                            </span>
                          </div>
                          <div className="multi-scenario__workspace-progress-bar">
                            <div
                              className="multi-scenario__workspace-progress-fill"
                              style={{ width: `${progressPercent}%` }}
                            />
                          </div>
                        </div>

                        {/* Enter Workspace CTA */}
                        <button
                          type="button"
                          onClick={() =>
                            setActiveScenario(row.key as DevelopmentScenario)
                          }
                          className="multi-scenario__workspace-cta"
                        >
                          {isActive ? 'Viewing Workspace' : 'Enter Workspace'}
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

            {/* Feasibility Signals */}
            {feasibilitySignals.length > 0 && (
              <div className="multi-scenario__signals">
                <div className="multi-scenario__signals-header">
                  <h3 className="multi-scenario__signals-title">
                    Feasibility Signals
                  </h3>
                  {propertyId && (
                    <Link
                      to={`/app/asset-feasibility?propertyId=${encodeURIComponent(propertyId)}`}
                      className="multi-scenario__workspace-link"
                    >
                      Open Feasibility Workspace →
                    </Link>
                  )}
                </div>
                <p className="multi-scenario__signals-description">
                  Highlights derived from quick analysis. Prioritise these
                  before handing off to the feasibility team.
                </p>
                {capturedProperty && (
                  <div className="multi-scenario__export-actions">
                    <button
                      type="button"
                      onClick={() => handleReportExport('json')}
                      disabled={isExportingReport}
                      className="multi-scenario__export-btn multi-scenario__export-btn--primary"
                    >
                      {isExportingReport ? 'Preparing JSON…' : 'Download JSON'}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleReportExport('pdf')}
                      disabled={isExportingReport}
                      className="multi-scenario__export-btn multi-scenario__export-btn--secondary"
                    >
                      {isExportingReport ? 'Preparing PDF…' : 'Download PDF'}
                    </button>
                    {reportExportMessage && (
                      <span
                        className={`multi-scenario__export-message ${reportExportMessage.toLowerCase().includes('unable') ? 'multi-scenario__export-message--error' : 'multi-scenario__export-message--success'}`}
                      >
                        {reportExportMessage}
                      </span>
                    )}
                  </div>
                )}
                <div className="multi-scenario__signals-grid">
                  {feasibilitySignals.map((entry) => (
                    <div
                      key={entry.scenario}
                      className="multi-scenario__signal-card"
                    >
                      <div className="multi-scenario__signal-header">
                        <strong className="multi-scenario__signal-label">
                          {entry.label}
                        </strong>
                      </div>
                      {entry.opportunities.length > 0 && (
                        <div className="multi-scenario__signal-section">
                          <span className="multi-scenario__signal-type multi-scenario__signal-type--opportunity">
                            Opportunities
                          </span>
                          <ul className="multi-scenario__signal-list multi-scenario__signal-list--opportunity">
                            {entry.opportunities.map((message) => (
                              <li key={message}>{message}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {entry.risks.length > 0 && (
                        <div className="multi-scenario__signal-section">
                          <span className="multi-scenario__signal-type multi-scenario__signal-type--risk">
                            Risks & Follow-ups
                          </span>
                          <ul className="multi-scenario__signal-list multi-scenario__signal-list--risk">
                            {entry.risks.map((message) => (
                              <li key={message}>{message}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {entry.opportunities.length === 0 &&
                        entry.risks.length === 0 && (
                          <p className="multi-scenario__signal-empty">
                            No automated guidance produced. Review the scenario
                            notes for additional context.
                          </p>
                        )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Scenario Focus Notice */}
            {activeScenario !== 'all' && comparisonScenariosCount > 0 && (
              <div className="multi-scenario__focus-notice">
                <strong>Scenario focus:</strong> Viewing{' '}
                {scenarioLookup.get(activeScenario)?.label ??
                  formatCategoryName(activeScenario)}{' '}
                metrics. Switch back to "All scenarios" to compare options
                side-by-side.
              </div>
            )}

            {/* Summary Footer - AI Studio: Aggregate stats at bottom */}
            <footer className="multi-scenario__summary-footer">
              <div className="multi-scenario__summary-stat">
                <span className="multi-scenario__summary-value">
                  {summaryStats.scenariosTracked}
                </span>
                <span className="multi-scenario__summary-label">
                  Scenarios Tracked
                </span>
              </div>
              <div className="multi-scenario__summary-stat">
                <span className="multi-scenario__summary-value">
                  {summaryStats.avgCondition !== null
                    ? `${summaryStats.avgCondition}/100`
                    : '—'}
                </span>
                <span className="multi-scenario__summary-label">
                  Avg Condition
                </span>
              </div>
              <div className="multi-scenario__summary-stat multi-scenario__summary-stat--opportunity">
                <span className="multi-scenario__summary-value">
                  {summaryStats.totalOpportunities}
                </span>
                <span className="multi-scenario__summary-label">
                  Opportunities
                </span>
              </div>
              <div className="multi-scenario__summary-stat multi-scenario__summary-stat--risk">
                <span className="multi-scenario__summary-value">
                  {summaryStats.totalRisks}
                </span>
                <span className="multi-scenario__summary-label">
                  Risks Flagged
                </span>
              </div>
            </footer>
          </div>
        )}
      </div>
    </section>
  )
}
