/**
 * Multi-Scenario Comparison Section Component
 *
 * Displays scenario comparison cards with condition ratings, checklist progress,
 * quick metrics, insights, and feasibility signals. Includes export functionality.
 */

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
  return (
    <section
      style={{
        background: 'white',
        border: '1px solid var(--ob-color-border-subtle)',
        borderRadius: 'var(--ob-radius-sm)',
        padding: '2rem',
        marginBottom: '2rem',
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
        Multi-Scenario Comparison
      </h2>
      {!capturedProperty ? (
        <div
          style={{
            padding: '3rem 2rem',
            textAlign: 'center',
            color: 'var(--ob-color-text-muted)',
            background: 'var(--ob-color-bg-surface-elevated)',
            borderRadius: 'var(--ob-radius-sm)',
          }}
        >
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📊</div>
          <p style={{ margin: 0, fontSize: '1.0625rem' }}>
            Capture a property to review scenario economics and development
            posture
          </p>
          <p style={{ margin: '0.5rem 0 0', fontSize: '0.9375rem' }}>
            Financial and planning metrics for each developer scenario appear
            here.
          </p>
        </div>
      ) : quickAnalysisScenariosCount === 0 ? (
        <div
          style={{
            padding: '2.5rem',
            textAlign: 'center',
            color: 'var(--ob-color-text-muted)',
            background: 'var(--ob-color-bg-surface-elevated)',
            borderRadius: 'var(--ob-radius-sm)',
          }}
        >
          <p style={{ margin: 0 }}>
            Quick analysis metrics unavailable for this capture. Try
            regenerating the scenarios.
          </p>
        </div>
      ) : (
        <div
          style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}
        >
          {/* Scenario Comparison Cards */}
          <div
            style={{
              display: 'grid',
              gap: '1rem',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            }}
          >
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
                  style={{
                    border: `2px solid ${isActive ? 'var(--ob-color-text-primary)' : 'var(--ob-color-border-subtle)'}`,
                    borderRadius: 'var(--ob-radius-sm)',
                    padding: '1.35rem',
                    background: isActive
                      ? 'white'
                      : 'var(--ob-color-bg-surface-elevated)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '1rem',
                    transition: 'border 0.2s ease, background 0.2s ease',
                  }}
                >
                  {/* Card Header */}
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                      gap: '0.75rem',
                      flexWrap: 'wrap',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.65rem',
                      }}
                    >
                      <span style={{ fontSize: '1.5rem' }}>{row.icon}</span>
                      <div
                        style={{
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '0.2rem',
                        }}
                      >
                        <span
                          style={{
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            letterSpacing: '0.08em',
                            textTransform: 'uppercase',
                            color: 'var(--ob-color-text-muted)',
                          }}
                        >
                          {row.key === 'all' ? 'Aggregate' : 'Scenario'}
                        </span>
                        <span
                          style={{
                            fontSize: '1.125rem',
                            fontWeight: 600,
                            letterSpacing: '-0.01em',
                          }}
                        >
                          {row.label}
                        </span>
                      </div>
                    </div>
                    {focusable ? (
                      isActive ? (
                        <span
                          style={{
                            borderRadius: 'var(--ob-radius-pill)',
                            background: 'var(--ob-color-brand-primary)',
                            color: 'white',
                            padding: '0.25rem 0.75rem',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            letterSpacing: '0.08em',
                            textTransform: 'uppercase',
                          }}
                        >
                          Focus
                        </span>
                      ) : (
                        <button
                          type="button"
                          onClick={() =>
                            setActiveScenario(row.key as DevelopmentScenario)
                          }
                          style={{
                            border: '1px solid var(--ob-color-text-primary)',
                            background: 'white',
                            color: 'var(--ob-color-text-primary)',
                            borderRadius: 'var(--ob-radius-pill)',
                            padding: '0.3rem 0.85rem',
                            fontSize: '0.78rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                          }}
                        >
                          Focus scenario
                        </button>
                      )
                    ) : (
                      <span
                        style={{
                          borderRadius: 'var(--ob-radius-pill)',
                          background: 'var(--ob-color-border-subtle)',
                          color: 'var(--ob-color-text-secondary)',
                          padding: '0.25rem 0.75rem',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          letterSpacing: '0.08em',
                          textTransform: 'uppercase',
                        }}
                      >
                        Summary
                      </span>
                    )}
                  </div>

                  {/* Inspector / Timestamp / Source */}
                  <div
                    style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      alignItems: 'center',
                      gap: '0.6rem',
                      fontSize: '0.78rem',
                      color: 'var(--ob-color-text-muted)',
                    }}
                  >
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
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                        borderRadius: 'var(--ob-radius-pill)',
                        padding: '0.15rem 0.6rem',
                        fontWeight: 600,
                        letterSpacing: '0.05em',
                        textTransform: 'uppercase',
                        background:
                          row.source === 'manual'
                            ? 'var(--ob-success-50)'
                            : 'rgba(37, 99, 235, 0.12)',
                        color:
                          row.source === 'manual'
                            ? 'var(--ob-success-700)'
                            : 'var(--ob-color-brand-primary)',
                      }}
                    >
                      {row.source === 'manual'
                        ? 'Manual inspection'
                        : 'Automated baseline'}
                    </span>
                  </div>

                  {/* Quick Headline */}
                  {row.quickHeadline && (
                    <p
                      style={{
                        margin: 0,
                        fontSize: '0.92rem',
                        color: 'var(--ob-color-text-secondary)',
                        lineHeight: 1.45,
                      }}
                    >
                      {row.quickHeadline}
                    </p>
                  )}

                  {/* Quick Metrics */}
                  {row.quickMetrics.length > 0 && (
                    <ul
                      style={{
                        margin: 0,
                        padding: 0,
                        listStyle: 'none',
                        display: 'grid',
                        gap: '0.45rem',
                        gridTemplateColumns:
                          'repeat(auto-fit, minmax(120px, 1fr))',
                      }}
                    >
                      {row.quickMetrics.map((metric) => (
                        <li
                          key={`${row.key}-${metric.label}`}
                          style={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '0.15rem',
                          }}
                        >
                          <span
                            style={{
                              fontSize: '0.75rem',
                              color: 'var(--ob-color-text-muted)',
                              letterSpacing: '0.06em',
                              textTransform: 'uppercase',
                            }}
                          >
                            {metric.label}
                          </span>
                          <strong
                            style={{
                              fontSize: '0.95rem',
                              color: 'var(--ob-color-text-primary)',
                            }}
                          >
                            {metric.value}
                          </strong>
                        </li>
                      ))}
                    </ul>
                  )}

                  {/* Condition / Checklist Progress */}
                  <div
                    style={{
                      display: 'grid',
                      gap: '0.75rem',
                      gridTemplateColumns:
                        'repeat(auto-fit, minmax(160px, 1fr))',
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
                          fontSize: '0.75rem',
                          letterSpacing: '0.06em',
                          textTransform: 'uppercase',
                          color: 'var(--ob-color-text-muted)',
                        }}
                      >
                        Condition
                      </span>
                      <span
                        style={{
                          fontSize: '1rem',
                          fontWeight: 600,
                          color: 'var(--ob-color-text-primary)',
                        }}
                      >
                        {row.conditionRating ? row.conditionRating : '—'}
                      </span>
                      <span
                        style={{
                          fontSize: '0.85rem',
                          color: 'var(--ob-color-text-secondary)',
                        }}
                      >
                        {row.conditionScore !== null
                          ? `${row.conditionScore}/100`
                          : '—'}{' '}
                        {row.riskLevel ? `· ${row.riskLevel} risk` : ''}
                      </span>
                    </div>
                    <div
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.25rem',
                      }}
                    >
                      <span
                        style={{
                          fontSize: '0.75rem',
                          letterSpacing: '0.06em',
                          textTransform: 'uppercase',
                          color: 'var(--ob-color-text-muted)',
                        }}
                      >
                        Checklist progress
                      </span>
                      {progressLabel ? (
                        <>
                          <div
                            style={{
                              height: '6px',
                              borderRadius: 'var(--ob-radius-pill)',
                              background: 'var(--ob-color-border-subtle)',
                              overflow: 'hidden',
                            }}
                          >
                            <div
                              style={{
                                width: `${progressPercent ?? 0}%`,
                                height: '100%',
                                background: 'var(--ob-color-brand-primary)',
                                transition: 'width 0.3s ease',
                              }}
                            />
                          </div>
                          <span
                            style={{
                              fontSize: '0.85rem',
                              color: 'var(--ob-color-text-secondary)',
                            }}
                          >
                            {progressLabel}
                            {progressPercent !== null
                              ? ` (${progressPercent}%)`
                              : ''}
                          </span>
                        </>
                      ) : (
                        <span
                          style={{
                            fontSize: '0.85rem',
                            color: 'var(--ob-color-text-muted)',
                          }}
                        >
                          No checklist items yet.
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Primary Insight */}
                  {row.primaryInsight && primaryVisuals && (
                    <div
                      style={{
                        border: `1px solid ${primaryVisuals.border}`,
                        background: primaryVisuals.background,
                        color: primaryVisuals.text,
                        borderRadius: 'var(--ob-radius-sm)',
                        padding: '1rem',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.5rem',
                      }}
                    >
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.4rem',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          letterSpacing: '0.08em',
                          textTransform: 'uppercase',
                        }}
                      >
                        <span
                          style={{
                            width: '0.35rem',
                            height: '0.35rem',
                            borderRadius: 'var(--ob-radius-pill)',
                            background: primaryVisuals.indicator,
                          }}
                        />
                        {primaryVisuals.label}
                      </span>
                      <strong style={{ fontSize: '0.95rem' }}>
                        {row.primaryInsight.title}
                      </strong>
                      <p
                        style={{
                          margin: 0,
                          fontSize: '0.85rem',
                          lineHeight: 1.45,
                        }}
                      >
                        {row.primaryInsight.detail}
                      </p>
                      {row.primaryInsight.specialist && (
                        <span style={{ fontSize: '0.78rem', opacity: 0.85 }}>
                          Specialist:{' '}
                          <strong>{row.primaryInsight.specialist}</strong>
                        </span>
                      )}
                    </div>
                  )}

                  {/* Recommended Action */}
                  {row.recommendedAction && (
                    <p
                      style={{
                        margin: 0,
                        fontSize: '0.85rem',
                        color: 'var(--ob-color-text-secondary)',
                      }}
                    >
                      <strong>Next action:</strong> {row.recommendedAction}
                    </p>
                  )}
                </article>
              )
            })}
          </div>

          {/* Feasibility Signals */}
          {feasibilitySignals.length > 0 && (
            <div
              style={{
                border: '1px solid var(--ob-color-border-subtle)',
                borderRadius: 'var(--ob-radius-sm)',
                padding: '1.5rem',
                background: 'var(--ob-color-bg-surface-elevated)',
                display: 'flex',
                flexDirection: 'column',
                gap: '1.25rem',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  justifyContent: 'space-between',
                  gap: '0.75rem',
                  alignItems: 'center',
                }}
              >
                <h3
                  style={{
                    fontSize: '1.125rem',
                    fontWeight: 600,
                    margin: 0,
                    letterSpacing: '-0.01em',
                  }}
                >
                  Feasibility Signals
                </h3>
                {propertyId && (
                  <Link
                    to={`/app/asset-feasibility?propertyId=${encodeURIComponent(propertyId)}`}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.35rem',
                      padding: '0.45rem 0.9rem',
                      borderRadius: 'var(--ob-radius-pill)',
                      border: '1px solid var(--ob-color-text-primary)',
                      background: 'var(--ob-color-text-primary)',
                      color: 'white',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      textDecoration: 'none',
                    }}
                  >
                    Open Feasibility Workspace →
                  </Link>
                )}
              </div>
              <p
                style={{
                  margin: 0,
                  fontSize: '0.9rem',
                  color: 'var(--ob-color-text-secondary)',
                }}
              >
                Highlights derived from quick analysis. Prioritise these before
                handing off to the feasibility team.
              </p>
              {capturedProperty && (
                <div
                  style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    alignItems: 'center',
                    gap: '0.6rem',
                  }}
                >
                  <button
                    type="button"
                    onClick={() => handleReportExport('json')}
                    disabled={isExportingReport}
                    style={{
                      border: '1px solid var(--ob-color-text-primary)',
                      background: 'var(--ob-color-text-primary)',
                      color: '#fff',
                      borderRadius: 'var(--ob-radius-pill)',
                      padding: '0.45rem 0.95rem',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      cursor: isExportingReport ? 'not-allowed' : 'pointer',
                      transition: 'background 0.2s ease, color 0.2s ease',
                    }}
                  >
                    {isExportingReport ? 'Preparing JSON…' : 'Download JSON'}
                  </button>
                  <button
                    type="button"
                    onClick={() => handleReportExport('pdf')}
                    disabled={isExportingReport}
                    style={{
                      border: '1px solid var(--ob-color-text-primary)',
                      background: 'transparent',
                      color: 'var(--ob-color-text-primary)',
                      borderRadius: 'var(--ob-radius-pill)',
                      padding: '0.45rem 0.95rem',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      cursor: isExportingReport ? 'not-allowed' : 'pointer',
                      transition: 'background 0.2s ease, color 0.2s ease',
                    }}
                  >
                    {isExportingReport ? 'Preparing PDF…' : 'Download PDF'}
                  </button>
                  {reportExportMessage && (
                    <span
                      style={{
                        fontSize: '0.78rem',
                        fontWeight: 500,
                        color: reportExportMessage
                          .toLowerCase()
                          .includes('unable')
                          ? 'var(--ob-error-700)'
                          : 'var(--ob-success-700)',
                      }}
                    >
                      {reportExportMessage}
                    </span>
                  )}
                </div>
              )}
              <div
                style={{
                  display: 'grid',
                  gap: '1rem',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                }}
              >
                {feasibilitySignals.map((entry) => (
                  <div
                    key={entry.scenario}
                    style={{
                      background: 'white',
                      borderRadius: 'var(--ob-radius-sm)',
                      border: '1px solid var(--ob-color-border-subtle)',
                      padding: '1.1rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.6rem',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        justifyContent: 'space-between',
                      }}
                    >
                      <strong
                        style={{
                          fontSize: '0.95rem',
                          color: 'var(--ob-color-text-primary)',
                        }}
                      >
                        {entry.label}
                      </strong>
                    </div>
                    {entry.opportunities.length > 0 && (
                      <div style={{ display: 'grid', gap: '0.35rem' }}>
                        <span
                          style={{
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            color: 'var(--ob-success-700)',
                            textTransform: 'uppercase',
                            letterSpacing: '0.08em',
                          }}
                        >
                          Opportunities
                        </span>
                        <ul
                          style={{
                            margin: 0,
                            paddingLeft: '1.1rem',
                            fontSize: '0.85rem',
                            color: 'var(--ob-success-700)',
                            lineHeight: 1.4,
                          }}
                        >
                          {entry.opportunities.map((message) => (
                            <li key={message}>{message}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {entry.risks.length > 0 && (
                      <div style={{ display: 'grid', gap: '0.35rem' }}>
                        <span
                          style={{
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            color: 'var(--ob-color-status-error-text)',
                            textTransform: 'uppercase',
                            letterSpacing: '0.08em',
                          }}
                        >
                          Risks & Follow-ups
                        </span>
                        <ul
                          style={{
                            margin: 0,
                            paddingLeft: '1.1rem',
                            fontSize: '0.85rem',
                            color: 'var(--ob-error-700)',
                            lineHeight: 1.4,
                          }}
                        >
                          {entry.risks.map((message) => (
                            <li key={message}>{message}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {entry.opportunities.length === 0 &&
                      entry.risks.length === 0 && (
                        <p
                          style={{
                            margin: 0,
                            fontSize: '0.85rem',
                            color: 'var(--ob-color-text-secondary)',
                          }}
                        >
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
            <div
              style={{
                padding: '1.25rem',
                background: 'var(--ob-info-50)',
                borderRadius: 'var(--ob-radius-sm)',
                border: '1px solid var(--ob-info-200)',
              }}
            >
              <strong>Scenario focus:</strong> Viewing{' '}
              {scenarioLookup.get(activeScenario)?.label ??
                formatCategoryName(activeScenario)}{' '}
              metrics. Switch back to "All scenarios" to compare options
              side-by-side.
            </div>
          )}
        </div>
      )}
    </section>
  )
}
