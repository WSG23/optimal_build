import { beforeEach, describe, expect, it, vi } from 'vitest'
import React from 'react'
import { fireEvent, render, screen } from '@testing-library/react'

import { DueDiligencePage } from './DueDiligencePage'

const mockUseRouterParams = vi.fn()
const mockLoadCaptureForProject = vi.fn()
const mockUseChecklist = vi.fn()
const mockUseConditionAssessment = vi.fn()
const mockUseScenarioComparison = vi.fn()

vi.mock('../../../router', () => ({
  Link: ({ to, children }: { to: string; children: React.ReactNode }) => (
    <a href={to}>{children}</a>
  ),
  useRouterParams: () => mockUseRouterParams(),
}))

vi.mock('../capture/utils/captureStorage', () => ({
  loadCaptureForProject: (projectId: string) =>
    mockLoadCaptureForProject(projectId),
}))

vi.mock('../site-acquisition/hooks/useChecklist', () => ({
  useChecklist: (args: unknown) => mockUseChecklist(args),
}))

vi.mock('../site-acquisition/hooks/useConditionAssessment', () => ({
  useConditionAssessment: (args: unknown) => mockUseConditionAssessment(args),
}))

vi.mock('../site-acquisition/hooks/useDueDiligenceScenarioComparison', () => ({
  useDueDiligenceScenarioComparison: (args: unknown) =>
    mockUseScenarioComparison(args),
}))

vi.mock(
  '../site-acquisition/components/checklist/DueDiligenceChecklistSection',
  () => ({
    DueDiligenceChecklistSection: () => (
      <div data-testid="dd-checklist">Checklist Content</div>
    ),
  }),
)

vi.mock(
  '../site-acquisition/components/condition-assessment/OverallAssessmentCard',
  () => ({
    OverallAssessmentCard: () => <div data-testid="overall-card" />,
  }),
)

vi.mock(
  '../site-acquisition/components/condition-assessment/ImmediateActionsGrid',
  () => ({
    ImmediateActionsGrid: () => <div data-testid="actions-grid" />,
  }),
)

vi.mock(
  '../site-acquisition/components/condition-assessment/AIInsightPanel',
  () => ({
    AIInsightPanel: () => <div data-testid="ai-panel" />,
  }),
)

vi.mock(
  '../site-acquisition/components/condition-assessment/InsightCard',
  () => ({
    InsightCard: ({ title }: { title: string }) => <div>{title}</div>,
  }),
)

vi.mock(
  '../site-acquisition/components/condition-assessment/SystemRatingCard',
  () => ({
    SystemRatingCard: ({ systemName }: { systemName: string }) => (
      <div>{systemName}</div>
    ),
  }),
)

vi.mock('../site-acquisition/components/InspectionHistorySummary', () => ({
  InspectionHistorySummary: () => <div data-testid="history-summary" />,
}))

vi.mock('../site-acquisition/components/inspection-history', () => ({
  InspectionHistoryContent: () => <div data-testid="history-content" />,
}))

describe('DueDiligencePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    window.sessionStorage.clear()

    mockUseRouterParams.mockReturnValue({})
    mockLoadCaptureForProject.mockReturnValue(null)

    mockUseChecklist.mockReturnValue({
      checklistItems: [],
      isLoadingChecklist: false,
      selectedCategory: null,
      setSelectedCategory: vi.fn(),
      activeScenario: 'all',
      setActiveScenario: vi.fn(),
      availableChecklistScenarios: ['raw_land'],
      filteredChecklistItems: [],
      displaySummary: null,
      activeScenarioDetails: null,
      scenarioChecklistProgress: {},
      scenarioLookup: new Map([
        ['raw_land', { label: 'Raw Land' }],
        ['en_bloc', { label: 'En Bloc' }],
      ]),
      handleChecklistUpdate: vi.fn(),
    })

    mockUseConditionAssessment.mockReturnValue({
      conditionAssessment: null,
      isLoadingCondition: false,
      assessmentSaveMessage: null,
      assessmentHistory: [],
      isLoadingAssessmentHistory: false,
      assessmentHistoryError: null,
      historyViewMode: 'timeline',
      setHistoryViewMode: vi.fn(),
      scenarioAssessments: [],
      isLoadingScenarioAssessments: false,
      scenarioAssessmentsError: null,
      isExportingReport: false,
      reportExportMessage: null,
      latestAssessmentEntry: null,
      previousAssessmentEntry: null,
      openAssessmentEditor: vi.fn(),
      handleReportExport: vi.fn(),
    })

    mockUseScenarioComparison.mockReturnValue({
      scenarioOverrideEntries: [],
      baseScenarioAssessment: null,
      scenarioComparisonEntries: [],
      systemComparisons: [],
      systemComparisonMap: new Map(),
      combinedConditionInsights: [],
      insightSubtitle: 'Inspection deltas compared with previous assessments.',
      recommendedActionDiff: { newActions: [], clearedActions: [] },
      comparisonSummary: null,
      latestAssessmentEntry: null,
      previousAssessmentEntry: null,
      scenarioComparisonTableRows: [],
      scenarioComparisonVisible: false,
      setScenarioComparisonBase: vi.fn(),
      formatScenarioLabel: (scenario: string | null | undefined) =>
        scenario === 'raw_land'
          ? 'Raw Land'
          : scenario === 'en_bloc'
            ? 'En Bloc'
            : 'All scenarios',
    })
  })

  it('renders an empty state when no captured property is available', () => {
    render(<DueDiligencePage />)

    expect(
      screen.getByText(/No captured property in context/i),
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /open capture/i })).toHaveAttribute(
      'href',
      '/app/capture',
    )
  })

  it('hydrates from session storage and switches between tabs', async () => {
    window.sessionStorage.setItem(
      'site-acquisition:captured-property',
      JSON.stringify({
        propertyId: 'prop-1',
        currencySymbol: 'S$',
        address: { fullAddress: '1 Cyber Ave', district: 'Downtown' },
        propertyInfo: { propertyName: 'Cyber Tower' },
        quickAnalysis: {
          generatedAt: '2026-01-06T10:00:00Z',
          scenarios: [{ scenario: 'raw_land' }],
        },
      }),
    )

    mockUseConditionAssessment.mockReturnValue({
      conditionAssessment: {
        overallRating: 'B',
        overallScore: 78,
        riskLevel: 'Low',
        summary: 'Stable base building.',
        scenarioContext: null,
        inspectorName: null,
        recordedAt: null,
        attachments: [],
        recommendedActions: [],
        systems: [
          {
            name: 'Facade',
            rating: 'B',
            score: 78,
            notes: 'Good condition',
            recommendedActions: [],
          },
        ],
      },
      isLoadingCondition: false,
      assessmentSaveMessage: null,
      assessmentHistory: [],
      isLoadingAssessmentHistory: false,
      assessmentHistoryError: null,
      historyViewMode: 'timeline',
      setHistoryViewMode: vi.fn(),
      scenarioAssessments: [],
      isLoadingScenarioAssessments: false,
      scenarioAssessmentsError: null,
      isExportingReport: false,
      reportExportMessage: null,
      latestAssessmentEntry: null,
      previousAssessmentEntry: null,
      openAssessmentEditor: vi.fn(),
      handleReportExport: vi.fn(),
    })

    mockUseScenarioComparison.mockReturnValue({
      scenarioOverrideEntries: [],
      baseScenarioAssessment: null,
      scenarioComparisonEntries: [],
      systemComparisons: [],
      systemComparisonMap: new Map(),
      combinedConditionInsights: [
        {
          id: 'insight-1',
          severity: 'warning',
          title: 'Facade maintenance window',
          detail: 'Monitor sealant wear before the wet season.',
          specialist: null,
        },
      ],
      insightSubtitle: 'Heuristic insights combined with inspection deltas.',
      recommendedActionDiff: { newActions: [], clearedActions: [] },
      comparisonSummary: null,
      latestAssessmentEntry: null,
      previousAssessmentEntry: null,
      scenarioComparisonTableRows: [
        {
          key: 'raw_land',
          label: 'Raw Land',
          icon: '🏗️',
          quickHeadline: 'Checklist progressing',
          quickMetrics: [],
          conditionRating: 'B',
          conditionScore: 78,
          riskLevel: 'moderate',
          checklistCompleted: 7,
          checklistTotal: 10,
          checklistPercent: 70,
          insights: [],
          primaryInsight: null,
          recommendedAction: null,
          recordedAt: '2026-01-06T10:00:00Z',
          inspectorName: null,
          source: 'manual',
        },
      ],
      scenarioComparisonVisible: false,
      setScenarioComparisonBase: vi.fn(),
      formatScenarioLabel: (scenario: string | null | undefined) =>
        scenario === 'raw_land' ? 'Raw Land' : 'All scenarios',
    })

    render(<DueDiligencePage />)

    expect(await screen.findByText(/1 Cyber Ave/i)).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /checklist/i })).toBeInTheDocument()
    expect(
      screen.getByRole('tab', { name: /condition assessment/i }),
    ).toBeInTheDocument()

    fireEvent.click(screen.getByRole('tab', { name: /condition assessment/i }))
    expect(
      await screen.findByText(/Facade maintenance window/i),
    ).toBeInTheDocument()

    fireEvent.click(screen.getByRole('tab', { name: /inspection history/i }))
    expect(await screen.findByTestId('history-content')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('tab', { name: /scenario overrides/i }))
    expect(await screen.findByText(/Due Diligence Matrix/i)).toBeInTheDocument()
    expect(screen.getByText('DILIGENCE GAUGE')).toBeInTheDocument()
    expect(screen.getByText('RISK VECTOR')).toBeInTheDocument()
    expect(screen.getAllByText('AVG CONDITION').length).toBeGreaterThan(0)
  })
})
