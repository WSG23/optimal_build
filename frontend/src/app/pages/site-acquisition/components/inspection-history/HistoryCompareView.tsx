/**
 * History Compare View Component
 *
 * Side-by-side comparison of the two most recent inspection assessments.
 * Shows overall score delta, rating/risk changes, system comparisons,
 * and recommended action diffs.
 */

import type React from 'react'
import { memo } from 'react'
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

import { ScenarioComparisonTable } from './ScenarioComparisonTable'
import { SystemComparisonPanel } from './SystemComparisonPanel'
import { RecommendedActionsDiffPanel } from './RecommendedActionsDiff'
import { ScenarioAssessmentsTable } from './ScenarioAssessmentsTable'

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

const InspectionCard = memo(function InspectionCard({
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
})

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
        <ScenarioComparisonTable
          scenarioComparisonRef={scenarioComparisonRef}
          scenarioComparisonTableRows={scenarioComparisonTableRows}
          formatRecordedTimestamp={formatRecordedTimestamp}
        />
      )}

      {/* Non-scenario comparison view (when !scenarioComparisonVisible) */}
      {!scenarioComparisonVisible && (
        <>
          {/* Overall score summary */}
          {comparisonSummary && (
            <OverallScoreSummary
              latestAssessmentEntry={latestAssessmentEntry}
              previousAssessmentEntry={previousAssessmentEntry}
              comparisonSummary={comparisonSummary}
              formatRecordedTimestamp={formatRecordedTimestamp}
            />
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
          <SystemComparisonPanel systemComparisons={systemComparisons} />

          {/* Recommended action diff */}
          <RecommendedActionsDiffPanel
            recommendedActionDiff={recommendedActionDiff}
          />

          {/* Scenario assessments table (if any) */}
          <ScenarioAssessmentsTable
            scenarioAssessments={scenarioAssessments}
            formatScenarioLabel={formatScenarioLabel}
            formatRecordedTimestamp={formatRecordedTimestamp}
          />
        </>
      )}
    </div>
  )
}

// ============================================================================
// Overall Score Summary (inline - small enough to keep here)
// ============================================================================

interface OverallScoreSummaryProps {
  latestAssessmentEntry: ConditionAssessment
  previousAssessmentEntry: ConditionAssessment
  comparisonSummary: ComparisonSummary
  formatRecordedTimestamp: (timestamp: string | null | undefined) => string
}

function OverallScoreSummary({
  latestAssessmentEntry,
  previousAssessmentEntry,
  comparisonSummary,
  formatRecordedTimestamp,
}: OverallScoreSummaryProps) {
  return (
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
  )
}
