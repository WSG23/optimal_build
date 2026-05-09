/**
 * DeveloperResults - Developer workspace wrapper for unified capture page
 *
 * Renders the full developer workspace sections after capture:
 * - Concept Preview (starter model first)
 * - Capture recommendation
 * - Scenario Focus Section
 * - Multi-Scenario Comparison
 * - Property Overview Section
 * - Preview Layers inspection
 * - Due Diligence handoff
 * - Project save CTA
 *
 * This component should be lazy-loaded to avoid bundle bloat for agent users.
 */

import {
  Suspense,
  lazy,
  useState,
  useMemo,
  useCallback,
  useEffect,
  useRef,
} from 'react'
import { Box, Typography } from '@mui/material'

import type {
  CaptureRecommendationScenario,
  SiteAcquisitionResult,
} from '../../../../api/siteAcquisition'
import type { CaptureOverrideIntent } from '../../../../api/siteAcquisition'
import type { DevelopmentScenario } from '../../../../api/agents'
import { Button } from '../../../../components/canonical/Button'
import { Card } from '../../../../components/canonical/Card'
import { Link } from '../../../../router'
import { useProject } from '../../../../contexts/useProject'
import {
  linkCaptureToProject,
  saveProjectFromCapture,
} from '../../../../api/siteAcquisition'
import {
  clearCaptureScenarioOverrideForProject,
  loadCaptureScenarioOverrideForProject,
  saveCaptureForProject,
  saveCaptureScenarioOverrideForProject,
} from '../utils/captureStorage'

// Import Site Acquisition hooks
import { usePreviewJob } from '../../site-acquisition/hooks/usePreviewJob'
import { useCaptureScenarioComparison } from '../../site-acquisition/hooks/useCaptureScenarioComparison'
import { buildFeasibilitySignals } from '../../site-acquisition/utils/signals'

// Import constants for scenario lookup
import { SCENARIO_OPTIONS } from '../../site-acquisition/constants'

// Import card builder utility
import { buildPropertyOverviewCards } from '../../site-acquisition/utils/cardBuilders'
import { mapSiteAcquisitionResultToCaptureResultV2 } from '../utils/captureResultV2'

// Import extracted sub-components
import { ConceptPreviewSection } from './ConceptPreviewSection'
import { CaptureRecommendationSection } from './CaptureRecommendationSection'
import { ScenarioFocusSection } from './ScenarioFocusSection'
import { SaveProjectDialog } from './SaveProjectDialog'
import { useStarterModelMemos } from './useStarterModelMemos'

const PropertyOverviewSection = lazy(async () => {
  const module =
    await import('../../site-acquisition/components/property-overview/PropertyOverviewSection')
  return { default: module.PropertyOverviewSection }
})

const PreviewLayersTable = lazy(async () => {
  const module =
    await import('../../site-acquisition/components/property-overview/PreviewLayersTable')
  return { default: module.PreviewLayersTable }
})

const MultiScenarioComparisonSection = lazy(async () => {
  const module =
    await import('../../site-acquisition/components/multi-scenario-comparison/MultiScenarioComparisonSection')
  return { default: module.MultiScenarioComparisonSection }
})

const OptimalIntelligenceCard = lazy(async () => {
  const module =
    await import('../../site-acquisition/components/OptimalIntelligenceCard')
  return { default: module.OptimalIntelligenceCard }
})

export interface DeveloperResultsProps {
  result: SiteAcquisitionResult
  selectedScenarios: DevelopmentScenario[]
}

export function DeveloperResults({
  result,
  selectedScenarios,
}: DeveloperResultsProps) {
  const sectionFallback = (
    <Card
      sx={{
        minHeight: 160,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 'var(--ob-space-150)',
      }}
    >
      <Typography
        sx={{
          fontSize: 'var(--ob-font-size-sm)',
          color: 'text.secondary',
        }}
      >
        Loading analysis section...
      </Typography>
    </Card>
  )

  const autoRequestedStarterModelRef = useRef<Set<string>>(new Set())
  const hydratedSavedOverrideProjectIdRef = useRef<string | null>(null)

  // Active scenario for filtering
  const [activeScenario, setActiveScenario] = useState<
    DevelopmentScenario | 'all'
  >('all')
  const [overrideIntent, setOverrideIntent] =
    useState<CaptureOverrideIntent | null>(null)
  const { currentProject, projects, setCurrentProject, refreshProjects } =
    useProject()
  const [saveDialogOpen, setSaveDialogOpen] = useState(false)
  const [saveMode, setSaveMode] = useState<'new' | 'existing'>('new')
  const [projectNameInput, setProjectNameInput] = useState('')
  const [existingProjectId, setExistingProjectId] = useState('')
  const [saveError, setSaveError] = useState<string | null>(null)
  const [savingProject, setSavingProject] = useState(false)
  const dueDiligencePath = currentProject
    ? `/projects/${currentProject.id}/due-diligence`
    : '/app/due-diligence'

  // Scenario lookup map for labels
  const scenarioLookup = useMemo(
    () => new Map(SCENARIO_OPTIONS.map((option) => [option.value, option])),
    [],
  )

  const captureResultV2 = useMemo(
    () =>
      mapSiteAcquisitionResultToCaptureResultV2(result, {
        selectedScenarios,
        overrideScenario: activeScenario !== 'all' ? activeScenario : undefined,
        overrideIntent,
      }),
    [activeScenario, overrideIntent, result, selectedScenarios],
  )

  const previewScenario = useMemo<DevelopmentScenario>(() => {
    const recommended = captureResultV2.scenarioRecommendation.recommended
    return recommended === 'scenario_pending'
      ? 'existing_building'
      : recommended
  }, [captureResultV2.scenarioRecommendation.recommended])

  // Currency symbol for formatting
  const currencySymbol = result.currencySymbol ?? 'S$'
  const suggestedProjectName =
    result.propertyInfo?.propertyName?.trim() ||
    result.address?.fullAddress?.trim() ||
    'Capture Project'

  // Number formatter for card values
  function formatNumber(
    value: number,
    options?: Intl.NumberFormatOptions,
  ): string {
    return new Intl.NumberFormat('en-SG', {
      maximumFractionDigits: 1,
      ...options,
    }).format(value)
  }

  // Format timestamp helper
  const formatRecordedTimestamp = useCallback(
    (timestamp?: string | null): string => {
      if (!timestamp) return '—'
      try {
        const date = new Date(timestamp)
        return date.toLocaleDateString('en-SG', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        })
      } catch {
        return timestamp
      }
    },
    [],
  )

  // Scenario comparison state
  const {
    quickAnalysisScenarios,
    comparisonScenarios,
    scenarioComparisonData,
    formatScenarioLabel,
  } = useCaptureScenarioComparison({
    capturedProperty: result,
    activeScenario,
    currencySymbol,
  })

  const formatCaptureScenarioLabel = useCallback(
    (
      scenario: CaptureRecommendationScenario | 'all' | null | undefined,
    ): string => {
      if (scenario === 'scenario_pending') {
        return 'Scenario pending'
      }
      if (scenario == null) {
        return formatScenarioLabel(null)
      }
      return formatScenarioLabel(scenario as DevelopmentScenario | 'all' | null)
    },
    [formatScenarioLabel],
  )

  // Preview job state
  const {
    previewJob,
    previewDetailLevel,
    setPreviewDetailLevel,
    isRefreshingPreview,
    isGeneratingStarterModel,
    hasPreferredScenarioPreview,
    previewGenerationError,
    previewLayerMetadata,
    previewLayerVisibility,
    previewFocusLayerId,
    isPreviewMetadataLoading,
    previewMetadataError,
    hiddenLayerCount,
    colorLegendEntries,
    legendHasPendingChanges,
    handleEnsureStarterModel,
    handleToggleLayerVisibility,
    handleSoloPreviewLayer,
    handleShowAllLayers,
    handleFocusLayer,
    handleResetLayerFocus,
    handleLegendEntryChange,
    handleLegendReset,
  } = usePreviewJob({
    capturedProperty: result,
    preferredScenario: previewScenario,
  })

  // Extracted starter model computations
  const {
    effectiveStarterModel,
    defaultRecommendationLabel,
    starterModelStatusSummary,
    scenarioFitSummary,
    captureDataBasis,
    starterModelAssumptionLines,
    starterModelAssetProfileLines,
    starterModelAssumptionSourceLine,
    starterModelAssumptionFallbackReason,
    starterModelOverridePreviewNotice,
    starterModelAssumptionBuckets,
    overrideModeLine,
    overrideIntentGuidance,
    recommendationCardTitle,
    starterModelActionLabel,
  } = useStarterModelMemos({
    captureResultV2,
    previewJob,
    isGeneratingStarterModel,
    isRefreshingPreview,
    hasPreferredScenarioPreview,
    previewJobs: result.previewJobs,
    formatScenarioLabel: formatCaptureScenarioLabel,
    formatNumber,
  })

  // Unified layer action handler for PreviewLayersTable
  const handleLayerAction = useCallback(
    (layerId: string, action: 'toggle' | 'solo' | 'focus') => {
      switch (action) {
        case 'toggle':
          handleToggleLayerVisibility(layerId)
          break
        case 'solo':
          handleSoloPreviewLayer(layerId)
          break
        case 'focus':
          handleFocusLayer(layerId)
          break
      }
    },
    [handleToggleLayerVisibility, handleSoloPreviewLayer, handleFocusLayer],
  )

  const handleOpenSaveDialog = useCallback(() => {
    setSaveError(null)
    void refreshProjects()
    if (currentProject) {
      setSaveMode('existing')
      setExistingProjectId(currentProject.id)
    } else {
      setSaveMode('new')
      setProjectNameInput(suggestedProjectName)
    }
    setSaveDialogOpen(true)
  }, [currentProject, suggestedProjectName, refreshProjects])

  const handleSaveProject = useCallback(async () => {
    if (savingProject) {
      return
    }
    setSaveError(null)
    setSavingProject(true)
    try {
      if (saveMode === 'existing') {
        if (!existingProjectId) {
          setSaveError('Select an existing project.')
          return
        }
        const linked = await linkCaptureToProject(
          result.propertyId,
          existingProjectId,
          {},
        )
        setCurrentProject({ id: linked.projectId, name: linked.projectName })
        saveCaptureForProject(linked.projectId, result)
      } else {
        const name = projectNameInput.trim()
        if (!name) {
          setSaveError('Project name is required.')
          return
        }
        const created = await saveProjectFromCapture(result.propertyId, {
          projectName: name,
        })
        setCurrentProject({ id: created.projectId, name: created.projectName })
        saveCaptureForProject(created.projectId, result)
      }
      await refreshProjects()
      setSaveDialogOpen(false)
    } catch (error) {
      setSaveError(
        error instanceof Error ? error.message : 'Unable to save project.',
      )
    } finally {
      setSavingProject(false)
    }
  }, [
    result,
    existingProjectId,
    projectNameInput,
    refreshProjects,
    saveMode,
    savingProject,
    setCurrentProject,
  ])

  const handleSaveProjectOverride = useCallback(() => {
    if (!currentProject?.id || activeScenario === 'all') {
      return
    }

    saveCaptureScenarioOverrideForProject(currentProject.id, activeScenario)
    setOverrideIntent('saved')
  }, [activeScenario, currentProject?.id])

  const handleClearProjectOverride = useCallback(() => {
    if (!currentProject?.id) {
      return
    }

    clearCaptureScenarioOverrideForProject(currentProject.id)
    if (activeScenario === 'all') {
      setOverrideIntent(null)
      return
    }

    setOverrideIntent('exploratory')
  }, [activeScenario, currentProject?.id])

  // Compute feasibility signals from quick analysis scenarios
  const feasibilitySignals = useMemo(() => {
    if (!quickAnalysisScenarios.length) {
      return []
    }
    return quickAnalysisScenarios.map((entry) => {
      const scenario =
        typeof entry.scenario === 'string' && entry.scenario
          ? (entry.scenario as DevelopmentScenario)
          : 'raw_land'
      const label =
        scenarioLookup.get(scenario)?.label ??
        formatScenarioLabel(scenario as DevelopmentScenario | 'all' | null)
      const signals = buildFeasibilitySignals({
        entry,
        capturedProperty: result,
        formatNumber,
      })
      return {
        scenario,
        label,
        opportunities: signals.opportunities,
        risks: signals.risks,
      }
    })
  }, [quickAnalysisScenarios, scenarioLookup, formatScenarioLabel, result])

  // Build overview cards from result using the official card builder
  const overviewCards = useMemo(() => {
    return buildPropertyOverviewCards({
      capturedProperty: result,
      previewJob,
      colorLegendEntries: colorLegendEntries ?? [],
      formatters: {
        formatNumber,
        formatCurrency: () => '—',
        formatTimestamp: formatRecordedTimestamp,
      },
    })
  }, [colorLegendEntries, formatRecordedTimestamp, previewJob, result])

  // Instant capture insight based on captured property data
  const aiInsight = useMemo(() => {
    if (!result) return null
    const recommendation = captureResultV2.scenarioRecommendation
    const starterModel = effectiveStarterModel
    const envelope = captureResultV2.codeConstraints
    const analysisPoints = [
      envelope.allowablePlotRatio != null
        ? `plot ratio ${formatNumber(envelope.allowablePlotRatio, {
            maximumFractionDigits: 2,
          })}`
        : null,
      envelope.maxBuildableGfaSqm != null
        ? `max buildable GFA ${formatNumber(envelope.maxBuildableGfaSqm, {
            maximumFractionDigits: 0,
          })} sqm`
        : null,
      envelope.buildingHeightLimitM != null
        ? `height limit ${formatNumber(envelope.buildingHeightLimitM, {
            maximumFractionDigits: 0,
          })} m`
        : null,
      envelope.siteCoveragePct != null
        ? `site coverage ${formatNumber(envelope.siteCoveragePct, {
            maximumFractionDigits: 0,
          })}%`
        : null,
    ].filter(Boolean)
    const previewStatus = starterModel.status.replace(/_/g, ' ').toLowerCase()
    const isFallbackCapture = starterModel.geometryScope === 'scalar_envelope'
    const analysisSummary =
      analysisPoints.length > 0
        ? analysisPoints.slice(0, 3).join(', ')
        : 'zoning and envelope controls are still resolving'
    const scopeNote = isFallbackCapture
      ? 'This is a preliminary capture: scalar controls only, with no setback or floor-by-floor compliance modelling.'
      : 'Capture reflects the currently resolved scalar controls for this site, without setback or floor-by-floor compliance modelling.'
    const scenarioNote = recommendation.userOverride
      ? recommendation.overrideIntent === 'exploratory'
        ? `Exploratory override active: ${formatCaptureScenarioLabel(recommendation.recommended)} is selected temporarily and does not change learned defaults.`
        : recommendation.overrideIntent === 'saved'
          ? `Saved project override active: ${formatCaptureScenarioLabel(recommendation.recommended)} is pinned for this project until you return to the Capture recommendation.`
          : `User override active: ${formatCaptureScenarioLabel(recommendation.recommended)} remains selected even though Capture would otherwise prefer ${recommendation.alternatives[0] ? formatScenarioLabel(recommendation.alternatives[0]) : 'another scenario'}.`
      : recommendation.defaultRecommended === 'scenario_pending'
        ? 'Capture cannot recommend a scenario yet because current GFA and current-code fit are pending.'
        : `Capture currently recommends ${formatCaptureScenarioLabel(recommendation.defaultRecommended)} first.`
    return `Instant capture analysis for ${result.address?.district ?? 'this location'} highlights ${analysisSummary}. Preview status: ${previewStatus}. ${scenarioNote} ${scopeNote}`
  }, [
    captureResultV2,
    effectiveStarterModel,
    formatCaptureScenarioLabel,
    formatScenarioLabel,
    result,
  ])

  // Hydrate saved override from project
  useEffect(() => {
    if (!currentProject?.id) {
      hydratedSavedOverrideProjectIdRef.current = null
      return
    }

    if (hydratedSavedOverrideProjectIdRef.current === currentProject.id) {
      return
    }

    hydratedSavedOverrideProjectIdRef.current = currentProject.id

    const savedOverride = loadCaptureScenarioOverrideForProject(
      currentProject.id,
    )
    if (savedOverride && selectedScenarios.includes(savedOverride)) {
      setActiveScenario(savedOverride)
      setOverrideIntent('saved')
      return
    }

    if (overrideIntent === 'saved') {
      setActiveScenario('all')
      setOverrideIntent(null)
    }
  }, [currentProject?.id, overrideIntent, selectedScenarios])

  // Auto-request starter model when preferred scenario changes
  useEffect(() => {
    const propertyId = result.propertyId
    if (
      !propertyId ||
      hasPreferredScenarioPreview ||
      isGeneratingStarterModel ||
      previewGenerationError
    ) {
      return
    }

    const requestKey = `${propertyId}:${previewScenario}`
    if (autoRequestedStarterModelRef.current.has(requestKey)) {
      return
    }

    autoRequestedStarterModelRef.current.add(requestKey)
    void handleEnsureStarterModel()
  }, [
    handleEnsureStarterModel,
    hasPreferredScenarioPreview,
    isGeneratingStarterModel,
    previewScenario,
    previewGenerationError,
    result.propertyId,
  ])

  const handleSelectAllScenarios = useCallback(() => {
    setActiveScenario('all')
    setOverrideIntent(null)
    if (currentProject?.id) {
      clearCaptureScenarioOverrideForProject(currentProject.id)
    }
  }, [currentProject?.id])

  const handleSelectScenario = useCallback((scenario: DevelopmentScenario) => {
    setActiveScenario(scenario)
    setOverrideIntent('exploratory')
  }, [])

  const handleCloseSaveDialog = useCallback(() => {
    setSaveDialogOpen(false)
    setSaveError(null)
  }, [])

  return (
    <div className="site-acquisition__developer-results">
      <ConceptPreviewSection
        effectiveStarterModel={effectiveStarterModel}
        previewDetailLevel={previewDetailLevel}
        setPreviewDetailLevel={setPreviewDetailLevel}
        isGeneratingStarterModel={isGeneratingStarterModel}
        isRefreshingPreview={isRefreshingPreview}
        starterModelActionLabel={starterModelActionLabel}
        starterModelStatusSummary={starterModelStatusSummary}
        handleEnsureStarterModel={handleEnsureStarterModel}
        formatScenarioLabel={formatScenarioLabel}
        recommendedScenario={previewScenario}
        supportsFullCompliance={
          captureResultV2.analysisStatus.supportsFullCompliance
        }
        previewMetadataError={previewMetadataError}
        previewGenerationError={previewGenerationError}
      />

      <CaptureRecommendationSection
        recommendationCardTitle={recommendationCardTitle}
        formatScenarioLabel={formatCaptureScenarioLabel}
        recommendedScenario={captureResultV2.scenarioRecommendation.recommended}
        userOverride={captureResultV2.scenarioRecommendation.userOverride}
        defaultRecommendationLabel={defaultRecommendationLabel}
        explanation={captureResultV2.scenarioRecommendation.explanation}
        programDirectionLabel={
          captureResultV2.scenarioRecommendation.programDirectionLabel
        }
        programDirectionSummary={
          captureResultV2.scenarioRecommendation.programDirectionSummary
        }
        programDrivers={captureResultV2.scenarioRecommendation.programDrivers}
        overrideModeLine={overrideModeLine}
        overrideIntentGuidance={overrideIntentGuidance}
        overrideIntent={captureResultV2.scenarioRecommendation.overrideIntent}
        currentProject={currentProject}
        confidence={captureResultV2.scenarioRecommendation.confidence}
        scenarioFitSummary={scenarioFitSummary}
        captureDataBasis={captureDataBasis}
        reasonCodes={captureResultV2.scenarioRecommendation.reasonCodes}
        handleSaveProjectOverride={handleSaveProjectOverride}
        handleClearProjectOverride={handleClearProjectOverride}
        starterModelAssumptionSourceLine={starterModelAssumptionSourceLine}
        starterModelAssumptionFallbackReason={
          starterModelAssumptionFallbackReason
        }
        starterModelOverridePreviewNotice={starterModelOverridePreviewNotice}
        starterModelAssumptionBuckets={starterModelAssumptionBuckets}
        starterModelAssumptionLines={starterModelAssumptionLines}
        starterModelAssetProfileLines={starterModelAssetProfileLines}
      />

      <ScenarioFocusSection
        activeScenario={activeScenario}
        selectedScenarios={selectedScenarios}
        defaultRecommendationLabel={defaultRecommendationLabel}
        formatScenarioLabel={formatScenarioLabel}
        onSelectAll={handleSelectAllScenarios}
        onSelectScenario={handleSelectScenario}
      />

      {/* Multi-Scenario Comparison */}
      <Suspense fallback={sectionFallback}>
        <MultiScenarioComparisonSection
          capturedProperty={result}
          quickAnalysisScenariosCount={quickAnalysisScenarios.length}
          scenarioComparisonData={scenarioComparisonData}
          feasibilitySignals={feasibilitySignals}
          comparisonScenariosCount={comparisonScenarios.length}
          activeScenario={activeScenario}
          scenarioLookup={scenarioLookup}
          propertyId={result.propertyId}
          setActiveScenario={setActiveScenario}
          formatRecordedTimestamp={formatRecordedTimestamp}
        />
      </Suspense>

      {/* Property Overview Section */}
      <Suspense fallback={sectionFallback}>
        <PropertyOverviewSection cards={overviewCards} />
      </Suspense>

      {/* AI Insight Card - Key intelligence from Optimal AI */}
      <Suspense fallback={sectionFallback}>
        <OptimalIntelligenceCard insight={aiInsight} hasProperty={!!result} />
      </Suspense>

      <section className="site-acquisition__preview-layers-inspection">
        <Box sx={{ mt: 'var(--ob-space-150)' }}>
          <Typography
            variant="h6"
            sx={{
              mb: 'var(--ob-space-125)',
              fontWeight: 'var(--ob-font-weight-semibold)',
              color: 'var(--ob-color-text-primary)',
            }}
          >
            Preview Layer Inspection
          </Typography>
          <Suspense fallback={sectionFallback}>
            <PreviewLayersTable
              layers={previewLayerMetadata}
              visibility={previewLayerVisibility}
              focusLayerId={previewFocusLayerId}
              hiddenLayerCount={hiddenLayerCount}
              isLoading={isPreviewMetadataLoading}
              error={previewMetadataError}
              onLayerAction={handleLayerAction}
              onShowAll={handleShowAllLayers}
              onResetFocus={handleResetLayerFocus}
              formatNumber={formatNumber}
              legendEntries={colorLegendEntries}
              onLegendChange={handleLegendEntryChange}
              legendHasPendingChanges={legendHasPendingChanges}
              onLegendReset={handleLegendReset}
            />
          </Suspense>
        </Box>
      </section>

      <section className="site-acquisition__finance-cta">
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            py: 'var(--ob-space-100)',
          }}
        >
          <Link to={dueDiligencePath}>
            <Button variant="secondary" size="lg">
              View Due Diligence →
            </Button>
          </Link>
        </Box>
      </section>

      {/* Project Save CTA */}
      <section className="site-acquisition__finance-cta">
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            gap: 'var(--ob-space-150)',
            flexWrap: 'wrap',
            py: 'var(--ob-space-200)',
          }}
        >
          <Button variant="secondary" size="lg" onClick={handleOpenSaveDialog}>
            Save as Project
          </Button>
          {currentProject && (
            <Link to={`/projects/${currentProject.id}`}>
              <Button variant="ghost" size="lg">
                View Project Hub →
              </Button>
            </Link>
          )}
        </Box>
      </section>

      <SaveProjectDialog
        open={saveDialogOpen}
        saveMode={saveMode}
        projectNameInput={projectNameInput}
        existingProjectId={existingProjectId}
        saveError={saveError}
        savingProject={savingProject}
        projects={projects}
        suggestedProjectName={suggestedProjectName}
        onClose={handleCloseSaveDialog}
        onSaveModeChange={setSaveMode}
        onProjectNameChange={setProjectNameInput}
        onExistingProjectIdChange={setExistingProjectId}
        onSave={handleSaveProject}
      />
    </div>
  )
}
