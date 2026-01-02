/**
 * Inspection History Modal
 *
 * Modal wrapper for InspectionHistoryContent component.
 * Uses createPortal to render outside the main component tree.
 */

import type React from 'react'
import { createPortal } from 'react-dom'
import type { RefObject } from 'react'
import { IconButton } from '@mui/material'
import { Close } from '@mui/icons-material'
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
        background: 'var(--ob-overlay-dark)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--ob-space-200)',
        zIndex: 1000,
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Inspection history"
        onClick={(event) => event.stopPropagation()}
        style={{
          background: 'var(--ob-color-bg-surface)',
          borderRadius: 'var(--ob-radius-lg)',
          width: 'min(1200px, 95vw)',
          maxHeight: '85vh',
          overflowY: 'auto',
          boxShadow: 'var(--ob-shadow-lg)',
          padding: 'var(--ob-space-200)',
          position: 'relative',
        }}
      >
        <IconButton
          onClick={onClose}
          aria-label="Close inspection history"
          sx={{
            position: 'absolute',
            top: 'var(--ob-space-100)',
            right: 'var(--ob-space-100)',
            color: 'var(--ob-color-text-muted)',
          }}
        >
          <Close />
        </IconButton>
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
