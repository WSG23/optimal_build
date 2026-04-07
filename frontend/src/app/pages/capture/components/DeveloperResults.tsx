/**
 * DeveloperResults - Developer workspace wrapper for unified capture page
 *
 * Renders the full developer workspace sections after capture:
 * - Property Overview Section
 * - Concept Preview (3D Viewer + Asset Mix)
 * - Preview Layers Table
 * - Scenario Focus Section
 * - Multi-Scenario Comparison
 * - Due Diligence handoff
 * - Project save CTA
 *
 * This component should be lazy-loaded to avoid bundle bloat for agent users.
 */

import { useState, useMemo, useCallback } from 'react'
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

import type { SiteAcquisitionResult } from '../../../../api/siteAcquisition'
import type { DevelopmentScenario } from '../../../../api/agents'
import { Button } from '../../../../components/canonical/Button'
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
  // Active scenario for filtering
  const [activeScenario, setActiveScenario] = useState<
    DevelopmentScenario | 'all'
  >(selectedScenarios[0] ?? 'all')
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
  // Preview job state - use hook with options object
  const {
    previewJob,
    previewDetailLevel,
    setPreviewDetailLevel,
    isRefreshingPreview,
    previewLayerMetadata,
    previewLayerVisibility,
    previewFocusLayerId,
    isPreviewMetadataLoading,
    previewMetadataError,
    hiddenLayerCount,
    colorLegendEntries,
    legendHasPendingChanges,
    handleRefreshPreview,
    handleToggleLayerVisibility,
    handleSoloPreviewLayer,
    handleShowAllLayers,
    handleFocusLayer,
    handleResetLayerFocus,
    handleLegendEntryChange,
    handleLegendReset,
  } = usePreviewJob({ capturedProperty: result })

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
      previewJob: result.previewJobs?.[0] ?? null,
      colorLegendEntries: colorLegendEntries ?? [],
      formatters: {
        formatNumber,
        formatCurrency: () => '—',
        formatTimestamp: formatRecordedTimestamp,
      },
    })
  }, [result, colorLegendEntries, formatNumber, formatRecordedTimestamp])

  // Instant capture insight based on captured property data
  const aiInsight = useMemo(() => {
    if (!result) return null
    const scenarios = selectedScenarios
      .map((s) => scenarioLookup.get(s)?.label ?? s)
      .join(', ')
    const envelope = result.buildEnvelope
    const analysisPoints = [
      envelope.allowablePlotRatio !== null
        ? `plot ratio ${formatNumber(envelope.allowablePlotRatio, {
            maximumFractionDigits: 2,
          })}`
        : null,
      envelope.maxBuildableGfaSqm !== null
        ? `max buildable GFA ${formatNumber(envelope.maxBuildableGfaSqm, {
            maximumFractionDigits: 0,
          })} sqm`
        : null,
      envelope.buildingHeightLimitM !== null
        ? `height limit ${formatNumber(envelope.buildingHeightLimitM, {
            maximumFractionDigits: 0,
          })} m`
        : null,
      envelope.siteCoveragePct !== null
        ? `site coverage ${formatNumber(envelope.siteCoveragePct, {
            maximumFractionDigits: 0,
          })}%`
        : null,
    ].filter(Boolean)
    const previewStatus =
      result.visualization?.status?.replace(/_/g, ' ').toLowerCase() ??
      'pending'
    const isFallbackCapture =
      result.visualization?.status?.toLowerCase() === 'placeholder' ||
      result.buildEnvelope?.buildingHeightLimitM == null ||
      result.buildEnvelope?.siteCoveragePct == null
    const analysisSummary =
      analysisPoints.length > 0
        ? analysisPoints.slice(0, 3).join(', ')
        : 'zoning and envelope controls are still resolving'
    const scopeNote = isFallbackCapture
      ? 'This is a preliminary capture: scalar controls only, with no setback or floor-by-floor compliance modelling.'
      : 'Capture reflects the currently resolved scalar controls for this site, without setback or floor-by-floor compliance modelling.'
    return `Instant capture analysis for ${result.address?.district ?? 'this location'} highlights ${analysisSummary}. Active scenarios: ${scenarios}. Preview status: ${previewStatus}. ${scopeNote}`
  }, [formatNumber, result, selectedScenarios, scenarioLookup])

  return (
    <div className="site-acquisition__developer-results">
      {/* Property Overview Section */}
      <PropertyOverviewSection cards={overviewCards} />

      {/* AI Insight Card - Key intelligence from Optimal AI */}
      <OptimalIntelligenceCard insight={aiInsight} hasProperty={!!result} />

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
                disabled={!previewJob}
                sx={{ minWidth: 'var(--ob-size-600)' }}
              >
                <MenuItem value="simple">Simple</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
              </Select>
            </FormControl>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => handleRefreshPreview()}
              disabled={isRefreshingPreview || !previewJob}
            >
              <RefreshIcon
                sx={{
                  fontSize: 'var(--ob-font-size-md)',
                  mr: 'var(--ob-space-025)',
                }}
              />
              Refresh Preview Status
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
            previewUrl={previewJob?.previewUrl ?? null}
            metadataUrl={previewJob?.metadataUrl ?? null}
            status={previewJob?.status ?? 'pending'}
            thumbnailUrl={previewJob?.thumbnailUrl ?? null}
          />

          {/* Preview Layers Table */}
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

        {previewMetadataError && (
          <Typography color="error" sx={{ mt: 'var(--ob-space-050)' }}>
            {previewMetadataError}
          </Typography>
        )}
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
          <Box sx={{ display: 'flex', gap: 'var(--ob-space-050)' }}>
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
