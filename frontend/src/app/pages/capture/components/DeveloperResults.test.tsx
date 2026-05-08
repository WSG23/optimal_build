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
      grossPlotRatio: 4.2,
      maxBuildableGfaSqm: 21000,
      currentGfaSqm: 18000,
      additionalPotentialGfaSqm: 3000,
      buildingHeightLimitM: 120,
      siteCoveragePct: 80,
      setbackFrontM: null,
      setbackRearM: null,
      setbackSideM: null,
      stepBacks: [],
      airRightsNote: null,
      assumptions: [],
      sourceReference: null,
      ruleCorpusStatus: null,
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
    optimizations: [
      {
        assetType: 'office',
        allocationPct: 60,
        allocatedGfaSqm: 10800,
        niaEfficiency: 0.81,
        targetFloorHeightM: 3.9,
        parkingRatioPer1000Sqm: null,
        rentPsmMonth: null,
        stabilisedVacancyPct: null,
        opexPctOfRent: null,
        estimatedRevenueSgd: null,
        estimatedCapexSgd: null,
        fitoutCostPsm: null,
        absorptionMonths: null,
        riskLevel: null,
        heritagePremiumPct: null,
        notes: [],
      },
      {
        assetType: 'retail',
        allocationPct: 25,
        allocatedGfaSqm: 4500,
        niaEfficiency: 0.78,
        targetFloorHeightM: 4.8,
        parkingRatioPer1000Sqm: null,
        rentPsmMonth: null,
        stabilisedVacancyPct: null,
        opexPctOfRent: null,
        estimatedRevenueSgd: null,
        estimatedCapexSgd: null,
        fitoutCostPsm: null,
        absorptionMonths: null,
        riskLevel: null,
        heritagePremiumPct: null,
        notes: [],
      },
    ],
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

  it('wires preview handlers and shows the due diligence handoff', async () => {
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

    fireEvent.click(
      await screen.findByRole('button', { name: /layer-toggle/i }),
    )
    expect(mockHandleToggleLayerVisibility).toHaveBeenCalledWith('layer-1')

    fireEvent.click(await screen.findByRole('button', { name: /layer-solo/i }))
    expect(mockHandleSoloPreviewLayer).toHaveBeenCalledWith('layer-2')

    fireEvent.click(await screen.findByRole('button', { name: /layer-focus/i }))
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

  it('derives capture feasibility signals from instant envelope metrics and passes them to MultiScenarioComparisonSection', async () => {
    render(
      <DeveloperResults
        result={buildResult()}
        selectedScenarios={
          ['raw_land', 'existing_building'] as DevelopmentScenario[]
        }
      />,
    )

    await screen.findByTestId('multi-scenario')

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

  it('passes no feasibility signals when quick analysis scenarios are missing', async () => {
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
      (await screen.findByTestId('multi-scenario')).getAttribute(
        'data-signals',
      ),
    ).toBe('0')
  })

  it('renders instant capture insight text without a report CTA', async () => {
    render(
      <DeveloperResults
        result={buildResult()}
        selectedScenarios={
          ['raw_land', 'existing_building'] as DevelopmentScenario[]
        }
      />,
    )

    expect(
      (await screen.findByTestId('ai-insight-text')).textContent,
    ).toContain('Instant capture analysis for Downtown highlights')
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
    result.propertyInfo = {
      currentUse: 'Hotel / lodging',
      currentUseEvidence: [
        {
          use: 'Hotel / lodging',
          source: 'google_places_autocomplete',
          confidence: 'medium',
          basis: 'Selected place is tagged as lodging.',
          placeName: 'lyf one-north Singapore',
          placeTypes: ['lodging', 'point_of_interest'],
        },
      ],
    }
    result.buildEnvelope.maxBuildableGfaSqm = result.buildEnvelope.currentGfaSqm
    result.buildEnvelope.additionalPotentialGfaSqm = 0
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
          assetProfiles: [
            {
              assetType: 'office',
              floorToFloorM: 3.7,
              clearCeilingM: 2.7,
              niaEfficiency: 0.82,
              source: 'hybrid',
            },
            {
              assetType: 'retail',
              floorToFloorM: 4.8,
              clearCeilingM: 3.8,
              niaEfficiency: 0.82,
              source: 'hybrid',
            },
          ],
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
          assetProfiles: [
            {
              assetType: 'office',
              floorToFloorM: 3.7,
              clearCeilingM: 2.7,
              niaEfficiency: 0.82,
              source: 'hybrid',
            },
            {
              assetType: 'retail',
              floorToFloorM: 4.8,
              clearCeilingM: 3.8,
              niaEfficiency: 0.82,
              source: 'hybrid',
            },
          ],
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
    expect(screen.getByText('Decision Brief')).toBeInTheDocument()
    expect(screen.getByText("Today's zoning program")).toBeInTheDocument()
    expect(screen.getByText('Office-led renovation mix')).toBeInTheDocument()
    expect(screen.queryByText('Use basis')).not.toBeInTheDocument()
    expect(
      screen.queryByText('Office primary / Retail support'),
    ).not.toBeInTheDocument()
    expect(screen.getByText('Commercial (C)')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Capture is shaping the starter model around office-led program with retail support for renovation within the current-code envelope.',
      ),
    ).toBeInTheDocument()
    expect(screen.getByText('Audit Trail')).toBeInTheDocument()
    expect(screen.queryByText('Program direction')).not.toBeInTheDocument()
    expect(screen.queryByText('Program basis')).not.toBeInTheDocument()
    expect(screen.queryByText('Capture completeness')).not.toBeInTheDocument()
    expect(screen.getByText('Partial capture')).toBeInTheDocument()
    expect(screen.queryByText('Site input')).not.toBeInTheDocument()
    expect(screen.queryByText('Envelope source')).not.toBeInTheDocument()
    expect(screen.queryByText('Use Signals')).not.toBeInTheDocument()
    expect(screen.queryByText('Program signals')).not.toBeInTheDocument()
    const detailsToggle = screen.getByRole('button', {
      name: /show data details/i,
    })
    expect(detailsToggle).toHaveAttribute('aria-expanded', 'false')
    fireEvent.click(detailsToggle)
    expect(detailsToggle).toHaveAttribute('aria-expanded', 'true')
    expect(
      screen.getAllByText("Today's zoning program").length,
    ).toBeGreaterThan(0)
    expect(screen.queryByText('Program basis')).not.toBeInTheDocument()
    expect(screen.getAllByText('Zoning').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Commercial (C)').length).toBeGreaterThan(0)
    expect(screen.getAllByText('GPR').length).toBeGreaterThan(0)
    expect(screen.getAllByText('4.2').length).toBeGreaterThan(0)
    expect(screen.getByText('Capture completeness')).toBeInTheDocument()
    expect(
      screen.getByText(/6 capture inputs are still unresolved/i),
    ).toBeInTheDocument()
    expect(screen.getByText('Site input')).toBeInTheDocument()
    expect(screen.getByText('Site-specific')).toBeInTheDocument()
    expect(
      screen.getByText('Address and coordinates are site-specific.'),
    ).toBeInTheDocument()
    expect(screen.getByText('Current use evidence')).toBeInTheDocument()
    expect(screen.getByText('Current use signal')).toBeInTheDocument()
    expect(
      screen.getByText(/Hotel \/ lodging \(lyf one-north Singapore\)/i),
    ).toBeInTheDocument()
    expect(screen.getByText('Envelope source')).toBeInTheDocument()
    expect(screen.getByText('Source unresolved')).toBeInTheDocument()
    expect(
      screen.getByText('Zoning envelope source is unresolved.'),
    ).toBeInTheDocument()
    expect(screen.getByText('Geometry')).toBeInTheDocument()
    expect(screen.getByText('Starter model pipeline')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Scenario-specific starter model is generated from the preview pipeline.',
      ),
    ).toBeInTheDocument()
    expect(screen.getByText('Program signals')).toBeInTheDocument()
    expect(
      screen.getByText('The renovation starter model is ready for review.'),
    ).toBeInTheDocument()
    expect(screen.getByText('Capture Recommendation')).toBeInTheDocument()
    expect(screen.getByText('ready')).toBeInTheDocument()
    expect(
      screen.getByText(/Geometry scope: massing stack/i),
    ).toBeInTheDocument()
    expect(screen.getByText(/Estimated floors: 6/i)).toBeInTheDocument()
    expect(
      screen.queryByText(/Capture recommended: Adaptive Reuse/i),
    ).not.toBeInTheDocument()
    expect(screen.queryByText(/User override/i)).not.toBeInTheDocument()
    expect(
      screen.getAllByText(/Current GFA appears to match today’s code envelope/i)
        .length,
    ).toBeGreaterThan(0)
    expect(screen.getByText('Vertical profile')).toBeInTheDocument()
    expect(
      screen.getByText('3.7 m floor-to-floor / 2.7 m clear'),
    ).toBeInTheDocument()
    expect(screen.getByText('Structure + core')).toBeInTheDocument()
    expect(screen.getByText('210 mm walls / 15% core')).toBeInTheDocument()
    expect(screen.getByText('Retention + yield')).toBeInTheDocument()
    expect(
      screen.getByText('preserve existing bulk / 0.96 efficiency'),
    ).toBeInTheDocument()
    expect(screen.getByText('Use-Type Profiles')).toBeInTheDocument()
    expect(screen.getAllByText('Office').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Retail').length).toBeGreaterThan(0)
    expect(
      screen.getByText('3.7 m floor-to-floor / 2.7 m clear / 0.82 efficiency'),
    ).toBeInTheDocument()
    expect(screen.getAllByText('Retail').length).toBeGreaterThan(0)
    expect(
      screen.getByText('4.8 m floor-to-floor / 3.8 m clear / 0.82 efficiency'),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        /Assumption source: Rule defaults with property-specific adjustments \(older building age\)\./i,
      ),
    ).toBeInTheDocument()
    expect(screen.getByText('Pinned by site facts')).toBeInTheDocument()
    expect(
      screen.getByText('Model inputs open for refinement'),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        'These values are modeling assumptions, not certified code controls.',
      ),
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
    expect(screen.getAllByText(/Exploratory override/i).length).toBeGreaterThan(
      0,
    )
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

  it('surfaces resolved official source ingestion in the capture data basis', () => {
    const result = buildResult()
    result.buildEnvelope.sourceReference = 'SG Rule Registry (RefRule)'
    result.buildEnvelope.ruleCorpusStatus = {
      coverage_state: 'partial',
      resolved_by: {
        plot_ratio: 'captured_zoning_metadata',
        building_height_limit_m: 'ref_rule',
      },
      unresolved_fields: ['setbacks'],
      official_source_gaps: [
        {
          field: 'setbacks',
          reason: 'not_resolved_from_current_registry',
          candidate_sources: [
            {
              authority: 'URA',
              title: 'Development Control Guidelines',
            },
          ],
        },
      ],
      official_source_ingestion: {
        resolved_count: 1,
        staged_count: 0,
        existing_count: 0,
        failed_count: 0,
        candidates: [
          {
            field: 'building_height_limit_m',
            status: 'resolved',
            rule_id: 202,
          },
        ],
      },
    }

    render(
      <DeveloperResults
        result={result}
        selectedScenarios={['existing_building'] as DevelopmentScenario[]}
      />,
    )

    expect(screen.getByText('Resolved')).toBeInTheDocument()
    expect(
      screen.getByText(
        '1 normalized into approved rules. Normalized source values are now available to the rule resolver.',
      ),
    ).toBeInTheDocument()
    expect(
      screen.queryByText(/height limit - separate official control/i),
    ).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /show data details/i }))
    expect(screen.getByText('Live source scan')).toBeInTheDocument()
  })

  it('keeps the compact recommendation decision-oriented while details stay behind the audit toggle', () => {
    const result = buildResult()
    result.buildEnvelope.sourceReference = 'SG Rule Registry (RefRule)'
    result.buildEnvelope.ruleCorpusStatus = {
      coverage_state: 'partial',
      resolved_by: {
        land_use: 'captured_zoning_metadata',
        plot_ratio: 'captured_zoning_metadata',
        building_height_limit_m: 'ref_rule',
        site_coverage_pct: 'captured_development_constraints',
      },
      unresolved_fields: ['setbacks', 'step_backs', 'air_rights_note'],
      official_source_gaps: [
        {
          field: 'setbacks',
          reason: 'not_resolved_from_current_registry',
          candidate_sources: [
            {
              authority: 'URA',
              title: 'Development Control Guidelines',
            },
          ],
        },
        {
          field: 'step_backs',
          reason: 'not_resolved_from_current_registry',
          candidate_sources: [
            {
              authority: 'URA',
              title: 'Development Control Guidelines',
            },
          ],
        },
        {
          field: 'air_rights_note',
          reason: 'project_specific_clearance_required',
          candidate_sources: [
            {
              authority: 'URA/CAAS',
              title: 'Height control and aviation-related clearance sources',
              resolution_workflow: 'project_specific_clearance',
            },
          ],
        },
      ],
      project_clearance_required: [
        {
          field: 'air_rights_note',
          reason: 'project_specific_clearance_required',
          candidate_sources: [
            {
              authority: 'URA/CAAS',
              title: 'Height control and aviation-related clearance sources',
              resolution_workflow: 'project_specific_clearance',
            },
          ],
        },
      ],
    }

    render(
      <DeveloperResults
        result={result}
        selectedScenarios={['existing_building'] as DevelopmentScenario[]}
      />,
    )

    expect(screen.getByText('Decision Brief')).toBeInTheDocument()
    expect(screen.getByText("Today's zoning program")).toBeInTheDocument()
    expect(screen.queryByText('Use basis')).not.toBeInTheDocument()
    expect(screen.getByText('GFA envelope')).toBeInTheDocument()
    expect(screen.getByText('Code fit')).toBeInTheDocument()
    expect(screen.getByText('Official controls pending')).toBeInTheDocument()
    expect(screen.getByText('Source review needed')).toBeInTheDocument()
    expect(screen.getByText('setbacks, step-backs.')).toBeInTheDocument()
    expect(screen.getByText('Project clearance required')).toBeInTheDocument()
    expect(
      screen.getByText(
        'air-rights clearance (URA/CAAS) requires site-specific aviation and height-clearance review. Capture does not resolve this clearance.',
      ),
    ).toBeInTheDocument()
    expect(screen.queryByText('Capture completeness')).not.toBeInTheDocument()
    expect(screen.queryByText('Control source status')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /show data details/i }))
    expect(screen.getByText('Capture completeness')).toBeInTheDocument()
    expect(
      screen.getByText(
        '2 official controls still need source review (setbacks, step-backs).',
      ),
    ).toBeInTheDocument()
    expect(screen.getByText('Control source status')).toBeInTheDocument()
    expect(
      screen.getByText(
        'setbacks (URA), step-backs (URA) have official source categories identified, but Capture has not mapped reviewed values for this zone yet.',
      ),
    ).toBeInTheDocument()
  })

  it('keeps Orchard commercial capture from becoming a false ground-up office assumption', () => {
    const result = buildResult()
    result.address = {
      fullAddress: '2 Orchard Turn, Singapore 238801',
      district: 'Orchard',
    }
    result.existingUse = 'Unknown'
    result.propertyInfo = {
      propertyName: 'ION Orchard',
      tenure: null,
      siteAreaSqm: null,
      gfaApproved: null,
      buildingHeight: null,
      completionYear: null,
      lastTransactionDate: null,
      lastTransactionPrice: null,
    }
    result.optimizations = []
    result.uraZoning = {
      zoneCode: 'SG:commercial',
      zoneDescription: 'Commercial',
      plotRatio: 6.3,
      buildingHeightLimit: null,
      siteCoverage: null,
      useGroups: ['Commercial'],
      specialConditions: null,
      source: 'ref_zoning_layer',
    }
    result.buildEnvelope = {
      ...result.buildEnvelope,
      zoneCode: 'SG:commercial',
      zoneDescription: 'Commercial',
      siteAreaSqm: null,
      allowablePlotRatio: 6.3,
      maxBuildableGfaSqm: null,
      currentGfaSqm: null,
      additionalPotentialGfaSqm: null,
      buildingHeightLimitM: null,
      siteCoveragePct: null,
      sourceReference: 'SG Rule Registry (RefRule + zoning layers)',
      ruleCorpusStatus: {
        coverage_state: 'partial',
        zone_code: 'SG:commercial',
        zone_description: 'Commercial',
        resolved_by: {
          land_use: 'ref_zoning_layer',
          plot_ratio: 'ref_zoning_layer',
          setbacks: 'ref_rule',
          step_backs: 'ref_rule',
        },
        unresolved_fields: [
          'building_height_limit_m',
          'site_coverage_pct',
          'air_rights_note',
        ],
        project_clearance_required: [
          {
            field: 'air_rights_note',
            candidate_sources: [
              {
                authority: 'URA/CAAS',
                resolution_workflow: 'project_specific_clearance',
              },
            ],
          },
        ],
        official_source_gaps: [
          {
            field: 'building_height_limit_m',
            candidate_sources: [{ authority: 'URA' }],
          },
          {
            field: 'site_coverage_pct',
            candidate_sources: [{ authority: 'URA' }],
          },
        ],
      },
    }

    render(
      <DeveloperResults
        result={result}
        selectedScenarios={['existing_building'] as DevelopmentScenario[]}
      />,
    )

    expect(screen.getAllByText('Scenario pending').length).toBeGreaterThan(0)
    expect(screen.getByText('Retail-led program pending')).toBeInTheDocument()
    expect(
      screen.queryByText('Retail primary / Office support'),
    ).not.toBeInTheDocument()
    expect(screen.getByText('Commercial (SG:commercial)')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Current GFA is unavailable, so current-versus-code fit is pending.',
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        'Max GFA cannot be calculated until site area is resolved; current GFA is unavailable.',
      ),
    ).toBeInTheDocument()
    expect(screen.getByText(/Existing GFA unavailable/i)).toBeInTheDocument()
    expect(
      screen.getByText(/Current-code comparison pending/i),
    ).toBeInTheDocument()
    expect(
      screen.queryByText(/No existing GFA detected/i),
    ).not.toBeInTheDocument()
    expect(screen.queryByText(/Ground up baseline/i)).not.toBeInTheDocument()
    expect(
      screen.queryByText('Retail-led renovation mix'),
    ).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /show data details/i }))
    expect(
      screen.getByText('Official land use + plot ratio'),
    ).toBeInTheDocument()
    expect(
      screen.getAllByText(
        'air-rights clearance (URA/CAAS) requires site-specific aviation and height-clearance review. Capture does not resolve this clearance.',
      ).length,
    ).toBeGreaterThan(0)
  })

  it('explains missing max GFA as envelope-control gap when site area is known', () => {
    const result = buildResult()
    result.buildEnvelope.currentGfaSqm = null
    result.buildEnvelope.maxBuildableGfaSqm = null
    result.buildEnvelope.additionalPotentialGfaSqm = null
    result.buildEnvelope.allowablePlotRatio = null
    result.buildEnvelope.siteAreaSqm = 557

    render(
      <DeveloperResults
        result={result}
        selectedScenarios={['existing_building'] as DevelopmentScenario[]}
      />,
    )

    expect(
      screen.getByText(
        'Max GFA cannot be calculated until plot ratio or envelope controls are resolved; current GFA is unavailable.',
      ),
    ).toBeInTheDocument()
  })

  it('presents Marina mixed-use zoning as mixed-use instead of residential-only', () => {
    const result = buildResult()
    result.address = {
      fullAddress: '10 Marina Boulevard, Singapore 018983',
      district: 'Marina Bay',
    }
    result.existingUse = 'Unknown'
    result.propertyInfo = {
      propertyName: null,
      tenure: null,
      siteAreaSqm: null,
      gfaApproved: null,
      buildingHeight: null,
      completionYear: null,
      lastTransactionDate: null,
      lastTransactionPrice: null,
    }
    result.optimizations = []
    result.uraZoning = {
      zoneCode: 'SG:mixed_use',
      zoneDescription: null,
      plotRatio: null,
      buildingHeightLimit: null,
      siteCoverage: null,
      useGroups: ['Commercial', 'Residential', 'Office'],
      specialConditions: null,
      source: 'ref_zoning_layer',
    }
    result.buildEnvelope = {
      ...result.buildEnvelope,
      zoneCode: 'SG:mixed_use',
      zoneDescription: null,
      siteAreaSqm: null,
      allowablePlotRatio: null,
      maxBuildableGfaSqm: null,
      currentGfaSqm: null,
      additionalPotentialGfaSqm: null,
      buildingHeightLimitM: null,
      siteCoveragePct: null,
      sourceReference: 'SG Rule Registry (RefRule + zoning layers)',
      ruleCorpusStatus: {
        coverage_state: 'partial',
        zone_code: 'SG:mixed_use',
        resolved_by: {
          land_use: 'ref_zoning_layer',
          setbacks: 'ref_rule',
          step_backs: 'ref_rule',
        },
        unresolved_fields: [
          'plot_ratio',
          'building_height_limit_m',
          'site_coverage_pct',
          'setbacks',
          'step_backs',
          'air_rights_note',
        ],
        project_clearance_required: [
          {
            field: 'air_rights_note',
            candidate_sources: [
              {
                authority: 'URA/CAAS',
                resolution_workflow: 'project_specific_clearance',
              },
            ],
          },
        ],
      },
    }

    render(
      <DeveloperResults
        result={result}
        selectedScenarios={['existing_building'] as DevelopmentScenario[]}
      />,
    )

    expect(screen.getAllByText('Scenario pending').length).toBeGreaterThan(0)
    expect(
      screen.getByText('Mixed-use-led program pending'),
    ).toBeInTheDocument()
    expect(lastUsePreviewJobOptions).toMatchObject({
      preferredScenario: 'existing_building',
    })
    expect(
      screen.getByText('Starter model scenario: Renovation'),
    ).toBeInTheDocument()
    expect(
      screen.queryByText('Mixed-use primary / Retail support'),
    ).not.toBeInTheDocument()
    expect(screen.getByText('SG:mixed_use')).toBeInTheDocument()
    expect(
      screen.queryByText('Residential-led renovation mix'),
    ).not.toBeInTheDocument()
    expect(
      screen.queryByText('Mixed-use-led renovation mix'),
    ).not.toBeInTheDocument()
    expect(
      screen.queryByText('Residential primary / Amenities support'),
    ).not.toBeInTheDocument()
  })

  it('presents hotel zoning as hotel-led while scenario remains pending', () => {
    const result = buildResult()
    result.address = {
      fullAddress: '10 Scotts Rd, Singapore 228211',
      district: 'Orchard',
    }
    result.existingUse = 'Unknown'
    result.propertyInfo = {
      propertyName: null,
      tenure: null,
      siteAreaSqm: 9711.9,
      gfaApproved: null,
      buildingHeight: null,
      completionYear: null,
      lastTransactionDate: null,
      lastTransactionPrice: null,
    }
    result.optimizations = []
    result.uraZoning = {
      zoneCode: 'SG:hotel',
      zoneDescription: 'Hotel',
      plotRatio: 4.2,
      buildingHeightLimit: null,
      siteCoverage: null,
      useGroups: ['Hotel', 'Retail'],
      specialConditions: null,
      source: 'ref_zoning_layer',
    }
    result.buildEnvelope = {
      ...result.buildEnvelope,
      zoneCode: 'SG:hotel',
      zoneDescription: 'Hotel',
      siteAreaSqm: 9711.9,
      allowablePlotRatio: 4.2,
      maxBuildableGfaSqm: 40790,
      currentGfaSqm: null,
      additionalPotentialGfaSqm: null,
      buildingHeightLimitM: null,
      siteCoveragePct: null,
      sourceReference: 'SG Rule Registry (RefRule + zoning layers)',
      ruleCorpusStatus: {
        coverage_state: 'partial',
        zone_code: 'SG:hotel',
        resolved_by: {
          land_use: 'ref_zoning_layer',
          plot_ratio: 'ref_zoning_layer',
          site_area: 'ref_parcel',
        },
        unresolved_fields: [
          'building_height_limit_m',
          'site_coverage_pct',
          'setbacks',
          'step_backs',
        ],
        official_source_gaps: [
          {
            field: 'height_limit_m',
            candidate_sources: [{ authority: 'URA' }],
          },
        ],
      },
    }
    previewJobsByScenarioValue = {
      existing_building: {
        id: 'preview-envelope',
        propertyId: 'prop-123',
        scenario: 'existing_building',
        status: 'ready',
        previewUrl: '/static/dev-previews/example/envelope.gltf',
        metadataUrl: '/static/dev-previews/example/envelope.json',
        thumbnailUrl: null,
        assetVersion: '20260506232000',
        requestedAt: '2026-05-06T23:20:00Z',
        startedAt: '2026-05-06T23:20:01Z',
        finishedAt: '2026-05-06T23:20:10Z',
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

    expect(screen.getAllByText('Scenario pending').length).toBeGreaterThan(0)
    expect(screen.getByText('Hotel-led program pending')).toBeInTheDocument()
    expect(
      screen.queryByText('Hotel primary / Retail support'),
    ).not.toBeInTheDocument()
    expect(screen.getByText('Hotel (SG:hotel)')).toBeInTheDocument()
    expect(
      screen.queryByText('Retail-led program pending'),
    ).not.toBeInTheDocument()
    expect(
      screen.getByText(
        'Current GFA unavailable for comparison with 40,790 sqm current-code max.',
      ),
    ).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /show data details/i }))
    expect(screen.getByText('Envelope starter model')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Envelope-based starter model is generated from the preview pipeline while scenario selection remains pending.',
      ),
    ).toBeInTheDocument()
    expect(screen.getByText('Control source status')).toBeInTheDocument()
    expect(screen.getByText('Control source not mapped')).toBeInTheDocument()
    expect(
      screen.queryByText('Source ingestion status'),
    ).not.toBeInTheDocument()
    expect(
      screen.queryByText('Source identified, not ingested'),
    ).not.toBeInTheDocument()
  })

  it('presents business park white zoning as business park led', () => {
    const result = buildResult()
    result.address = {
      fullAddress: '1 Fusionopolis Way, Singapore 138632',
      district: 'one-north',
    }
    result.existingUse = 'Unknown'
    result.propertyInfo = {
      propertyName: null,
      tenure: null,
      siteAreaSqm: 34496.6,
      gfaApproved: null,
      buildingHeight: null,
      completionYear: null,
      lastTransactionDate: null,
      lastTransactionPrice: null,
    }
    result.optimizations = []
    result.uraZoning = {
      zoneCode: 'SG:business_park_white',
      zoneDescription: 'Business Park - White',
      plotRatio: 3.5,
      buildingHeightLimit: null,
      siteCoverage: null,
      useGroups: ['Business park', 'Office-lab'],
      specialConditions: null,
      source: 'ref_zoning_layer',
    }
    result.buildEnvelope = {
      ...result.buildEnvelope,
      zoneCode: 'SG:business_park_white',
      zoneDescription: 'Business Park - White',
      siteAreaSqm: 34496.6,
      allowablePlotRatio: 3.5,
      maxBuildableGfaSqm: 120738,
      currentGfaSqm: null,
      additionalPotentialGfaSqm: null,
      buildingHeightLimitM: null,
      siteCoveragePct: null,
      sourceReference: 'SG Rule Registry (RefRule + zoning layers)',
      ruleCorpusStatus: {
        coverage_state: 'partial',
        zone_code: 'SG:business_park_white',
        resolved_by: {
          land_use: 'ref_zoning_layer',
          plot_ratio: 'ref_zoning_layer',
          site_area: 'ref_parcel',
        },
        unresolved_fields: [
          'building_height_limit_m',
          'site_coverage_pct',
          'setbacks',
          'step_backs',
        ],
      },
    }

    render(
      <DeveloperResults
        result={result}
        selectedScenarios={['existing_building'] as DevelopmentScenario[]}
      />,
    )

    expect(screen.getAllByText('Scenario pending').length).toBeGreaterThan(0)
    expect(
      screen.getByText('Business park-led program pending'),
    ).toBeInTheDocument()
    expect(
      screen.queryByText('Business park primary / Office-lab support'),
    ).not.toBeInTheDocument()
    expect(
      screen.getByText('Business Park - White (SG:business_park_white)'),
    ).toBeInTheDocument()
    expect(
      screen.queryByText('Office-led program pending'),
    ).not.toBeInTheDocument()
    expect(
      screen.queryByText('Office primary / Retail support'),
    ).not.toBeInTheDocument()
  })

  it('presents health and medical zoning as healthcare led', () => {
    const result = buildResult()
    result.address = {
      fullAddress: '5 Lower Kent Ridge Rd, Singapore 119074',
      district: 'Queenstown',
    }
    result.existingUse = 'Unknown'
    result.propertyInfo = {
      propertyName: null,
      tenure: null,
      siteAreaSqm: 5000,
      gfaApproved: null,
      buildingHeight: null,
      completionYear: null,
      lastTransactionDate: null,
      lastTransactionPrice: null,
    }
    result.optimizations = []
    result.uraZoning = {
      zoneCode: 'SG:health_medical_care',
      zoneDescription: 'Health & Medical Care',
      plotRatio: null,
      buildingHeightLimit: null,
      siteCoverage: null,
      useGroups: ['Health & Medical Care'],
      specialConditions: null,
      source: 'ref_zoning_layer',
    }
    result.buildEnvelope = {
      ...result.buildEnvelope,
      zoneCode: 'SG:health_medical_care',
      zoneDescription: 'Health & Medical Care',
      siteAreaSqm: 5000,
      allowablePlotRatio: null,
      maxBuildableGfaSqm: null,
      currentGfaSqm: null,
      additionalPotentialGfaSqm: null,
      buildingHeightLimitM: null,
      siteCoveragePct: null,
      sourceReference: 'SG Rule Registry (RefRule + zoning layers)',
      ruleCorpusStatus: {
        coverage_state: 'partial',
        zone_code: 'SG:health_medical_care',
        site_development_status: 'developed',
        resolved_by: {
          land_use: 'ref_zoning_layer',
          site_area: 'ref_parcel',
        },
        unresolved_fields: [
          'plot_ratio',
          'building_height_limit_m',
          'site_coverage_pct',
          'setbacks',
          'step_backs',
        ],
      },
    }

    render(
      <DeveloperResults
        result={result}
        selectedScenarios={['existing_building'] as DevelopmentScenario[]}
      />,
    )

    expect(screen.getAllByText('Scenario pending').length).toBeGreaterThan(0)
    expect(
      screen.getByText('Specialized operator-led program'),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        'Capture matched health/medical-care zoning. Scenario selection stays pending because this is a specialized operator-led use; Capture needs current GFA and site-specific controls before recommending renovation or redevelopment.',
      ),
    ).toBeInTheDocument()
    expect(
      screen.queryByText('Healthcare primary / Institutional support'),
    ).not.toBeInTheDocument()
    expect(
      screen.getByText('Health & Medical Care (SG:health_medical_care)'),
    ).toBeInTheDocument()
    expect(
      screen.queryByText('Office-led program pending'),
    ).not.toBeInTheDocument()
    expect(
      screen.queryByText('Office primary / Retail support'),
    ).not.toBeInTheDocument()
  })

  it('presents sports and recreation zoning without office retail fallback copy', () => {
    const result = buildResult()
    result.address = {
      fullAddress: '39A Soon Lee Rd, Singapore',
      district: 'Boon Lay',
    }
    result.existingUse = 'Unknown'
    result.propertyInfo = {
      propertyName: null,
      tenure: null,
      siteAreaSqm: 8000,
      gfaApproved: null,
      buildingHeight: null,
      completionYear: null,
      lastTransactionDate: null,
      lastTransactionPrice: null,
    }
    result.optimizations = []
    result.uraZoning = {
      zoneCode: 'SG:sports_recreation',
      zoneDescription: 'Sports & Recreation',
      plotRatio: null,
      buildingHeightLimit: null,
      siteCoverage: null,
      useGroups: ['Sports & Recreation'],
      specialConditions: null,
      source: 'ref_zoning_layer',
    }
    result.buildEnvelope = {
      ...result.buildEnvelope,
      zoneCode: 'SG:sports_recreation',
      zoneDescription: 'Sports & Recreation',
      siteAreaSqm: 8000,
      allowablePlotRatio: null,
      grossPlotRatio: null,
      maxBuildableGfaSqm: null,
      currentGfaSqm: null,
      additionalPotentialGfaSqm: null,
      sourceReference: 'SG Rule Registry (RefRule + zoning layers)',
      ruleCorpusStatus: {
        coverage_state: 'partial',
        zone_code: 'SG:sports_recreation',
        site_development_status: 'developed',
        resolved_by: {
          land_use: 'ref_zoning_layer',
          site_area: 'ref_parcel',
        },
        unresolved_fields: ['plot_ratio', 'building_height_limit_m'],
      },
    }

    render(
      <DeveloperResults
        result={result}
        selectedScenarios={['existing_building'] as DevelopmentScenario[]}
      />,
    )

    expect(
      screen.getByText('Specialized operator-led program'),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        'Capture matched sports/recreation zoning. Scenario selection stays pending because this is a specialized operator-led use; Capture needs current GFA and site-specific controls before recommending renovation or redevelopment.',
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText('Sports & Recreation (SG:sports_recreation)'),
    ).toBeInTheDocument()
    expect(screen.getByText("Today's zoning program")).toBeInTheDocument()
    expect(
      screen.queryByText('Office-led program pending'),
    ).not.toBeInTheDocument()
    expect(
      screen.queryByText('Office primary / Retail support'),
    ).not.toBeInTheDocument()
    expect(screen.queryByText('Use basis')).not.toBeInTheDocument()
  })

  it('presents park zoning as no standard building program without duplicate review copy', () => {
    const result = buildResult()
    result.address = {
      fullAddress: '1 Nassim Rd, Singapore',
      district: 'Tanglin',
    }
    result.existingUse = 'Unknown'
    result.propertyInfo = {
      propertyName: null,
      tenure: null,
      siteAreaSqm: 4200,
      gfaApproved: null,
      buildingHeight: null,
      completionYear: null,
      lastTransactionDate: null,
      lastTransactionPrice: null,
    }
    result.optimizations = []
    result.uraZoning = {
      zoneCode: 'SG:park',
      zoneDescription: 'Park',
      plotRatio: null,
      buildingHeightLimit: null,
      siteCoverage: null,
      useGroups: [],
      specialConditions: 'non_standard_or_non_developable_control',
      developmentControlStatus: 'non_standard_or_non_developable',
      source: 'ref_zoning_layer',
    }
    result.buildEnvelope = {
      ...result.buildEnvelope,
      zoneCode: 'SG:park',
      zoneDescription: 'Park',
      siteAreaSqm: 4200,
      allowablePlotRatio: null,
      grossPlotRatio: null,
      maxBuildableGfaSqm: null,
      currentGfaSqm: null,
      additionalPotentialGfaSqm: null,
      sourceReference: 'SG Rule Registry (RefRule + zoning layers)',
      ruleCorpusStatus: {
        coverage_state: 'partial',
        zone_code: 'SG:park',
        site_development_status: 'developed',
        resolved_by: {
          land_use: 'ref_zoning_layer',
          site_area: 'ref_parcel',
        },
        unresolved_fields: ['plot_ratio', 'building_height_limit_m'],
      },
    }

    render(
      <DeveloperResults
        result={result}
        selectedScenarios={['existing_building'] as DevelopmentScenario[]}
      />,
    )

    const parkReviewCopy =
      'Capture matched park/open-space zoning. Scenario selection stays pending because this control is not a standard private development program; site-specific approval, rezoning, or public-use review may be required before a building scenario is studied.'

    expect(screen.getByText('No standard private program')).toBeInTheDocument()
    expect(screen.getByText('Park (SG:park)')).toBeInTheDocument()
    expect(screen.getAllByText(parkReviewCopy)).toHaveLength(1)
    expect(screen.queryByText('Control review pending')).not.toBeInTheDocument()
    expect(
      screen.queryByText(
        'Capture matched a non-standard planning control. Scenario selection stays pending until the official control is reviewed.',
      ),
    ).not.toBeInTheDocument()
    expect(
      screen.queryByText('Office-led program pending'),
    ).not.toBeInTheDocument()
  })

  it('surfaces resolved and unresolved rule fields in the capture data basis', () => {
    const result = buildResult()
    result.buildEnvelope.sourceReference = 'SG Rule Registry (RefRule)'
    result.buildEnvelope.ruleCorpusStatus = {
      coverage_state: 'partial',
      resolved_by: {
        plot_ratio: 'captured_zoning_metadata',
        setbacks: 'ref_rule',
      },
      unresolved_fields: [
        'building_height_limit_m',
        'air_rights_note',
        'step_backs',
      ],
      official_source_gaps: [
        {
          field: 'building_height_limit_m',
          reason: 'not_resolved_from_current_registry',
          candidate_sources: [
            {
              authority: 'URA',
              title: 'Development Control Guidelines',
            },
          ],
        },
        {
          field: 'air_rights_note',
          reason: 'project_specific_clearance_required',
          candidate_sources: [
            {
              authority: 'URA/CAAS',
              title: 'Height control and aviation-related clearance sources',
              resolution_workflow: 'project_specific_clearance',
            },
          ],
        },
        {
          field: 'step_backs',
          reason: 'not_resolved_from_current_registry',
          candidate_sources: [
            {
              authority: 'URA',
              title: 'Development Control Guidelines',
            },
          ],
        },
      ],
      official_source_ingestion: {
        resolved_count: 0,
        staged_count: 1,
        existing_count: 1,
        failed_count: 0,
        candidates: [],
      },
    }

    render(
      <DeveloperResults
        result={result}
        selectedScenarios={['existing_building'] as DevelopmentScenario[]}
      />,
    )

    expect(screen.getByText('Official controls pending')).toBeInTheDocument()
    expect(screen.queryByText('Resolved controls')).not.toBeInTheDocument()
    expect(screen.queryByText('Unresolved controls')).not.toBeInTheDocument()
    expect(screen.queryByText('Control source status')).not.toBeInTheDocument()
    expect(screen.queryByText('Mixed source')).not.toBeInTheDocument()
    expect(screen.getByText('Site / captured')).toBeInTheDocument()
    expect(screen.getByText('plot ratio.')).toBeInTheDocument()
    expect(screen.getByText('Rule-backed')).toBeInTheDocument()
    expect(screen.getByText('setbacks.')).toBeInTheDocument()
    expect(screen.getAllByText('Source review needed').length).toBeGreaterThan(
      0,
    )
    expect(
      screen.getByText('height limit - separate official control, step-backs.'),
    ).toBeInTheDocument()
    expect(
      screen.queryByText('Control source not mapped'),
    ).not.toBeInTheDocument()
    expect(
      screen.queryByText(
        'height limit - separate official control (URA), air-rights clearance (URA/CAAS), step-backs (URA) have official source categories identified, but Capture has not mapped reviewed values for this zone yet.',
      ),
    ).not.toBeInTheDocument()
    expect(
      screen.getAllByText('Project clearance required').length,
    ).toBeGreaterThan(0)
    expect(screen.queryByText('Live source scan')).not.toBeInTheDocument()
    expect(screen.getByText('Review required')).toBeInTheDocument()
    expect(
      screen.getByText(
        '1 staged for review / 1 already staged. Pending source candidates still require review before Capture treats those controls as resolved.',
      ),
    ).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /show data details/i }))
    expect(
      screen.getByText(
        '2 official controls still need source review (height limit - separate official control, step-backs).',
      ),
    ).toBeInTheDocument()
    expect(screen.getByText('Site captured controls')).toBeInTheDocument()
    expect(screen.getAllByText('Rule-backed controls').length).toBeGreaterThan(
      0,
    )
    expect(
      screen.getAllByText('Official controls pending').length,
    ).toBeGreaterThan(0)
    expect(screen.getByText('Control source status')).toBeInTheDocument()
    expect(screen.getByText('Control source not mapped')).toBeInTheDocument()
    expect(
      screen.getByText(
        'height limit - separate official control (URA), step-backs (URA) have official source categories identified, but Capture has not mapped reviewed values for this zone yet.',
      ),
    ).toBeInTheDocument()
    expect(
      screen.getAllByText('Project clearance required').length,
    ).toBeGreaterThan(0)
    expect(
      screen.getAllByText(
        'air-rights clearance (URA/CAAS) requires site-specific aviation and height-clearance review. Capture does not resolve this clearance.',
      ).length,
    ).toBeGreaterThan(0)
    expect(screen.getByText('Live source scan')).toBeInTheDocument()
  })

  it('uses singular source-review copy for one unresolved official control', () => {
    const result = buildResult()
    result.buildEnvelope.sourceReference = 'SG Rule Registry (RefRule)'
    result.buildEnvelope.ruleCorpusStatus = {
      zone_code: 'SG:industrial',
      resolved_by: {
        land_use: 'captured_zoning_metadata',
        plot_ratio: 'captured_zoning_metadata',
        building_height_limit_m: 'ref_rule',
        site_coverage_pct: 'captured_development_constraints',
        setbacks: 'ref_rule',
        step_backs: 'ref_rule',
      },
      unresolved_fields: ['air_rights_note'],
      official_source_gaps: [
        {
          field: 'air_rights_note',
          reason: 'project_specific_clearance_required',
          candidate_sources: [
            {
              authority: 'URA/CAAS',
              title: 'Height control and aviation-related clearance sources',
              url: 'https://www.ura.gov.sg/Corporate/Guidelines/Development-Control',
              resolution_workflow: 'project_specific_clearance',
            },
          ],
        },
      ],
      project_clearance_required: [
        {
          field: 'air_rights_note',
          reason: 'project_specific_clearance_required',
          candidate_sources: [
            {
              authority: 'URA/CAAS',
              title: 'Height control and aviation-related clearance sources',
              url: 'https://www.ura.gov.sg/Corporate/Guidelines/Development-Control',
              resolution_workflow: 'project_specific_clearance',
            },
          ],
        },
      ],
    }

    render(
      <DeveloperResults
        result={result}
        selectedScenarios={['existing_building'] as DevelopmentScenario[]}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: /show data details/i }))
    expect(
      screen.getByText(
        '1 project clearance is still required (air-rights clearance (URA/CAAS)).',
      ),
    ).toBeInTheDocument()
    expect(screen.queryByText('Source review needed')).not.toBeInTheDocument()
    expect(
      screen.getAllByText('Project clearance required').length,
    ).toBeGreaterThan(0)
    expect(
      screen.getAllByText(
        'air-rights clearance (URA/CAAS) requires site-specific aviation and height-clearance review. Capture does not resolve this clearance.',
      ).length,
    ).toBeGreaterThan(0)
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
      screen.getByText('3.9 m floor-to-floor / 2.8 m clear'),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/Assumption source: Frontend fallback defaults\./i),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        /Capture is using fallback assumptions because no scenario-specific preview jobs are attached to this property yet\./i,
      ),
    ).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /show data details/i }))
    expect(
      screen.getByText(
        'Geometry is still preliminary and may rely on fallback or placeholder massing.',
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText('Model inputs open for refinement'),
    ).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /raw land/i }))

    expect(screen.getByText('Current Scenario Override')).toBeInTheDocument()
    expect(
      screen.getByText(/Capture recommended: Adaptive Reuse/i),
    ).toBeInTheDocument()
    expect(screen.getAllByText(/Exploratory override/i).length).toBeGreaterThan(
      0,
    )
    expect(
      screen.getByText('4.2 m floor-to-floor / 3.2 m clear'),
    ).toBeInTheDocument()
    expect(screen.getByText('250 mm walls / 18% core')).toBeInTheDocument()
    expect(
      screen.getByText(
        /Capture is using fallback assumptions because no scenario-specific preview jobs are attached to this property yet\./i,
      ),
    ).toBeInTheDocument()
  })

  it('labels rules-only starter assumptions as modeling defaults', () => {
    const result = buildResult()
    result.buildEnvelope.maxBuildableGfaSqm = result.buildEnvelope.currentGfaSqm
    result.buildEnvelope.additionalPotentialGfaSqm = 0
    previewJobsByScenarioValue = {
      existing_building: {
        id: 'preview-rules-only',
        propertyId: 'prop-123',
        scenario: 'existing_building',
        status: 'ready',
        previewUrl: '/static/dev-previews/example/rules-only.gltf',
        metadataUrl: '/static/dev-previews/example/rules-only.json',
        thumbnailUrl: '/static/dev-previews/example/rules-only.png',
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
          source: 'rules',
          retentionStrategy: 'preserve_existing_bulk',
          efficiencyFactor: 0.96,
          provenance: {
            summary: 'rules_only',
            fields: {
              retention_strategy: 'rules',
              efficiency_factor: 'rules',
              floor_to_floor_m: 'rules',
              clear_ceiling_m: 'rules',
              wall_thickness_mm: 'rules',
              core_ratio_pct: 'rules',
              common_area_ratio_pct: 'rules',
              hvac_space_ratio_pct: 'rules',
              electrical_space_ratio_pct: 'rules',
            },
            adjustments: [],
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

    expect(
      screen.getByText(/Assumption source: Starter model defaults\./i),
    ).toBeInTheDocument()
    expect(
      screen.queryByText(/Assumption source: Rule defaults only\./i),
    ).not.toBeInTheDocument()
    expect(
      screen.getByText('Model inputs open for refinement'),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        'These values are modeling assumptions, not certified code controls.',
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
          assetProfiles: [
            {
              assetType: 'retail',
              floorToFloorM: 4.8,
              clearCeilingM: 3.9,
              niaEfficiency: 0.75,
              source: 'hybrid',
            },
            {
              assetType: 'amenities',
              floorToFloorM: 3.6,
              clearCeilingM: 2.7,
              niaEfficiency: 0.75,
              source: 'hybrid',
            },
          ],
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
      screen.getByText('4.2 m floor-to-floor / 3.2 m clear'),
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

    expect(screen.getAllByText(/Exploratory override/i).length).toBeGreaterThan(
      0,
    )
    expect(
      screen.getByRole('button', { name: /save as project override/i }),
    ).toBeInTheDocument()

    fireEvent.click(
      screen.getByRole('button', { name: /save as project override/i }),
    )

    expect(screen.getByText('Saved Scenario Override')).toBeInTheDocument()
    expect(
      screen.getAllByText(/Saved project override/i).length,
    ).toBeGreaterThan(0)
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
      screen.getAllByText(/Saved project override/i).length,
    ).toBeGreaterThan(0)
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
      screen.getByText('3.6 m floor-to-floor / 2.7 m clear'),
    ).toBeInTheDocument()
    expect(
      screen.getByText('conservation retention / 0.92 efficiency'),
    ).toBeInTheDocument()
    expect(
      screen.queryByText(/Frontend fallback defaults/i),
    ).not.toBeInTheDocument()
    expect(
      screen.queryByText(/Capture is using fallback assumptions/i),
    ).not.toBeInTheDocument()
    expect(screen.getByText('Pinned by site facts')).toBeInTheDocument()
    expect(
      screen.getByText('Model inputs open for refinement'),
    ).toBeInTheDocument()
    expect(screen.queryByText('Use-Type Profiles')).not.toBeInTheDocument()
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

  it('updates active scenario and propagates it to MultiScenarioComparisonSection', async () => {
    render(
      <DeveloperResults
        result={buildResult()}
        selectedScenarios={
          ['raw_land', 'existing_building'] as DevelopmentScenario[]
        }
      />,
    )

    const module = await screen.findByTestId('multi-scenario')
    expect(module.getAttribute('data-active')).toBe('all')

    fireEvent.click(screen.getByRole('button', { name: /all scenarios/i }))
    expect(module.getAttribute('data-active')).toBe('all')

    fireEvent.click(screen.getByRole('button', { name: /renovation/i }))
    expect(module.getAttribute('data-active')).toBe('existing_building')
  })

  it('keeps the post-scan workspace model-first with layer inspection below supporting facts', async () => {
    render(
      <DeveloperResults
        result={buildResult()}
        selectedScenarios={
          ['raw_land', 'existing_building'] as DevelopmentScenario[]
        }
      />,
    )

    const preview = screen.getByText('Concept Preview')
    const recommendation = screen.getByText('Capture Recommendation')
    const comparison = await screen.findByTestId('multi-scenario')
    const overview = await screen.findByTestId('property-overview')
    const layers = await screen.findByTestId('preview-layers')

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
