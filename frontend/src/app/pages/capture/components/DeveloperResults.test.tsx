import { describe, expect, it, vi } from 'vitest'
import React from 'react'
import { fireEvent, render, screen } from '@testing-library/react'

import type { SiteAcquisitionResult } from '../../../../api/siteAcquisition'
import type { DevelopmentScenario } from '../../../../api/agents'
import { DeveloperResults } from './DeveloperResults'

vi.mock('../../site-acquisition/utils/cardBuilders', () => ({
  buildPropertyOverviewCards: () => [],
}))

vi.mock('../../site-acquisition/hooks/usePreviewJob', () => ({
  usePreviewJob: () => ({
    previewJob: null,
    previewDetailLevel: 'medium',
    setPreviewDetailLevel: vi.fn(),
    isRefreshingPreview: false,
    previewLayerMetadata: [],
    previewLayerVisibility: {},
    previewFocusLayerId: null,
    isPreviewMetadataLoading: false,
    previewMetadataError: null,
    hiddenLayerCount: 0,
    colorLegendEntries: [],
    legendHasPendingChanges: false,
    handleRefreshPreview: vi.fn(),
    handleToggleLayerVisibility: vi.fn(),
    handleSoloPreviewLayer: vi.fn(),
    handleShowAllLayers: vi.fn(),
    handleFocusLayer: vi.fn(),
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
    handleChecklistUpdate: vi.fn(),
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
    handleReportExport: vi.fn(),
    assessmentHistory: [],
    scenarioAssessments: [],
    isLoadingAssessmentHistory: false,
    assessmentHistoryError: null,
    isLoadingScenarioAssessments: false,
    scenarioAssessmentsError: null,
    assessmentSaveMessage: null,
    openAssessmentEditor: vi.fn(),
  }),
}))

vi.mock('../../site-acquisition/hooks/useScenarioComparison', () => ({
  useScenarioComparison: () => ({
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
  }),
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
    PreviewLayersTable: () => <div data-testid="preview-layers" />,
  }),
)
vi.mock(
  '../../site-acquisition/components/checklist/DueDiligenceChecklistSection',
  () => ({
    DueDiligenceChecklistSection: () => <div data-testid="checklist" />,
  }),
)
vi.mock(
  '../../site-acquisition/components/condition-assessment/ConditionAssessmentSection',
  () => ({
    ConditionAssessmentSection: () => (
      <div data-testid="condition-assessment" />
    ),
  }),
)
vi.mock('../../site-acquisition/components/InspectionHistorySummary', () => ({
  InspectionHistorySummary: () => <div data-testid="inspection-history" />,
}))

vi.mock(
  '../../site-acquisition/components/multi-scenario-comparison/MultiScenarioComparisonSection',
  () => ({
    MultiScenarioComparisonSection: ({
      activeScenario,
    }: {
      activeScenario: string
    }) => <div data-testid="multi-scenario" data-active={activeScenario} />,
  }),
)

describe('DeveloperResults', () => {
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
