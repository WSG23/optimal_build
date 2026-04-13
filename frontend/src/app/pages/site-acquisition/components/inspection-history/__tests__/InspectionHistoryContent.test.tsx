import { fireEvent, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState, type RefObject } from 'react'
import { describe, expect, it, vi, beforeEach } from 'vitest'

import type {
  ConditionAssessment,
  DevelopmentScenario,
} from '../../../../../../api/siteAcquisition'
import { InspectionHistoryContent } from '../InspectionHistoryContent'

function buildAssessment(
  overrides: Partial<ConditionAssessment> = {},
): ConditionAssessment {
  return {
    propertyId: 'property-1',
    scenario: 'raw_land',
    overallScore: 80,
    overallRating: 'B',
    riskLevel: 'medium',
    summary: 'Base inspection summary',
    scenarioContext: null,
    systems: [
      {
        name: 'Structure',
        rating: 'B',
        score: 80,
        notes: 'Stable',
        recommendedActions: ['Monitor joints'],
      },
    ],
    recommendedActions: ['Monitor joints'],
    inspectorName: 'Alex Inspector',
    recordedBy: 'alex@example.com',
    recordedAt: '2026-04-10T10:00:00Z',
    attachments: [],
    insights: [],
    ...overrides,
  }
}

const historyEntries: ConditionAssessment[] = [
  buildAssessment({
    scenario: 'raw_land',
    overallScore: 92,
    overallRating: 'A',
    riskLevel: 'low',
    summary: 'Newest assessment',
    inspectorName: 'Morgan Longname Inspector',
    recordedAt: '2026-04-12T09:00:00Z',
    systems: [
      {
        name: 'Structure',
        rating: 'A',
        score: 92,
        notes: 'Improved',
        recommendedActions: ['Inspect facade seal'],
      },
      {
        name: 'Electrical',
        rating: 'B',
        score: 81,
        notes: 'Stable',
        recommendedActions: [],
      },
    ],
    recommendedActions: ['Inspect facade seal'],
  }),
  buildAssessment({
    scenario: 'heritage_property',
    overallScore: 76,
    overallRating: 'B',
    riskLevel: 'medium',
    summary: 'Mid assessment',
    recordedAt: '2026-04-08T09:00:00Z',
    systems: [
      {
        name: 'Structure',
        rating: 'B',
        score: 76,
        notes: 'Stable',
        recommendedActions: ['Monitor joints'],
      },
      {
        name: 'Electrical',
        rating: 'C',
        score: 69,
        notes: 'Needs work',
        recommendedActions: ['Replace panel'],
      },
    ],
    recommendedActions: ['Monitor joints', 'Replace panel'],
  }),
  buildAssessment({
    scenario: 'all',
    overallScore: 58,
    overallRating: 'C',
    riskLevel: 'high',
    summary: 'Oldest assessment',
    recordedAt: '2026-04-02T09:00:00Z',
    systems: [
      {
        name: 'Structure',
        rating: 'C',
        score: 58,
        notes: 'Deteriorated',
        recommendedActions: ['Stabilize canopy'],
      },
    ],
    recommendedActions: ['Stabilize canopy'],
  }),
]

type HarnessProps = {
  initialMode?: 'timeline' | 'compare'
}

function Harness({ initialMode = 'timeline' }: HarnessProps) {
  const [historyViewMode, setHistoryViewMode] = useState<
    'timeline' | 'compare'
  >(initialMode)

  return (
    <InspectionHistoryContent
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
        if (timestamp === '2026-04-08T09:00:00Z') return 'Apr 8, 2026'
        if (timestamp === '2026-04-02T09:00:00Z') return 'Apr 2, 2026'
        return 'Unknown'
      }}
    />
  )
}

describe('InspectionHistoryContent', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('updates comparison content when users choose a different inspection pair', async () => {
    const user = userEvent.setup()

    render(<Harness initialMode="compare" />)

    await user.selectOptions(
      screen.getByLabelText(/select current inspection/i),
      '2',
    )
    await user.selectOptions(
      screen.getByLabelText(/select baseline inspection/i),
      '1',
    )

    expect(
      screen.getByText('Declined by 18 points from 76.'),
    ).toBeInTheDocument()
    expect(
      screen.getByText('Risk level changed from medium to high.'),
    ).toBeInTheDocument()
    expect(screen.getByText('Stabilize canopy')).toBeInTheDocument()
    expect(screen.getByText('Monitor joints')).toBeInTheDocument()
  })

  it('copies a comparison snapshot to the clipboard', async () => {
    const user = userEvent.setup()
    const writeText = vi.fn().mockResolvedValue(undefined)
    vi.stubGlobal('navigator', {
      clipboard: {
        writeText,
      },
    })

    render(<Harness initialMode="compare" />)

    await user.click(screen.getByRole('button', { name: /copy summary/i }))

    expect(writeText).toHaveBeenCalledTimes(1)
    expect(writeText.mock.calls[0][0]).toContain('Inspection comparison')
    expect(writeText.mock.calls[0][0]).toContain('Score delta: +16')
    expect(screen.getByText('Copied comparison snapshot.')).toBeInTheDocument()
  })

  it('supports keyboard switching between timeline and compare views', async () => {
    render(<Harness initialMode="timeline" />)

    const tablist = screen.getByRole('tablist', {
      name: /inspection history views/i,
    })
    fireEvent.keyDown(tablist, { key: 'ArrowRight' })

    expect(
      screen.getByLabelText(/select current inspection/i),
    ).toBeInTheDocument()

    fireEvent.keyDown(tablist, { key: 'ArrowLeft' })

    expect(
      screen.getByLabelText(/sort inspection timeline/i),
    ).toBeInTheDocument()
  })

  it('resorts the timeline by score', async () => {
    const user = userEvent.setup()
    const { container } = render(<Harness initialMode="timeline" />)

    await user.selectOptions(
      screen.getByLabelText(/sort inspection timeline/i),
      'lowest-score',
    )

    const summaries = Array.from(container.querySelectorAll('summary'))
    expect(summaries).toHaveLength(3)
    expect(
      within(summaries[0] as HTMLElement).getByText('All Scenarios'),
    ).toBeInTheDocument()
    expect(
      within(summaries[1] as HTMLElement).getByText('Heritage Retrofit'),
    ).toBeInTheDocument()
    expect(
      within(summaries[2] as HTMLElement).getByText('New Construction'),
    ).toBeInTheDocument()
  })
})
