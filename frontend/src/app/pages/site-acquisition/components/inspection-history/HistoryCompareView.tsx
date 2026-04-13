/**
 * History Compare View Component
 *
 * Side-by-side comparison of the two most recent inspection assessments.
 * Shows overall score delta, rating/risk changes, system comparisons,
 * and recommended action diffs.
 */

import type React from 'react'
import type { RefObject } from 'react'
import type {
  ConditionAssessment,
  DevelopmentScenario,
} from '../../../../../api/siteAcquisition'
import type {
  ScenarioComparisonDatum,
  SystemComparisonEntry,
} from '../../types'
import type {
  HistoryComparisonSummary as ComparisonSummary,
  HistoryRecommendedActionDiff as RecommendedActionDiff,
} from '../../utils/historyComparisons'
export type {
  HistoryComparisonSummary as ComparisonSummary,
  HistoryRecommendedActionDiff as RecommendedActionDiff,
} from '../../utils/historyComparisons'

// ============================================================================
// Types
// ============================================================================

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
  formatScenarioLabel: (
    scenario: DevelopmentScenario | 'all' | null | undefined,
  ) => string
  formatRecordedTimestamp: (timestamp: string | null | undefined) => string
}

// ============================================================================
// Sub-components
// ============================================================================

interface InspectionCardProps {
  entry: ConditionAssessment
  label: 'Current inspection' | 'Previous inspection'
  isCurrent: boolean
  formatScenarioLabel: (
    scenario: DevelopmentScenario | 'all' | null | undefined,
  ) => string
  formatRecordedTimestamp: (timestamp: string | null | undefined) => string
}

function InspectionCard({
  entry,
  label,
  isCurrent,
  formatScenarioLabel,
  formatRecordedTimestamp,
}: InspectionCardProps) {
  const labelColor = isCurrent
    ? 'var(--ob-color-brand-500)'
    : 'var(--ob-color-text-secondary)'

  return (
    <div
      style={{
        border: '1px solid var(--ob-color-border-primary)',
        borderRadius: 'var(--ob-radius-sm)',
        padding: '1.25rem',
        display: 'grid',
        gap: '0.6rem',
        background: isCurrent
          ? 'var(--ob-color-surface-brand-subtle)'
          : undefined,
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
            fontSize: 'var(--ob-font-size-xs)',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            color: labelColor,
          }}
        >
          {label}
        </span>
        <span
          style={{
            fontSize: 'var(--ob-font-size-xs)',
            color: 'var(--ob-color-text-secondary)',
          }}
        >
          {formatRecordedTimestamp(entry.recordedAt)}
        </span>
      </div>

      {/* Scenario */}
      <strong style={{ fontSize: 'var(--ob-font-size-base)', fontWeight: 600 }}>
        {formatScenarioLabel(entry.scenario ?? null)}
      </strong>

      {/* Rating / Score / Risk */}
      <span
        style={{
          fontSize: 'var(--ob-font-size-sm)',
          color: 'var(--ob-color-text-primary)',
        }}
      >
        Rating {entry.overallRating} · {entry.overallScore}/100 ·{' '}
        {entry.riskLevel} risk
      </span>

      {/* Summary */}
      {entry.summary && (
        <p
          style={{
            margin: 0,
            fontSize: 'var(--ob-font-size-sm)',
            color: 'var(--ob-color-text-primary)',
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
          fontSize: 'var(--ob-font-size-xs)',
          color: 'var(--ob-color-text-secondary)',
        }}
      >
        <span>
          Inspector:{' '}
          <strong>{entry.inspectorName?.trim() || 'Not recorded'}</strong>
        </span>
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
            background: entry.recordedAt
              ? 'var(--ob-success-50)'
              : 'var(--ob-color-surface-brand-subtle)',
            color: entry.recordedAt
              ? 'var(--ob-success-800)'
              : 'var(--ob-color-brand-600)',
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
              fontSize: 'var(--ob-font-size-xs)',
              fontWeight: 600,
              textTransform: 'uppercase',
              color: 'var(--ob-color-text-secondary)',
              letterSpacing: '0.06em',
            }}
          >
            Attachments
          </span>
          <ul style={{ margin: '0.3rem 0 0', paddingLeft: '1.2rem' }}>
            {entry.attachments.map((attachment, index) => (
              <li
                key={`${isCurrent ? 'latest' : 'previous'}-attachment-${index}`}
                style={{ fontSize: 'var(--ob-font-size-sm)' }}
              >
                {attachment.url ? (
                  <a
                    href={attachment.url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ color: 'var(--ob-color-brand-500)' }}
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
  const highlightedDeltaRows = systemComparisons.filter(
    (entry) => typeof entry.scoreDelta === 'number' && entry.scoreDelta !== 0,
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Scenario comparison table (when visible) */}
      {scenarioComparisonVisible && (
        <div ref={scenarioComparisonRef as React.RefObject<HTMLDivElement>}>
          <details
            open
            style={{
              border: '1px solid var(--ob-color-border-primary)',
              borderRadius: 'var(--ob-radius-sm)',
              background: 'var(--ob-color-bg-primary)',
              overflow: 'hidden',
            }}
          >
            <summary
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '0.75rem',
                padding: '0.85rem 1rem',
                fontSize: 'var(--ob-font-size-sm)',
                fontWeight: 600,
                cursor: 'pointer',
                listStyle: 'none',
                outline: 'none',
              }}
            >
              <span>Detailed comparison table</span>
              <span
                aria-hidden="true"
                style={{
                  fontSize: 'var(--ob-font-size-xs)',
                  color: 'var(--ob-color-text-secondary)',
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                }}
              >
                Collapse
              </span>
            </summary>
            <div
              style={{
                borderTop: '1px solid var(--ob-color-border-primary)',
                overflowX: 'auto',
              }}
            >
              <table
                style={{
                  width: '100%',
                  borderCollapse: 'collapse',
                  minWidth: '960px',
                }}
              >
                <thead style={{ background: 'var(--ob-color-bg-primary)' }}>
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
                          fontSize: 'var(--ob-font-size-xs)',
                          letterSpacing: '0.08em',
                          textTransform: 'uppercase',
                          color: 'var(--ob-color-text-secondary)',
                          borderBottom:
                            '1px solid var(--ob-color-border-primary)',
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
                          borderBottom:
                            '1px solid var(--ob-color-border-primary)',
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
                            <span
                              style={{
                                fontSize: 'var(--ob-font-size-xs)',
                                color: 'var(--ob-color-text-secondary)',
                              }}
                            >
                              {formatRecordedTimestamp(row.recordedAt)}
                            </span>
                          )}
                        </div>
                      </td>
                      <td
                        style={{
                          padding: '0.85rem 1rem',
                          borderBottom:
                            '1px solid var(--ob-color-border-primary)',
                          color: 'var(--ob-color-text-primary)',
                          fontSize: 'var(--ob-font-size-sm)',
                          maxWidth: '220px',
                        }}
                      >
                        {row.quickHeadline ?? '—'}
                      </td>
                      <td
                        style={{
                          padding: '0.85rem 1rem',
                          borderBottom:
                            '1px solid var(--ob-color-border-primary)',
                          color: 'var(--ob-color-text-primary)',
                          fontSize: 'var(--ob-font-size-sm)',
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
                          borderBottom:
                            '1px solid var(--ob-color-border-primary)',
                          color: 'var(--ob-color-text-primary)',
                          fontSize: 'var(--ob-font-size-sm)',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {row.conditionRating ? (
                          <div
                            style={{
                              display: 'flex',
                              flexDirection: 'column',
                              gap: '0.2rem',
                            }}
                          >
                            <strong>{row.conditionRating}</strong>
                            <span>
                              {row.conditionScore !== null
                                ? `${row.conditionScore}/100`
                                : '—'}{' '}
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
                          borderBottom:
                            '1px solid var(--ob-color-border-primary)',
                          color: 'var(--ob-color-text-primary)',
                          fontSize: 'var(--ob-font-size-sm)',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {row.checklistCompleted !== null &&
                        row.checklistTotal !== null
                          ? `${row.checklistCompleted}/${row.checklistTotal}` +
                            (row.checklistPercent !== null
                              ? ` (${row.checklistPercent}%)`
                              : '')
                          : '—'}
                      </td>
                      <td
                        style={{
                          padding: '0.85rem 1rem',
                          borderBottom:
                            '1px solid var(--ob-color-border-primary)',
                          color: 'var(--ob-color-text-primary)',
                          fontSize: 'var(--ob-font-size-sm)',
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
                          borderBottom:
                            '1px solid var(--ob-color-border-primary)',
                          color: 'var(--ob-color-text-primary)',
                          fontSize: 'var(--ob-font-size-sm)',
                          maxWidth: '200px',
                        }}
                      >
                        {row.recommendedAction ?? '—'}
                      </td>
                      <td
                        style={{
                          padding: '0.85rem 1rem',
                          borderBottom:
                            '1px solid var(--ob-color-border-primary)',
                          color: 'var(--ob-color-text-primary)',
                          fontSize: 'var(--ob-font-size-sm)',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {row.inspectorName ?? '—'}
                      </td>
                      <td
                        style={{
                          padding: '0.85rem 1rem',
                          borderBottom:
                            '1px solid var(--ob-color-border-primary)',
                          color: 'var(--ob-color-text-primary)',
                          fontSize: 'var(--ob-font-size-sm)',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {row.source === 'manual'
                          ? 'Manual inspection'
                          : 'Automated baseline'}
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
                border: '1px solid var(--ob-color-border-primary)',
                borderRadius: 'var(--ob-radius-sm)',
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem',
                background: 'var(--ob-color-surface-brand-subtle)',
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
                    fontSize: 'var(--ob-font-size-xs)',
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    color: 'var(--ob-color-brand-500)',
                  }}
                >
                  Overall score
                </span>
                <span
                  style={{
                    fontSize: 'var(--ob-font-size-xs)',
                    color: 'var(--ob-color-text-secondary)',
                  }}
                >
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
                <span
                  style={{
                    fontSize: 'var(--ob-font-size-sm)',
                    color: 'var(--ob-color-text-primary)',
                  }}
                >
                  /100
                </span>
                <span
                  style={{
                    fontSize: 'var(--ob-font-size-sm)',
                    fontWeight: 600,
                    color:
                      comparisonSummary.scoreDelta > 0
                        ? 'var(--ob-success-700)'
                        : comparisonSummary.scoreDelta < 0
                          ? 'var(--ob-error-700)'
                          : 'var(--ob-color-text-secondary)',
                  }}
                >
                  {comparisonSummary.scoreDelta > 0 ? '+' : ''}
                  {comparisonSummary.scoreDelta}
                </span>
              </div>
              <p
                style={{
                  margin: 0,
                  fontSize: 'var(--ob-font-size-sm)',
                  color: 'var(--ob-color-text-primary)',
                }}
              >
                {comparisonSummary.scoreDelta === 0
                  ? 'Overall score held steady vs previous inspection.'
                  : comparisonSummary.scoreDelta > 0
                    ? `Improved by ${comparisonSummary.scoreDelta} points from ${previousAssessmentEntry.overallScore}.`
                    : `Declined by ${Math.abs(comparisonSummary.scoreDelta)} points from ${previousAssessmentEntry.overallScore}.`}
              </p>
              <p
                style={{
                  margin: 0,
                  fontSize: 'var(--ob-font-size-sm)',
                  color: 'var(--ob-color-text-primary)',
                }}
              >
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
              <p
                style={{
                  margin: 0,
                  fontSize: 'var(--ob-font-size-sm)',
                  color: 'var(--ob-color-text-primary)',
                }}
              >
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
              border: '1px solid var(--ob-color-border-primary)',
              borderRadius: 'var(--ob-radius-sm)',
              padding: '1.25rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.75rem',
            }}
          >
            <h4
              style={{
                margin: 0,
                fontSize: 'var(--ob-font-size-sm)',
                fontWeight: 600,
              }}
            >
              System comparison
            </h4>
            <div style={{ display: 'grid', rowGap: '0.6rem' }}>
              {/* Header row */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns:
                    'minmax(160px, 2fr) repeat(3, minmax(110px, 1fr))',
                  fontSize: 'var(--ob-font-size-xs)',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  color: 'var(--ob-color-text-secondary)',
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
                const isImproved =
                  scoreDeltaValue !== null && scoreDeltaValue > 0
                const isDeclined =
                  scoreDeltaValue !== null && scoreDeltaValue < 0
                const rowBackground = isImproved
                  ? 'var(--ob-success-50)'
                  : isDeclined
                    ? 'var(--ob-color-surface-error)'
                    : 'transparent'
                return (
                  <div
                    key={entry.name}
                    style={{
                      display: 'grid',
                      gridTemplateColumns:
                        'minmax(160px, 2fr) repeat(3, minmax(110px, 1fr))',
                      gap: '0.4rem',
                      alignItems: 'center',
                      fontSize: 'var(--ob-font-size-sm)',
                      color: 'var(--ob-color-text-primary)',
                      padding: '0.55rem 0.6rem',
                      borderRadius: 'var(--ob-radius-xs)',
                      background: rowBackground,
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
                            ? 'var(--ob-color-text-secondary)'
                            : scoreDeltaValue > 0
                              ? 'var(--ob-success-700)'
                              : scoreDeltaValue < 0
                                ? 'var(--ob-error-700)'
                                : 'var(--ob-color-text-secondary)',
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
            {highlightedDeltaRows.length > 0 ? (
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '0.5rem',
                  fontSize: 'var(--ob-font-size-xs)',
                  color: 'var(--ob-color-text-secondary)',
                }}
              >
                {highlightedDeltaRows.map((entry) => {
                  const delta = entry.scoreDelta as number
                  return (
                    <span
                      key={`delta-chip-${entry.name}`}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                        padding: '0.2rem 0.5rem',
                        borderRadius: 'var(--ob-radius-pill)',
                        background:
                          delta > 0
                            ? 'var(--ob-success-50)'
                            : 'var(--ob-color-surface-error)',
                        color:
                          delta > 0
                            ? 'var(--ob-success-800)'
                            : 'var(--ob-color-status-error)',
                      }}
                    >
                      <strong>{entry.name}</strong>
                      {delta > 0 ? `+${delta}` : delta}
                    </span>
                  )
                })}
              </div>
            ) : null}
          </div>

          {/* Recommended action diff */}
          <div
            style={{
              border: '1px solid var(--ob-color-border-primary)',
              borderRadius: 'var(--ob-radius-sm)',
              padding: '1.25rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.75rem',
            }}
          >
            <h4
              style={{
                margin: 0,
                fontSize: 'var(--ob-font-size-sm)',
                fontWeight: 600,
              }}
            >
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
                    fontSize: 'var(--ob-font-size-sm)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    color: 'var(--ob-success-700)',
                  }}
                >
                  New this cycle
                </strong>
                {recommendedActionDiff.newActions.length > 0 ? (
                  <ul
                    style={{
                      margin: '0.4rem 0 0',
                      paddingLeft: '1.1rem',
                      fontSize: 'var(--ob-font-size-sm)',
                      color: 'var(--ob-color-text-primary)',
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
                      fontSize: 'var(--ob-font-size-sm)',
                      color: 'var(--ob-color-text-secondary)',
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
                    fontSize: 'var(--ob-font-size-sm)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    color: 'var(--ob-color-brand-500)',
                  }}
                >
                  Completed / Cleared
                </strong>
                {recommendedActionDiff.clearedActions.length > 0 ? (
                  <ul
                    style={{
                      margin: '0.4rem 0 0',
                      paddingLeft: '1.1rem',
                      fontSize: 'var(--ob-font-size-sm)',
                      color: 'var(--ob-color-text-primary)',
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
                      fontSize: 'var(--ob-font-size-sm)',
                      color: 'var(--ob-color-text-secondary)',
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
                border: '1px solid var(--ob-color-border-primary)',
                borderRadius: 'var(--ob-radius-sm)',
                overflow: 'hidden',
              }}
            >
              <h4
                style={{
                  margin: 0,
                  padding: '1rem 1.25rem',
                  fontSize: 'var(--ob-font-size-sm)',
                  fontWeight: 600,
                  background: 'var(--ob-color-surface-secondary)',
                  borderBottom: '1px solid var(--ob-color-border-primary)',
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
                      {[
                        'Scenario',
                        'Recorded',
                        'Rating',
                        'Score',
                        'Risk',
                        'Inspector',
                      ].map((header) => (
                        <th
                          key={header}
                          style={{
                            textAlign: 'left',
                            padding: '0.75rem 1rem',
                            borderBottom:
                              '1px solid var(--ob-color-border-primary)',
                            fontWeight: 600,
                            fontSize: 'var(--ob-font-size-sm)',
                            letterSpacing: '0.04em',
                            textTransform: 'uppercase',
                          }}
                        >
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {scenarioAssessments.map((assessment, index) => (
                      <tr
                        key={`scenario-assessment-${assessment.scenario ?? index}`}
                      >
                        <td
                          style={{
                            padding: '0.75rem 1rem',
                            borderBottom:
                              '1px solid var(--ob-color-border-primary)',
                            fontWeight: 600,
                          }}
                        >
                          {formatScenarioLabel(assessment.scenario)}
                        </td>
                        <td
                          style={{
                            padding: '0.75rem 1rem',
                            borderBottom:
                              '1px solid var(--ob-color-border-primary)',
                            color: 'var(--ob-color-text-secondary)',
                            fontSize: 'var(--ob-font-size-sm)',
                          }}
                        >
                          {formatRecordedTimestamp(assessment.recordedAt)}
                        </td>
                        <td
                          style={{
                            padding: '0.75rem 1rem',
                            borderBottom:
                              '1px solid var(--ob-color-border-primary)',
                            fontWeight: 600,
                          }}
                        >
                          {assessment.overallRating}
                        </td>
                        <td
                          style={{
                            padding: '0.75rem 1rem',
                            borderBottom:
                              '1px solid var(--ob-color-border-primary)',
                          }}
                        >
                          {assessment.overallScore}/100
                        </td>
                        <td
                          style={{
                            padding: '0.75rem 1rem',
                            borderBottom:
                              '1px solid var(--ob-color-border-primary)',
                            textTransform: 'capitalize',
                          }}
                        >
                          {assessment.riskLevel}
                        </td>
                        <td
                          style={{
                            padding: '0.75rem 1rem',
                            borderBottom:
                              '1px solid var(--ob-color-border-primary)',
                            color: 'var(--ob-color-text-secondary)',
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
