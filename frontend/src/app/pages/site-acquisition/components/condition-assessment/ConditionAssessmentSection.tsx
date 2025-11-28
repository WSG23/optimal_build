/**
 * Condition Assessment Section Component
 *
 * Displays the property condition assessment with:
 * - Overall rating and score display
 * - Immediate actions
 * - Condition insights
 * - Systems grid with ratings
 * - Manual inspection capture controls
 * - Inspection history summary
 * - Scenario overrides comparison
 *
 * Receives all data and handlers via props (no internal state).
 */

import type { CSSProperties } from 'react'
import type {
  ConditionAssessment,
  DevelopmentScenario,
} from '../../../../../api/siteAcquisition'
import type { ScenarioOption } from '../../constants'
import { formatDeltaValue } from '../../utils'
import {
  classifySystemSeverity,
  getSeverityVisuals,
  getDeltaVisuals,
} from '../../utils/insights'

// ============================================================================
// Types
// ============================================================================

export interface SystemComparison {
  name: string
  previous: { rating: string; score: number } | null
  scoreDelta: number | null | undefined
}

export interface ConditionInsight {
  id: string
  severity: 'critical' | 'warning' | 'info' | 'positive'
  title: string
  detail: string
  specialist?: string | null
}

export interface ConditionAssessmentSectionProps {
  // Core data
  capturedProperty: unknown | null
  conditionAssessment: ConditionAssessment | null
  isLoadingCondition: boolean

  // Assessment history
  latestAssessmentEntry: ConditionAssessment | null
  previousAssessmentEntry: ConditionAssessment | null
  assessmentHistoryError: string | null
  isLoadingAssessmentHistory: boolean
  assessmentSaveMessage: string | null

  // Scenario assessments
  scenarioAssessments: ConditionAssessment[]
  isLoadingScenarioAssessments: boolean
  scenarioAssessmentsError: string | null
  scenarioOverrideEntries: ConditionAssessment[]
  baseScenarioAssessment: ConditionAssessment | null
  scenarioComparisonEntries: ConditionAssessment[]

  // Insights
  combinedConditionInsights: ConditionInsight[]
  insightSubtitle: string
  systemComparisonMap: Map<string, SystemComparison>

  // Export state
  isExportingReport: boolean

  // Lookup helpers
  scenarioLookup: Map<DevelopmentScenario, ScenarioOption>

  // Formatters (stable callbacks from parent)
  formatRecordedTimestamp: (timestamp?: string | null) => string
  formatScenarioLabel: (scenario: DevelopmentScenario | 'all' | null | undefined) => string
  describeRatingChange: (
    current: string,
    reference: string,
  ) => { text: string; tone: 'positive' | 'negative' | 'neutral' }
  describeRiskChange: (
    current: string,
    reference: string,
  ) => { text: string; tone: 'positive' | 'negative' | 'neutral' }

  // Handlers (stable callbacks from parent)
  openAssessmentEditor: (mode: 'new' | 'edit') => void
  setScenarioComparisonBase: (scenario: DevelopmentScenario) => void
  handleReportExport: (format: 'json' | 'pdf') => void
  setHistoryModalOpen: (open: boolean) => void

  // Inline component (will be extracted separately in Phase 1)
  InlineInspectionHistorySummary: React.ComponentType
}

// ============================================================================
// Component
// ============================================================================

export function ConditionAssessmentSection({
  capturedProperty,
  conditionAssessment,
  isLoadingCondition,
  latestAssessmentEntry,
  previousAssessmentEntry: _previousAssessmentEntry,
  assessmentHistoryError: _assessmentHistoryError,
  isLoadingAssessmentHistory: _isLoadingAssessmentHistory,
  assessmentSaveMessage,
  scenarioAssessments: _scenarioAssessments,
  isLoadingScenarioAssessments,
  scenarioAssessmentsError,
  scenarioOverrideEntries,
  baseScenarioAssessment,
  scenarioComparisonEntries,
  combinedConditionInsights,
  insightSubtitle,
  systemComparisonMap,
  isExportingReport,
  scenarioLookup: _scenarioLookup,
  formatRecordedTimestamp,
  formatScenarioLabel,
  describeRatingChange,
  describeRiskChange,
  openAssessmentEditor,
  setScenarioComparisonBase,
  handleReportExport,
  setHistoryModalOpen: _setHistoryModalOpen,
  InlineInspectionHistorySummary,
}: ConditionAssessmentSectionProps) {
  return (
    <section
      style={{
        background: 'white',
        border: '1px solid #d2d2d7',
        borderRadius: '18px',
        padding: '2rem',
      }}
    >
      <h2
        style={{
          fontSize: '1.5rem',
          fontWeight: 600,
          marginBottom: '1rem',
          letterSpacing: '-0.01em',
        }}
      >
        Property Condition Assessment
      </h2>
      {isLoadingCondition ? (
        <div
          style={{
            padding: '2.5rem',
            textAlign: 'center',
            color: '#6e6e73',
            background: '#f5f5f7',
            borderRadius: '12px',
          }}
        >
          <p style={{ margin: 0 }}>Analysing building condition...</p>
        </div>
      ) : !capturedProperty ? (
        <div
          style={{
            padding: '3rem 2rem',
            textAlign: 'center',
            color: '#6e6e73',
            background: '#f5f5f7',
            borderRadius: '12px',
          }}
        >
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🏢</div>
          <p style={{ margin: 0, fontSize: '1.0625rem' }}>
            Capture a property to generate the developer condition assessment
          </p>
          <p style={{ margin: '0.5rem 0 0', fontSize: '0.9375rem' }}>
            Structural, M&amp;E, and compliance insights will appear here with targeted actions.
          </p>
        </div>
      ) : !conditionAssessment ? (
        <div
          style={{
            padding: '2.5rem 2rem',
            textAlign: 'center',
            color: '#6e6e73',
            background:
              (capturedProperty as { propertyId?: string })?.propertyId === 'offline-property'
                ? '#f5f5f7'
                : '#fff7ed',
            borderRadius: '12px',
            border:
              (capturedProperty as { propertyId?: string })?.propertyId === 'offline-property'
                ? 'none'
                : '1px solid #fed7aa',
          }}
        >
          <p style={{ margin: 0 }}>
            {(capturedProperty as { propertyId?: string })?.propertyId === 'offline-property'
              ? 'Condition assessment not available in offline mode. Capture a real property to access inspection data.'
              : 'Unable to load condition assessment. Please retry after refreshing the capture.'}
          </p>
        </div>
      ) : (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '1.75rem',
          }}
        >
          {/* Overall Rating and Actions */}
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '1.5rem',
              alignItems: 'flex-start',
            }}
          >
            <div
              style={{
                flex: '1 1 260px',
                background: '#f5f5f7',
                borderRadius: '12px',
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.5rem',
              }}
            >
              <span
                style={{
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  color: '#6e6e73',
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                }}
              >
                Overall Rating
              </span>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'baseline',
                  gap: '0.75rem',
                }}
              >
                <span style={{ fontSize: '2.5rem', fontWeight: 700 }}>
                  {conditionAssessment.overallRating}
                </span>
                <span style={{ fontSize: '1rem', color: '#6e6e73' }}>
                  {conditionAssessment.overallScore}/100 · {conditionAssessment.riskLevel} risk
                </span>
              </div>
              <p
                style={{
                  margin: 0,
                  fontSize: '0.9375rem',
                  color: '#3a3a3c',
                  lineHeight: 1.5,
                }}
              >
                {conditionAssessment.summary}
              </p>
              {conditionAssessment.scenarioContext && (
                <p
                  style={{
                    margin: 0,
                    fontSize: '0.875rem',
                    color: '#0071e3',
                  }}
                >
                  {conditionAssessment.scenarioContext}
                </p>
              )}
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '0.75rem',
                  fontSize: '0.8125rem',
                  color: '#6e6e73',
                }}
              >
                <span>
                  Inspector:{' '}
                  <strong>{conditionAssessment.inspectorName?.trim() || 'Not recorded'}</strong>
                </span>
                {conditionAssessment.recordedAt && (
                  <span>Logged {formatRecordedTimestamp(conditionAssessment.recordedAt)}</span>
                )}
              </div>
              {conditionAssessment.attachments.length > 0 && (
                <div>
                  <span
                    style={{
                      display: 'inline-block',
                      marginTop: '0.5rem',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      textTransform: 'uppercase',
                      color: '#6e6e73',
                      letterSpacing: '0.06em',
                    }}
                  >
                    Attachments
                  </span>
                  <ul style={{ margin: '0.35rem 0 0', paddingLeft: '1.2rem' }}>
                    {conditionAssessment.attachments.map((attachment, index) => (
                      <li key={`current-attachment-${index}`} style={{ fontSize: '0.85rem' }}>
                        {attachment.url ? (
                          <a
                            href={attachment.url}
                            target="_blank"
                            rel="noreferrer"
                            style={{ color: '#0a84ff' }}
                          >
                            {attachment.label}
                          </a>
                        ) : (
                          attachment.label
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            <div
              style={{
                flex: '1 1 280px',
                background: '#f5f5f7',
                borderRadius: '12px',
                padding: '1.5rem',
              }}
            >
              <h3
                style={{
                  margin: '0 0 0.75rem',
                  fontSize: '1.0625rem',
                  fontWeight: 600,
                }}
              >
                Immediate Actions
              </h3>
              <ul
                style={{
                  margin: 0,
                  paddingLeft: '1.2rem',
                  color: '#3a3a3c',
                  fontSize: '0.9375rem',
                  lineHeight: 1.5,
                }}
              >
                {conditionAssessment.recommendedActions.map((action) => (
                  <li key={action}>{action}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Condition Insights */}
          {combinedConditionInsights.length > 0 && (
            <div
              style={{
                border: '1px solid #e5e5e7',
                borderRadius: '12px',
                padding: '1.5rem',
                background: '#f8fafc',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '0.75rem',
                }}
              >
                <h3
                  style={{
                    margin: 0,
                    fontSize: '1.125rem',
                    fontWeight: 600,
                    letterSpacing: '-0.01em',
                  }}
                >
                  Condition insights
                </h3>
                <span style={{ fontSize: '0.85rem', color: '#475569' }}>{insightSubtitle}</span>
              </div>
              <div
                style={{
                  display: 'grid',
                  gap: '1rem',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                }}
              >
                {combinedConditionInsights.map((insight) => {
                  const visuals = getSeverityVisuals(insight.severity)
                  const isChecklistInsight = insight.id.startsWith('checklist-')
                  const chipStyle: CSSProperties = {
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                    padding: '0.3rem 0.6rem',
                    borderRadius: '9999px',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    background: 'rgba(15, 23, 42, 0.08)',
                    color: '#0f172a',
                    border: '1px solid rgba(15, 23, 42, 0.12)',
                  }
                  return (
                    <div
                      key={insight.id}
                      style={{
                        border: `1px solid ${visuals.border}`,
                        background: visuals.background,
                        color: visuals.text,
                        borderRadius: '12px',
                        padding: '1.2rem',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.65rem',
                      }}
                    >
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.4rem',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          textTransform: 'uppercase',
                          letterSpacing: '0.08em',
                        }}
                      >
                        <span
                          style={{
                            width: '0.35rem',
                            height: '0.35rem',
                            borderRadius: '9999px',
                            background: visuals.indicator,
                          }}
                        />
                        {visuals.label}
                      </span>
                      <strong style={{ fontSize: '0.95rem', lineHeight: 1.4 }}>
                        {insight.title}
                      </strong>
                      <p
                        style={{
                          margin: 0,
                          fontSize: '0.85rem',
                          lineHeight: 1.4,
                        }}
                      >
                        {insight.detail}
                      </p>
                      {(insight.specialist || isChecklistInsight) && (
                        <div
                          style={{
                            display: 'flex',
                            flexWrap: 'wrap',
                            gap: '0.5rem',
                          }}
                        >
                          {isChecklistInsight && (
                            <span
                              style={{
                                ...chipStyle,
                                background: 'rgba(29, 78, 216, 0.08)',
                                color: '#1d4ed8',
                                border: '1px solid rgba(29, 78, 216, 0.15)',
                              }}
                            >
                              Checklist follow-up
                            </span>
                          )}
                          {insight.specialist && (
                            <span style={chipStyle}>
                              Specialist · <strong>{insight.specialist}</strong>
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Systems Grid */}
          <div
            style={{
              display: 'grid',
              gap: '1rem',
              gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            }}
          >
            {conditionAssessment.systems.map((system) => {
              const comparison = systemComparisonMap.get(system.name)
              const delta =
                comparison && typeof comparison.scoreDelta === 'number'
                  ? comparison.scoreDelta
                  : null
              const previousRating = comparison?.previous?.rating ?? null
              const previousScore =
                typeof comparison?.previous?.score === 'number' ? comparison?.previous?.score : null
              const systemSeverity = classifySystemSeverity(system.rating, delta)
              const badgeVisuals = getSeverityVisuals(systemSeverity)
              const deltaVisuals = getDeltaVisuals(delta)

              return (
                <div
                  key={system.name}
                  style={{
                    border: '1px solid #e5e5e7',
                    borderRadius: '12px',
                    padding: '1.25rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.75rem',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                      flexWrap: 'wrap',
                      gap: '0.6rem',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.35rem',
                      }}
                    >
                      <h3
                        style={{
                          margin: 0,
                          fontSize: '1.0625rem',
                          fontWeight: 600,
                        }}
                      >
                        {system.name}
                      </h3>
                      {previousRating && previousScore !== null && (
                        <span style={{ fontSize: '0.8rem', color: '#6e6e73' }}>
                          Previous {previousRating} · {previousScore}/100
                        </span>
                      )}
                    </div>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        flexWrap: 'wrap',
                        gap: '0.45rem',
                      }}
                    >
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.35rem',
                          padding: '0.3rem 0.65rem',
                          borderRadius: '9999px',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          textTransform: 'uppercase',
                          letterSpacing: '0.05em',
                          border: `1px solid ${badgeVisuals.border}`,
                          background: badgeVisuals.background,
                          color: badgeVisuals.text,
                        }}
                      >
                        <span
                          style={{
                            width: '0.35rem',
                            height: '0.35rem',
                            borderRadius: '9999px',
                            background: badgeVisuals.indicator,
                          }}
                        />
                        {system.rating} · {system.score}/100
                      </span>
                      {delta !== null && (
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.25rem',
                            padding: '0.25rem 0.55rem',
                            borderRadius: '9999px',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            background: deltaVisuals.background,
                            color: deltaVisuals.text,
                            border: `1px solid ${deltaVisuals.border}`,
                          }}
                        >
                          {delta > 0 ? '▲' : delta < 0 ? '▼' : '■'} {formatDeltaValue(delta)}
                        </span>
                      )}
                    </div>
                  </div>
                  <p
                    style={{
                      margin: 0,
                      fontSize: '0.9rem',
                      color: '#3a3a3c',
                      lineHeight: 1.5,
                    }}
                  >
                    {system.notes}
                  </p>
                  <ul
                    style={{
                      margin: 0,
                      paddingLeft: '1.1rem',
                      fontSize: '0.875rem',
                      color: '#3a3a3c',
                      lineHeight: 1.4,
                    }}
                  >
                    {system.recommendedActions.map((action) => (
                      <li key={action}>{action}</li>
                    ))}
                  </ul>
                </div>
              )
            })}
          </div>

          {/* Manual Inspection Capture */}
          <div
            style={{
              border: '1px solid #e5e5e7',
              borderRadius: '12px',
              padding: '1.5rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '0.75rem',
              }}
            >
              <div
                style={{
                  maxWidth: '520px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.35rem',
                }}
              >
                <h3
                  style={{
                    margin: 0,
                    fontSize: '1.0625rem',
                    fontWeight: 600,
                  }}
                >
                  Manual inspection capture
                </h3>
                <p style={{ margin: 0, fontSize: '0.9rem', color: '#4b5563', lineHeight: 1.5 }}>
                  Log a fresh site visit or update the latest inspection without waiting for
                  automated sync.
                </p>
              </div>
              <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  onClick={() => openAssessmentEditor('new')}
                  disabled={!capturedProperty}
                  style={{
                    border: '1px solid #1d1d1f',
                    background: capturedProperty ? '#1d1d1f' : '#f5f5f7',
                    color: capturedProperty ? 'white' : '#1d1d1f88',
                    borderRadius: '9999px',
                    padding: '0.45rem 1.1rem',
                    fontSize: '0.8125rem',
                    fontWeight: 600,
                    cursor: capturedProperty ? 'pointer' : 'not-allowed',
                  }}
                >
                  Log inspection
                </button>
                {conditionAssessment && (
                  <button
                    type="button"
                    onClick={() => openAssessmentEditor('edit')}
                    disabled={!capturedProperty}
                    style={{
                      border: '1px solid #1d1d1f',
                      background: 'white',
                      color: '#1d1d1f',
                      borderRadius: '9999px',
                      padding: '0.45rem 1.1rem',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      cursor: capturedProperty ? 'pointer' : 'not-allowed',
                    }}
                  >
                    Edit latest
                  </button>
                )}
              </div>
            </div>
            {assessmentSaveMessage && (
              <p
                style={{
                  margin: 0,
                  fontSize: '0.85rem',
                  color: assessmentSaveMessage.includes('success') ? '#15803d' : '#c53030',
                }}
              >
                {assessmentSaveMessage}
              </p>
            )}
            {capturedProperty ? (
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '0.6rem',
                  fontSize: '0.85rem',
                  color: '#4b5563',
                }}
              >
                {latestAssessmentEntry ? (
                  <>
                    <span>
                      Last recorded:{' '}
                      <strong>{formatRecordedTimestamp(latestAssessmentEntry.recordedAt)}</strong>
                    </span>
                    <span>•</span>
                    <span>
                      Scenario:{' '}
                      <strong>{formatScenarioLabel(latestAssessmentEntry.scenario)}</strong>
                    </span>
                    <span>•</span>
                    <span>
                      Rating:{' '}
                      <strong>
                        {latestAssessmentEntry.overallRating} ·{' '}
                        {latestAssessmentEntry.overallScore}/100
                      </strong>
                    </span>
                  </>
                ) : (
                  <span>
                    No manual inspections logged yet - use &quot;Log inspection&quot; to create one.
                  </span>
                )}
              </div>
            ) : (
              <p style={{ margin: 0, fontSize: '0.85rem', color: '#6b7280' }}>
                Capture a property to enable manual inspection logging.
              </p>
            )}
          </div>

          {/* Inspection History Summary */}
          <InlineInspectionHistorySummary />

          {/* Scenario Overrides */}
          <div
            style={{
              border: '1px solid #e5e5e7',
              borderRadius: '12px',
              padding: '1.5rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '0.75rem',
              }}
            >
              <h3
                style={{
                  margin: 0,
                  fontSize: '1.0625rem',
                  fontWeight: 600,
                }}
              >
                Scenario Overrides
              </h3>
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '0.5rem',
                  alignItems: 'center',
                }}
              >
                <button
                  type="button"
                  onClick={() => handleReportExport('json')}
                  disabled={!capturedProperty || isExportingReport}
                  style={{
                    border: '1px solid #1d1d1f',
                    background: '#1d1d1f',
                    color: 'white',
                    borderRadius: '9999px',
                    padding: '0.4rem 0.9rem',
                    fontSize: '0.8125rem',
                    fontWeight: 600,
                    cursor: isExportingReport ? 'not-allowed' : 'pointer',
                  }}
                >
                  {isExportingReport ? 'Preparing JSON…' : 'Download JSON'}
                </button>
                <button
                  type="button"
                  onClick={() => handleReportExport('pdf')}
                  disabled={!capturedProperty || isExportingReport}
                  style={{
                    border: '1px solid #1d1d1f',
                    background: 'white',
                    color: '#1d1d1f',
                    borderRadius: '9999px',
                    padding: '0.4rem 0.9rem',
                    fontSize: '0.8125rem',
                    fontWeight: 600,
                    cursor: isExportingReport ? 'not-allowed' : 'pointer',
                  }}
                >
                  {isExportingReport ? 'Preparing PDF…' : 'Download PDF'}
                </button>
                {scenarioOverrideEntries.length > 1 && baseScenarioAssessment && (
                  <label
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      fontSize: '0.85rem',
                      color: '#3a3a3c',
                    }}
                  >
                    <span style={{ fontWeight: 600 }}>Baseline scenario</span>
                    <select
                      value={baseScenarioAssessment.scenario ?? ''}
                      onChange={(event) =>
                        setScenarioComparisonBase(event.target.value as DevelopmentScenario)
                      }
                      style={{
                        borderRadius: '8px',
                        border: '1px solid #d2d2d7',
                        padding: '0.4rem 0.6rem',
                        fontSize: '0.85rem',
                      }}
                    >
                      {scenarioOverrideEntries.map((entry) => (
                        <option key={entry.scenario ?? 'all'} value={entry.scenario ?? ''}>
                          {formatScenarioLabel(entry.scenario)}
                        </option>
                      ))}
                    </select>
                  </label>
                )}
              </div>
            </div>
            {scenarioAssessmentsError ? (
              <p
                style={{
                  margin: 0,
                  fontSize: '0.85rem',
                  color: '#c53030',
                }}
              >
                {scenarioAssessmentsError}
              </p>
            ) : isLoadingScenarioAssessments ? (
              <div
                style={{
                  padding: '1.5rem',
                  textAlign: 'center',
                  color: '#6e6e73',
                  background: '#f5f5f7',
                  borderRadius: '10px',
                }}
              >
                <p style={{ margin: 0, fontSize: '0.9rem' }}>Loading scenario overrides...</p>
              </div>
            ) : scenarioOverrideEntries.length === 0 ? (
              <div
                style={{
                  padding: '1.5rem',
                  textAlign: 'center',
                  color: '#6e6e73',
                  background: '#f5f5f7',
                  borderRadius: '10px',
                }}
              >
                <p style={{ margin: 0, fontSize: '0.9rem' }}>
                  No scenario-specific overrides recorded yet. Save an inspection for a specific
                  scenario to compare outcomes.
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                {scenarioOverrideEntries.length > 0 && (
                  <div
                    style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '0.75rem',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: '1rem',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.25rem',
                      }}
                    >
                      <span
                        style={{
                          fontSize: '0.8rem',
                          fontWeight: 600,
                          letterSpacing: '0.06em',
                          textTransform: 'uppercase',
                          color: '#6e6e73',
                        }}
                      >
                        Compare against
                      </span>
                      <span style={{ fontSize: '0.95rem', color: '#1d1d1f' }}>
                        Choose the baseline inspection to benchmark other scenarios.
                      </span>
                    </div>
                    <label
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        fontSize: '0.9rem',
                        color: '#3a3a3c',
                      }}
                    >
                      <span style={{ fontWeight: 600 }}>Baseline scenario</span>
                      <select
                        value={baseScenarioAssessment?.scenario ?? ''}
                        onChange={(event) => {
                          const selected = event.target.value as DevelopmentScenario
                          if (selected) {
                            setScenarioComparisonBase(selected)
                          }
                        }}
                        style={{
                          borderRadius: '9999px',
                          border: '1px solid #d2d2d7',
                          padding: '0.4rem 0.9rem',
                          background: 'white',
                          fontSize: '0.9rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        {scenarioOverrideEntries.map((assessment) => (
                          <option key={assessment.scenario ?? 'all'} value={assessment.scenario ?? ''}>
                            {formatScenarioLabel(assessment.scenario)}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>
                )}

                {baseScenarioAssessment && (
                  <div
                    style={{
                      border: '1px solid #d2d2d7',
                      borderRadius: '12px',
                      padding: '1.25rem',
                      background: '#f5f5f7',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.6rem',
                    }}
                  >
                    <span
                      style={{
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        letterSpacing: '0.08em',
                        textTransform: 'uppercase',
                        color: '#6e6e73',
                      }}
                    >
                      Baseline scenario
                    </span>
                    <strong style={{ fontSize: '1rem', fontWeight: 600 }}>
                      {formatScenarioLabel(baseScenarioAssessment.scenario)}
                    </strong>
                    <div
                      style={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '0.75rem',
                        alignItems: 'center',
                        color: '#3a3a3c',
                        fontSize: '0.9rem',
                      }}
                    >
                      <span>Rating {baseScenarioAssessment.overallRating}</span>
                      <span>{baseScenarioAssessment.overallScore}/100 score</span>
                      <span style={{ textTransform: 'capitalize' }}>
                        {baseScenarioAssessment.riskLevel} risk
                      </span>
                    </div>
                    <p
                      style={{
                        margin: 0,
                        fontSize: '0.9rem',
                        color: '#3a3a3c',
                        lineHeight: 1.5,
                      }}
                    >
                      {baseScenarioAssessment.summary}
                    </p>
                    {baseScenarioAssessment.scenarioContext && (
                      <p
                        style={{
                          margin: 0,
                          fontSize: '0.85rem',
                          color: '#0071e3',
                        }}
                      >
                        {baseScenarioAssessment.scenarioContext}
                      </p>
                    )}
                    {baseScenarioAssessment.recommendedActions.length > 0 && (
                      <div style={{ display: 'grid', gap: '0.4rem' }}>
                        <strong style={{ fontSize: '0.85rem' }}>Actions</strong>
                        <ul
                          style={{
                            margin: 0,
                            paddingLeft: '1.1rem',
                            fontSize: '0.85rem',
                            color: '#3a3a3c',
                            lineHeight: 1.4,
                          }}
                        >
                          {baseScenarioAssessment.recommendedActions.map((action) => (
                            <li key={action}>{action}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
                {scenarioComparisonEntries.length === 0 ? (
                  <div
                    style={{
                      padding: '1.25rem',
                      border: '1px solid #d2d2d7',
                      borderRadius: '12px',
                      background: '#ffffff',
                      color: '#6e6e73',
                      fontSize: '0.9rem',
                    }}
                  >
                    Capture another scenario-specific override to compare with the baseline.
                  </div>
                ) : (
                  <div
                    style={{
                      display: 'grid',
                      gap: '1rem',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                    }}
                  >
                    {scenarioComparisonEntries.map((assessment) => {
                      if (!baseScenarioAssessment) {
                        return null
                      }
                      const scoreDelta =
                        assessment.overallScore - baseScenarioAssessment.overallScore
                      const ratingInfo = describeRatingChange(
                        assessment.overallRating,
                        baseScenarioAssessment.overallRating,
                      )
                      const riskInfo = describeRiskChange(
                        assessment.riskLevel,
                        baseScenarioAssessment.riskLevel,
                      )
                      const toneColorMap: Record<'positive' | 'negative' | 'neutral', string> = {
                        positive: '#15803d',
                        negative: '#c53030',
                        neutral: '#6e6e73',
                      }

                      return (
                        <div
                          key={assessment.scenario}
                          style={{
                            border: '1px solid #e5e5e7',
                            borderRadius: '12px',
                            padding: '1.25rem',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '0.6rem',
                            background: '#ffffff',
                          }}
                        >
                          <strong style={{ fontSize: '1rem', fontWeight: 600 }}>
                            {formatScenarioLabel(assessment.scenario)}
                          </strong>
                          <div
                            style={{
                              display: 'flex',
                              flexDirection: 'column',
                              gap: '0.4rem',
                              fontSize: '0.9rem',
                              color: '#3a3a3c',
                            }}
                          >
                            <span>
                              Score {assessment.overallScore}/100{' '}
                              <span
                                style={{
                                  color:
                                    scoreDelta > 0
                                      ? '#15803d'
                                      : scoreDelta < 0
                                        ? '#c53030'
                                        : '#6e6e73',
                                  fontWeight: 600,
                                }}
                              >
                                {scoreDelta === 0
                                  ? 'Δ 0'
                                  : `Δ ${scoreDelta > 0 ? '+' : ''}${scoreDelta}`}
                              </span>
                            </span>
                            <span
                              style={{
                                color: toneColorMap[ratingInfo.tone],
                                fontWeight: 600,
                              }}
                            >
                              {ratingInfo.text}
                            </span>
                            <span
                              style={{
                                color: toneColorMap[riskInfo.tone],
                                fontWeight: 600,
                              }}
                            >
                              {riskInfo.text}
                            </span>
                          </div>
                          <p
                            style={{
                              margin: 0,
                              fontSize: '0.9rem',
                              color: '#3a3a3c',
                              lineHeight: 1.5,
                            }}
                          >
                            {assessment.summary}
                          </p>
                          {assessment.scenarioContext && (
                            <p
                              style={{
                                margin: 0,
                                fontSize: '0.85rem',
                                color: '#0071e3',
                              }}
                            >
                              {assessment.scenarioContext}
                            </p>
                          )}
                          {assessment.recommendedActions.length > 0 && (
                            <div style={{ display: 'grid', gap: '0.4rem' }}>
                              <strong style={{ fontSize: '0.85rem' }}>Actions</strong>
                              <ul
                                style={{
                                  margin: 0,
                                  paddingLeft: '1.1rem',
                                  fontSize: '0.85rem',
                                  color: '#3a3a3c',
                                  lineHeight: 1.4,
                                }}
                              >
                                {assessment.recommendedActions.map((action) => (
                                  <li key={action}>{action}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  )
}
