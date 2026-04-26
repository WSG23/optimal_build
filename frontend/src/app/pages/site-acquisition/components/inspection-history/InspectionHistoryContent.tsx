/**
 * Inspection History Content Component
 *
 * Main container for inspection history display.
 * Includes header with Timeline/Compare toggle and renders the appropriate view.
 */

import { Skeleton } from '@mui/material'
import {
  useEffect,
  useMemo,
  useState,
  type KeyboardEvent,
  type RefObject,
} from 'react'
import type {
  ConditionAssessment,
  DevelopmentScenario,
} from '../../../../../api/siteAcquisition'
import type {
  ScenarioComparisonDatum,
  SystemComparisonEntry,
} from '../../types'
import {
  buildHistoryComparisonSummary,
  buildHistoryRecommendedActionDiff,
  buildHistorySystemComparisons,
} from '../../utils/historyComparisons'
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

export function InspectionHistoryContent(props: InspectionHistoryContentProps) {
  const {
    historyViewMode,
    setHistoryViewMode,
    assessmentHistoryError,
    isLoadingAssessmentHistory,
    assessmentHistory,
    activeScenario,
    latestAssessmentEntry,
    previousAssessmentEntry,
    scenarioComparisonVisible,
    scenarioComparisonRef,
    scenarioComparisonTableRows,
    scenarioAssessments,
    formatScenarioLabel,
    formatRecordedTimestamp,
  } = props

  const comparisonOptions = useMemo(
    () =>
      assessmentHistory.map((entry, index) => ({
        value: String(index),
        label: `${index === 0 ? 'Most recent' : `Inspection ${index + 1}`} · ${formatScenarioLabel(
          entry.scenario,
        )} · ${formatRecordedTimestamp(entry.recordedAt)}`,
      })),
    [assessmentHistory, formatRecordedTimestamp, formatScenarioLabel],
  )

  const [currentComparisonIndex, setCurrentComparisonIndex] = useState('0')
  const [baselineComparisonIndex, setBaselineComparisonIndex] = useState('1')
  const [comparisonCopyStatus, setComparisonCopyStatus] = useState<
    'idle' | 'copied' | 'failed'
  >('idle')
  const [timelineSortMode, setTimelineSortMode] = useState<
    'newest' | 'oldest' | 'highest-score' | 'lowest-score'
  >('newest')

  useEffect(() => {
    setCurrentComparisonIndex('0')
    setBaselineComparisonIndex(assessmentHistory.length > 1 ? '1' : '0')
  }, [assessmentHistory])

  const selectedCurrentAssessment =
    assessmentHistory[Number(currentComparisonIndex)] ?? latestAssessmentEntry
  const selectedBaselineAssessment =
    assessmentHistory[Number(baselineComparisonIndex)] ??
    previousAssessmentEntry
  const comparisonSelectionInvalid =
    !selectedCurrentAssessment ||
    !selectedBaselineAssessment ||
    currentComparisonIndex === baselineComparisonIndex

  const selectedComparisonSummary = useMemo(() => {
    return buildHistoryComparisonSummary(
      selectedCurrentAssessment,
      selectedBaselineAssessment,
    ) as ComparisonSummary | null
  }, [selectedBaselineAssessment, selectedCurrentAssessment])

  const selectedRecommendedActionDiff = useMemo(() => {
    return buildHistoryRecommendedActionDiff(
      selectedCurrentAssessment,
      selectedBaselineAssessment,
    )
  }, [selectedBaselineAssessment, selectedCurrentAssessment])

  const selectedSystemComparisons = useMemo<SystemComparisonEntry[]>(() => {
    return buildHistorySystemComparisons(
      selectedCurrentAssessment,
      selectedBaselineAssessment,
    )
  }, [selectedBaselineAssessment, selectedCurrentAssessment])

  const sortedTimelineHistory = useMemo(() => {
    const items = [...assessmentHistory]
    switch (timelineSortMode) {
      case 'oldest':
        return items.reverse()
      case 'highest-score':
        return items.sort((a, b) => b.overallScore - a.overallScore)
      case 'lowest-score':
        return items.sort((a, b) => a.overallScore - b.overallScore)
      case 'newest':
      default:
        return items
    }
  }, [assessmentHistory, timelineSortMode])

  const comparisonExportText = useMemo(() => {
    if (
      comparisonSelectionInvalid ||
      !selectedCurrentAssessment ||
      !selectedBaselineAssessment
    ) {
      return ''
    }

    const lines = [
      `Inspection comparison`,
      `Current: ${formatScenarioLabel(selectedCurrentAssessment.scenario)} | ${formatRecordedTimestamp(selectedCurrentAssessment.recordedAt)} | ${selectedCurrentAssessment.overallRating} | ${selectedCurrentAssessment.overallScore}/100 | ${selectedCurrentAssessment.riskLevel} risk`,
      `Baseline: ${formatScenarioLabel(selectedBaselineAssessment.scenario)} | ${formatRecordedTimestamp(selectedBaselineAssessment.recordedAt)} | ${selectedBaselineAssessment.overallRating} | ${selectedBaselineAssessment.overallScore}/100 | ${selectedBaselineAssessment.riskLevel} risk`,
      '',
    ]

    if (selectedComparisonSummary) {
      lines.push(
        `Score delta: ${selectedComparisonSummary.scoreDelta > 0 ? '+' : ''}${selectedComparisonSummary.scoreDelta}`,
        `Rating trend: ${selectedComparisonSummary.ratingChanged ? `${selectedBaselineAssessment.overallRating} -> ${selectedCurrentAssessment.overallRating}` : 'unchanged'}`,
        `Risk trend: ${selectedComparisonSummary.riskChanged ? `${selectedBaselineAssessment.riskLevel} -> ${selectedCurrentAssessment.riskLevel}` : 'unchanged'}`,
        '',
      )
    }

    if (selectedSystemComparisons.length > 0) {
      lines.push('System comparison')
      selectedSystemComparisons.forEach((entry) => {
        lines.push(
          `${entry.name}: ${entry.latest ? `${entry.latest.rating} ${entry.latest.score}/100` : '—'} | ${entry.previous ? `${entry.previous.rating} ${entry.previous.score}/100` : '—'} | delta ${typeof entry.scoreDelta === 'number' ? entry.scoreDelta : '—'}`,
        )
      })
      lines.push('')
    }

    lines.push('New actions')
    if (selectedRecommendedActionDiff.newActions.length === 0) {
      lines.push('None')
    } else {
      selectedRecommendedActionDiff.newActions.forEach((action) => {
        lines.push(`- ${action}`)
      })
    }
    lines.push('')
    lines.push('Cleared actions')
    if (selectedRecommendedActionDiff.clearedActions.length === 0) {
      lines.push('None')
    } else {
      selectedRecommendedActionDiff.clearedActions.forEach((action) => {
        lines.push(`- ${action}`)
      })
    }

    return lines.join('\n')
  }, [
    comparisonSelectionInvalid,
    formatRecordedTimestamp,
    formatScenarioLabel,
    selectedBaselineAssessment,
    selectedComparisonSummary,
    selectedCurrentAssessment,
    selectedRecommendedActionDiff.clearedActions,
    selectedRecommendedActionDiff.newActions,
    selectedSystemComparisons,
  ])

  const moveComparisonIndex = (
    currentValue: string,
    setter: (value: string) => void,
    direction: -1 | 1,
  ) => {
    const currentIndex = Number(currentValue)
    const nextIndex = Math.max(
      0,
      Math.min(assessmentHistory.length - 1, currentIndex + direction),
    )
    setter(String(nextIndex))
  }

  const handleViewToggleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (
      event.key !== 'ArrowLeft' &&
      event.key !== 'ArrowRight' &&
      event.key !== 'Home' &&
      event.key !== 'End'
    ) {
      return
    }

    event.preventDefault()

    if (event.key === 'Home') {
      setHistoryViewMode('timeline')
      return
    }

    if (event.key === 'End') {
      setHistoryViewMode('compare')
      return
    }

    setHistoryViewMode(historyViewMode === 'timeline' ? 'compare' : 'timeline')
  }

  const handleCompareControlsKeyDown = (
    event: KeyboardEvent<HTMLDivElement>,
  ) => {
    if (event.altKey && event.key === 'ArrowLeft') {
      event.preventDefault()
      moveComparisonIndex(
        baselineComparisonIndex,
        setBaselineComparisonIndex,
        -1,
      )
      return
    }

    if (event.altKey && event.key === 'ArrowRight') {
      event.preventDefault()
      moveComparisonIndex(
        baselineComparisonIndex,
        setBaselineComparisonIndex,
        1,
      )
      return
    }

    if (event.shiftKey && event.key === 'ArrowLeft') {
      event.preventDefault()
      moveComparisonIndex(currentComparisonIndex, setCurrentComparisonIndex, -1)
      return
    }

    if (event.shiftKey && event.key === 'ArrowRight') {
      event.preventDefault()
      moveComparisonIndex(currentComparisonIndex, setCurrentComparisonIndex, 1)
    }
  }

  const handleSwapComparison = () => {
    setCurrentComparisonIndex(baselineComparisonIndex)
    setBaselineComparisonIndex(currentComparisonIndex)
  }

  const handleCopyComparison = async () => {
    if (!comparisonExportText || !navigator.clipboard?.writeText) {
      setComparisonCopyStatus('failed')
      return
    }

    try {
      await navigator.clipboard.writeText(comparisonExportText)
      setComparisonCopyStatus('copied')
    } catch {
      setComparisonCopyStatus('failed')
    }
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-100)',
      }}
    >
      {/* Header with toggle */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          gap: 'var(--ob-space-100)',
          flexWrap: 'wrap',
        }}
      >
        <div>
          <h3
            style={{
              margin: 0,
              fontSize: 'var(--ob-font-size-base)',
              fontWeight: 'var(--ob-font-weight-semibold)',
            }}
          >
            Inspection History
          </h3>
          <p
            style={{
              margin: 'var(--ob-space-035) 0 0',
              fontSize: 'var(--ob-font-size-sm)',
              color: 'var(--ob-color-text-secondary)',
              maxWidth: '480px',
            }}
          >
            Review the inspection timeline or compare any two recorded
            assessments side-by-side.
          </p>
        </div>
        <div
          role="tablist"
          aria-label="Inspection history views"
          onKeyDown={handleViewToggleKeyDown}
          style={{
            display: 'inline-grid',
            gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
            gap: 'var(--ob-space-035)',
            padding: 'var(--ob-space-025)',
            border: '1px solid var(--ob-color-border-primary)',
            borderRadius: 'var(--ob-radius-sm)',
            background: 'var(--ob-color-surface-secondary)',
            minWidth: '220px',
          }}
        >
          <button
            type="button"
            onClick={() => setHistoryViewMode('timeline')}
            role="tab"
            aria-selected={historyViewMode === 'timeline'}
            aria-pressed={historyViewMode === 'timeline'}
            style={{
              border: '1px solid transparent',
              background:
                historyViewMode === 'timeline'
                  ? 'var(--ob-color-bg-primary)'
                  : 'transparent',
              color:
                historyViewMode === 'timeline'
                  ? 'var(--ob-color-text-primary)'
                  : 'var(--ob-color-text-secondary)',
              borderRadius: 'var(--ob-radius-xs)',
              padding: 'var(--ob-space-025) var(--ob-space-085)',
              fontSize: 'var(--ob-font-size-sm)',
              fontWeight: 'var(--ob-font-weight-semibold)',
              cursor: 'pointer',
              boxShadow:
                historyViewMode === 'timeline'
                  ? '0 0 0 1px var(--ob-color-border-primary)'
                  : 'none',
            }}
          >
            Timeline
          </button>
          <button
            type="button"
            onClick={() => setHistoryViewMode('compare')}
            role="tab"
            aria-selected={historyViewMode === 'compare'}
            aria-pressed={historyViewMode === 'compare'}
            style={{
              border: '1px solid transparent',
              background:
                historyViewMode === 'compare'
                  ? 'var(--ob-color-bg-primary)'
                  : 'transparent',
              color:
                historyViewMode === 'compare'
                  ? 'var(--ob-color-text-primary)'
                  : 'var(--ob-color-text-secondary)',
              borderRadius: 'var(--ob-radius-xs)',
              padding: 'var(--ob-space-025) var(--ob-space-085)',
              fontSize: 'var(--ob-font-size-sm)',
              fontWeight: 'var(--ob-font-weight-semibold)',
              cursor: 'pointer',
              boxShadow:
                historyViewMode === 'compare'
                  ? '0 0 0 1px var(--ob-color-border-primary)'
                  : 'none',
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
            padding: 'var(--ob-space-085) var(--ob-space-100)',
            fontSize: 'var(--ob-font-size-sm)',
            color: 'var(--ob-color-status-error)',
            border: '1px solid var(--ob-color-border-primary)',
            borderRadius: 'var(--ob-radius-sm)',
            background: 'var(--ob-color-surface-error)',
          }}
        >
          {assessmentHistoryError}. Refresh the property record or reopen this
          panel to retry.
        </p>
      ) : isLoadingAssessmentHistory ? (
        <div
          style={{
            padding: 'var(--ob-space-150)',
            background: 'var(--ob-color-surface-secondary)',
            borderRadius: 'var(--ob-radius-sm)',
            border: '1px solid var(--ob-color-border-primary)',
          }}
        >
          <div
            aria-label="Loading inspection history"
            style={{ display: 'grid', gap: 'var(--ob-space-075)' }}
          >
            <Skeleton
              variant="text"
              width="28%"
              height={28}
              sx={{ transform: 'none' }}
            />
            <Skeleton
              variant="rectangular"
              height={112}
              sx={{ borderRadius: 'var(--ob-radius-sm)' }}
            />
            <Skeleton
              variant="rectangular"
              height={112}
              sx={{ borderRadius: 'var(--ob-radius-sm)' }}
            />
          </div>
        </div>
      ) : assessmentHistory.length === 0 ? (
        <div
          style={{
            padding: 'var(--ob-space-150)',
            textAlign: 'center',
            color: 'var(--ob-color-text-secondary)',
            background: 'var(--ob-color-surface-secondary)',
            borderRadius: 'var(--ob-radius-sm)',
            border: '1px solid var(--ob-color-border-primary)',
          }}
        >
          <p style={{ margin: 0, fontSize: 'var(--ob-font-size-base)' }}>
            No developer inspections recorded yet.
          </p>
          <p
            style={{
              margin: 'var(--ob-space-035) 0 0',
              fontSize: 'var(--ob-font-size-sm)',
            }}
          >
            Save an inspection above to start the audit trail.
          </p>
        </div>
      ) : historyViewMode === 'timeline' ? (
        <div style={{ display: 'grid', gap: 'var(--ob-space-085)' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: 'var(--ob-space-075)',
              flexWrap: 'wrap',
              padding: 'var(--ob-space-085) var(--ob-space-100)',
              border: '1px solid var(--ob-color-border-primary)',
              borderRadius: 'var(--ob-radius-sm)',
              background: 'var(--ob-color-surface-secondary)',
            }}
          >
            <p
              style={{
                margin: 0,
                fontSize: 'var(--ob-font-size-sm)',
                color: 'var(--ob-color-text-secondary)',
              }}
            >
              {assessmentHistory.length} inspections loaded. Sort for recency or
              score to scan faster.
            </p>
            <label
              style={{
                display: 'inline-grid',
                gap: 'var(--ob-space-035)',
                fontSize: 'var(--ob-font-size-xs)',
                fontWeight: 'var(--ob-font-weight-semibold)',
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
                color: 'var(--ob-color-text-secondary)',
              }}
            >
              Sort timeline
              <select
                aria-label="Sort inspection timeline"
                value={timelineSortMode}
                onChange={(event) =>
                  setTimelineSortMode(
                    event.target.value as
                      | 'newest'
                      | 'oldest'
                      | 'highest-score'
                      | 'lowest-score',
                  )
                }
                style={{
                  minHeight: '2.5rem',
                  minWidth: '220px',
                  padding: '0.55rem 0.7rem',
                  border: '1px solid var(--ob-color-border-primary)',
                  borderRadius: 'var(--ob-radius-xs)',
                  background: 'var(--ob-color-bg-primary)',
                  color: 'var(--ob-color-text-primary)',
                  fontSize: 'var(--ob-font-size-sm)',
                }}
              >
                <option value="newest">Newest first</option>
                <option value="oldest">Oldest first</option>
                <option value="highest-score">Highest score first</option>
                <option value="lowest-score">Lowest score first</option>
              </select>
            </label>
          </div>
          <HistoryTimelineView
            assessmentHistory={sortedTimelineHistory}
            activeScenario={activeScenario}
            formatScenarioLabel={formatScenarioLabel}
            formatRecordedTimestamp={formatRecordedTimestamp}
          />
        </div>
      ) : historyViewMode === 'compare' ? (
        assessmentHistory.length < 2 ||
        !latestAssessmentEntry ||
        !previousAssessmentEntry ? (
          <div
            style={{
              padding: 'var(--ob-space-150)',
              textAlign: 'center',
              color: 'var(--ob-color-text-secondary)',
              background: 'var(--ob-color-surface-secondary)',
              borderRadius: 'var(--ob-radius-sm)',
              border: '1px solid var(--ob-color-border-primary)',
            }}
          >
            <p style={{ margin: 0, fontSize: 'var(--ob-font-size-base)' }}>
              Capture one more inspection to unlock comparison view.
            </p>
          </div>
        ) : (
          <div style={{ display: 'grid', gap: 'var(--ob-space-100)' }}>
            <div
              onKeyDown={handleCompareControlsKeyDown}
              style={{
                display: 'grid',
                gap: 'var(--ob-space-085)',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                padding: 'var(--ob-space-100)',
                border: '1px solid var(--ob-color-border-primary)',
                borderRadius: 'var(--ob-radius-sm)',
                background: 'var(--ob-color-surface-secondary)',
              }}
            >
              <label
                style={{
                  display: 'grid',
                  gap: 'var(--ob-space-035)',
                  fontSize: 'var(--ob-font-size-xs)',
                  fontWeight: 'var(--ob-font-weight-semibold)',
                  letterSpacing: '0.06em',
                  textTransform: 'uppercase',
                  color: 'var(--ob-color-text-secondary)',
                }}
              >
                Current
                <select
                  aria-label="Select current inspection"
                  value={currentComparisonIndex}
                  onChange={(event) =>
                    setCurrentComparisonIndex(event.target.value)
                  }
                  style={{
                    minHeight: '2.5rem',
                    padding: '0.55rem 0.7rem',
                    border: '1px solid var(--ob-color-border-primary)',
                    borderRadius: 'var(--ob-radius-xs)',
                    background: 'var(--ob-color-bg-primary)',
                    color: 'var(--ob-color-text-primary)',
                    fontSize: 'var(--ob-font-size-sm)',
                  }}
                >
                  {comparisonOptions.map((option) => (
                    <option
                      key={`current-${option.value}`}
                      value={option.value}
                    >
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label
                style={{
                  display: 'grid',
                  gap: 'var(--ob-space-035)',
                  fontSize: 'var(--ob-font-size-xs)',
                  fontWeight: 'var(--ob-font-weight-semibold)',
                  letterSpacing: '0.06em',
                  textTransform: 'uppercase',
                  color: 'var(--ob-color-text-secondary)',
                }}
              >
                Baseline
                <select
                  aria-label="Select baseline inspection"
                  value={baselineComparisonIndex}
                  onChange={(event) =>
                    setBaselineComparisonIndex(event.target.value)
                  }
                  style={{
                    minHeight: '2.5rem',
                    padding: '0.55rem 0.7rem',
                    border: '1px solid var(--ob-color-border-primary)',
                    borderRadius: 'var(--ob-radius-xs)',
                    background: 'var(--ob-color-bg-primary)',
                    color: 'var(--ob-color-text-primary)',
                    fontSize: 'var(--ob-font-size-sm)',
                  }}
                >
                  {comparisonOptions.map((option) => (
                    <option
                      key={`baseline-${option.value}`}
                      value={option.value}
                    >
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <p
                style={{
                  margin: 0,
                  alignSelf: 'end',
                  fontSize: 'var(--ob-font-size-sm)',
                  color: comparisonSelectionInvalid
                    ? 'var(--ob-color-status-error)'
                    : 'var(--ob-color-text-secondary)',
                }}
              >
                {comparisonSelectionInvalid
                  ? 'Choose two different inspections to compare.'
                  : 'Shift + Left/Right moves Current. Alt + Left/Right moves Baseline.'}
              </p>
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: 'var(--ob-space-050)',
                  alignItems: 'end',
                }}
              >
                <button
                  type="button"
                  onClick={handleSwapComparison}
                  disabled={comparisonSelectionInvalid}
                  style={{
                    minHeight: '2.5rem',
                    padding: '0.55rem 0.85rem',
                    border: '1px solid var(--ob-color-border-primary)',
                    borderRadius: 'var(--ob-radius-xs)',
                    background: 'var(--ob-color-bg-primary)',
                    color: 'var(--ob-color-text-primary)',
                    fontSize: 'var(--ob-font-size-sm)',
                    fontWeight: 'var(--ob-font-weight-semibold)',
                    cursor: comparisonSelectionInvalid
                      ? 'not-allowed'
                      : 'pointer',
                    opacity: comparisonSelectionInvalid ? 0.55 : 1,
                  }}
                >
                  Swap
                </button>
                <button
                  type="button"
                  onClick={() => {
                    void handleCopyComparison()
                  }}
                  disabled={comparisonSelectionInvalid}
                  style={{
                    minHeight: '2.5rem',
                    padding: '0.55rem 0.85rem',
                    border: '1px solid var(--ob-color-border-primary)',
                    borderRadius: 'var(--ob-radius-xs)',
                    background: 'var(--ob-color-bg-primary)',
                    color: 'var(--ob-color-text-primary)',
                    fontSize: 'var(--ob-font-size-sm)',
                    fontWeight: 'var(--ob-font-weight-semibold)',
                    cursor: comparisonSelectionInvalid
                      ? 'not-allowed'
                      : 'pointer',
                    opacity: comparisonSelectionInvalid ? 0.55 : 1,
                  }}
                >
                  Copy Summary
                </button>
                <span
                  aria-live="polite"
                  style={{
                    fontSize: 'var(--ob-font-size-xs)',
                    color:
                      comparisonCopyStatus === 'failed'
                        ? 'var(--ob-color-status-error)'
                        : 'var(--ob-color-text-secondary)',
                  }}
                >
                  {comparisonCopyStatus === 'copied'
                    ? 'Copied comparison snapshot.'
                    : comparisonCopyStatus === 'failed'
                      ? 'Clipboard unavailable in this session.'
                      : 'Use the copy action for board-deck notes.'}
                </span>
              </div>
            </div>

            {!comparisonSelectionInvalid &&
            selectedCurrentAssessment &&
            selectedBaselineAssessment ? (
              <HistoryCompareView
                latestAssessmentEntry={selectedCurrentAssessment}
                previousAssessmentEntry={selectedBaselineAssessment}
                comparisonSummary={selectedComparisonSummary}
                systemComparisons={selectedSystemComparisons}
                recommendedActionDiff={selectedRecommendedActionDiff}
                scenarioComparisonVisible={scenarioComparisonVisible}
                scenarioComparisonRef={scenarioComparisonRef}
                scenarioComparisonTableRows={scenarioComparisonTableRows}
                scenarioAssessments={scenarioAssessments}
                formatScenarioLabel={formatScenarioLabel}
                formatRecordedTimestamp={formatRecordedTimestamp}
              />
            ) : null}
          </div>
        )
      ) : null}
    </div>
  )
}
