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
const mockHandleEnsureStarterModel = vi.fn()
const mockHandleToggleLayerVisibility = vi.fn()
const mockHandleSoloPreviewLayer = vi.fn()
const mockHandleFocusLayer = vi.fn()
const mockSetPreviewDetailLevel = vi.fn()

let previewMetadataErrorValue: string | null = null
let previewGenerationErrorValue: string | null = null
let isGeneratingStarterModelValue = false
let lastMultiScenarioProps: unknown = null
let lastInsightProps: unknown = null
let lastPreviewViewerProps: unknown = null
let lastUsePreviewJobOptions: unknown = null
let lastOverviewCardArgs: unknown = null
let previewJobsByScenarioValue: Record<string, unknown> = {}

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
    previewJob,
    formatters,
  }: {
    previewJob: unknown
    formatters: {
      formatNumber: (value: number) => string
      formatCurrency: (value: number) => string
      formatTimestamp: (timestamp?: string | null) => string
    }
  }) => {
    lastOverviewCardArgs = { previewJob }
    formatters.formatNumber(1.23)
    formatters.formatCurrency(1234)
    formatters.formatTimestamp(null)
    formatters.formatTimestamp('not-a-real-date')
    return []
  },
}))

vi.mock('../../site-acquisition/hooks/usePreviewJob', () => ({
  usePreviewJob: (options: unknown) => {
    lastUsePreviewJobOptions = options
    const preferredScenario =
      typeof options === 'object' &&
      options !== null &&
      'preferredScenario' in options
        ? String(
            (options as { preferredScenario?: string | null })
              .preferredScenario ?? '',
          )
        : ''
    const previewJob = preferredScenario
      ? (previewJobsByScenarioValue[preferredScenario] ?? null)
      : null
    return {
      previewJob,
      previewDetailLevel: 'medium',
      setPreviewDetailLevel: mockSetPreviewDetailLevel,
      isRefreshingPreview: false,
      isGeneratingStarterModel: isGeneratingStarterModelValue,
      hasPreferredScenarioPreview: Boolean(previewJob),
      previewGenerationError: previewGenerationErrorValue,
      previewLayerMetadata: [],
      previewLayerVisibility: {},
      previewFocusLayerId: null,
      isPreviewMetadataLoading: false,
      previewMetadataError: previewMetadataErrorValue,
      hiddenLayerCount: 0,
      colorLegendEntries: [],
      legendHasPendingChanges: false,
      handleEnsureStarterModel: mockHandleEnsureStarterModel,
      handleRefreshPreview: mockHandleRefreshPreview,
      handleToggleLayerVisibility: mockHandleToggleLayerVisibility,
      handleSoloPreviewLayer: mockHandleSoloPreviewLayer,
      handleShowAllLayers: vi.fn(),
      handleFocusLayer: mockHandleFocusLayer,
      handleResetLayerFocus: vi.fn(),
      handleLegendEntryChange: vi.fn(),
      handleLegendReset: vi.fn(),
    }
  },
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
  Preview3DViewer: (props: unknown) => {
    lastPreviewViewerProps = props
    return <div data-testid="preview-3d" />
  },
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
    previewGenerationErrorValue = null
    isGeneratingStarterModelValue = false
    lastMultiScenarioProps = null
    lastInsightProps = null
    lastPreviewViewerProps = null
    lastUsePreviewJobOptions = null
    lastOverviewCardArgs = null
    previewJobsByScenarioValue = {
      underused_asset: {
        id: 'preview-underused',
        propertyId: 'prop-123',
        scenario: 'underused_asset',
        status: 'queued',
        previewUrl: null,
        metadataUrl: null,
        thumbnailUrl: null,
        assetVersion: null,
        requestedAt: '2026-01-06T10:00:00Z',
        startedAt: null,
        finishedAt: null,
        message: null,
        geometryDetailLevel: 'medium',
      },
    }

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
            : scenario === 'underused_asset'
              ? 'Adaptive Reuse'
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

    fireEvent.click(
      screen.getByRole('button', { name: /refresh starter model/i }),
    )
    expect(mockHandleEnsureStarterModel).toHaveBeenCalled()

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
    expect(screen.getByTestId('ai-insight-text').textContent).toContain(
      'Capture currently recommends Adaptive Reuse first.',
    )
    expect(screen.getByTestId('ai-insight-text').textContent).toContain(
      'with no setback or floor-by-floor compliance modelling',
    )
    expect(screen.getByTestId('ai-is-generating').textContent).toBe('idle')
    expect(
      screen.queryByRole('button', { name: /generate-report/i }),
    ).not.toBeInTheDocument()
    expect(lastInsightProps).toBeTruthy()
  })

  it('renders the capture recommendation and starter-model summary from CaptureResultV2', () => {
    const result = buildResult()
    result.previewJobs = [
      {
        id: 'preview-1',
        propertyId: 'prop-123',
        scenario: 'raw_land',
        status: 'ready',
        previewUrl: '/static/dev-previews/example/raw-land.gltf',
        metadataUrl: '/static/dev-previews/example/raw-land.json',
        thumbnailUrl: '/static/dev-previews/example/raw-land.png',
        assetVersion: '20260407093405',
        requestedAt: '2026-01-06T10:00:00Z',
        startedAt: '2026-01-06T10:00:02Z',
        finishedAt: '2026-01-06T10:00:10Z',
        message: null,
        geometryDetailLevel: 'medium',
      },
      {
        id: 'preview-2',
        propertyId: 'prop-123',
        scenario: 'existing_building',
        status: 'ready',
        previewUrl: '/static/dev-previews/example/preview.gltf',
        metadataUrl: '/static/dev-previews/example/preview.json',
        thumbnailUrl: '/static/dev-previews/example/thumb.png',
        assetVersion: '20260407093405',
        requestedAt: '2026-01-06T10:00:00Z',
        startedAt: '2026-01-06T10:00:02Z',
        finishedAt: '2026-01-06T10:00:10Z',
        message: null,
        geometryDetailLevel: 'medium',
      },
    ] as SiteAcquisitionResult['previewJobs']
    result.visualization = {
      ...result.visualization,
      status: 'ready',
      previewAvailable: true,
      conceptMeshUrl: '/static/dev-previews/example/preview.gltf',
      previewMetadataUrl: '/static/dev-previews/example/preview.json',
      thumbnailUrl: '/static/dev-previews/example/thumb.png',
      massingLayers: [
        {
          assetType: 'office',
          allocationPct: 100,
          gfaSqm: 21000,
          niaSqm: 17850,
          estimatedHeightM: 24,
          color: '#3366ff',
        },
      ],
    }
    previewJobsByScenarioValue = {
      existing_building: {
        id: 'preview-2',
        propertyId: 'prop-123',
        scenario: 'existing_building',
        status: 'ready',
        previewUrl: '/static/dev-previews/example/preview.gltf',
        metadataUrl: '/static/dev-previews/example/preview.json',
        thumbnailUrl: '/static/dev-previews/example/thumb.png',
        assetVersion: '20260407093405',
        requestedAt: '2026-01-06T10:00:00Z',
        startedAt: '2026-01-06T10:00:02Z',
        finishedAt: '2026-01-06T10:00:10Z',
        message: null,
        geometryDetailLevel: 'medium',
      },
    }

    render(
      <DeveloperResults
        result={result}
        selectedScenarios={['existing_building'] as DevelopmentScenario[]}
      />,
    )

    expect(screen.getByText('Capture Recommendation')).toBeInTheDocument()
    expect(screen.getByText('Starter Model Status')).toBeInTheDocument()
    expect(
      screen.getByText('The renovation starter model is ready for review.'),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        'User-selected existing building overrides the default capture recommendation.',
      ),
    ).toBeInTheDocument()
    expect(screen.getByText('ready')).toBeInTheDocument()
    expect(
      screen.getByText(/Geometry scope: massing stack/i),
    ).toBeInTheDocument()
    expect(screen.getByText(/Estimated floors: 6/i)).toBeInTheDocument()
    expect(screen.getByText(/Recommended: Renovation/i)).toBeInTheDocument()

    expect(lastPreviewViewerProps).toMatchObject({
      previewUrl: '/static/dev-previews/example/preview.gltf',
      metadataUrl: '/static/dev-previews/example/preview.json',
      status: 'ready',
      thumbnailUrl: '/static/dev-previews/example/thumb.png',
    })
    expect(lastUsePreviewJobOptions).toMatchObject({
      preferredScenario: 'existing_building',
    })
    expect(lastOverviewCardArgs).toMatchObject({
      previewJob: expect.objectContaining({ scenario: 'existing_building' }),
    })
  })

  it('switches the starter model to the user-selected scenario when scenario focus overrides the recommendation', () => {
    const result = buildResult()
    result.previewJobs = [
      {
        id: 'preview-1',
        propertyId: 'prop-123',
        scenario: 'raw_land',
        status: 'ready',
        previewUrl: '/static/dev-previews/example/raw-land.gltf',
        metadataUrl: '/static/dev-previews/example/raw-land.json',
        thumbnailUrl: '/static/dev-previews/example/raw-land.png',
        assetVersion: '20260407093405',
        requestedAt: '2026-01-06T10:00:00Z',
        startedAt: '2026-01-06T10:00:02Z',
        finishedAt: '2026-01-06T10:00:10Z',
        message: null,
        geometryDetailLevel: 'medium',
      },
      {
        id: 'preview-2',
        propertyId: 'prop-123',
        scenario: 'existing_building',
        status: 'ready',
        previewUrl: '/static/dev-previews/example/renovation.gltf',
        metadataUrl: '/static/dev-previews/example/renovation.json',
        thumbnailUrl: '/static/dev-previews/example/renovation.png',
        assetVersion: '20260407093406',
        requestedAt: '2026-01-06T10:01:00Z',
        startedAt: '2026-01-06T10:01:02Z',
        finishedAt: '2026-01-06T10:01:10Z',
        message: null,
        geometryDetailLevel: 'medium',
      },
    ] as SiteAcquisitionResult['previewJobs']
    result.visualization = {
      ...result.visualization,
      status: 'ready',
      previewAvailable: true,
      conceptMeshUrl: '/static/dev-previews/example/fallback.gltf',
      previewMetadataUrl: '/static/dev-previews/example/fallback.json',
      thumbnailUrl: '/static/dev-previews/example/fallback.png',
      massingLayers: [
        {
          assetType: 'office',
          allocationPct: 100,
          gfaSqm: 21000,
          niaSqm: 17850,
          estimatedHeightM: 24,
          color: '#3366ff',
        },
      ],
    }
    previewJobsByScenarioValue = {
      existing_building: {
        id: 'preview-2',
        propertyId: 'prop-123',
        scenario: 'existing_building',
        status: 'ready',
        previewUrl: '/static/dev-previews/example/renovation.gltf',
        metadataUrl: '/static/dev-previews/example/renovation.json',
        thumbnailUrl: '/static/dev-previews/example/renovation.png',
        assetVersion: '20260407093406',
        requestedAt: '2026-01-06T10:01:00Z',
        startedAt: '2026-01-06T10:01:02Z',
        finishedAt: '2026-01-06T10:01:10Z',
        message: null,
        geometryDetailLevel: 'medium',
      },
    }

    render(
      <DeveloperResults
        result={result}
        selectedScenarios={
          ['raw_land', 'existing_building'] as DevelopmentScenario[]
        }
      />,
    )

    expect(screen.getByText(/Recommended: Adaptive Reuse/i)).toBeInTheDocument()
    expect(lastPreviewViewerProps).toMatchObject({
      previewUrl: '/static/dev-previews/example/fallback.gltf',
      status: 'ready',
    })

    fireEvent.click(screen.getByRole('button', { name: /renovation/i }))

    expect(lastPreviewViewerProps).toMatchObject({
      previewUrl: '/static/dev-previews/example/renovation.gltf',
      metadataUrl: '/static/dev-previews/example/renovation.json',
      thumbnailUrl: '/static/dev-previews/example/renovation.png',
      status: 'ready',
    })
    expect(lastUsePreviewJobOptions).toMatchObject({
      preferredScenario: 'existing_building',
    })
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

  it('auto-requests a starter model when the preferred scenario has no preview yet', () => {
    previewJobsByScenarioValue = {}

    render(
      <DeveloperResults
        result={buildResult()}
        selectedScenarios={
          ['raw_land', 'existing_building'] as DevelopmentScenario[]
        }
      />,
    )

    expect(
      screen.getByRole('button', { name: /generate starter model/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/starter model has been queued/i),
    ).toBeInTheDocument()
    expect(mockHandleEnsureStarterModel).toHaveBeenCalledTimes(1)
  })

  it('shows active generation copy while a starter model request is in flight', () => {
    previewJobsByScenarioValue = {}
    isGeneratingStarterModelValue = true

    render(
      <DeveloperResults
        result={buildResult()}
        selectedScenarios={
          ['raw_land', 'existing_building'] as DevelopmentScenario[]
        }
      />,
    )

    expect(
      screen.getByRole('button', { name: /generating starter model/i }),
    ).toBeDisabled()
    expect(
      screen.getByText(
        /Capture is generating the adaptive reuse starter model now/i,
      ),
    ).toBeInTheDocument()
  })

  it('shows generate starter model action and generation errors when no preferred preview exists yet', () => {
    previewJobsByScenarioValue = {}
    previewGenerationErrorValue =
      'Scenario-specific starter model generation is not available yet.'

    render(
      <DeveloperResults
        result={buildResult()}
        selectedScenarios={
          ['raw_land', 'existing_building'] as DevelopmentScenario[]
        }
      />,
    )

    expect(
      screen.getByRole('button', { name: /generate starter model/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        /Scenario-specific starter model generation is not available yet/i,
      ),
    ).toBeInTheDocument()
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
    expect(module.getAttribute('data-active')).toBe('all')

    fireEvent.click(screen.getByRole('button', { name: /all scenarios/i }))
    expect(module.getAttribute('data-active')).toBe('all')

    fireEvent.click(screen.getByRole('button', { name: /renovation/i }))
    expect(module.getAttribute('data-active')).toBe('existing_building')
  })

  it('keeps the post-scan workspace model-first with layer inspection below supporting facts', () => {
    render(
      <DeveloperResults
        result={buildResult()}
        selectedScenarios={
          ['raw_land', 'existing_building'] as DevelopmentScenario[]
        }
      />,
    )

    const preview = screen.getByTestId('preview-3d')
    const recommendation = screen.getByText('Capture Recommendation')
    const comparison = screen.getByTestId('multi-scenario')
    const overview = screen.getByTestId('property-overview')
    const layers = screen.getByTestId('preview-layers')

    expect(
      preview.compareDocumentPosition(recommendation) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy()
    expect(
      recommendation.compareDocumentPosition(comparison) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy()
    expect(
      comparison.compareDocumentPosition(overview) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy()
    expect(
      overview.compareDocumentPosition(layers) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy()
    expect(screen.getByText('Preview Layer Inspection')).toBeInTheDocument()
  })
})
