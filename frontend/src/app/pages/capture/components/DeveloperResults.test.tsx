import { beforeEach, describe, expect, it, vi } from 'vitest'
import React from 'react'
import { fireEvent, render, screen } from '@testing-library/react'

import type { SiteAcquisitionResult } from '../../../../api/siteAcquisition'
import type { DevelopmentScenario } from '../../../../api/agents'
import { DeveloperResults } from './DeveloperResults'

let currentProjectValue: { id: string; name: string } | null = null

vi.mock('../../../../contexts/useProject', () => ({
  useProject: () => ({
    currentProject: currentProjectValue,
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

let previewMetadataErrorValue: string | null = null
let lastMultiScenarioProps: unknown = null
let lastInsightProps: unknown = null

const mockUseCaptureScenarioComparison = vi.fn()

function buildResult(): SiteAcquisitionResult {
  return {
    propertyId: 'prop-123',
    currencySymbol: 'S$',
    address: { fullAddress: '1 Cyber Ave', district: 'Downtown' },
    quickAnalysis: {
      generatedAt: '2026-01-06T10:00:00Z',
      scenarios: [],
    },
    buildEnvelope: {
      zoneCode: 'C',
      zoneDescription: 'Commercial',
      siteAreaSqm: 5000,
      allowablePlotRatio: 4.2,
      maxBuildableGfaSqm: 21000,
      currentGfaSqm: 18000,
      additionalPotentialGfaSqm: 3000,
      buildingHeightLimitM: 120,
      siteCoveragePct: 80,
      assumptions: [],
      sourceReference: null,
    },
    visualization: {
      status: 'queued',
      previewAvailable: false,
      notes: [],
      conceptMeshUrl: null,
      previewMetadataUrl: null,
      thumbnailUrl: null,
      cameraOrbitHint: null,
      previewSeed: null,
      previewJobId: null,
      massingLayers: [],
      colorLegend: [],
    },
    optimizations: [],
    financialSummary: {
      totalEstimatedRevenueSgd: null,
      totalEstimatedCapexSgd: null,
      dominantRiskProfile: null,
      notes: [],
      financeBlueprint: null,
    },
    heritageContext: null,
    previewJobs: [],
    previewJob: null,
  } as SiteAcquisitionResult
}

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

vi.mock('../../site-acquisition/hooks/useCaptureScenarioComparison', () => ({
  useCaptureScenarioComparison: (...args: unknown[]) =>
    mockUseCaptureScenarioComparison(...args),
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

vi.mock('../../site-acquisition/components/OptimalIntelligenceCard', () => ({
  OptimalIntelligenceCard: ({
    insight,
    isGenerating,
    onGenerateReport,
  }: {
    insight: string | null
    isGenerating: boolean
    onGenerateReport?: () => Promise<void>
  }) => {
    lastInsightProps = { insight, isGenerating }
    return (
      <div data-testid="ai-insight">
        <div data-testid="ai-insight-text">{insight ?? ''}</div>
        <div data-testid="ai-is-generating">
          {isGenerating ? 'generating' : 'idle'}
        </div>
        {onGenerateReport ? (
          <button type="button" onClick={() => void onGenerateReport()}>
            generate-report
          </button>
        ) : null}
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
    currentProjectValue = null
    previewMetadataErrorValue = null
    lastMultiScenarioProps = null
    lastInsightProps = null

    mockUseCaptureScenarioComparison.mockImplementation(() => ({
      quickAnalysisScenarios: [
        {
          scenario: 'raw_land',
          metrics: {
            potential_gfa_sqm: 20000,
            plot_ratio: 4,
            site_area_sqm: 5000,
          },
        },
        {
          scenario: 'existing_building',
          metrics: { gfa_uplift_sqm: 1800 },
        },
      ],
      comparisonScenarios: [],
      scenarioComparisonData: [],
      formatScenarioLabel: (scenario: string) =>
        scenario === 'raw_land'
          ? 'Raw Land'
          : scenario === 'existing_building'
            ? 'Renovation'
            : scenario,
    }))
  })

  it('wires preview handlers and shows the due diligence handoff', () => {
    render(
      <DeveloperResults
        result={buildResult()}
        selectedScenarios={
          ['raw_land', 'existing_building'] as DevelopmentScenario[]
        }
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

    const dueDiligenceLink = screen.getByRole('link', {
      name: /view due diligence/i,
    })
    expect(dueDiligenceLink).toHaveAttribute('href', '/app/due-diligence')
  })

  it('uses the project-scoped due diligence path when a project is active', () => {
    currentProjectValue = { id: 'proj-9', name: 'Project Nine' }

    render(
      <DeveloperResults
        result={buildResult()}
        selectedScenarios={['raw_land'] as DevelopmentScenario[]}
      />,
    )

    const dueDiligenceLink = screen.getByRole('link', {
      name: /view due diligence/i,
    })
    expect(dueDiligenceLink).toHaveAttribute(
      'href',
      '/projects/proj-9/due-diligence',
    )
  })

  it('derives capture feasibility signals from instant envelope metrics and passes them to MultiScenarioComparisonSection', () => {
    render(
      <DeveloperResults
        result={buildResult()}
        selectedScenarios={
          ['raw_land', 'existing_building'] as DevelopmentScenario[]
        }
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
    expect(props?.feasibilitySignals[1]?.scenario).toBe('existing_building')
    expect(props?.feasibilitySignals[1]?.opportunities.length).toBeGreaterThan(
      0,
    )
  })

  it('passes no feasibility signals when quick analysis scenarios are missing', () => {
    mockUseCaptureScenarioComparison.mockImplementationOnce(() => ({
      quickAnalysisScenarios: [],
      comparisonScenarios: [],
      scenarioComparisonData: [],
      formatScenarioLabel: (scenario: string) =>
        scenario === 'raw_land'
          ? 'Raw Land'
          : scenario === 'existing_building'
            ? 'Renovation'
            : scenario,
    }))

    render(
      <DeveloperResults
        result={buildResult()}
        selectedScenarios={
          ['raw_land', 'existing_building'] as DevelopmentScenario[]
        }
      />,
    )

    expect(
      screen.getByTestId('multi-scenario').getAttribute('data-signals'),
    ).toBe('0')
  })

  it('renders instant capture insight text without a report CTA', () => {
    render(
      <DeveloperResults
        result={buildResult()}
        selectedScenarios={
          ['raw_land', 'existing_building'] as DevelopmentScenario[]
        }
      />,
    )

    expect(screen.getByTestId('ai-insight-text').textContent).toContain(
      'Instant capture analysis for Downtown highlights',
    )
    expect(screen.getByTestId('ai-is-generating').textContent).toBe('idle')
    expect(
      screen.queryByRole('button', { name: /generate-report/i }),
    ).not.toBeInTheDocument()
    expect(lastInsightProps).toBeTruthy()
  })

  it('renders preview metadata errors when present', () => {
    previewMetadataErrorValue = 'Preview metadata failed'

    render(
      <DeveloperResults
        result={buildResult()}
        selectedScenarios={
          ['raw_land', 'existing_building'] as DevelopmentScenario[]
        }
      />,
    )

    expect(screen.getByText(/Preview metadata failed/i)).toBeInTheDocument()
  })

  it('updates active scenario and propagates it to MultiScenarioComparisonSection', () => {
    render(
      <DeveloperResults
        result={buildResult()}
        selectedScenarios={
          ['raw_land', 'existing_building'] as DevelopmentScenario[]
        }
      />,
    )

    const module = screen.getByTestId('multi-scenario')
    expect(module.getAttribute('data-active')).toBe('raw_land')

    fireEvent.click(screen.getByRole('button', { name: /all scenarios/i }))
    expect(module.getAttribute('data-active')).toBe('all')

    fireEvent.click(screen.getByRole('button', { name: /renovation/i }))
    expect(module.getAttribute('data-active')).toBe('existing_building')
  })
})
