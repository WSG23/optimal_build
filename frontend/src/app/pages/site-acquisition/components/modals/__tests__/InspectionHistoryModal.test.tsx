import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState, type RefObject } from 'react'
import { describe, expect, it, vi } from 'vitest'

import type {
  ConditionAssessment,
  DevelopmentScenario,
} from '../../../../../../api/siteAcquisition'
import { InspectionHistoryModal } from '../InspectionHistoryModal'

function buildAssessment(
  overrides: Partial<ConditionAssessment> = {},
): ConditionAssessment {
  return {
    propertyId: 'property-1',
    scenario: 'raw_land',
    overallScore: 88,
    overallRating: 'A',
    riskLevel: 'low',
    summary: 'Inspection summary',
    scenarioContext: null,
    systems: [
      {
        name: 'Structure',
        rating: 'A',
        score: 88,
        notes: 'Strong',
        recommendedActions: ['Monitor drainage'],
      },
    ],
    recommendedActions: ['Monitor drainage'],
    inspectorName: 'Morgan Inspector',
    recordedBy: 'morgan@example.com',
    recordedAt: '2026-04-12T09:00:00Z',
    attachments: [],
    insights: [],
    ...overrides,
  }
}

const historyEntries: ConditionAssessment[] = [
  buildAssessment({
    scenario: 'raw_land',
    overallScore: 91,
    overallRating: 'A',
    riskLevel: 'low',
    summary: 'Latest inspection',
    recordedAt: '2026-04-12T09:00:00Z',
  }),
  buildAssessment({
    scenario: 'heritage_property',
    overallScore: 74,
    overallRating: 'B',
    riskLevel: 'medium',
    summary: 'Previous inspection',
    recordedAt: '2026-04-07T09:00:00Z',
  }),
]

type HarnessProps = {
  isOpen?: boolean
  onClose?: () => void
}

function Harness({ isOpen = true, onClose = () => undefined }: HarnessProps) {
  const [historyViewMode, setHistoryViewMode] = useState<
    'timeline' | 'compare'
  >('compare')

  return (
    <InspectionHistoryModal
      isOpen={isOpen}
      onClose={onClose}
      historyViewMode={historyViewMode}
      setHistoryViewMode={setHistoryViewMode}
      assessmentHistoryError={null}
      isLoadingAssessmentHistory={false}
      assessmentHistory={historyEntries}
      activeScenario={'all' as DevelopmentScenario | 'all'}
      latestAssessmentEntry={historyEntries[0]}
      previousAssessmentEntry={historyEntries[1]}
      comparisonSummary={null}
      systemComparisons={[]}
      recommendedActionDiff={{ newActions: [], clearedActions: [] }}
      scenarioComparisonVisible={false}
      scenarioComparisonRef={{ current: null } as RefObject<HTMLDivElement>}
      scenarioComparisonTableRows={[]}
      scenarioAssessments={[]}
      formatScenarioLabel={(scenario) => {
        if (scenario === 'raw_land') return 'New Construction'
        if (scenario === 'heritage_property') return 'Heritage Retrofit'
        return 'All Scenarios'
      }}
      formatRecordedTimestamp={(timestamp) => {
        if (timestamp === '2026-04-12T09:00:00Z') return 'Apr 12, 2026'
        if (timestamp === '2026-04-07T09:00:00Z') return 'Apr 7, 2026'
        return 'Unknown'
      }}
    />
  )
}

describe('InspectionHistoryModal', () => {
  it('renders the dialog into the document body when open', () => {
    render(<Harness />)

    expect(
      screen.getByRole('dialog', { name: /inspection history/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByLabelText(/select current inspection/i),
    ).toBeInTheDocument()
  })

  it('does not render when closed', () => {
    render(<Harness isOpen={false} />)

    expect(
      screen.queryByRole('dialog', { name: /inspection history/i }),
    ).not.toBeInTheDocument()
  })

  it('closes when users click the close button', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()

    render(<Harness onClose={onClose} />)

    await user.click(
      screen.getByRole('button', { name: /close inspection history/i }),
    )

    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('closes when users click the overlay but not when they click inside the dialog', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()

    render(<Harness onClose={onClose} />)

    await user.click(
      screen.getByRole('dialog', { name: /inspection history/i }),
    )
    expect(onClose).not.toHaveBeenCalled()

    const overlay = screen.getByRole('presentation')
    await user.click(overlay)

    expect(onClose).toHaveBeenCalledTimes(1)
  })
})
