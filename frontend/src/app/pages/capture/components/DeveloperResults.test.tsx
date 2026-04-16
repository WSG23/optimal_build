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
    window.localStorage.clear()
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
            : scenario === 'heritage_property'
              ? 'Heritage Integration'
              : scenario === 'underused_asset'
                ? 'Adaptive Reuse'
                : scenario === 'mixed_use_redevelopment'
                  ? 'Mixed-Use Redevelopment'
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
    result.previewJobs = [
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
        starterModelAssumptions: {
          wallThicknessMm: 210,
          coreRatioPct: 15,
          commonAreaRatioPct: 11,
          floorToFloorM: 3.7,
          clearCeilingM: 2.7,
          hvacSpaceRatioPct: 7,
          electricalSpaceRatioPct: 4,
          structuralGridNote: 'preserve existing bulk',
          source: 'hybrid',
          retentionStrategy: 'preserve_existing_bulk',
          efficiencyFactor: 0.96,
          provenance: {
            summary: 'rules_with_property_adjustments',
            fields: {
              floor_to_floor_m: 'property_specific',
              efficiency_factor: 'property_specific',
              wall_thickness_mm: 'rules',
            },
            adjustments: ['older_building_age'],
          },
        },
      },
    ] as SiteAcquisitionResult['previewJobs']
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
        starterModelAssumptions: {
          wallThicknessMm: 210,
          coreRatioPct: 15,
          commonAreaRatioPct: 11,
          floorToFloorM: 3.7,
          clearCeilingM: 2.7,
          hvacSpaceRatioPct: 7,
          electricalSpaceRatioPct: 4,
          structuralGridNote: 'preserve existing bulk',
          source: 'hybrid',
          retentionStrategy: 'preserve_existing_bulk',
          efficiencyFactor: 0.96,
          provenance: {
            summary: 'rules_with_property_adjustments',
            fields: {
              floor_to_floor_m: 'property_specific',
              efficiency_factor: 'property_specific',
              wall_thickness_mm: 'rules',
            },
            adjustments: ['older_building_age'],
          },
        },
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
    expect(screen.getByText('Starter Model Assumptions')).toBeInTheDocument()
    expect(
      screen.getByText('The renovation starter model is ready for review.'),
    ).toBeInTheDocument()
    expect(screen.getByText('Capture Recommendation')).toBeInTheDocument()
    expect(
      screen.getByText(
        'User-selected renovation overrides the default capture recommendation.',
      ),
    ).toBeInTheDocument()
    expect(screen.getByText('ready')).toBeInTheDocument()
    expect(
      screen.getByText(/Geometry scope: massing stack/i),
    ).toBeInTheDocument()
    expect(screen.getByText(/Estimated floors: 6/i)).toBeInTheDocument()
    expect(
      screen.getByText(/Capture recommended: Adaptive Reuse/i),
    ).toBeInTheDocument()
    expect(screen.getByText(/Mode: User override/i)).toBeInTheDocument()
    expect(
      screen.getByText(
        /Code fit: Current GFA remains below today’s code envelope/i,
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        /Floor-to-floor 3.7 m \/ clear ceiling 2.7 m \(property-specific\)/i,
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/Wall thickness 210 mm \/ core ratio 15% \(rules\)/i),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        /Retention strategy preserve existing bulk \/ efficiency factor 0.96 \(property-specific\)/i,
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        /Assumption source: Rule defaults with property-specific adjustments \(older building age\)\./i,
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        /Pinned by site facts: efficiency factor, floor-to-floor\./i,
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/Starter defaults still tunable: wall thickness\./i),
    ).toBeInTheDocument()

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

    expect(screen.getByText('Current Scenario Override')).toBeInTheDocument()
    expect(
      screen.getByText(/Capture recommended: Adaptive Reuse/i),
    ).toBeInTheDocument()
    expect(lastPreviewViewerProps).toMatchObject({
      previewUrl: '/static/dev-previews/example/renovation.gltf',
      metadataUrl: '/static/dev-previews/example/renovation.json',
      thumbnailUrl: '/static/dev-previews/example/renovation.png',
      status: 'ready',
    })
    expect(lastUsePreviewJobOptions).toMatchObject({
      preferredScenario: 'existing_building',
    })
    expect(screen.getByText(/Mode: Exploratory override/i)).toBeInTheDocument()
    expect(
      screen.getByText(
        /This scenario selection is temporary for the current session and does not update learned defaults\./i,
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        /Exploratory renovation override is active for this session\./i,
      ),
    ).toBeInTheDocument()
  })

  it('updates starter model assumptions when the user overrides to a ground-up scenario', () => {
    const result = buildResult()
    previewJobsByScenarioValue = {}

    render(
      <DeveloperResults
        result={result}
        selectedScenarios={
          ['raw_land', 'existing_building'] as DevelopmentScenario[]
        }
      />,
    )

    expect(
      screen.getByText(
        /Floor-to-floor 3.9 m \/ clear ceiling 2.8 m \(heuristic fallback\)/i,
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/Assumption source: Frontend fallback defaults\./i),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        /Capture is using fallback assumptions because no scenario-specific preview jobs are attached to this property yet\./i,
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        /Starter defaults still tunable: retention strategy, floor-to-floor, clear ceiling, wall thickness, core ratio, common area, HVAC, electrical\./i,
      ),
    ).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /raw land/i }))

    expect(screen.getByText('Current Scenario Override')).toBeInTheDocument()
    expect(
      screen.getByText(/Capture recommended: Adaptive Reuse/i),
    ).toBeInTheDocument()
    expect(screen.getByText(/Mode: Exploratory override/i)).toBeInTheDocument()
    expect(
      screen.getByText(
        /Floor-to-floor 4.2 m \/ clear ceiling 3.2 m \(heuristic fallback\)/i,
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        /Wall thickness 250 mm \/ core ratio 18% \(heuristic fallback\)/i,
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        /Capture is using fallback assumptions because no scenario-specific preview jobs are attached to this property yet\./i,
      ),
    ).toBeInTheDocument()
  })

  it('explains when an override is using provisional assumptions while the recommended preview is still shown', () => {
    const result = buildResult()
    result.heritageContext = {
      flag: true,
      risk: 'medium',
      notes: [],
      constraints: ['Conservation review required'],
      assumption: null,
      overlay: {
        name: 'Heritage overlay detected',
        source: 'URA',
        heritagePremiumPct: null,
      },
    }
    result.visualization = {
      ...result.visualization,
      status: 'ready',
      previewAvailable: true,
      previewJobId: 'preview-heritage',
      conceptMeshUrl: '/static/dev-previews/example/heritage-preview.gltf',
      previewMetadataUrl: '/static/dev-previews/example/heritage-preview.json',
      thumbnailUrl: '/static/dev-previews/example/heritage-preview.png',
    }
    result.previewJobs = [
      {
        id: 'preview-heritage',
        propertyId: 'prop-123',
        scenario: 'heritage_property',
        status: 'ready',
        previewUrl: '/static/dev-previews/example/heritage-preview.gltf',
        metadataUrl: '/static/dev-previews/example/heritage-preview.json',
        thumbnailUrl: '/static/dev-previews/example/heritage-preview.png',
        assetVersion: '20260413125700',
        requestedAt: '2026-04-13T12:57:00Z',
        startedAt: '2026-04-13T12:57:02Z',
        finishedAt: '2026-04-13T12:57:05Z',
        message: null,
        geometryDetailLevel: 'medium',
        starterModelAssumptions: {
          wallThicknessMm: 240,
          coreRatioPct: 14,
          commonAreaRatioPct: 14,
          floorToFloorM: 3.6,
          clearCeilingM: 2.7,
          hvacSpaceRatioPct: 9,
          electricalSpaceRatioPct: 5,
          structuralGridNote: 'conservation retention',
          source: 'rules',
          retentionStrategy: 'conservation_retention',
          efficiencyFactor: 0.92,
          provenance: {
            summary: 'rules_with_property_adjustments',
            fields: {
              retention_strategy: 'property_specific',
              efficiency_factor: 'property_specific',
            },
            adjustments: ['heritage_context'],
          },
        },
      },
    ] as SiteAcquisitionResult['previewJobs']
    previewJobsByScenarioValue = {
      heritage_property: result.previewJobs[0]!,
    }

    render(
      <DeveloperResults
        result={result}
        selectedScenarios={
          ['raw_land', 'heritage_property'] as DevelopmentScenario[]
        }
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: /raw land/i }))

    expect(
      screen.getByText(
        /The raw land starter model is not ready yet\. Capture is still showing the heritage integration preview until a scenario-specific model is available\./i,
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        /Requested scenario: Raw Land\. The preview above still reflects Heritage Integration until a scenario-specific starter model is ready\./i,
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        /Floor-to-floor 4.2 m \/ clear ceiling 3.2 m \(heuristic fallback\)/i,
      ),
    ).toBeInTheDocument()
  })

  it('can promote an exploratory scenario to a saved project override', () => {
    currentProjectValue = { id: 'proj-9', name: 'Project Nine' }
    const result = buildResult()

    render(
      <DeveloperResults
        result={result}
        selectedScenarios={
          ['raw_land', 'existing_building'] as DevelopmentScenario[]
        }
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: /renovation/i }))

    expect(screen.getByText(/Mode: Exploratory override/i)).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /save as project override/i }),
    ).toBeInTheDocument()

    fireEvent.click(
      screen.getByRole('button', { name: /save as project override/i }),
    )

    expect(screen.getByText('Saved Scenario Override')).toBeInTheDocument()
    expect(
      screen.getByText(/Mode: Saved project override/i),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        /This override is saved for the project and will continue to guide downstream work\./i,
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /clear saved override/i }),
    ).toBeInTheDocument()
    expect(window.localStorage.getItem('ob_capture_override:proj-9')).toContain(
      'existing_building',
    )
  })

  it('restores a saved project override when the project is reopened', () => {
    currentProjectValue = { id: 'proj-9', name: 'Project Nine' }
    window.localStorage.setItem(
      'ob_capture_override:proj-9',
      JSON.stringify({
        projectId: 'proj-9',
        scenario: 'existing_building',
        savedAt: '2026-04-10T10:00:00Z',
      }),
    )

    render(
      <DeveloperResults
        result={buildResult()}
        selectedScenarios={
          ['raw_land', 'existing_building'] as DevelopmentScenario[]
        }
      />,
    )

    expect(
      screen.getByText(/Mode: Saved project override/i),
    ).toBeInTheDocument()
    expect(screen.getByText('Saved Scenario Override')).toBeInTheDocument()
    expect(
      screen.getByText(
        /renovation is applied as the saved project override\./i,
      ),
    ).toBeInTheDocument()
  })

  it('prefers backend starter-model assumptions from the active preview job over the stale capture snapshot', () => {
    const result = buildResult()
    result.previewJobs = [
      {
        id: 'legacy-preview',
        propertyId: 'prop-123',
        scenario: 'heritage_property',
        status: 'ready',
        previewUrl: '/static/dev-previews/example/legacy-heritage.gltf',
        metadataUrl: '/static/dev-previews/example/legacy-heritage.json',
        thumbnailUrl: '/static/dev-previews/example/legacy-heritage.png',
        assetVersion: '20260407093405',
        requestedAt: '2026-01-06T10:00:00Z',
        startedAt: '2026-01-06T10:00:02Z',
        finishedAt: '2026-01-06T10:00:10Z',
        message: null,
        geometryDetailLevel: 'medium',
      },
    ] as SiteAcquisitionResult['previewJobs']
    result.heritageContext = {
      flag: true,
      risk: 'medium',
      notes: [],
      constraints: ['Conservation dialogue required'],
      assumption: null,
      overlay: {
        name: 'Heritage overlay detected',
        source: 'URA',
        heritagePremiumPct: null,
      },
    }
    previewJobsByScenarioValue = {
      heritage_property: {
        id: 'fresh-preview',
        propertyId: 'prop-123',
        scenario: 'heritage_property',
        status: 'ready',
        previewUrl: '/static/dev-previews/example/fresh-heritage.gltf',
        metadataUrl: '/static/dev-previews/example/fresh-heritage.json',
        thumbnailUrl: '/static/dev-previews/example/fresh-heritage.png',
        assetVersion: '20260407093406',
        requestedAt: '2026-01-06T10:05:00Z',
        startedAt: '2026-01-06T10:05:02Z',
        finishedAt: '2026-01-06T10:05:10Z',
        message: null,
        geometryDetailLevel: 'medium',
        starterModelAssumptions: {
          wallThicknessMm: 240,
          coreRatioPct: 14,
          commonAreaRatioPct: 14,
          floorToFloorM: 3.6,
          clearCeilingM: 2.7,
          hvacSpaceRatioPct: 9,
          electricalSpaceRatioPct: 5,
          structuralGridNote: 'conservation retention',
          source: 'hybrid',
          retentionStrategy: 'conservation_retention',
          efficiencyFactor: 0.92,
          provenance: {
            summary: 'rules_with_property_adjustments',
            fields: {
              retention_strategy: 'property_specific',
              efficiency_factor: 'property_specific',
              floor_to_floor_m: 'rules',
              clear_ceiling_m: 'rules',
              wall_thickness_mm: 'rules',
              core_ratio_pct: 'rules',
              common_area_ratio_pct: 'rules',
              hvac_space_ratio_pct: 'rules',
              electrical_space_ratio_pct: 'rules',
            },
            adjustments: ['heritage_context'],
          },
        },
      },
    }

    render(
      <DeveloperResults
        result={result}
        selectedScenarios={['heritage_property'] as DevelopmentScenario[]}
      />,
    )

    expect(
      screen.getByText(
        /Assumption source: Rule defaults with property-specific adjustments \(heritage context\)\./i,
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        /Floor-to-floor 3.6 m \/ clear ceiling 2.7 m \(rules\)/i,
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        /Retention strategy conservation retention \/ efficiency factor 0.92 \(property-specific\)/i,
      ),
    ).toBeInTheDocument()
    expect(
      screen.queryByText(/Frontend fallback defaults/i),
    ).not.toBeInTheDocument()
    expect(
      screen.queryByText(/Capture is using fallback assumptions/i),
    ).not.toBeInTheDocument()
    expect(
      screen.getByText(
        /Pinned by site facts: retention strategy, efficiency factor\./i,
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        /Starter defaults still tunable: floor-to-floor, clear ceiling, wall thickness, core ratio, common area, HVAC, electrical\./i,
      ),
    ).toBeInTheDocument()
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
