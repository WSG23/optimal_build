import { beforeEach, describe, expect, it, vi } from 'vitest'
import React from 'react'
import { act, fireEvent, render, screen } from '@testing-library/react'

import type { SiteAcquisitionResult } from '../../../../api/siteAcquisition'
import type { DevelopmentScenario } from '../../../../api/agents'
import { DeveloperResults } from './DeveloperResults'

vi.mock('../../../../contexts/useProject', () => ({
  useProject: () => ({
    currentProject: null,
    projects: [],
    setCurrentProject: vi.fn(),
    refreshProjects: vi.fn(),
  }),
}))

vi.mock('@mui/material', async (importOriginal) => {
  const actual = (await importOriginal()) as Record<string, unknown>
  return {
    ...actual,
    Select: ({
      value,
      onChange,
      children,
      ...rest
    }: {
      value: string
      onChange: (event: React.ChangeEvent<HTMLSelectElement>) => void
      children: React.ReactNode
    }) => (
      <select
        data-testid="preview-detail-select"
        value={value}
        onChange={onChange}
        {...rest}
      >
        {children}
      </select>
    ),
    MenuItem: ({
      value,
      children,
      ...rest
    }: {
      value: string
      children: React.ReactNode
    }) => (
      <option value={value} {...rest}>
        {children}
      </option>
    ),
  }
})

const mockHandleRefreshPreview = vi.fn()
const mockHandleToggleLayerVisibility = vi.fn()
const mockHandleSoloPreviewLayer = vi.fn()
const mockHandleFocusLayer = vi.fn()
const mockSetPreviewDetailLevel = vi.fn()

const mockHandleChecklistUpdate = vi.fn()
const mockHandleReportExport = vi.fn()
const mockOpenAssessmentEditor = vi.fn()

let previewMetadataErrorValue: string | null = null
let lastMultiScenarioProps: unknown = null
let lastInsightProps: unknown = null

const mockUseScenarioComparison = vi.fn()

vi.mock('../../site-acquisition/utils/cardBuilders', () => ({
  buildPropertyOverviewCards: ({
    formatters,
  }: {
    formatters: {
      formatNumber: (value: number) => string
      formatCurrency: (value: number) => string
      formatTimestamp: (timestamp?: string | null) => string
    }
  }) => {
    formatters.formatNumber(1.23)
    formatters.formatCurrency(1234)
    formatters.formatTimestamp(null)
    formatters.formatTimestamp('not-a-real-date')
    return []
  },
}))

vi.mock('../../site-acquisition/hooks/usePreviewJob', () => ({
  usePreviewJob: () => ({
    previewJob: null,
    previewDetailLevel: 'medium',
    setPreviewDetailLevel: mockSetPreviewDetailLevel,
    isRefreshingPreview: false,
    previewLayerMetadata: [],
    previewLayerVisibility: {},
    previewFocusLayerId: null,
    isPreviewMetadataLoading: false,
    previewMetadataError: previewMetadataErrorValue,
    hiddenLayerCount: 0,
    colorLegendEntries: [],
    legendHasPendingChanges: false,
    handleRefreshPreview: mockHandleRefreshPreview,
    handleToggleLayerVisibility: mockHandleToggleLayerVisibility,
    handleSoloPreviewLayer: mockHandleSoloPreviewLayer,
    handleShowAllLayers: vi.fn(),
    handleFocusLayer: mockHandleFocusLayer,
    handleResetLayerFocus: vi.fn(),
    handleLegendEntryChange: vi.fn(),
    handleLegendReset: vi.fn(),
  }),
}))

vi.mock('../../site-acquisition/hooks/useChecklist', () => ({
  useChecklist: () => ({
    checklistItems: [],
    filteredChecklistItems: [],
    selectedCategory: null,
    isLoadingChecklist: false,
    setSelectedCategory: vi.fn(),
    handleChecklistUpdate: mockHandleChecklistUpdate,
    displaySummary: {},
    activeScenarioDetails: null,
    scenarioChecklistProgress: {},
  }),
}))

vi.mock('../../site-acquisition/hooks/useConditionAssessment', () => ({
  useConditionAssessment: () => ({
    conditionAssessment: null,
    latestAssessmentEntry: null,
    previousAssessmentEntry: null,
    isLoadingCondition: false,
    isExportingReport: false,
    reportExportMessage: null,
    handleReportExport: mockHandleReportExport,
    assessmentHistory: [],
    scenarioAssessments: [],
    isLoadingAssessmentHistory: false,
    assessmentHistoryError: null,
    isLoadingScenarioAssessments: false,
    scenarioAssessmentsError: null,
    assessmentSaveMessage: null,
    openAssessmentEditor: mockOpenAssessmentEditor,
  }),
}))

vi.mock('../../site-acquisition/hooks/useScenarioComparison', () => ({
  useScenarioComparison: (...args: unknown[]) =>
    mockUseScenarioComparison(...args),
}))

vi.mock(
  '../../site-acquisition/components/property-overview/PropertyOverviewSection',
  () => ({
    PropertyOverviewSection: () => <div data-testid="property-overview" />,
  }),
)
vi.mock('../../../components/site-acquisition/Preview3DViewer', () => ({
  Preview3DViewer: () => <div data-testid="preview-3d" />,
}))
vi.mock(
  '../../site-acquisition/components/property-overview/PreviewLayersTable',
  () => ({
    PreviewLayersTable: ({
      onLayerAction,
    }: {
      onLayerAction: (
        layerId: string,
        action: 'toggle' | 'solo' | 'focus',
      ) => void
    }) => (
      <div data-testid="preview-layers">
        <button
          type="button"
          onClick={() => onLayerAction('layer-1', 'toggle')}
        >
          layer-toggle
        </button>
        <button type="button" onClick={() => onLayerAction('layer-2', 'solo')}>
          layer-solo
        </button>
        <button type="button" onClick={() => onLayerAction('layer-3', 'focus')}>
          layer-focus
        </button>
      </div>
    ),
  }),
)
vi.mock(
  '../../site-acquisition/components/checklist/DueDiligenceChecklistSection',
  () => ({
    DueDiligenceChecklistSection: ({
      handleChecklistUpdate,
    }: {
      handleChecklistUpdate: (
        itemId: string,
        status: 'pending' | 'in_progress' | 'completed' | 'not_applicable',
      ) => void
    }) => (
      <div data-testid="checklist">
        <button
          type="button"
          onClick={() => handleChecklistUpdate('item-123', 'completed')}
        >
          checklist-complete
        </button>
      </div>
    ),
  }),
)
vi.mock(
  '../../site-acquisition/components/condition-assessment/ConditionAssessmentSection',
  () => ({
    ConditionAssessmentSection: ({
      handleReportExport,
      describeRatingChange,
      describeRiskChange,
      formatRecordedTimestamp,
      InlineInspectionHistorySummary,
    }: {
      handleReportExport: (format: 'json' | 'pdf') => void
      describeRatingChange: (
        current: string,
        reference: string,
      ) => { text: string; tone: 'positive' | 'negative' | 'neutral' }
      describeRiskChange: (
        current: string,
        reference: string,
      ) => { text: string; tone: 'positive' | 'negative' | 'neutral' }
      formatRecordedTimestamp: (timestamp?: string | null) => string
      InlineInspectionHistorySummary: React.ComponentType
    }) => (
      <div data-testid="condition-assessment">
        <button type="button" onClick={() => handleReportExport('pdf')}>
          export-pdf
        </button>
        <div data-testid="rating-change">
          {describeRatingChange('A', 'B').text}
        </div>
        <div data-testid="risk-change">
          {describeRiskChange('Low', 'High').text}
        </div>
        <div data-testid="formatted-timestamp">
          {formatRecordedTimestamp('not-a-real-date')}
        </div>
        <InlineInspectionHistorySummary />
      </div>
    ),
  }),
)
vi.mock('../../site-acquisition/components/InspectionHistorySummary', () => ({
  InspectionHistorySummary: ({
    onLogInspection,
    onViewTimeline,
  }: {
    onLogInspection: () => void
    onViewTimeline: () => void
  }) => (
    <div data-testid="inspection-history">
      <button type="button" onClick={onLogInspection}>
        log-inspection
      </button>
      <button type="button" onClick={onViewTimeline}>
        view-timeline
      </button>
    </div>
  ),
}))

vi.mock('../../site-acquisition/components/OptimalIntelligenceCard', () => ({
  OptimalIntelligenceCard: ({
    insight,
    isGenerating,
    onGenerateReport,
  }: {
    insight: string | null
    isGenerating: boolean
    onGenerateReport: () => Promise<void>
  }) => {
    lastInsightProps = { insight, isGenerating }
    return (
      <div data-testid="ai-insight">
        <div data-testid="ai-insight-text">{insight ?? ''}</div>
        <div data-testid="ai-is-generating">
          {isGenerating ? 'generating' : 'idle'}
        </div>
        <button type="button" onClick={() => void onGenerateReport()}>
          generate-report
        </button>
      </div>
    )
  },
}))

vi.mock(
  '../../site-acquisition/components/multi-scenario-comparison/MultiScenarioComparisonSection',
  () => ({
    MultiScenarioComparisonSection: ({
      activeScenario,
      feasibilitySignals,
    }: {
      activeScenario: string
      feasibilitySignals: Array<{
        scenario: string
        opportunities: string[]
        risks: string[]
      }>
    }) => {
      lastMultiScenarioProps = { activeScenario, feasibilitySignals }
      return (
        <div
          data-testid="multi-scenario"
          data-active={activeScenario}
          data-signals={feasibilitySignals.length}
        />
      )
    },
  }),
)

describe('DeveloperResults', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    previewMetadataErrorValue = null
    lastMultiScenarioProps = null
    lastInsightProps = null

    mockUseScenarioComparison.mockImplementation(() => ({
      quickAnalysisScenarios: [
        { scenario: 'raw_land', metrics: { est_irr: 16 } },
        { scenario: 'en_bloc', metrics: { est_irr: 8 } },
      ],
      comparisonScenarios: [],
      scenarioComparisonData: [],
      formatScenarioLabel: (scenario: string) =>
        scenario === 'raw_land'
          ? 'Raw Land'
          : scenario === 'en_bloc'
            ? 'En Bloc'
            : scenario,
      combinedConditionInsights: [],
      insightSubtitle: null,
      systemComparisonMap: new Map(),
      scenarioOverrideEntries: [],
      baseScenarioAssessment: null,
      scenarioComparisonEntries: [],
      setScenarioComparisonBase: vi.fn(),
    }))
  })

  it('wires preview, checklist, and export handlers to child sections', () => {
    render(
      <DeveloperResults
        result={
          {
            propertyId: 'prop-123',
            currencySymbol: 'S$',
            address: { fullAddress: '1 Cyber Ave', district: 'Downtown' },
            quickAnalysis: {
              generatedAt: '2026-01-06T10:00:00Z',
              scenarios: [],
            },
            previewJob: null,
          } as SiteAcquisitionResult
        }
        selectedScenarios={['raw_land', 'en_bloc'] as DevelopmentScenario[]}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: /refresh/i }))
    expect(mockHandleRefreshPreview).toHaveBeenCalled()

    fireEvent.change(screen.getByTestId('preview-detail-select'), {
      target: { value: 'simple' },
    })
    expect(mockSetPreviewDetailLevel).toHaveBeenCalledWith('simple')

    fireEvent.click(screen.getByRole('button', { name: /layer-toggle/i }))
    expect(mockHandleToggleLayerVisibility).toHaveBeenCalledWith('layer-1')

    fireEvent.click(screen.getByRole('button', { name: /layer-solo/i }))
    expect(mockHandleSoloPreviewLayer).toHaveBeenCalledWith('layer-2')

    fireEvent.click(screen.getByRole('button', { name: /layer-focus/i }))
    expect(mockHandleFocusLayer).toHaveBeenCalledWith('layer-3')

    fireEvent.click(screen.getByRole('button', { name: /checklist-complete/i }))
    expect(mockHandleChecklistUpdate).toHaveBeenCalledWith(
      'item-123',
      'completed',
    )

    fireEvent.click(screen.getByRole('button', { name: /export-pdf/i }))
    expect(mockHandleReportExport).toHaveBeenCalledWith('pdf')

    fireEvent.click(screen.getByRole('button', { name: /log-inspection/i }))
    expect(mockOpenAssessmentEditor).toHaveBeenCalledWith('new')

    expect(screen.getByTestId('rating-change').textContent).toMatch(/Rating/i)
    expect(screen.getByTestId('risk-change').textContent).toMatch(/Risk level/i)
    expect(screen.getByTestId('formatted-timestamp').textContent).toBe(
      'Invalid Date',
    )
  })

  it('derives feasibility signals from scenario IRR and passes them to MultiScenarioComparisonSection', () => {
    render(
      <DeveloperResults
        result={
          {
            propertyId: 'prop-123',
            currencySymbol: 'S$',
            address: { fullAddress: '1 Cyber Ave', district: 'Downtown' },
            quickAnalysis: {
              generatedAt: '2026-01-06T10:00:00Z',
              scenarios: [],
            },
            previewJob: null,
          } as SiteAcquisitionResult
        }
        selectedScenarios={['raw_land', 'en_bloc'] as DevelopmentScenario[]}
      />,
    )

    const props = lastMultiScenarioProps as {
      activeScenario: string
      feasibilitySignals: Array<{
        scenario: string
        opportunities: string[]
        risks: string[]
      }>
    } | null

    expect(props).not.toBeNull()
    expect(props?.feasibilitySignals.length).toBe(2)
    expect(props?.feasibilitySignals[0]?.scenario).toBe('raw_land')
    expect(props?.feasibilitySignals[0]?.opportunities.length).toBeGreaterThan(
      0,
    )
    expect(props?.feasibilitySignals[1]?.scenario).toBe('en_bloc')
    expect(props?.feasibilitySignals[1]?.risks.length).toBeGreaterThan(0)
  })

  it('passes no feasibility signals when quick analysis scenarios are missing', () => {
    mockUseScenarioComparison.mockImplementationOnce(() => ({
      quickAnalysisScenarios: [],
      comparisonScenarios: [],
      scenarioComparisonData: [],
      formatScenarioLabel: (scenario: string) =>
        scenario === 'raw_land'
          ? 'Raw Land'
          : scenario === 'en_bloc'
            ? 'En Bloc'
            : scenario,
      combinedConditionInsights: [],
      insightSubtitle: null,
      systemComparisonMap: new Map(),
      scenarioOverrideEntries: [],
      baseScenarioAssessment: null,
      scenarioComparisonEntries: [],
      setScenarioComparisonBase: vi.fn(),
    }))

    render(
      <DeveloperResults
        result={
          {
            propertyId: 'prop-123',
            currencySymbol: 'S$',
            address: { fullAddress: '1 Cyber Ave', district: 'Downtown' },
            quickAnalysis: {
              generatedAt: '2026-01-06T10:00:00Z',
              scenarios: [],
            },
            previewJob: null,
          } as SiteAcquisitionResult
        }
        selectedScenarios={['raw_land', 'en_bloc'] as DevelopmentScenario[]}
      />,
    )

    expect(
      screen.getByTestId('multi-scenario').getAttribute('data-signals'),
    ).toBe('0')
  })

  it('generates an AI insight and toggles generating state while creating a report', async () => {
    vi.useFakeTimers()
    try {
      render(
        <DeveloperResults
          result={
            {
              propertyId: 'prop-123',
              currencySymbol: 'S$',
              address: { fullAddress: '1 Cyber Ave', district: 'Downtown' },
              quickAnalysis: {
                generatedAt: '2026-01-06T10:00:00Z',
                scenarios: [],
              },
              previewJob: null,
            } as SiteAcquisitionResult
          }
          selectedScenarios={['raw_land', 'en_bloc'] as DevelopmentScenario[]}
        />,
      )

      expect(screen.getByTestId('ai-insight-text').textContent).toContain(
        "Downtown's zoning profile",
      )
      expect(screen.getByTestId('ai-is-generating').textContent).toBe('idle')

      await act(async () => {
        fireEvent.click(
          screen.getByRole('button', { name: /generate-report/i }),
        )
      })

      expect(screen.getByTestId('ai-is-generating').textContent).toBe(
        'generating',
      )

      await act(async () => {
        await vi.advanceTimersByTimeAsync(2000)
      })

      expect(screen.getByTestId('ai-is-generating').textContent).toBe('idle')
      expect(lastInsightProps).toBeTruthy()
    } finally {
      vi.useRealTimers()
    }
  })

  it('renders preview metadata errors when present', () => {
    previewMetadataErrorValue = 'Preview metadata failed'

    render(
      <DeveloperResults
        result={
          {
            propertyId: 'prop-123',
            currencySymbol: 'S$',
            address: { fullAddress: '1 Cyber Ave', district: 'Downtown' },
            quickAnalysis: {
              generatedAt: '2026-01-06T10:00:00Z',
              scenarios: [],
            },
            previewJob: null,
          } as SiteAcquisitionResult
        }
        selectedScenarios={['raw_land', 'en_bloc'] as DevelopmentScenario[]}
      />,
    )

    expect(screen.getByText(/Preview metadata failed/i)).toBeInTheDocument()
  })

  it('updates active scenario and propagates it to MultiScenarioComparisonSection', () => {
    render(
      <DeveloperResults
        result={
          {
            propertyId: 'prop-123',
            currencySymbol: 'S$',
            address: { fullAddress: '1 Cyber Ave', district: 'Downtown' },
            quickAnalysis: {
              generatedAt: '2026-01-06T10:00:00Z',
              scenarios: [],
            },
            previewJob: null,
          } as SiteAcquisitionResult
        }
        selectedScenarios={['raw_land', 'en_bloc'] as DevelopmentScenario[]}
      />,
    )

    const module = screen.getByTestId('multi-scenario')
    expect(module.getAttribute('data-active')).toBe('raw_land')

    fireEvent.click(screen.getByRole('button', { name: /All Scenarios/i }))
    expect(module.getAttribute('data-active')).toBe('all')

    fireEvent.click(screen.getByRole('button', { name: /En Bloc/i }))
    expect(module.getAttribute('data-active')).toBe('en_bloc')
  })
})
