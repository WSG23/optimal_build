import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
// createPortal is used by modal components
import {
  capturePropertyForDevelopment,
  type DevelopmentScenario,
  type SiteAcquisitionResult,
  type GeometryDetailLevel,
} from '../../../api/siteAcquisition'
import { forwardGeocodeAddress } from '../../../api/geocoding'
import { Preview3DViewer } from '../../components/site-acquisition/Preview3DViewer'
import { useFeaturePreferences } from '../../../hooks/useFeaturePreferences'

// Extracted types, constants, utils, and hooks
import type { QuickAnalysisEntry } from './types'
import {
  // SCENARIO_OPTIONS and JURISDICTION_OPTIONS are used by PropertyCaptureForm
  CONDITION_RATINGS,
  CONDITION_RISK_LEVELS,
  PREVIEW_DETAIL_OPTIONS,
  PREVIEW_DETAIL_LABELS,
} from './constants'
import {
  describeDetailLevel,
  buildPropertyOverviewCards,
  buildFeasibilitySignals,
} from './utils'
// formatCategoryName and getSeverityVisuals are used by child components
import { usePreviewJob } from './hooks/usePreviewJob'
import { useChecklist } from './hooks/useChecklist'
import { useConditionAssessment } from './hooks/useConditionAssessment'
import { useScenarioComparison } from './hooks/useScenarioComparison'
import { DueDiligenceChecklistSection } from './components/checklist/DueDiligenceChecklistSection'
import { InspectionHistorySummary } from './components/InspectionHistorySummary'
import { ConditionAssessmentSection } from './components/condition-assessment'
import { SalesVelocityCard } from './components/advisory/SalesVelocityCard'
// InspectionHistoryContent is used by InspectionHistoryModal component
import {
  PropertyOverviewSection,
  LayerBreakdownCards,
  ColorLegendEditor,
  PreviewLayersTable,
  type LayerAction,
} from './components/property-overview'
import { ScenarioFocusSection } from './components/scenario-focus'
import { MultiScenarioComparisonSection } from './components/multi-scenario-comparison'
// Modals not yet used but planned for future integration
// import { QuickAnalysisHistoryModal, InspectionHistoryModal } from './components/modals'
import { PropertyCaptureForm } from './components/capture-form'

// MUI & Canonical Components
import {
  Box,
  Stack,
  Typography,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material'
import { Refresh } from '@mui/icons-material'

export function SiteAcquisitionPage() {
  const [jurisdictionCode] = useState('SG')
  const [latitude, setLatitude] = useState('1.3000')
  const [longitude, setLongitude] = useState('103.8500')
  const [address, setAddress] = useState('')
  const [selectedScenarios, setSelectedScenarios] = useState<
    DevelopmentScenario[]
  >([])
  const [isCapturing, setIsCapturing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [capturedProperty, setCapturedProperty] =
    useState<SiteAcquisitionResult | null>(null)
  const [isGeocoding, setIsGeocoding] = useState(false)

  // Auto-geocode address to coordinates when address field loses focus
  const handleAddressBlur = useCallback(async () => {
    const trimmed = address.trim()
    // Only geocode if address is non-empty and coordinates are empty/default
    if (!trimmed) return
    const lat = parseFloat(latitude)
    const lon = parseFloat(longitude)
    // Skip if coordinates already look valid and non-default
    if (!isNaN(lat) && !isNaN(lon) && (lat !== 1.3 || lon !== 103.85)) return

    setIsGeocoding(true)
    try {
      const result = await forwardGeocodeAddress(trimmed)
      setLatitude(result.latitude.toFixed(6))
      setLongitude(result.longitude.toFixed(6))
      // Optionally update address with formatted version
      if (result.formattedAddress) {
        setAddress(result.formattedAddress)
      }
    } catch (err) {
      // Silently fail - user can still enter coordinates manually
      console.warn('Forward geocoding failed:', err)
    } finally {
      setIsGeocoding(false)
    }
  }, [address, latitude, longitude])

  // Feature preferences for toggling optional features
  // Using 'developer' role by default for Site Acquisition page
  const { preferences: _preferences } = useFeaturePreferences('developer')

  // Preview job state - managed by usePreviewJob hook
  const {
    previewJob,
    setPreviewJob,
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
    previewViewerMetadataUrl,
    layerBreakdown,
    handleRefreshPreview,
    handleToggleLayerVisibility,
    handleSoloPreviewLayer,
    handleShowAllLayers,
    handleFocusLayer,
    handleResetLayerFocus,
    handleLegendEntryChange,
    handleLegendReset,
  } = usePreviewJob({ capturedProperty })

  // Checklist state - managed by useChecklist hook
  // Note: scenarioFilterOptions is computed locally (includes scenarioOverrideEntries)
  const {
    checklistItems,
    isLoadingChecklist,
    selectedCategory,
    setSelectedCategory,
    activeScenario,
    setActiveScenario,
    availableChecklistScenarios,
    filteredChecklistItems,
    displaySummary,
    activeScenarioDetails,
    scenarioChecklistProgress,
    scenarioLookup,
    handleChecklistUpdate,
  } = useChecklist({ capturedProperty })

  // Condition assessment state from hook
  const {
    conditionAssessment,
    isLoadingCondition,
    isEditingAssessment,
    assessmentEditorMode: _assessmentEditorMode,
    assessmentDraft: _assessmentDraft,
    isSavingAssessment: _isSavingAssessment,
    assessmentSaveMessage,
    assessmentHistory,
    isLoadingAssessmentHistory,
    assessmentHistoryError,
    historyViewMode: _historyViewMode,
    setHistoryViewMode: _setHistoryViewMode,
    scenarioAssessments,
    isLoadingScenarioAssessments,
    scenarioAssessmentsError,
    isExportingReport,
    reportExportMessage,
    latestAssessmentEntry,
    previousAssessmentEntry,
    openAssessmentEditor,
    closeAssessmentEditor,
    handleAssessmentFieldChange: _handleAssessmentFieldChange,
    handleAssessmentSystemChange: _handleAssessmentSystemChange,
    handleAssessmentSubmit: _handleAssessmentSubmit,
    resetAssessmentDraft: _resetAssessmentDraft,
    handleReportExport,
  } = useConditionAssessment({ capturedProperty, activeScenario })

  // Currency symbol for formatting (needed by useScenarioComparison)
  const currencySymbol = capturedProperty?.currencySymbol || 'S$'

  // Scenario comparison state from hook
  const {
    quickAnalysisScenarios,
    comparisonScenarios,
    scenarioOverrideEntries,
    scenarioComparisonData,
    scenarioComparisonTableRows: _scenarioComparisonTableRows,
    scenarioComparisonVisible,
    activeScenarioSummary,
    baseScenarioAssessment,
    setScenarioComparisonBase,
    scenarioComparisonEntries,
    systemComparisons: _systemComparisons,
    systemComparisonMap,
    combinedConditionInsights,
    insightSubtitle,
    recommendedActionDiff: _recommendedActionDiff,
    comparisonSummary: _comparisonSummary,
    quickAnalysisHistory,
    formatScenarioMetricValue: _formatScenarioMetricValue,
    summariseScenarioMetrics: _summariseScenarioMetrics,
    formatScenarioLabel,
    formatNumberMetric,
    formatCurrency,
  } = useScenarioComparison({
    capturedProperty,
    activeScenario,
    conditionAssessment,
    assessmentHistory,
    scenarioAssessments,
    scenarioChecklistProgress,
    displaySummary,
    currencySymbol,
  })

  const [isHistoryModalOpen, setHistoryModalOpen] = useState(false)
  const [isQuickAnalysisHistoryOpen, setQuickAnalysisHistoryOpen] =
    useState(false)
  useEffect(() => {
    if (quickAnalysisHistory.length === 0 && isQuickAnalysisHistoryOpen) {
      setQuickAnalysisHistoryOpen(false)
    }
  }, [quickAnalysisHistory.length, isQuickAnalysisHistoryOpen])

  // Escape key handling for modals (useConditionAssessment handles history view mode reset)
  useEffect(() => {
    if (!isHistoryModalOpen && !isEditingAssessment) {
      return
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        if (isEditingAssessment) {
          closeAssessmentEditor()
        } else if (isHistoryModalOpen) {
          setHistoryModalOpen(false)
        }
      }
    }

    const originalOverflow = document.body.style.overflow
    window.addEventListener('keydown', handleKeyDown)
    document.body.style.overflow = 'hidden'

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = originalOverflow
    }
  }, [isHistoryModalOpen, isEditingAssessment, closeAssessmentEditor])

  // Note: Condition assessment reset is handled by useConditionAssessment hook
  // Note: quickAnalysisScenarios, comparisonScenarios, scenarioOverrideEntries are provided by useScenarioComparison hook

  // scenarioFilterOptions is computed locally because it includes scenarioOverrideEntries from hook
  const scenarioFilterOptions = useMemo(() => {
    const collected = new Set<DevelopmentScenario>()
    availableChecklistScenarios.forEach((scenario) => collected.add(scenario))
    quickAnalysisScenarios.forEach((scenario) =>
      collected.add(scenario.scenario as DevelopmentScenario),
    )
    scenarioOverrideEntries.forEach((assessment) =>
      collected.add(assessment.scenario),
    )
    return Array.from(collected)
  }, [
    availableChecklistScenarios,
    quickAnalysisScenarios,
    scenarioOverrideEntries,
  ])

  const scenarioFocusOptions = useMemo(
    () =>
      ['all', ...scenarioFilterOptions] as Array<'all' | DevelopmentScenario>,
    [scenarioFilterOptions],
  )

  // Note: scenarioChecklistProgress is provided by useChecklist hook
  // Note: formatScenarioLabel, formatNumberMetric, formatCurrency, formatScenarioMetricValue,
  // summariseScenarioMetrics are provided by useScenarioComparison hook

  const scenarioComparisonRef = useRef<HTMLDivElement | null>(null)
  const formatTimestamp = useCallback((value: string) => {
    const parsed = new Date(value)
    if (Number.isNaN(parsed.getTime())) {
      return value
    }
    return new Intl.DateTimeFormat('en-SG', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(parsed)
  }, [])
  const handleScenarioComparisonScroll = useCallback(() => {
    scenarioComparisonRef.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'start',
    })
  }, [])

  // Wrapper for the pure buildFeasibilitySignals function
  const getFeasibilitySignals = useCallback(
    (entry: QuickAnalysisEntry) =>
      buildFeasibilitySignals({
        entry,
        capturedProperty,
        formatNumber: formatNumberMetric,
      }),
    [capturedProperty, formatNumberMetric],
  )
  const propertyInfoSummary = capturedProperty?.propertyInfo ?? null
  const zoningSummary = capturedProperty?.uraZoning ?? null
  const nearestMrtStation =
    capturedProperty?.nearbyAmenities?.mrtStations?.[0] ?? null
  const nearestBusStop =
    capturedProperty?.nearbyAmenities?.busStops?.[0] ?? null

  const propertyOverviewCards = useMemo(() => {
    if (!capturedProperty) {
      return []
    }
    return buildPropertyOverviewCards({
      capturedProperty,
      propertyInfoSummary,
      zoningSummary,
      nearestMrtStation,
      nearestBusStop,
      previewJob,
      colorLegendEntries,
      formatters: {
        formatNumber: formatNumberMetric,
        formatCurrency,
        formatTimestamp,
      },
    })
  }, [
    capturedProperty,
    propertyInfoSummary,
    zoningSummary,
    nearestMrtStation,
    nearestBusStop,
    previewJob,
    colorLegendEntries,
    formatNumberMetric,
    formatCurrency,
    formatTimestamp,
  ])

  // Note: layerBreakdown is now provided by usePreviewJob hook

  // Unified layer action handler for PreviewLayersTable
  const handleLayerAction = useCallback(
    (layerId: string, action: LayerAction) => {
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

  // Note: scenarioComparisonBase useEffect, baseScenarioAssessment, and scenarioComparisonEntries
  // are provided by useScenarioComparison hook

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
        scenarioLookup.get(scenario)?.label ?? formatScenarioLabel(scenario)
      const signals = getFeasibilitySignals(entry)
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
    getFeasibilitySignals,
    formatScenarioLabel,
  ])

  const describeRatingChange = useCallback(
    (current: string, reference: string) => {
      type Rating = (typeof CONDITION_RATINGS)[number]
      const currentIndex = CONDITION_RATINGS.indexOf(current as Rating)
      const referenceIndex = CONDITION_RATINGS.indexOf(reference as Rating)
      if (currentIndex === -1 || referenceIndex === -1) {
        if (current === reference) {
          return { text: 'Rating unchanged.', tone: 'neutral' as const }
        }
        return {
          text: `Rating changed from ${reference} to ${current}.`,
          tone: 'neutral' as const,
        }
      }
      if (currentIndex === referenceIndex) {
        return { text: 'Rating unchanged.', tone: 'neutral' as const }
      }
      if (currentIndex < referenceIndex) {
        return {
          text: `Rating improved from ${reference} to ${current}.`,
          tone: 'positive' as const,
        }
      }
      return {
        text: `Rating declined from ${reference} to ${current}.`,
        tone: 'negative' as const,
      }
    },
    [],
  )

  const describeRiskChange = useCallback(
    (current: string, reference: string) => {
      type RiskLevel = (typeof CONDITION_RISK_LEVELS)[number]
      const currentIndex = CONDITION_RISK_LEVELS.indexOf(current as RiskLevel)
      const referenceIndex = CONDITION_RISK_LEVELS.indexOf(
        reference as RiskLevel,
      )
      if (currentIndex === -1 || referenceIndex === -1) {
        if (current === reference) {
          return { text: 'Risk level unchanged.', tone: 'neutral' as const }
        }
        return {
          text: `Risk level changed from ${reference} to ${current}.`,
          tone: 'neutral' as const,
        }
      }
      if (currentIndex === referenceIndex) {
        return { text: 'Risk level unchanged.', tone: 'neutral' as const }
      }
      if (currentIndex < referenceIndex) {
        return {
          text: `Risk eased from ${reference} to ${current}.`,
          tone: 'positive' as const,
        }
      }
      return {
        text: `Risk intensified from ${reference} to ${current}.`,
        tone: 'negative' as const,
      }
    },
    [],
  )

  // Note: systemComparisons, systemComparisonMap, systemTrendInsights, backendInsightViews,
  // combinedConditionInsights, insightSubtitle, scenarioComparisonData, scenarioComparisonTableRows,
  // scenarioComparisonVisible, activeScenarioSummary, recommendedActionDiff, comparisonSummary,
  // and the quick analysis history snapshot effect are provided by useScenarioComparison hook

  const formatRecordedTimestamp = useCallback((timestamp?: string | null) => {
    if (!timestamp) {
      return 'Draft assessment'
    }
    const parsed = new Date(timestamp)
    if (Number.isNaN(parsed.getTime())) {
      return timestamp
    }
    return parsed.toLocaleString()
  }, [])

  useEffect(() => {
    setSelectedCategory(null)
  }, [activeScenario, setSelectedCategory])

  // Note: All condition assessment loading, effects, and handlers are now provided by useConditionAssessment hook

  function toggleScenario(scenario: DevelopmentScenario) {
    setSelectedScenarios((prev) =>
      prev.includes(scenario)
        ? prev.filter((s) => s !== scenario)
        : [...prev, scenario],
    )
  }

  const buildAssetMixStorageKey = (propertyId: string) =>
    `developer-asset-mix:${propertyId}`

  async function handleCapture(e: React.FormEvent) {
    e.preventDefault()
    const lat = parseFloat(latitude)
    const lon = parseFloat(longitude)

    if (isNaN(lat) || isNaN(lon)) {
      setError('Please enter valid coordinates')
      return
    }

    if (selectedScenarios.length === 0) {
      setError('Please select at least one development scenario')
      return
    }

    setIsCapturing(true)
    setError(null)

    try {
      const result = await capturePropertyForDevelopment({
        latitude: lat,
        longitude: lon,
        developmentScenarios: selectedScenarios,
        previewDetailLevel,
        jurisdictionCode,
      })

      setCapturedProperty(result)
      setPreviewJob(result.previewJobs?.[0] ?? null)
      if (result.propertyId) {
        try {
          const propertyLabel =
            result.propertyInfo?.propertyName?.trim() ||
            result.address?.fullAddress?.trim() ||
            null
          sessionStorage.setItem(
            buildAssetMixStorageKey(result.propertyId),
            JSON.stringify({
              optimizations: result.optimizations,
              buildEnvelope: result.buildEnvelope,
              financialSummary: result.financialSummary,
              visualization: result.visualization,
              propertyInfo: result.propertyInfo,
              address: result.address,
              metadata: {
                propertyId: result.propertyId,
                propertyName: propertyLabel,
                capturedAt: result.timestamp ?? new Date().toISOString(),
              },
            }),
          )
        } catch (storageError) {
          console.warn('Unable to persist asset mix snapshot', storageError)
        }
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to capture property',
      )
    } finally {
      setIsCapturing(false)
    }
  }

  // Note: handleChecklistUpdate is provided by useChecklist hook
  // Note: handleReportExport is provided by useConditionAssessment hook

  const InlineInspectionHistorySummary = () => (
    <InspectionHistorySummary
      hasProperty={!!capturedProperty}
      isLoading={isLoadingAssessmentHistory}
      error={assessmentHistoryError}
      latestEntry={latestAssessmentEntry}
      previousEntry={previousAssessmentEntry}
      formatScenario={(scenario) =>
        formatScenarioLabel(
          scenario as DevelopmentScenario | 'all' | null | undefined,
        )
      }
      formatTimestamp={formatRecordedTimestamp}
      onViewTimeline={() => setHistoryModalOpen(true)}
      onLogInspection={() => openAssessmentEditor('new')}
    />
  )

  return (
    <Box
      className="page site-acquisition"
      sx={{ width: '100%', pb: 'var(--ob-space-300)' }}
    >
      <Stack spacing="var(--ob-space-200)">
        {/* Property Capture Form - Component provides its own surface */}
        <PropertyCaptureForm
          address={address}
          setAddress={setAddress}
          latitude={latitude}
          setLatitude={setLatitude}
          longitude={longitude}
          setLongitude={setLongitude}
          selectedScenarios={selectedScenarios}
          isCapturing={isCapturing}
          isGeocoding={isGeocoding}
          error={error}
          capturedProperty={capturedProperty}
          onCapture={handleCapture}
          onToggleScenario={toggleScenario}
          onAddressBlur={handleAddressBlur}
        />

        {capturedProperty && (
          <>
            {/* Property Overview - Content vs Context pattern */}
            <Box>
              {/* Header on background */}
              <Typography variant="h5" fontWeight={600} gutterBottom>
                Property Overview
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mb: 'var(--ob-space-200)' }}
              >
                Captured property data and development metrics
              </Typography>

              {/* Data cards - no wrapper needed, cards have their own styling */}
              <Box>
                <PropertyOverviewSection cards={propertyOverviewCards} />

                {previewJob && (
                  <Box
                    sx={{
                      mt: 'var(--ob-space-400)',
                      bgcolor: 'background.default',
                      borderRadius: 'var(--ob-radius-sm)',
                      overflow: 'hidden',
                    }}
                  >
                    <Box
                      sx={{
                        p: 'var(--ob-space-200)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        borderBottom: '1px solid',
                        borderColor: 'divider',
                      }}
                    >
                      <Typography variant="h6">Development Preview</Typography>
                      <Typography
                        variant="overline"
                        sx={{
                          px: 'var(--ob-space-100)',
                          border: '1px solid',
                          borderColor: 'secondary.main',
                          borderRadius: 'var(--ob-radius-xs)',
                        }}
                      >
                        {previewJob.status.toUpperCase()}
                      </Typography>
                    </Box>

                    <Box sx={{ height: 500, bgcolor: 'black' }}>
                      <Preview3DViewer
                        previewUrl={previewJob.previewUrl}
                        metadataUrl={previewViewerMetadataUrl}
                        status={previewJob.status}
                        thumbnailUrl={previewJob.thumbnailUrl}
                        layerVisibility={previewLayerVisibility}
                        focusLayerId={previewFocusLayerId}
                      />
                    </Box>

                    <Box
                      sx={{
                        p: 'var(--ob-space-200)',
                        borderTop: '1px solid',
                        borderColor: 'divider',
                      }}
                    >
                      <Stack
                        direction="row"
                        spacing="var(--ob-space-300)"
                        alignItems="center"
                      >
                        <FormControl size="small" sx={{ minWidth: 200 }}>
                          <InputLabel>Geometry Detail</InputLabel>
                          <Select
                            value={previewDetailLevel}
                            label="Geometry Detail"
                            onChange={(e) =>
                              setPreviewDetailLevel(
                                e.target.value as GeometryDetailLevel,
                              )
                            }
                            disabled={isRefreshingPreview}
                          >
                            {PREVIEW_DETAIL_OPTIONS.map((option) => (
                              <MenuItem key={option} value={option}>
                                {PREVIEW_DETAIL_LABELS[option]}
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>

                        <Button
                          variant="outlined"
                          startIcon={
                            <Refresh
                              className={isRefreshingPreview ? 'fa-spin' : ''}
                            />
                          }
                          onClick={handleRefreshPreview}
                          disabled={isRefreshingPreview}
                        >
                          {isRefreshingPreview
                            ? 'Refreshing...'
                            : 'Refresh Render'}
                        </Button>

                        <Typography variant="caption" color="text.secondary">
                          Geometry detail:{' '}
                          <strong>
                            {describeDetailLevel(
                              previewJob.geometryDetailLevel,
                            )}
                          </strong>
                        </Typography>
                      </Stack>
                    </Box>
                  </Box>
                )}

                {previewJob && (
                  <Box sx={{ mt: 'var(--ob-space-200)' }}>
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
                      formatNumber={formatNumberMetric}
                    />
                  </Box>
                )}

                <Box sx={{ mt: 'var(--ob-space-200)' }}>
                  <ColorLegendEditor
                    entries={colorLegendEntries}
                    hasPendingChanges={legendHasPendingChanges}
                    onChange={handleLegendEntryChange}
                    onReset={handleLegendReset}
                  />
                </Box>

                <Box sx={{ mt: 'var(--ob-space-200)' }}>
                  <LayerBreakdownCards layers={layerBreakdown} />
                </Box>
              </Box>
            </Box>

            {/* Scenario Focus - Depth 1 */}
            {scenarioFocusOptions.length > 0 && (
              <ScenarioFocusSection
                scenarioFocusOptions={scenarioFocusOptions}
                scenarioLookup={scenarioLookup}
                activeScenario={activeScenario}
                activeScenarioSummary={activeScenarioSummary}
                scenarioChecklistProgress={scenarioChecklistProgress}
                displaySummary={displaySummary}
                quickAnalysisHistoryCount={quickAnalysisHistory.length}
                scenarioComparisonVisible={scenarioComparisonVisible}
                setActiveScenario={setActiveScenario}
                onCompareScenarios={handleScenarioComparisonScroll}
                onOpenQuickAnalysisHistory={() =>
                  setQuickAnalysisHistoryOpen(true)
                }
                onOpenInspectionHistory={() => setHistoryModalOpen(true)}
                formatScenarioLabel={formatScenarioLabel}
              />
            )}

            <SalesVelocityCard jurisdictionCode={jurisdictionCode} />

            {/* Due Diligence Checklist - Depth 1 */}
            <DueDiligenceChecklistSection
              capturedProperty={capturedProperty}
              checklistItems={checklistItems}
              filteredChecklistItems={filteredChecklistItems}
              availableChecklistScenarios={availableChecklistScenarios}
              scenarioLookup={scenarioLookup}
              displaySummary={displaySummary}
              activeScenario={activeScenario}
              activeScenarioDetails={activeScenarioDetails}
              selectedCategory={selectedCategory}
              isLoadingChecklist={isLoadingChecklist}
              setActiveScenario={setActiveScenario}
              setSelectedCategory={setSelectedCategory}
              handleChecklistUpdate={handleChecklistUpdate}
            />

            {/* Multi-Scenario Comparison - Depth 1 */}
            <MultiScenarioComparisonSection
              capturedProperty={capturedProperty}
              quickAnalysisScenariosCount={quickAnalysisScenarios.length}
              scenarioComparisonData={scenarioComparisonData}
              feasibilitySignals={feasibilitySignals}
              comparisonScenariosCount={comparisonScenarios.length}
              activeScenario={activeScenario}
              scenarioLookup={scenarioLookup}
              propertyId={capturedProperty?.propertyId ?? null}
              isExportingReport={isExportingReport}
              reportExportMessage={reportExportMessage}
              setActiveScenario={setActiveScenario}
              handleReportExport={handleReportExport}
              formatRecordedTimestamp={formatRecordedTimestamp}
            />

            {/* Condition Assessment - Depth 1 */}
            <ConditionAssessmentSection
              capturedProperty={capturedProperty}
              conditionAssessment={conditionAssessment}
              isLoadingCondition={isLoadingCondition}
              latestAssessmentEntry={latestAssessmentEntry}
              previousAssessmentEntry={previousAssessmentEntry}
              assessmentHistoryError={assessmentHistoryError}
              isLoadingAssessmentHistory={isLoadingAssessmentHistory}
              assessmentSaveMessage={assessmentSaveMessage}
              scenarioAssessments={scenarioAssessments}
              isLoadingScenarioAssessments={isLoadingScenarioAssessments}
              scenarioAssessmentsError={scenarioAssessmentsError}
              scenarioOverrideEntries={scenarioOverrideEntries}
              baseScenarioAssessment={baseScenarioAssessment}
              scenarioComparisonEntries={scenarioComparisonEntries}
              combinedConditionInsights={combinedConditionInsights}
              insightSubtitle={insightSubtitle}
              systemComparisonMap={systemComparisonMap}
              isExportingReport={isExportingReport}
              scenarioLookup={scenarioLookup}
              formatRecordedTimestamp={formatRecordedTimestamp}
              formatScenarioLabel={formatScenarioLabel}
              describeRatingChange={describeRatingChange}
              describeRiskChange={describeRiskChange}
              openAssessmentEditor={openAssessmentEditor}
              setScenarioComparisonBase={setScenarioComparisonBase}
              handleReportExport={handleReportExport}
              setHistoryModalOpen={setHistoryModalOpen}
              InlineInspectionHistorySummary={InlineInspectionHistorySummary}
            />
          </>
        )}
      </Stack>
    </Box>
  )
}
