import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
// createPortal is used by modal components
import {
  capturePropertyForDevelopment,
  type DevelopmentScenario,
  type SiteAcquisitionResult,
  type GeometryDetailLevel,
} from '../../../api/siteAcquisition'
import { Preview3DViewer } from '../../components/site-acquisition/Preview3DViewer'
import {
  forwardGeocodeAddress,
  reverseGeocodeCoords,
} from '../../../api/geocoding'

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
import {
  ConditionAssessmentSection,
  ConditionAssessmentEditor,
} from './components/condition-assessment'
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
import {
  QuickAnalysisHistoryModal,
  InspectionHistoryModal,
} from './components/modals'
import { PropertyCaptureForm } from './components/capture-form'

// Note: Constants, types, and utility functions are now imported from:
// - ./types - Page-specific types
// - ./constants - All constants (SCENARIO_OPTIONS, JURISDICTION_OPTIONS, etc.)
// - ./utils - Utility functions (formatters, insights, draftBuilders)
// - ./hooks - Custom hooks (usePreviewJob, useChecklist, useConditionAssessment, useScenarioComparison)

export function SiteAcquisitionPage() {
  const [jurisdictionCode, setJurisdictionCode] = useState('SG')
  const [latitude, setLatitude] = useState('1.3000')
  const [longitude, setLongitude] = useState('103.8500')
  const [address, setAddress] = useState('')
  const [geocodeError, setGeocodeError] = useState<string | null>(null)
  const [selectedScenarios, setSelectedScenarios] = useState<
    DevelopmentScenario[]
  >([])
  const [isCapturing, setIsCapturing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [capturedProperty, setCapturedProperty] =
    useState<SiteAcquisitionResult | null>(null)

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
    assessmentEditorMode,
    assessmentDraft,
    isSavingAssessment,
    assessmentSaveMessage,
    assessmentHistory,
    isLoadingAssessmentHistory,
    assessmentHistoryError,
    historyViewMode,
    setHistoryViewMode,
    scenarioAssessments,
    isLoadingScenarioAssessments,
    scenarioAssessmentsError,
    isExportingReport,
    reportExportMessage,
    latestAssessmentEntry,
    previousAssessmentEntry,
    openAssessmentEditor,
    closeAssessmentEditor,
    handleAssessmentFieldChange,
    handleAssessmentSystemChange,
    handleAssessmentSubmit,
    resetAssessmentDraft,
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
    scenarioComparisonTableRows,
    scenarioComparisonVisible,
    activeScenarioSummary,
    baseScenarioAssessment,
    setScenarioComparisonBase,
    scenarioComparisonEntries,
    systemComparisons,
    systemComparisonMap,
    combinedConditionInsights,
    insightSubtitle,
    recommendedActionDiff,
    comparisonSummary,
    quickAnalysisHistory,
    formatScenarioMetricValue,
    summariseScenarioMetrics,
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

  const handleForwardGeocode = useCallback(async () => {
    if (!address.trim()) {
      setGeocodeError('Please enter an address to geocode.')
      return
    }
    try {
      setGeocodeError(null)
      const result = await forwardGeocodeAddress(address.trim())
      setLatitude(result.latitude.toString())
      setLongitude(result.longitude.toString())
    } catch (err) {
      console.error('Forward geocode failed', err)
      setGeocodeError(
        err instanceof Error ? err.message : 'Unable to geocode address.',
      )
    }
  }, [address])

  const handleReverseGeocode = useCallback(async () => {
    const parsedLat = Number(latitude)
    const parsedLon = Number(longitude)
    if (!Number.isFinite(parsedLat) || !Number.isFinite(parsedLon)) {
      setGeocodeError(
        'Please provide valid coordinates before reverse geocoding.',
      )
      return
    }
    try {
      setGeocodeError(null)
      const result = await reverseGeocodeCoords(parsedLat, parsedLon)
      setAddress(result.formattedAddress)
    } catch (err) {
      console.error('Reverse geocode failed', err)
      setGeocodeError(
        err instanceof Error ? err.message : 'Unable to reverse geocode.',
      )
    }
  }, [latitude, longitude])

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
      formatScenario={formatScenarioLabel}
      formatTimestamp={formatRecordedTimestamp}
      onViewTimeline={() => setHistoryModalOpen(true)}
      onLogInspection={() => openAssessmentEditor('new')}
    />
  )

  return (
    <div
      style={{
        padding: '3rem 2rem',
        maxWidth: '1200px',
        margin: '0 auto',
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", system-ui, sans-serif',
        color: '#1d1d1f',
      }}
    >
      {/* Header */}
      <header style={{ marginBottom: '3rem' }}>
        <h1
          style={{
            fontSize: '3rem',
            fontWeight: 700,
            letterSpacing: '-0.015em',
            margin: '0 0 0.5rem',
            lineHeight: 1.1,
          }}
        >
          Site Acquisition
        </h1>
        <p
          style={{
            fontSize: '1.25rem',
            color: '#6e6e73',
            margin: 0,
            lineHeight: 1.5,
            letterSpacing: '-0.005em',
          }}
        >
          Comprehensive property capture and development feasibility analysis
          for developers
        </p>
      </header>

      {/* Property Capture Form */}
      <PropertyCaptureForm
        jurisdictionCode={jurisdictionCode}
        setJurisdictionCode={setJurisdictionCode}
        address={address}
        setAddress={setAddress}
        latitude={latitude}
        setLatitude={setLatitude}
        longitude={longitude}
        setLongitude={setLongitude}
        selectedScenarios={selectedScenarios}
        isCapturing={isCapturing}
        error={error}
        geocodeError={geocodeError}
        capturedProperty={capturedProperty}
        onCapture={handleCapture}
        onForwardGeocode={handleForwardGeocode}
        onReverseGeocode={handleReverseGeocode}
        onToggleScenario={toggleScenario}
      />

      {capturedProperty && (
        <section
          style={{
            background: 'white',
            border: '1px solid #d2d2d7',
            borderRadius: '18px',
            padding: '2rem',
            marginBottom: '2rem',
          }}
        >
          <h2
            style={{
              fontSize: '1.5rem',
              fontWeight: 600,
              marginBottom: '1.5rem',
              letterSpacing: '-0.01em',
            }}
          >
            Property Overview
          </h2>
          <PropertyOverviewSection cards={propertyOverviewCards} />
          {previewJob && (
            <div
              style={{
                marginTop: '2rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <h3
                  style={{
                    margin: 0,
                    fontSize: '1.1rem',
                    fontWeight: 600,
                    letterSpacing: '-0.01em',
                    color: '#111827',
                  }}
                >
                  Development Preview
                </h3>
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    letterSpacing: '0.08em',
                    color: '#4b5563',
                    textTransform: 'uppercase',
                  }}
                >
                  {previewJob.status.toUpperCase()}
                </span>
              </div>
              <Preview3DViewer
                previewUrl={previewJob.previewUrl}
                metadataUrl={previewViewerMetadataUrl}
                status={previewJob.status}
                thumbnailUrl={previewJob.thumbnailUrl}
                layerVisibility={previewLayerVisibility}
                focusLayerId={previewFocusLayerId}
              />
              <p style={{ margin: 0, fontSize: '0.85rem', color: '#4b5563' }}>
                Geometry detail:{' '}
                <strong>
                  {describeDetailLevel(previewJob.geometryDetailLevel)}
                </strong>
              </p>
            </div>
          )}
          {previewJob && (
            <div
              style={{
                marginTop: '1rem',
                display: 'flex',
                flexWrap: 'wrap',
                alignItems: 'flex-end',
                gap: '1rem',
              }}
            >
              <label
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.4rem',
                  fontSize: '0.85rem',
                  color: '#374151',
                }}
              >
                <span style={{ fontWeight: 600, color: '#111827' }}>
                  Geometry detail
                </span>
                <select
                  value={previewDetailLevel}
                  onChange={(event) =>
                    setPreviewDetailLevel(
                      event.target.value as GeometryDetailLevel,
                    )
                  }
                  disabled={isRefreshingPreview}
                  style={{
                    minWidth: '240px',
                    padding: '0.45rem 0.65rem',
                    borderRadius: '8px',
                    border: '1px solid #d1d5db',
                    background: isRefreshingPreview ? '#f3f4f6' : '#fff',
                    color: '#111827',
                  }}
                >
                  {PREVIEW_DETAIL_OPTIONS.map((option) => (
                    <option key={option} value={option}>
                      {PREVIEW_DETAIL_LABELS[option]}
                    </option>
                  ))}
                </select>
                <span style={{ fontSize: '0.8rem', color: '#6b7280' }}>
                  {previewDetailLevel === 'simple'
                    ? 'Fast render for smoke testing.'
                    : 'Detailed render with setbacks, podiums, and floor lines.'}
                </span>
              </label>
              <button
                type="button"
                onClick={handleRefreshPreview}
                disabled={isRefreshingPreview}
                style={{
                  padding: '0.5rem 0.85rem',
                  borderRadius: '9999px',
                  border: '1px solid',
                  borderColor: isRefreshingPreview ? '#cbd5f5' : '#6366f1',
                  background: isRefreshingPreview ? '#eef2ff' : '#4f46e5',
                  color: '#fff',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  cursor: isRefreshingPreview ? 'wait' : 'pointer',
                  transition: 'background 0.2s ease',
                }}
              >
                {isRefreshingPreview
                  ? 'Refreshing preview…'
                  : 'Refresh preview render'}
              </button>
              <span style={{ fontSize: '0.85rem', color: '#4b5563' }}>
                Status updates automatically while processing.
              </span>
            </div>
          )}
          {previewJob && (
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
          )}
          <ColorLegendEditor
            entries={colorLegendEntries}
            hasPendingChanges={legendHasPendingChanges}
            onChange={handleLegendEntryChange}
            onReset={handleLegendReset}
          />
          <LayerBreakdownCards layers={layerBreakdown} />
        </section>
      )}

      {capturedProperty && scenarioFocusOptions.length > 0 && (
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
          onOpenQuickAnalysisHistory={() => setQuickAnalysisHistoryOpen(true)}
          onOpenInspectionHistory={() => setHistoryModalOpen(true)}
          formatScenarioLabel={formatScenarioLabel}
        />
      )}

      {/* Due Diligence Checklist */}
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

      <MultiScenarioComparisonSection
        capturedProperty={capturedProperty}
        quickAnalysisScenariosCount={quickAnalysisScenarios.length}
        scenarioComparisonData={scenarioComparisonData}
        feasibilitySignals={feasibilitySignals}
        comparisonScenariosCount={comparisonScenarios.length}
        activeScenario={activeScenario}
        scenarioLookup={scenarioLookup}
        propertyId={propertyId}
        isExportingReport={isExportingReport}
        reportExportMessage={reportExportMessage}
        setActiveScenario={setActiveScenario}
        handleReportExport={handleReportExport}
        formatRecordedTimestamp={formatRecordedTimestamp}
      />

      {/* Property Condition Assessment Section */}
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

      {/* Condition Assessment Editor Modal */}
      <ConditionAssessmentEditor
        isOpen={isEditingAssessment}
        mode={assessmentEditorMode}
        draft={assessmentDraft}
        isSaving={isSavingAssessment}
        activeScenario={activeScenario}
        scenarioFocusOptions={scenarioFocusOptions}
        scenarioLookup={scenarioLookup}
        formatScenarioLabel={formatScenarioLabel}
        onClose={closeAssessmentEditor}
        onReset={resetAssessmentDraft}
        onSubmit={handleAssessmentSubmit}
        onFieldChange={handleAssessmentFieldChange}
        onSystemChange={handleAssessmentSystemChange}
        setActiveScenario={setActiveScenario}
      />

      <QuickAnalysisHistoryModal
        isOpen={isQuickAnalysisHistoryOpen}
        onClose={() => setQuickAnalysisHistoryOpen(false)}
        quickAnalysisHistory={quickAnalysisHistory}
        scenarioLookup={scenarioLookup}
        formatScenarioLabel={formatScenarioLabel}
        summariseScenarioMetrics={summariseScenarioMetrics}
        formatScenarioMetricValue={formatScenarioMetricValue}
      />

      <InspectionHistoryModal
        isOpen={isHistoryModalOpen}
        onClose={() => setHistoryModalOpen(false)}
        historyViewMode={historyViewMode}
        setHistoryViewMode={setHistoryViewMode}
        assessmentHistoryError={assessmentHistoryError}
        isLoadingAssessmentHistory={isLoadingAssessmentHistory}
        assessmentHistory={assessmentHistory}
        activeScenario={activeScenario}
        latestAssessmentEntry={latestAssessmentEntry}
        previousAssessmentEntry={previousAssessmentEntry}
        comparisonSummary={comparisonSummary}
        systemComparisons={systemComparisons}
        recommendedActionDiff={recommendedActionDiff}
        scenarioComparisonVisible={scenarioComparisonVisible}
        scenarioComparisonRef={scenarioComparisonRef}
        scenarioComparisonTableRows={scenarioComparisonTableRows}
        scenarioAssessments={scenarioAssessments}
        formatScenarioLabel={formatScenarioLabel}
        formatRecordedTimestamp={formatRecordedTimestamp}
      />
    </div>
  )
}
