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
 */

import { useState, useMemo } from 'react'
import { Link } from '../../../../../router'
import type {
  DevelopmentScenario,
  CapturedProperty,
} from '../../../../../api/siteAcquisition'
import type {
  ScenarioComparisonDatum,
  FeasibilitySignalEntry,
  ScenarioOption,
} from '../../types'
import { getSeverityVisuals } from '../../utils/insights'
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
  formatRecordedTimestamp,
}: MultiScenarioComparisonSectionProps) {
  // Progressive disclosure state for AI insights
  const [expandedInsights, setExpandedInsights] = useState<Set<string>>(
    new Set(),
  )

  const toggleInsight = (key: string) => {
    setExpandedInsights((prev) => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }

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
      {/* Content container - individual cards have their own styling */}
      <div className="multi-scenario__card">
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
            {/* Scenario Comparison Cards */}
            <div className="multi-scenario__cards-grid">
              {scenarioComparisonData.map((row) => {
                const isActive =
                  row.key === 'all'
                    ? activeScenario === 'all'
                    : activeScenario === row.key
                const progressLabel =
                  row.checklistCompleted !== null && row.checklistTotal !== null
                    ? `${row.checklistCompleted}/${row.checklistTotal}`
                    : null
                const progressPercent = row.checklistPercent ?? null
                const focusable = row.key !== 'all'
                const primaryVisuals = row.primaryInsight
                  ? getSeverityVisuals(row.primaryInsight.severity)
                  : null

                return (
                  <article
                    key={row.key}
                    className={`multi-scenario__card-item ${isActive ? 'multi-scenario__card-item--active' : ''}`}
                  >
                    {/* Card Header */}
                    <div className="multi-scenario__card-header">
                      <div className="multi-scenario__card-identity">
                        <span className="multi-scenario__card-icon">
                          {row.icon}
                        </span>
                        <div className="multi-scenario__card-labels">
                          <span className="multi-scenario__card-type">
                            {row.key === 'all' ? 'Aggregate' : 'Scenario'}
                          </span>
                          <span className="multi-scenario__card-name">
                            {row.label}
                          </span>
                        </div>
                      </div>
                      {focusable ? (
                        isActive ? (
                          <span className="multi-scenario__badge multi-scenario__badge--focus">
                            Focus
                          </span>
                        ) : (
                          <button
                            type="button"
                            onClick={() =>
                              setActiveScenario(row.key as DevelopmentScenario)
                            }
                            className="multi-scenario__focus-btn"
                          >
                            Focus scenario
                          </button>
                        )
                      ) : (
                        <span className="multi-scenario__badge multi-scenario__badge--summary">
                          Summary
                        </span>
                      )}
                    </div>

                    {/* Inspector / Timestamp / Source */}
                    <div className="multi-scenario__card-meta">
                      <span>
                        Inspector:{' '}
                        <strong>
                          {row.inspectorName?.trim() || 'Not recorded'}
                        </strong>
                      </span>
                      {row.recordedAt && (
                        <span>
                          Logged {formatRecordedTimestamp(row.recordedAt)}
                        </span>
                      )}
                      <span
                        className={`multi-scenario__source-badge ${row.source === 'manual' ? 'multi-scenario__source-badge--manual' : 'multi-scenario__source-badge--auto'}`}
                      >
                        {row.source === 'manual'
                          ? 'Manual inspection'
                          : 'Automated baseline'}
                      </span>
                    </div>

                    {/* Quick Headline */}
                    {row.quickHeadline && (
                      <p className="multi-scenario__card-headline">
                        {row.quickHeadline}
                      </p>
                    )}

                    {/* Quick Metrics */}
                    {row.quickMetrics.length > 0 && (
                      <ul className="multi-scenario__metrics-list">
                        {row.quickMetrics.map((metric) => (
                          <li
                            key={`${row.key}-${metric.label}`}
                            className="multi-scenario__metric"
                          >
                            <span className="multi-scenario__metric-label">
                              {metric.label}
                            </span>
                            <strong className="multi-scenario__metric-value">
                              {metric.value}
                            </strong>
                          </li>
                        ))}
                      </ul>
                    )}

                    {/* Condition / Checklist Progress */}
                    <div className="multi-scenario__status-grid">
                      <div className="multi-scenario__status-item">
                        <span className="multi-scenario__status-label">
                          Condition
                        </span>
                        <span className="multi-scenario__status-value">
                          {row.conditionRating ? row.conditionRating : '—'}
                        </span>
                        <span className="multi-scenario__status-detail">
                          {row.conditionScore !== null
                            ? `${row.conditionScore}/100`
                            : '—'}{' '}
                          {row.riskLevel ? `· ${row.riskLevel} risk` : ''}
                        </span>
                      </div>
                      <div className="multi-scenario__status-item">
                        <span className="multi-scenario__status-label">
                          Checklist progress
                        </span>
                        {progressLabel ? (
                          <>
                            <div className="multi-scenario__progress-bar">
                              <div
                                className="multi-scenario__progress-fill"
                                style={{ width: `${progressPercent ?? 0}%` }}
                              />
                            </div>
                            <span className="multi-scenario__progress-text">
                              {progressLabel}
                              {progressPercent !== null
                                ? ` (${progressPercent}%)`
                                : ''}
                            </span>
                          </>
                        ) : (
                          <span className="multi-scenario__status-empty">
                            No checklist items yet.
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Primary Insight - Progressive Disclosure Pattern */}
                    {row.primaryInsight && primaryVisuals && (
                      <div className="multi-scenario__insight-container">
                        {/* Always visible: AI insight toggle button */}
                        <button
                          type="button"
                          className="multi-scenario__insight-toggle"
                          onClick={() => toggleInsight(row.key)}
                          aria-expanded={expandedInsights.has(row.key)}
                        >
                          <span
                            className="multi-scenario__insight-dot"
                            style={{ background: primaryVisuals.indicator }}
                          />
                          <span className="multi-scenario__insight-toggle-label">
                            {primaryVisuals.label}: {row.primaryInsight.title}
                          </span>
                          <span className="multi-scenario__insight-chevron">
                            {expandedInsights.has(row.key) ? '▲' : '▼'}
                          </span>
                        </button>

                        {/* Expandable content */}
                        {expandedInsights.has(row.key) && (
                          <div
                            className="multi-scenario__insight"
                            style={{
                              borderColor: primaryVisuals.border,
                              background: primaryVisuals.background,
                              color: primaryVisuals.text,
                            }}
                          >
                            <p className="multi-scenario__insight-detail">
                              {row.primaryInsight.detail}
                            </p>
                            {row.primaryInsight.specialist && (
                              <span className="multi-scenario__insight-specialist">
                                Specialist:{' '}
                                <strong>{row.primaryInsight.specialist}</strong>
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Recommended Action */}
                    {row.recommendedAction && (
                      <p className="multi-scenario__next-action">
                        <strong>Next action:</strong> {row.recommendedAction}
                      </p>
                    )}
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
