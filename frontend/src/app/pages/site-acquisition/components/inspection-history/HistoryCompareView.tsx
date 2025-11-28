/**
 * History Compare View Component
 *
 * Side-by-side comparison of the two most recent inspection assessments.
 * Shows overall score delta, rating/risk changes, system comparisons,
 * and recommended action diffs.
 */

import type React from 'react'
import type { RefObject } from 'react'
import type { ConditionAssessment, DevelopmentScenario } from '../../../../../api/siteAcquisition'
import type { ScenarioComparisonDatum, SystemComparisonEntry } from '../../types'

// ============================================================================
// Types
// ============================================================================

export interface ComparisonSummary {
  scoreDelta: number
  ratingTrend: 'improved' | 'declined' | 'same' | 'changed'
  riskTrend: 'improved' | 'declined' | 'same' | 'changed'
  ratingChanged: boolean
  riskChanged: boolean
}

export interface RecommendedActionDiff {
  newActions: string[]
  clearedActions: string[]
}

export interface HistoryCompareViewProps {
  // Assessment data
  latestAssessmentEntry: ConditionAssessment
  previousAssessmentEntry: ConditionAssessment

  // Comparison data from hook
  comparisonSummary: ComparisonSummary | null
  systemComparisons: SystemComparisonEntry[]
  recommendedActionDiff: RecommendedActionDiff

  // Scenario comparison (optional - shown when scenarioComparisonVisible)
  scenarioComparisonVisible: boolean
  scenarioComparisonRef: RefObject<HTMLDivElement | null>
  scenarioComparisonTableRows: ScenarioComparisonDatum[]
  scenarioAssessments: ConditionAssessment[]

  // Formatters (stable callbacks)
  formatScenarioLabel: (scenario: DevelopmentScenario | 'all' | null | undefined) => string
  formatRecordedTimestamp: (timestamp: string | null | undefined) => string
}

// ============================================================================
// Sub-components
// ============================================================================

interface InspectionCardProps {
  entry: ConditionAssessment
  label: 'Current inspection' | 'Previous inspection'
  isCurrent: boolean
  formatScenarioLabel: (scenario: DevelopmentScenario | 'all' | null | undefined) => string
  formatRecordedTimestamp: (timestamp: string | null | undefined) => string
}

function InspectionCard({
  entry,
  label,
  isCurrent,
  formatScenarioLabel,
  formatRecordedTimestamp,
}: InspectionCardProps) {
  const labelColor = isCurrent ? '#0a84ff' : '#6e6e73'

  return (
    <div
      style={{
        border: '1px solid #e5e5e7',
        borderRadius: '10px',
        padding: '1.25rem',
        display: 'grid',
        gap: '0.6rem',
        background: isCurrent ? '#f0f9ff' : undefined,
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          gap: '0.5rem',
          flexWrap: 'wrap',
        }}
      >
        <span
          style={{
            fontSize: '0.75rem',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            color: labelColor,
          }}
        >
          {label}
        </span>
        <span style={{ fontSize: '0.8125rem', color: '#6e6e73' }}>
          {formatRecordedTimestamp(entry.recordedAt)}
        </span>
      </div>

      {/* Scenario */}
      <strong style={{ fontSize: '1rem', fontWeight: 600 }}>
        {formatScenarioLabel(entry.scenario ?? null)}
      </strong>

      {/* Rating / Score / Risk */}
      <span style={{ fontSize: '0.9rem', color: '#3a3a3c' }}>
        Rating {entry.overallRating} · {entry.overallScore}/100 · {entry.riskLevel} risk
      </span>

      {/* Summary */}
      {entry.summary && (
        <p
          style={{
            margin: 0,
            fontSize: '0.875rem',
            color: '#3a3a3c',
            lineHeight: 1.5,
          }}
        >
          {entry.summary}
        </p>
      )}

      {/* Inspector & Source */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '0.6rem',
          fontSize: '0.78rem',
          color: '#475569',
        }}
      >
        <span>
          Inspector: <strong>{entry.inspectorName?.trim() || 'Not recorded'}</strong>
        </span>
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.3rem',
            borderRadius: '9999px',
            padding: '0.15rem 0.6rem',
            fontWeight: 600,
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
            background: entry.recordedAt ? '#dcfce7' : 'rgba(37, 99, 235, 0.12)',
            color: entry.recordedAt ? '#166534' : '#1d4ed8',
          }}
        >
          {entry.recordedAt ? 'Manual inspection' : 'Automated baseline'}
        </span>
      </div>

      {/* Attachments */}
      {entry.attachments.length > 0 && (
        <div>
          <span
            style={{
              display: 'inline-block',
              marginTop: '0.35rem',
              fontSize: '0.75rem',
              fontWeight: 600,
              textTransform: 'uppercase',
              color: '#6e6e73',
              letterSpacing: '0.06em',
            }}
          >
            Attachments
          </span>
          <ul style={{ margin: '0.3rem 0 0', paddingLeft: '1.2rem' }}>
            {entry.attachments.map((attachment, index) => (
              <li
                key={`${isCurrent ? 'latest' : 'previous'}-attachment-${index}`}
                style={{ fontSize: '0.85rem' }}
              >
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
  )
}

// ============================================================================
// Main Component
// ============================================================================

export function HistoryCompareView({
  latestAssessmentEntry,
  previousAssessmentEntry,
  comparisonSummary,
  systemComparisons,
  recommendedActionDiff,
  scenarioComparisonVisible,
  scenarioComparisonRef,
  scenarioComparisonTableRows,
  scenarioAssessments,
  formatScenarioLabel,
  formatRecordedTimestamp,
}: HistoryCompareViewProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Scenario comparison table (when visible) */}
      {scenarioComparisonVisible && (
        <div ref={scenarioComparisonRef as React.RefObject<HTMLDivElement>}>
          <details
            open
            style={{
              border: '1px solid #e5e5e7',
              borderRadius: '14px',
              background: 'white',
              overflow: 'hidden',
            }}
          >
            <summary
              style={{
                padding: '0.85rem 1rem',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
                listStyle: 'none',
                outline: 'none',
              }}
            >
              Detailed comparison table
            </summary>
            <div style={{ borderTop: '1px solid #e5e5e7', overflowX: 'auto' }}>
              <table
                style={{
                  width: '100%',
                  borderCollapse: 'collapse',
                  minWidth: '960px',
                }}
              >
                <thead style={{ background: '#ffffff' }}>
                  <tr>
                    {[
                      'Scenario',
                      'Quick headline',
                      'Key metrics',
                      'Condition',
                      'Checklist',
                      'Key insight',
                      'Next action',
                      'Inspector',
                      'Source',
                    ].map((header) => (
                      <th
                        key={header}
                        style={{
                          textAlign: 'left',
                          padding: '0.85rem 1rem',
                          fontSize: '0.75rem',
                          letterSpacing: '0.08em',
                          textTransform: 'uppercase',
                          color: '#6e6e73',
                          borderBottom: '1px solid #ebebf0',
                        }}
                      >
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {scenarioComparisonTableRows.map((row) => (
                    <tr key={`comparison-table-${row.key}`}>
                      <td
                        style={{
                          padding: '0.85rem 1rem',
                          borderBottom: '1px solid #f4f4f8',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        <div
                          style={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '0.2rem',
                            alignItems: 'flex-start',
                          }}
                        >
                          <span style={{ fontWeight: 600 }}>{row.label}</span>
                          {row.recordedAt && (
                            <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                              {formatRecordedTimestamp(row.recordedAt)}
                            </span>
                          )}
                        </div>
                      </td>
                      <td
                        style={{
                          padding: '0.85rem 1rem',
                          borderBottom: '1px solid #f4f4f8',
                          color: '#3a3a3c',
                          fontSize: '0.9rem',
                          maxWidth: '220px',
                        }}
                      >
                        {row.quickHeadline ?? '—'}
                      </td>
                      <td
                        style={{
                          padding: '0.85rem 1rem',
                          borderBottom: '1px solid #f4f4f8',
                          color: '#3a3a3c',
                          fontSize: '0.9rem',
                          maxWidth: '220px',
                        }}
                      >
                        {row.quickMetrics.length === 0 ? (
                          '—'
                        ) : (
                          <ul
                            style={{
                              margin: 0,
                              paddingLeft: '1.1rem',
                              display: 'flex',
                              flexDirection: 'column',
                              gap: '0.2rem',
                            }}
                          >
                            {row.quickMetrics.map((metric) => (
                              <li key={`${row.key}-${metric.label}`}>
                                {metric.label}: {metric.value}
                              </li>
                            ))}
                          </ul>
                        )}
                      </td>
                      <td
                        style={{
                          padding: '0.85rem 1rem',
                          borderBottom: '1px solid #f4f4f8',
                          color: '#3a3a3c',
                          fontSize: '0.9rem',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {row.conditionRating ? (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                            <strong>{row.conditionRating}</strong>
                            <span>
                              {row.conditionScore !== null ? `${row.conditionScore}/100` : '—'}{' '}
                              {row.riskLevel ? `· ${row.riskLevel} risk` : ''}
                            </span>
                          </div>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td
                        style={{
                          padding: '0.85rem 1rem',
                          borderBottom: '1px solid #f4f4f8',
                          color: '#3a3a3c',
                          fontSize: '0.9rem',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {row.checklistCompleted !== null && row.checklistTotal !== null
                          ? `${row.checklistCompleted}/${row.checklistTotal}` +
                            (row.checklistPercent !== null ? ` (${row.checklistPercent}%)` : '')
                          : '—'}
                      </td>
                      <td
                        style={{
                          padding: '0.85rem 1rem',
                          borderBottom: '1px solid #f4f4f8',
                          color: '#3a3a3c',
                          fontSize: '0.9rem',
                          maxWidth: '240px',
                        }}
                      >
                        {row.primaryInsight ? (
                          <>
                            <strong>{row.primaryInsight.title}</strong>
                            <div>{row.primaryInsight.detail}</div>
                          </>
                        ) : row.insights.length > 0 ? (
                          <div>{row.insights[0].title}</div>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td
                        style={{
                          padding: '0.85rem 1rem',
                          borderBottom: '1px solid #f4f4f8',
                          color: '#3a3a3c',
                          fontSize: '0.9rem',
                          maxWidth: '200px',
                        }}
                      >
                        {row.recommendedAction ?? '—'}
                      </td>
                      <td
                        style={{
                          padding: '0.85rem 1rem',
                          borderBottom: '1px solid #f4f4f8',
                          color: '#3a3a3c',
                          fontSize: '0.9rem',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {row.inspectorName ?? '—'}
                      </td>
                      <td
                        style={{
                          padding: '0.85rem 1rem',
                          borderBottom: '1px solid #f4f4f8',
                          color: '#3a3a3c',
                          fontSize: '0.9rem',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {row.source === 'manual' ? 'Manual inspection' : 'Automated baseline'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </div>
      )}

      {/* Non-scenario comparison view (when !scenarioComparisonVisible) */}
      {!scenarioComparisonVisible && (
        <>
          {/* Overall score summary */}
          {comparisonSummary && (
            <div
              style={{
                border: '1px solid #e5e5e7',
                borderRadius: '12px',
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem',
                background: '#f0f9ff',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  flexWrap: 'wrap',
                  gap: '0.5rem',
                }}
              >
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    color: '#0a84ff',
                  }}
                >
                  Overall score
                </span>
                <span style={{ fontSize: '0.8125rem', color: '#6e6e73' }}>
                  {formatRecordedTimestamp(latestAssessmentEntry.recordedAt)}
                </span>
              </div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'baseline',
                  gap: '0.5rem',
                }}
              >
                <span style={{ fontSize: '2rem', fontWeight: 700 }}>
                  {latestAssessmentEntry.overallScore}
                </span>
                <span style={{ fontSize: '0.85rem', color: '#1d1d1f' }}>/100</span>
                <span
                  style={{
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    color:
                      comparisonSummary.scoreDelta > 0
                        ? '#15803d'
                        : comparisonSummary.scoreDelta < 0
                          ? '#c53030'
                          : '#6e6e73',
                  }}
                >
                  {comparisonSummary.scoreDelta > 0 ? '+' : ''}
                  {comparisonSummary.scoreDelta}
                </span>
              </div>
              <p style={{ margin: 0, fontSize: '0.875rem', color: '#3a3a3c' }}>
                {comparisonSummary.scoreDelta === 0
                  ? 'Overall score held steady vs previous inspection.'
                  : comparisonSummary.scoreDelta > 0
                    ? `Improved by ${comparisonSummary.scoreDelta} points from ${previousAssessmentEntry.overallScore}.`
                    : `Declined by ${Math.abs(comparisonSummary.scoreDelta)} points from ${previousAssessmentEntry.overallScore}.`}
              </p>
              <p style={{ margin: 0, fontSize: '0.875rem', color: '#3a3a3c' }}>
                {comparisonSummary.ratingChanged
                  ? `Rating ${
                      comparisonSummary.ratingTrend === 'improved'
                        ? 'improved'
                        : comparisonSummary.ratingTrend === 'declined'
                          ? 'declined'
                          : 'changed'
                    } from ${previousAssessmentEntry.overallRating} to ${latestAssessmentEntry.overallRating}.`
                  : 'Rating unchanged from previous inspection.'}
              </p>
              <p style={{ margin: 0, fontSize: '0.875rem', color: '#3a3a3c' }}>
                {comparisonSummary.riskChanged
                  ? `Risk level ${
                      comparisonSummary.riskTrend === 'improved'
                        ? 'eased'
                        : comparisonSummary.riskTrend === 'declined'
                          ? 'intensified'
                          : 'changed'
                    } from ${previousAssessmentEntry.riskLevel} to ${latestAssessmentEntry.riskLevel}.`
                  : 'Risk level unchanged.'}
              </p>
            </div>
          )}

          {/* Current / Previous inspection cards */}
          <div
            style={{
              display: 'grid',
              gap: '1rem',
              gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            }}
          >
            <InspectionCard
              entry={latestAssessmentEntry}
              label="Current inspection"
              isCurrent={true}
              formatScenarioLabel={formatScenarioLabel}
              formatRecordedTimestamp={formatRecordedTimestamp}
            />
            <InspectionCard
              entry={previousAssessmentEntry}
              label="Previous inspection"
              isCurrent={false}
              formatScenarioLabel={formatScenarioLabel}
              formatRecordedTimestamp={formatRecordedTimestamp}
            />
          </div>

          {/* System comparison table */}
          <div
            style={{
              border: '1px solid #e5e5e7',
              borderRadius: '10px',
              padding: '1.25rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.75rem',
            }}
          >
            <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 600 }}>
              System comparison
            </h4>
            <div style={{ display: 'grid', rowGap: '0.6rem' }}>
              {/* Header row */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'minmax(160px, 2fr) repeat(3, minmax(110px, 1fr))',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  color: '#6e6e73',
                }}
              >
                <span>System</span>
                <span>Current</span>
                <span>Previous</span>
                <span>Delta Score</span>
              </div>

              {/* System rows */}
              {systemComparisons.map((entry) => {
                const scoreDeltaValue =
                  typeof entry.scoreDelta === 'number' ? entry.scoreDelta : null
                return (
                  <div
                    key={entry.name}
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'minmax(160px, 2fr) repeat(3, minmax(110px, 1fr))',
                      gap: '0.4rem',
                      alignItems: 'center',
                      fontSize: '0.85rem',
                      color: '#3a3a3c',
                    }}
                  >
                    <span style={{ fontWeight: 600 }}>{entry.name}</span>
                    <span>
                      {entry.latest
                        ? `${entry.latest.rating} · ${entry.latest.score}/100`
                        : '—'}
                    </span>
                    <span>
                      {entry.previous
                        ? `${entry.previous.rating} · ${entry.previous.score}/100`
                        : '—'}
                    </span>
                    <span
                      style={{
                        fontWeight: 600,
                        color:
                          scoreDeltaValue === null
                            ? '#6e6e73'
                            : scoreDeltaValue > 0
                              ? '#15803d'
                              : scoreDeltaValue < 0
                                ? '#c53030'
                                : '#6e6e73',
                      }}
                    >
                      {scoreDeltaValue === null
                        ? '—'
                        : scoreDeltaValue > 0
                          ? `+${scoreDeltaValue}`
                          : scoreDeltaValue}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Recommended action diff */}
          <div
            style={{
              border: '1px solid #e5e5e7',
              borderRadius: '10px',
              padding: '1.25rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.75rem',
            }}
          >
            <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 600 }}>
              Recommended actions diff
            </h4>
            <div
              style={{
                display: 'grid',
                gap: '0.75rem',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              }}
            >
              {/* New actions */}
              <div>
                <strong
                  style={{
                    fontSize: '0.85rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    color: '#15803d',
                  }}
                >
                  New this cycle
                </strong>
                {recommendedActionDiff.newActions.length > 0 ? (
                  <ul
                    style={{
                      margin: '0.4rem 0 0',
                      paddingLeft: '1.1rem',
                      fontSize: '0.85rem',
                      color: '#3a3a3c',
                      lineHeight: 1.4,
                    }}
                  >
                    {recommendedActionDiff.newActions.map((action) => (
                      <li key={action}>{action}</li>
                    ))}
                  </ul>
                ) : (
                  <p
                    style={{
                      margin: '0.35rem 0 0',
                      fontSize: '0.825rem',
                      color: '#6e6e73',
                    }}
                  >
                    No new actions added.
                  </p>
                )}
              </div>

              {/* Cleared actions */}
              <div>
                <strong
                  style={{
                    fontSize: '0.85rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    color: '#0071e3',
                  }}
                >
                  Completed / Cleared
                </strong>
                {recommendedActionDiff.clearedActions.length > 0 ? (
                  <ul
                    style={{
                      margin: '0.4rem 0 0',
                      paddingLeft: '1.1rem',
                      fontSize: '0.85rem',
                      color: '#3a3a3c',
                      lineHeight: 1.4,
                    }}
                  >
                    {recommendedActionDiff.clearedActions.map((action) => (
                      <li key={action}>{action}</li>
                    ))}
                  </ul>
                ) : (
                  <p
                    style={{
                      margin: '0.35rem 0 0',
                      fontSize: '0.825rem',
                      color: '#6e6e73',
                    }}
                  >
                    No actions cleared.
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Scenario assessments table (if any) */}
          {scenarioAssessments.length > 0 && (
            <div
              style={{
                border: '1px solid #e5e5e7',
                borderRadius: '10px',
                overflow: 'hidden',
              }}
            >
              <h4
                style={{
                  margin: 0,
                  padding: '1rem 1.25rem',
                  fontSize: '0.95rem',
                  fontWeight: 600,
                  background: '#f5f5f7',
                  borderBottom: '1px solid #e5e5e7',
                }}
              >
                Scenario assessments
              </h4>
              <div style={{ overflowX: 'auto' }}>
                <table
                  style={{
                    width: '100%',
                    borderCollapse: 'collapse',
                    minWidth: '600px',
                  }}
                >
                  <thead>
                    <tr>
                      {['Scenario', 'Recorded', 'Rating', 'Score', 'Risk', 'Inspector'].map(
                        (header) => (
                          <th
                            key={header}
                            style={{
                              textAlign: 'left',
                              padding: '0.75rem 1rem',
                              borderBottom: '1px solid #e5e5e7',
                              fontWeight: 600,
                              fontSize: '0.8rem',
                              letterSpacing: '0.04em',
                              textTransform: 'uppercase',
                            }}
                          >
                            {header}
                          </th>
                        ),
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {scenarioAssessments.map((assessment, index) => (
                      <tr key={`scenario-assessment-${assessment.scenario ?? index}`}>
                        <td
                          style={{
                            padding: '0.75rem 1rem',
                            borderBottom: '1px solid #f4f4f8',
                            fontWeight: 600,
                          }}
                        >
                          {formatScenarioLabel(assessment.scenario)}
                        </td>
                        <td
                          style={{
                            padding: '0.75rem 1rem',
                            borderBottom: '1px solid #f4f4f8',
                            color: '#6e6e73',
                            fontSize: '0.85rem',
                          }}
                        >
                          {formatRecordedTimestamp(assessment.recordedAt)}
                        </td>
                        <td
                          style={{
                            padding: '0.75rem 1rem',
                            borderBottom: '1px solid #f4f4f8',
                            fontWeight: 600,
                          }}
                        >
                          {assessment.overallRating}
                        </td>
                        <td
                          style={{
                            padding: '0.75rem 1rem',
                            borderBottom: '1px solid #f4f4f8',
                          }}
                        >
                          {assessment.overallScore}/100
                        </td>
                        <td
                          style={{
                            padding: '0.75rem 1rem',
                            borderBottom: '1px solid #f4f4f8',
                            textTransform: 'capitalize',
                          }}
                        >
                          {assessment.riskLevel}
                        </td>
                        <td
                          style={{
                            padding: '0.75rem 1rem',
                            borderBottom: '1px solid #f4f4f8',
                            color: '#6e6e73',
                          }}
                        >
                          {assessment.inspectorName?.trim() || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
