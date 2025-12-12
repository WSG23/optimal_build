/**
 * Inspection History Modal
 *
 * Modal wrapper for InspectionHistoryContent component.
 * Uses createPortal to render outside the main component tree.
 */

import type React from 'react'
import { createPortal } from 'react-dom'
import type { RefObject } from 'react'
import type {
  ConditionAssessment,
  DevelopmentScenario,
} from '../../../../../api/siteAcquisition'
import type {
  ScenarioComparisonDatum,
  SystemComparisonEntry,
} from '../../types'
import {
  InspectionHistoryContent,
  type ComparisonSummary,
  type RecommendedActionDiff,
} from '../inspection-history'

// ============================================================================
// Types
// ============================================================================

export interface InspectionHistoryModalProps {
  isOpen: boolean
  onClose: () => void

  // History content props
  historyViewMode: 'timeline' | 'compare'
  setHistoryViewMode: (mode: 'timeline' | 'compare') => void
  assessmentHistoryError: string | null
  isLoadingAssessmentHistory: boolean
  assessmentHistory: ConditionAssessment[]
  activeScenario: 'all' | DevelopmentScenario
  latestAssessmentEntry: ConditionAssessment | null
  previousAssessmentEntry: ConditionAssessment | null
  comparisonSummary: ComparisonSummary | null
  systemComparisons: SystemComparisonEntry[]
  recommendedActionDiff: RecommendedActionDiff
  scenarioComparisonVisible: boolean
  scenarioComparisonRef: RefObject<HTMLDivElement | null>
  scenarioComparisonTableRows: ScenarioComparisonDatum[]
  scenarioAssessments: ConditionAssessment[]
  formatScenarioLabel: (
    scenario: DevelopmentScenario | 'all' | null | undefined,
  ) => string
  formatRecordedTimestamp: (timestamp: string | null | undefined) => string
}

// ============================================================================
// Component
// ============================================================================

export function InspectionHistoryModal({
  isOpen,
  onClose,
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
}: InspectionHistoryModalProps) {
  if (!isOpen) return null

  return createPortal(
    <div
      role="presentation"
      onClick={(event) => {
        if (event.target === event.currentTarget) {
          onClose()
        }
      }}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.45)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem',
        zIndex: 1000,
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Inspection history"
        onClick={(event) => event.stopPropagation()}
        style={{
          background: 'white',
          borderRadius: '8px',
          width: 'min(1200px, 95vw)',
          maxHeight: '85vh',
          overflowY: 'auto',
          boxShadow: '0 20px 40px rgba(0,0,0,0.25)',
          padding: '2rem',
          position: 'relative',
        }}
      >
        <button
          type="button"
          onClick={onClose}
          aria-label="Close inspection history"
          style={{
            position: 'absolute',
            top: '1rem',
            right: '1rem',
            border: 'none',
            background: 'transparent',
            fontSize: '1.5rem',
            cursor: 'pointer',
            color: '#6e6e73',
          }}
        >
          ×
        </button>
        <InspectionHistoryContent
          historyViewMode={historyViewMode}
          setHistoryViewMode={setHistoryViewMode}
          assessmentHistoryError={assessmentHistoryError}
          isLoadingAssessmentHistory={isLoadingAssessmentHistory}
          assessmentHistory={assessmentHistory}
          activeScenario={activeScenario}
          latestAssessmentEntry={latestAssessmentEntry}
          previousAssessmentEntry={previousAssessmentEntry}
          comparisonSummary={comparisonSummary}
          systemComparisons={systemComparisons}
          recommendedActionDiff={recommendedActionDiff}
          scenarioComparisonVisible={scenarioComparisonVisible}
          scenarioComparisonRef={
            scenarioComparisonRef as React.RefObject<HTMLDivElement>
          }
          scenarioComparisonTableRows={scenarioComparisonTableRows}
          scenarioAssessments={scenarioAssessments}
          formatScenarioLabel={formatScenarioLabel}
          formatRecordedTimestamp={formatRecordedTimestamp}
        />
      </div>
    </div>,
    document.body,
  )
}
