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

import { useState, useMemo, useCallback, useEffect, useRef } from 'react'
import {
  Box,
  Typography,
  Select,
  MenuItem,
  FormControl,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
  Stack,
} from '@mui/material'
import RefreshIcon from '@mui/icons-material/Refresh'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import ViewInArIcon from '@mui/icons-material/ViewInAr'

import type { SiteAcquisitionResult } from '../../../../api/siteAcquisition'
import type { DevelopmentScenario } from '../../../../api/agents'
import { Button } from '../../../../components/canonical/Button'
import { Card } from '../../../../components/canonical/Card'
import { Link } from '../../../../router'
import { useProject } from '../../../../contexts/useProject'
import {
  linkCaptureToProject,
  saveProjectFromCapture,
} from '../../../../api/siteAcquisition'
import { saveCaptureForProject } from '../utils/captureStorage'

// Import Site Acquisition components
import { PropertyOverviewSection } from '../../site-acquisition/components/property-overview/PropertyOverviewSection'
import { Preview3DViewer } from '../../../components/site-acquisition/Preview3DViewer'
import { PreviewLayersTable } from '../../site-acquisition/components/property-overview/PreviewLayersTable'
import { MultiScenarioComparisonSection } from '../../site-acquisition/components/multi-scenario-comparison/MultiScenarioComparisonSection'

// Import Site Acquisition hooks
import { usePreviewJob } from '../../site-acquisition/hooks/usePreviewJob'
import { useCaptureScenarioComparison } from '../../site-acquisition/hooks/useCaptureScenarioComparison'
import { buildFeasibilitySignals } from '../../site-acquisition/utils/signals'

// Import constants for scenario lookup
import { SCENARIO_OPTIONS } from '../../site-acquisition/constants'

// Import card builder utility
import { buildPropertyOverviewCards } from '../../site-acquisition/utils/cardBuilders'
import { mapSiteAcquisitionResultToCaptureResultV2 } from '../utils/captureResultV2'

// Import OptimalIntelligenceCard for AI insights
import { OptimalIntelligenceCard } from '../../site-acquisition/components/OptimalIntelligenceCard'

export interface DeveloperResultsProps {
  result: SiteAcquisitionResult
  selectedScenarios: DevelopmentScenario[]
}

export function DeveloperResults({
  result,
  selectedScenarios,
}: DeveloperResultsProps) {
  const autoRequestedStarterModelRef = useRef<Set<string>>(new Set())
  // Active scenario for filtering
  const [activeScenario, setActiveScenario] = useState<
    DevelopmentScenario | 'all'
  >('all')
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
      }),
    [activeScenario, result, selectedScenarios],
  )

  // Preview job state - use hook with options object
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
    preferredScenario: captureResultV2.scenarioRecommendation.recommended,
  })

  const effectiveStarterModel = useMemo(() => {
    const baseModel = captureResultV2.starterModel
    if (previewJob) {
      const rawStatus = previewJob.status.toLowerCase()
      const status =
        rawStatus === 'ready' ||
        rawStatus === 'failed' ||
        rawStatus === 'queued' ||
        rawStatus === 'processing' ||
        rawStatus === 'placeholder'
          ? rawStatus
          : baseModel.status
      return {
        ...baseModel,
        status,
        modelUrl: previewJob.previewUrl ?? baseModel.modelUrl,
        metadataUrl: previewJob.metadataUrl ?? baseModel.metadataUrl,
        thumbnailUrl: previewJob.thumbnailUrl ?? baseModel.thumbnailUrl,
        generatedFrom: Array.from(
          new Set(['preview_job', ...baseModel.generatedFrom]),
        ),
      }
    }

    if (isGeneratingStarterModel) {
      return {
        ...baseModel,
        status: 'processing' as const,
      }
    }

    return baseModel
  }, [captureResultV2.starterModel, isGeneratingStarterModel, previewJob])

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

  // Currency symbol for formatting
  const currencySymbol = result.currencySymbol ?? 'S$'
  const suggestedProjectName =
    result.propertyInfo?.propertyName?.trim() ||
    result.address?.fullAddress?.trim() ||
    'Capture Project'

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

  // Scenario comparison state - pass required options object and extract all values
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

  // Number formatter for card values
  const formatNumber = useCallback(
    (value: number, options?: Intl.NumberFormatOptions) => {
      return new Intl.NumberFormat('en-SG', {
        maximumFractionDigits: 1,
        ...options,
      }).format(value)
    },
    [],
  )

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
  }, [
    quickAnalysisScenarios,
    scenarioLookup,
    formatNumber,
    formatScenarioLabel,
    result,
  ])

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
  }, [
    colorLegendEntries,
    formatNumber,
    formatRecordedTimestamp,
    previewJob,
    result,
  ])

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
      ? `User override active: ${formatScenarioLabel(recommendation.recommended)} remains selected even though Capture would otherwise prefer ${recommendation.alternatives[0] ? formatScenarioLabel(recommendation.alternatives[0]) : 'another scenario'}.`
      : `Capture currently recommends ${formatScenarioLabel(recommendation.recommended)} first.`
    return `Instant capture analysis for ${result.address?.district ?? 'this location'} highlights ${analysisSummary}. Preview status: ${previewStatus}. ${scenarioNote} ${scopeNote}`
  }, [
    captureResultV2,
    effectiveStarterModel,
    formatNumber,
    formatScenarioLabel,
    result,
  ])

  const starterModelActionLabel = isGeneratingStarterModel
    ? 'Generating Starter Model...'
    : isRefreshingPreview
      ? 'Refreshing Starter Model...'
      : hasPreferredScenarioPreview
        ? 'Refresh Starter Model'
        : 'Generate Starter Model'

  const starterModelStatusSummary = useMemo(() => {
    const scenarioLabel = formatScenarioLabel(
      captureResultV2.scenarioRecommendation.recommended,
    )
    switch (effectiveStarterModel.status) {
      case 'queued':
        return `A ${scenarioLabel.toLowerCase()} starter model has been queued. Capture will replace the fallback preview when the render is ready.`
      case 'processing':
        return `Capture is generating the ${scenarioLabel.toLowerCase()} starter model now.`
      case 'ready':
        return hasPreferredScenarioPreview
          ? `The ${scenarioLabel.toLowerCase()} starter model is ready for review.`
          : 'Capture is still showing the current fallback preview for this site.'
      case 'failed':
        return `Capture could not generate the ${scenarioLabel.toLowerCase()} starter model yet. Retry generation from this panel.`
      case 'placeholder':
      default:
        return 'No scenario-specific starter model is available yet. Capture is currently showing the best available fallback preview.'
    }
  }, [
    captureResultV2.scenarioRecommendation.recommended,
    effectiveStarterModel.status,
    formatScenarioLabel,
    hasPreferredScenarioPreview,
  ])

  const scenarioFitSummary = useMemo(() => {
    const codeConstraints = captureResultV2.codeConstraints
    const comparisonSummary =
      codeConstraints.currentVsCodeStatus === 'above'
        ? 'Current GFA exceeds today’s code envelope and may reflect a grandfathered condition.'
        : codeConstraints.currentVsCodeStatus === 'below'
          ? 'Current GFA remains below today’s code envelope, leaving compliant headroom to study.'
          : codeConstraints.currentVsCodeStatus === 'at_limit'
            ? 'Current GFA appears to match today’s code envelope.'
            : 'Current-versus-code envelope relationship is still unresolved.'

    const headroomSummary =
      codeConstraints.maxBuildableGfaSqm != null &&
      codeConstraints.currentGfaSqm != null
        ? `${formatNumber(codeConstraints.currentGfaSqm, {
            maximumFractionDigits: 0,
          })} sqm current vs ${formatNumber(
            codeConstraints.maxBuildableGfaSqm,
            {
              maximumFractionDigits: 0,
            },
          )} sqm current-code max.`
        : 'Current and maximum GFA comparison is still pending.'

    const heritageSummary = captureResultV2.siteContext.heritageOverlay
      ? `Context: ${captureResultV2.siteContext.heritageOverlay}.`
      : 'No heritage overlay is currently driving the starter model.'

    return {
      comparisonSummary,
      headroomSummary,
      heritageSummary,
    }
  }, [
    captureResultV2.codeConstraints,
    captureResultV2.siteContext,
    formatNumber,
  ])

  const starterModelAssumptionLines = useMemo(() => {
    const assumptions = captureResultV2.engineeringAssumptions
    const lines = [
      assumptions.floorToFloorM != null && assumptions.clearCeilingM != null
        ? `Floor-to-floor ${formatNumber(assumptions.floorToFloorM, {
            maximumFractionDigits: 1,
          })} m / clear ceiling ${formatNumber(assumptions.clearCeilingM, {
            maximumFractionDigits: 1,
          })} m`
        : null,
      assumptions.wallThicknessMm != null && assumptions.coreRatioPct != null
        ? `Wall thickness ${formatNumber(assumptions.wallThicknessMm, {
            maximumFractionDigits: 0,
          })} mm / core ratio ${formatNumber(assumptions.coreRatioPct, {
            maximumFractionDigits: 0,
          })}%`
        : null,
      assumptions.commonAreaRatioPct != null &&
      assumptions.hvacSpaceRatioPct != null &&
      assumptions.electricalSpaceRatioPct != null
        ? `Common area ${formatNumber(assumptions.commonAreaRatioPct, {
            maximumFractionDigits: 0,
          })}% / HVAC ${formatNumber(assumptions.hvacSpaceRatioPct, {
            maximumFractionDigits: 0,
          })}% / electrical ${formatNumber(
            assumptions.electricalSpaceRatioPct,
            {
              maximumFractionDigits: 0,
            },
          )}%`
        : null,
      assumptions.retentionStrategy
        ? `Retention strategy ${assumptions.retentionStrategy.replace(/_/g, ' ')}${
            assumptions.efficiencyFactor != null
              ? ` / efficiency factor ${formatNumber(
                  assumptions.efficiencyFactor,
                  {
                    maximumFractionDigits: 2,
                  },
                )}`
              : ''
          }`
        : assumptions.efficiencyFactor != null
          ? `Efficiency factor ${formatNumber(assumptions.efficiencyFactor, {
              maximumFractionDigits: 2,
            })}`
          : null,
      assumptions.structuralGridNote ?? null,
    ].filter((line): line is string => Boolean(line))

    return lines
  }, [captureResultV2.engineeringAssumptions, formatNumber])

  const starterModelAssumptionSourceLine = useMemo(() => {
    const assumptions = captureResultV2.engineeringAssumptions
    const summary = assumptions.provenance?.summary ?? null
    const adjustments = assumptions.provenance?.adjustments ?? []

    const summaryLabel =
      summary === 'rules_with_property_adjustments'
        ? 'Rule defaults with property-specific adjustments'
        : summary === 'rules_only'
          ? 'Rule defaults only'
          : summary === 'frontend_fallback_defaults'
            ? 'Frontend fallback defaults'
            : assumptions.source === 'hybrid'
              ? 'Mixed-source assumptions'
              : assumptions.source === 'heuristic_fallback'
                ? 'Heuristic fallback defaults'
                : assumptions.source === 'rules'
                  ? 'Rule defaults'
                  : assumptions.source.replace(/_/g, ' ')

    if (!adjustments.length) {
      return `Assumption source: ${summaryLabel}.`
    }

    const adjustmentLabel = adjustments
      .map((adjustment) => adjustment.replace(/_/g, ' '))
      .join(', ')

    return `Assumption source: ${summaryLabel} (${adjustmentLabel}).`
  }, [captureResultV2.engineeringAssumptions])

  useEffect(() => {
    const preferredScenario = captureResultV2.scenarioRecommendation.recommended
    const propertyId = result.propertyId
    if (
      !propertyId ||
      !preferredScenario ||
      hasPreferredScenarioPreview ||
      isGeneratingStarterModel ||
      previewGenerationError
    ) {
      return
    }

    const requestKey = `${propertyId}:${preferredScenario}`
    if (autoRequestedStarterModelRef.current.has(requestKey)) {
      return
    }

    autoRequestedStarterModelRef.current.add(requestKey)
    void handleEnsureStarterModel()
  }, [
    captureResultV2.scenarioRecommendation.recommended,
    handleEnsureStarterModel,
    hasPreferredScenarioPreview,
    isGeneratingStarterModel,
    previewGenerationError,
    result.propertyId,
  ])

  return (
    <div className="site-acquisition__developer-results">
      {/* Concept Preview Section */}
      <section className="site-acquisition__preview">
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 'var(--ob-space-150)',
          }}
        >
          <Typography
            variant="h6"
            sx={{
              fontWeight: 'var(--ob-font-weight-semibold)',
              color: 'var(--ob-color-text-primary)',
            }}
          >
            Concept Preview
          </Typography>
          <Box
            sx={{
              display: 'flex',
              gap: 'var(--ob-space-100)',
              alignItems: 'center',
            }}
          >
            <FormControl size="small">
              <Select
                value={previewDetailLevel}
                onChange={(e) =>
                  setPreviewDetailLevel(e.target.value as 'simple' | 'medium')
                }
                disabled={isGeneratingStarterModel || isRefreshingPreview}
                sx={{ minWidth: 'var(--ob-size-600)' }}
              >
                <MenuItem value="simple">Simple</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
              </Select>
            </FormControl>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => void handleEnsureStarterModel()}
              disabled={isRefreshingPreview || isGeneratingStarterModel}
            >
              <RefreshIcon
                sx={{
                  fontSize: 'var(--ob-font-size-md)',
                  mr: 'var(--ob-space-025)',
                }}
              />
              {starterModelActionLabel}
            </Button>
          </Box>
        </Box>

        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' },
            gap: 'var(--ob-space-150)',
          }}
        >
          {/* 3D Viewer */}
          <Preview3DViewer
            previewUrl={effectiveStarterModel.modelUrl}
            metadataUrl={effectiveStarterModel.metadataUrl}
            status={effectiveStarterModel.status}
            thumbnailUrl={effectiveStarterModel.thumbnailUrl}
          />

          <Card
            sx={{
              p: 'var(--ob-space-125)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-075)',
            }}
          >
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-050)',
              }}
            >
              <ViewInArIcon
                sx={{
                  fontSize: 'var(--ob-size-icon-sm)',
                  color: 'info.main',
                }}
              />
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-xs)',
                  fontWeight: 'var(--ob-font-weight-semibold)',
                  letterSpacing: '0.05em',
                  textTransform: 'uppercase',
                  color: 'text.secondary',
                }}
              >
                Starter Model Status
              </Typography>
            </Box>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-lg)',
                fontWeight: 'var(--ob-font-weight-bold)',
                color: 'text.primary',
                textTransform: 'capitalize',
              }}
            >
              {effectiveStarterModel.status.replace(/_/g, ' ')}
              {isGeneratingStarterModel ? ' (updating)' : ''}
            </Typography>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-sm)',
                color: 'text.secondary',
                lineHeight: 1.5,
              }}
            >
              {starterModelStatusSummary}
            </Typography>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-sm)',
                color: 'text.secondary',
                lineHeight: 1.5,
              }}
            >
              Geometry scope:{' '}
              {effectiveStarterModel.geometryScope.replace(/_/g, ' ')}.
              {effectiveStarterModel.floorsEstimate != null
                ? ` Estimated floors: ${effectiveStarterModel.floorsEstimate}.`
                : ' Floor count estimate pending.'}
            </Typography>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'text.secondary',
              }}
            >
              Starter model scenario:{' '}
              {formatScenarioLabel(
                captureResultV2.scenarioRecommendation.recommended,
              )}
            </Typography>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'text.secondary',
              }}
            >
              Full compliance support:{' '}
              {captureResultV2.analysisStatus.supportsFullCompliance
                ? 'Yes'
                : 'No'}
            </Typography>
          </Card>
        </Box>

        {previewMetadataError && (
          <Typography color="error" sx={{ mt: 'var(--ob-space-050)' }}>
            {previewMetadataError}
          </Typography>
        )}
        {previewGenerationError && (
          <Typography color="error" sx={{ mt: 'var(--ob-space-050)' }}>
            {previewGenerationError}
          </Typography>
        )}
      </section>

      <section className="site-acquisition__capture-summary">
        <Box
          sx={{
            mb: 'var(--ob-space-150)',
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', xl: '1fr 1fr' },
            gap: 'var(--ob-space-150)',
          }}
        >
          <Card
            sx={{
              p: 'var(--ob-space-125)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-075)',
            }}
          >
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-050)',
              }}
            >
              <AutoAwesomeIcon
                sx={{
                  fontSize: 'var(--ob-size-icon-sm)',
                  color: 'info.main',
                }}
              />
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-xs)',
                  fontWeight: 'var(--ob-font-weight-semibold)',
                  letterSpacing: '0.05em',
                  textTransform: 'uppercase',
                  color: 'text.secondary',
                }}
              >
                Capture Recommendation
              </Typography>
            </Box>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-lg)',
                fontWeight: 'var(--ob-font-weight-bold)',
                color: 'text.primary',
              }}
            >
              {formatScenarioLabel(
                captureResultV2.scenarioRecommendation.recommended,
              )}
            </Typography>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-sm)',
                color: 'text.secondary',
                lineHeight: 1.5,
              }}
            >
              {captureResultV2.scenarioRecommendation.explanation}
            </Typography>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'text.secondary',
              }}
            >
              Mode:{' '}
              {captureResultV2.scenarioRecommendation.userOverride
                ? 'User override'
                : 'Rule-based default'}
            </Typography>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'text.secondary',
              }}
            >
              Confidence:{' '}
              {captureResultV2.scenarioRecommendation.confidence.replace(
                /_/g,
                ' ',
              )}
            </Typography>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'text.secondary',
                lineHeight: 1.5,
              }}
            >
              Code fit: {scenarioFitSummary.comparisonSummary}
            </Typography>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'text.secondary',
                lineHeight: 1.5,
              }}
            >
              Envelope check: {scenarioFitSummary.headroomSummary}
            </Typography>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'text.secondary',
                lineHeight: 1.5,
              }}
            >
              {scenarioFitSummary.heritageSummary}
            </Typography>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'text.secondary',
              }}
            >
              Reasons:{' '}
              {captureResultV2.scenarioRecommendation.reasonCodes
                .map((code) => code.replace(/_/g, ' ').toLowerCase())
                .join(', ')}
            </Typography>
          </Card>

          <Card
            sx={{
              p: 'var(--ob-space-125)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-075)',
            }}
          >
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-050)',
              }}
            >
              <ViewInArIcon
                sx={{
                  fontSize: 'var(--ob-size-icon-sm)',
                  color: 'info.main',
                }}
              />
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-xs)',
                  fontWeight: 'var(--ob-font-weight-semibold)',
                  letterSpacing: '0.05em',
                  textTransform: 'uppercase',
                  color: 'text.secondary',
                }}
              >
                Starter Model Assumptions
              </Typography>
            </Box>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-sm)',
                color: 'text.secondary',
                lineHeight: 1.5,
              }}
            >
              These defaults shape the first scenario-specific model before
              deeper engineering inputs are added.
            </Typography>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'text.secondary',
                lineHeight: 1.5,
              }}
            >
              {starterModelAssumptionSourceLine}
            </Typography>
            {starterModelAssumptionLines.map((line) => (
              <Typography
                key={line}
                sx={{
                  fontSize: 'var(--ob-font-size-xs)',
                  color: 'text.secondary',
                  lineHeight: 1.5,
                }}
              >
                {line}
              </Typography>
            ))}
          </Card>
        </Box>
      </section>

      {/* Scenario Focus Section */}
      <section className="site-acquisition__scenario-focus">
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 'var(--ob-space-150)',
          }}
        >
          <Typography
            variant="h6"
            sx={{
              fontWeight: 'var(--ob-font-weight-semibold)',
              color: 'var(--ob-color-text-primary)',
            }}
          >
            Scenario Focus
          </Typography>
          <Box
            sx={{
              display: 'flex',
              gap: 'var(--ob-space-050)',
              alignItems: 'center',
              flexWrap: 'wrap',
            }}
          >
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'text.secondary',
              }}
            >
              Recommended:{' '}
              {formatScenarioLabel(
                captureResultV2.scenarioRecommendation.recommended,
              )}
            </Typography>
            <Button
              key="all"
              variant={activeScenario === 'all' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setActiveScenario('all')}
            >
              All Scenarios
            </Button>
            {selectedScenarios.map((scenario) => (
              <Button
                key={scenario}
                variant={activeScenario === scenario ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setActiveScenario(scenario)}
              >
                {formatScenarioLabel(scenario)}
              </Button>
            ))}
          </Box>
        </Box>
      </section>

      {/* Multi-Scenario Comparison */}
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

      {/* Property Overview Section */}
      <PropertyOverviewSection cards={overviewCards} />

      {/* AI Insight Card - Key intelligence from Optimal AI */}
      <OptimalIntelligenceCard insight={aiInsight} hasProperty={!!result} />

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

      <Dialog
        open={saveDialogOpen}
        onClose={() => {
          setSaveDialogOpen(false)
          setSaveError(null)
        }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Save Capture as Project</DialogTitle>
        <DialogContent>
          <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
            <Button
              variant={saveMode === 'new' ? 'primary' : 'secondary'}
              onClick={() => {
                setSaveMode('new')
                setProjectNameInput(suggestedProjectName)
              }}
            >
              Create New
            </Button>
            <Button
              variant={saveMode === 'existing' ? 'primary' : 'secondary'}
              onClick={() => setSaveMode('existing')}
            >
              Use Existing
            </Button>
          </Stack>
          {saveMode === 'new' ? (
            <TextField
              label="Project name"
              value={projectNameInput}
              onChange={(event) => setProjectNameInput(event.target.value)}
              fullWidth
            />
          ) : (
            <FormControl fullWidth>
              <Select
                value={existingProjectId}
                displayEmpty
                onChange={(event) =>
                  setExistingProjectId(String(event.target.value))
                }
              >
                <MenuItem value="">
                  <em>Select a project</em>
                </MenuItem>
                {projects.map((project) => (
                  <MenuItem key={project.id} value={project.id}>
                    {project.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
          {saveError && (
            <Typography color="error" variant="body2" sx={{ mt: 1 }}>
              {saveError}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button
            variant="ghost"
            onClick={() => setSaveDialogOpen(false)}
            disabled={savingProject}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleSaveProject}
            disabled={savingProject}
          >
            {savingProject ? 'Saving...' : 'Save Project'}
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  )
}
