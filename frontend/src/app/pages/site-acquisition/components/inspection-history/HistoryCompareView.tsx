/**
 * History Compare View Component
 *
 * Side-by-side comparison of the two most recent inspection assessments.
 * Shows overall score delta, rating/risk changes, system comparisons,
 * and recommended action diffs.
 */

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
        padding: 'var(--ob-space-125)',
        display: 'grid',
        gap: 'var(--ob-space-065)',
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
          gap: 'var(--ob-space-050)',
          flexWrap: 'wrap',
        }}
      >
        <span
          style={{
            fontSize: 'var(--ob-font-size-xs)',
            fontWeight: 'var(--ob-font-weight-semibold)',
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
      <strong
        style={{
          fontSize: 'var(--ob-font-size-base)',
          fontWeight: 'var(--ob-font-weight-semibold)',
        }}
      >
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
            lineHeight: 'var(--ob-line-height-normal)',
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
          gap: 'var(--ob-space-065)',
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
            gap: 'var(--ob-space-035)',
            borderRadius: 'var(--ob-radius-pill)',
            padding: 'var(--ob-space-025) var(--ob-space-065)',
            fontWeight: 'var(--ob-font-weight-semibold)',
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
              marginTop: 'var(--ob-space-035)',
              fontSize: 'var(--ob-font-size-xs)',
              fontWeight: 'var(--ob-font-weight-semibold)',
              textTransform: 'uppercase',
              color: 'var(--ob-color-text-secondary)',
              letterSpacing: '0.06em',
            }}
          >
            Attachments
          </span>
          <ul
            style={{
              margin: 'var(--ob-space-035) 0 0',
              paddingLeft: 'var(--ob-space-120)',
            }}
          >
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
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-150)',
      }}
    >
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
              gap: 'var(--ob-space-100)',
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
        padding: 'var(--ob-space-150)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-075)',
        background: 'var(--ob-color-surface-brand-subtle)',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: 'var(--ob-space-050)',
        }}
      >
        <span
          style={{
            fontSize: 'var(--ob-font-size-xs)',
            fontWeight: 'var(--ob-font-weight-semibold)',
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
          gap: 'var(--ob-space-050)',
        }}
      >
        <span
          style={{
            fontSize: 'var(--ob-font-size-3xl)',
            fontWeight: 'var(--ob-font-weight-bold)',
          }}
        >
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
            fontWeight: 'var(--ob-font-weight-semibold)',
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
