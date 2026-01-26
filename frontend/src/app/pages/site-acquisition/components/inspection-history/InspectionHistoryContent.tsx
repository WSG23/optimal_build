/**
 * Inspection History Content Component
 *
 * Main container for inspection history display.
 * Includes header with Timeline/Compare toggle and renders the appropriate view.
 * All data and callbacks received via props (no internal state).
 */

import type { RefObject } from 'react'
import type {
  ConditionAssessment,
  DevelopmentScenario,
} from '../../../../../api/siteAcquisition'
import type {
  ScenarioComparisonDatum,
  SystemComparisonEntry,
} from '../../types'
import { HistoryTimelineView } from './HistoryTimelineView'
import {
  HistoryCompareView,
  type ComparisonSummary,
  type RecommendedActionDiff,
} from './HistoryCompareView'

// ============================================================================
// Types
// ============================================================================

export interface InspectionHistoryContentProps {
  // View state
  historyViewMode: 'timeline' | 'compare'
  setHistoryViewMode: (mode: 'timeline' | 'compare') => void

  // Loading / error states
  assessmentHistoryError: string | null
  isLoadingAssessmentHistory: boolean

  // Data
  assessmentHistory: ConditionAssessment[]
  activeScenario: 'all' | DevelopmentScenario

  // Comparison data (from useScenarioComparison hook)
  latestAssessmentEntry: ConditionAssessment | null
  previousAssessmentEntry: ConditionAssessment | null
  comparisonSummary: ComparisonSummary | null
  systemComparisons: SystemComparisonEntry[]
  recommendedActionDiff: RecommendedActionDiff
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
// Component
// ============================================================================

export function InspectionHistoryContent({
  historyViewMode,
  setHistoryViewMode,
  assessmentHistoryError,
  isLoadingAssessmentHistory,
  assessmentHistory,
  activeScenario,
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
}: InspectionHistoryContentProps) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-200)',
      }}
    >
      {/* Header with toggle */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          gap: 'var(--ob-space-200)',
          flexWrap: 'wrap',
        }}
      >
        <div>
          <h3
            style={{
              margin: 0,
              fontSize: '1.0625rem',
              fontWeight: 600,
            }}
          >
            Inspection History
          </h3>
          <p
            style={{
              margin: 'var(--ob-space-50) 0 0',
              fontSize: '0.875rem',
              color: 'var(--ob-color-text-secondary)',
              maxWidth: '480px',
            }}
          >
            Review the developer inspection timeline or compare the two most
            recent assessments side-by-side.
          </p>
        </div>
        <div
          style={{
            display: 'flex',
            gap: 'var(--ob-space-100)',
            flexWrap: 'wrap',
          }}
        >
          <button
            type="button"
            onClick={() => setHistoryViewMode('timeline')}
            style={{
              border: '1px solid var(--ob-color-bg-inverse)',
              background: historyViewMode === 'timeline' ? '#1d1d1f' : 'white',
              color:
                historyViewMode === 'timeline'
                  ? 'white'
                  : 'var(--ob-color-bg-inverse)',
              borderRadius: 'var(--ob-radius-lg)',
              padding: 'var(--ob-space-100) 0.9rem',
              fontSize: '0.8125rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Timeline
          </button>
          <button
            type="button"
            onClick={() => setHistoryViewMode('compare')}
            style={{
              border: '1px solid var(--ob-color-bg-inverse)',
              background: historyViewMode === 'compare' ? '#1d1d1f' : 'white',
              color:
                historyViewMode === 'compare'
                  ? 'white'
                  : 'var(--ob-color-bg-inverse)',
              borderRadius: 'var(--ob-radius-lg)',
              padding: 'var(--ob-space-100) 0.9rem',
              fontSize: '0.8125rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Compare
          </button>
        </div>
      </div>

      {/* Content based on state */}
      {assessmentHistoryError ? (
        <p
          style={{
            margin: 0,
            fontSize: '0.85rem',
            color: '#c53030',
          }}
        >
          {assessmentHistoryError}
        </p>
      ) : isLoadingAssessmentHistory ? (
        <div
          style={{
            padding: 'var(--ob-space-300)',
            textAlign: 'center',
            color: 'var(--ob-color-text-secondary)',
            background: 'var(--ob-color-bg-muted)',
            borderRadius: 'var(--ob-radius-sm)',
          }}
        >
          <p style={{ margin: 0, fontSize: '0.9rem' }}>
            Loading inspection history...
          </p>
        </div>
      ) : assessmentHistory.length === 0 ? (
        <div
          style={{
            padding: 'var(--ob-space-300)',
            textAlign: 'center',
            color: 'var(--ob-color-text-secondary)',
            background: 'var(--ob-color-bg-muted)',
            borderRadius: 'var(--ob-radius-sm)',
          }}
        >
          <p style={{ margin: 0, fontSize: '0.9rem' }}>
            No developer inspections recorded yet.
          </p>
          <p style={{ margin: 'var(--ob-space-50) 0 0', fontSize: '0.8rem' }}>
            Save an inspection above to start the audit trail.
          </p>
        </div>
      ) : historyViewMode === 'timeline' ? (
        <HistoryTimelineView
          assessmentHistory={assessmentHistory}
          activeScenario={activeScenario}
          formatScenarioLabel={formatScenarioLabel}
          formatRecordedTimestamp={formatRecordedTimestamp}
        />
      ) : historyViewMode === 'compare' ? (
        assessmentHistory.length < 2 ||
        !latestAssessmentEntry ||
        !previousAssessmentEntry ? (
          <div
            style={{
              padding: 'var(--ob-space-300)',
              textAlign: 'center',
              color: 'var(--ob-color-text-secondary)',
              background: 'var(--ob-color-bg-muted)',
              borderRadius: 'var(--ob-radius-sm)',
            }}
          >
            <p style={{ margin: 0, fontSize: '0.9rem' }}>
              Capture one more inspection to unlock comparison view.
            </p>
          </div>
        ) : (
          <HistoryCompareView
            latestAssessmentEntry={latestAssessmentEntry}
            previousAssessmentEntry={previousAssessmentEntry}
            comparisonSummary={comparisonSummary}
            systemComparisons={systemComparisons}
            recommendedActionDiff={recommendedActionDiff}
            scenarioComparisonVisible={scenarioComparisonVisible}
            scenarioComparisonRef={scenarioComparisonRef}
            scenarioComparisonTableRows={scenarioComparisonTableRows}
            scenarioAssessments={scenarioAssessments}
            formatScenarioLabel={formatScenarioLabel}
            formatRecordedTimestamp={formatRecordedTimestamp}
          />
        )
      ) : null}
    </div>
  )
}
