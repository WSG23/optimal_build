import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
// createPortal is used by modal components
import {
  capturePropertyForDevelopment,
  createFinanceProjectFromCapture,
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
  SCENARIO_OPTIONS,
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
  PreviewLayersTable,
  AssetMixChart,
  type LayerAction,
} from './components/property-overview'
import { ScenarioFocusSection } from './components/scenario-focus'
import { MultiScenarioComparisonSection } from './components/multi-scenario-comparison'
// Removed redundant components (consolidated into PreviewLayersTable):
// - LayerBreakdownCards (data shown in table)
// - ColorLegendEditor (integrated as inline accordion in table)
// - MassingLayersPanel (visibility controls integrated in table)
import { VoiceObservationsPanel } from './components/VoiceObservationsPanel'
import { OptimalIntelligenceCard } from './components/OptimalIntelligenceCard'
// Modals not yet used but planned for future integration
// import { QuickAnalysisHistoryModal, InspectionHistoryModal } from './components/modals'
// PropertyCaptureForm replaced by CommandBar + inline components for map-dominant layout
import { CommandBar } from './components/CommandBar'
import {
  PropertyLocationMap,
  type HeritageFeature,
  type NearbyAmenity,
} from './components/map'

// MUI & Canonical Components
import {
  Box,
  Stack,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material'
import { Refresh } from '@mui/icons-material'
import { Button } from '../../../components/canonical/Button'
import { useRouterController } from '../../../router'

// Storage keys for property persistence
const CAPTURED_PROPERTY_STORAGE_KEY = 'site-acquisition:captured-property'

/**
 * Get captured property from sessionStorage
 */
function getStoredCapturedProperty(): SiteAcquisitionResult | null {
  try {
    const stored = sessionStorage.getItem(CAPTURED_PROPERTY_STORAGE_KEY)
    if (!stored) return null
    return JSON.parse(stored) as SiteAcquisitionResult
  } catch {
    return null
  }
}

/**
 * Store captured property in sessionStorage for navigation persistence
 */
function storeCapturedProperty(property: SiteAcquisitionResult): void {
  try {
    sessionStorage.setItem(
      CAPTURED_PROPERTY_STORAGE_KEY,
      JSON.stringify(property),
    )
  } catch (err) {
    console.warn('Unable to persist captured property:', err)
  }
}

/**
 * Clear captured property from sessionStorage
 * Called when user wants to start a new capture
 */
function clearStoredCapturedProperty(): void {
  try {
    sessionStorage.removeItem(CAPTURED_PROPERTY_STORAGE_KEY)
  } catch {
    // Silently ignore storage errors
  }
}

export function SiteAcquisitionPage() {
  const router = useRouterController()
  const [jurisdictionCode] = useState('SG')
  const [latitude, setLatitude] = useState('1.3000')
  const [longitude, setLongitude] = useState('103.8500')
  const [address, setAddress] = useState('')
  const [selectedScenarios, setSelectedScenarios] = useState<
    DevelopmentScenario[]
  >([])
  const [isCapturing, setIsCapturing] = useState(false)
  const [isCreatingFinanceProject, setIsCreatingFinanceProject] =
    useState(false)
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
    // layerBreakdown removed - no longer needed after consolidation
    handleRefreshPreview,
    handleToggleLayerVisibility,
    handleSoloPreviewLayer,
    handleShowAllLayers,
    handleFocusLayer,
    handleResetLayerFocus,
    handleLegendEntryChange,
    handleLegendReset,
  } = usePreviewJob({ capturedProperty })

  // Restore captured property from sessionStorage on mount
  // This enables navigation persistence - data survives page changes
  useEffect(() => {
    // Only restore if we don't already have a captured property
    if (capturedProperty) return

    const storedProperty = getStoredCapturedProperty()
    if (storedProperty) {
      setCapturedProperty(storedProperty)
      // Also restore coordinates and address from stored property
      if (storedProperty.address?.fullAddress) {
        setAddress(storedProperty.address.fullAddress)
      }
      // Restore preview job if available
      if (storedProperty.previewJobs?.[0]) {
        setPreviewJob(storedProperty.previewJobs[0])
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // Only run on mount

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
  // NOTE: Removed overflow manipulation - it was causing scroll lock issues.
  // The modals themselves should handle their own overflow via their own useEffect.
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

    window.addEventListener('keydown', handleKeyDown)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
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

  // Transform nearby amenities for the map component (copied from PropertyCaptureForm)
  const mapAmenities = useMemo(() => {
    if (!capturedProperty?.nearbyAmenities) return undefined

    const amenities = capturedProperty.nearbyAmenities
    const hasCoordinates = (item: { latitude?: number; longitude?: number }) =>
      typeof item.latitude === 'number' && typeof item.longitude === 'number'

    return {
      mrtStations: amenities.mrtStations
        ?.filter(hasCoordinates)
        .map((station) => ({
          name: station.name,
          type: 'mrt' as const,
          latitude: station.latitude!,
          longitude: station.longitude!,
          distance_m: station.distanceM ?? undefined,
        })) as NearbyAmenity[] | undefined,
      busStops: amenities.busStops?.filter(hasCoordinates).map((stop) => ({
        name: stop.name,
        type: 'bus' as const,
        latitude: stop.latitude!,
        longitude: stop.longitude!,
        distance_m: stop.distanceM ?? undefined,
      })) as NearbyAmenity[] | undefined,
      schools: amenities.schools?.filter(hasCoordinates).map((school) => ({
        name: school.name,
        type: 'school' as const,
        latitude: school.latitude!,
        longitude: school.longitude!,
        distance_m: school.distanceM ?? undefined,
      })) as NearbyAmenity[] | undefined,
      malls: amenities.shoppingMalls?.filter(hasCoordinates).map((mall) => ({
        name: mall.name,
        type: 'mall' as const,
        latitude: mall.latitude!,
        longitude: mall.longitude!,
        distance_m: mall.distanceM ?? undefined,
      })) as NearbyAmenity[] | undefined,
      parks: amenities.parks?.filter(hasCoordinates).map((park) => ({
        name: park.name,
        type: 'park' as const,
        latitude: park.latitude!,
        longitude: park.longitude!,
        distance_m: park.distanceM ?? undefined,
      })) as NearbyAmenity[] | undefined,
    }
  }, [capturedProperty?.nearbyAmenities])

  // Check if any amenities have coordinates
  const hasAmenityCoordinates = useMemo(() => {
    if (!mapAmenities) return false
    return Object.values(mapAmenities).some((arr) => arr && arr.length > 0)
  }, [mapAmenities])

  // Transform heritage context for the map
  const heritageFeatures = useMemo((): HeritageFeature[] | undefined => {
    if (!capturedProperty?.heritageContext?.flag) return undefined
    const heritage = capturedProperty.heritageContext
    if (heritage.overlay?.name) {
      return [
        {
          name: heritage.overlay.name,
          status: heritage.risk ?? undefined,
          risk_level:
            heritage.risk === 'high'
              ? 'high'
              : heritage.risk === 'low'
                ? 'low'
                : 'medium',
          latitude: parseFloat(latitude) || 1.3,
          longitude: parseFloat(longitude) || 103.85,
        },
      ]
    }
    return undefined
  }, [capturedProperty?.heritageContext, latitude, longitude])

  // Asset mix data for the donut chart in Development Preview sidebar
  // Extract from propertyOverviewCards (the "Recommended asset mix" card)
  const assetMixData = useMemo(() => {
    // Find the asset mix card from overview cards
    const assetMixCard = propertyOverviewCards.find((card) =>
      card.title.toLowerCase().includes('asset mix'),
    )
    if (!assetMixCard) return []

    // Parse asset mix data from card items
    return assetMixCard.items.map((item) => {
      // Parse percentage from value string (e.g., "54% • 7,560 sqm • ...")
      const percentMatch = item.value.match(/^(\d+(?:\.\d+)?)\s*%/)
      const percentage = percentMatch ? parseFloat(percentMatch[1]) : 0

      // Parse GFA if present
      const gfaMatch = item.value.match(
        /(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:k\s*)?sqm/i,
      )
      const gfa = gfaMatch
        ? parseFloat(gfaMatch[1].replace(/,/g, '')) *
          (gfaMatch[0].includes('k') ? 1000 : 1)
        : undefined

      return {
        label: item.label,
        value: percentage,
        allocatedGfa: gfa,
      }
    })
  }, [propertyOverviewCards])

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

      // Store full captured property for navigation persistence
      storeCapturedProperty(result)

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

  /**
   * Clear captured property and reset form for a new capture
   * Clears sessionStorage and resets all capture-related state
   */
  const handleNewCapture = useCallback(() => {
    clearStoredCapturedProperty()
    setCapturedProperty(null)
    setPreviewJob(null)
    setError(null)
    // Reset coordinates to defaults
    setLatitude('1.3000')
    setLongitude('103.8500')
    setAddress('')
    setSelectedScenarios([])
  }, [setPreviewJob])

  const handleCreateFinanceProject = useCallback(async () => {
    if (!capturedProperty?.propertyId) {
      setError('Capture a property before creating a finance project.')
      return
    }
    if (isCreatingFinanceProject) {
      return
    }

    setIsCreatingFinanceProject(true)
    setError(null)

    try {
      const projectLabel =
        capturedProperty.propertyInfo?.propertyName?.trim() ||
        capturedProperty.address?.fullAddress?.trim() ||
        'GPS Capture'

      const created = await createFinanceProjectFromCapture(
        capturedProperty.propertyId,
        {
          projectName: projectLabel,
          scenarioName: 'Base Case',
          totalEstimatedCapexSgd:
            capturedProperty.financialSummary?.totalEstimatedCapexSgd ?? null,
          totalEstimatedRevenueSgd:
            capturedProperty.financialSummary?.totalEstimatedRevenueSgd ?? null,
        },
      )

      const query = new URLSearchParams()
      query.set('projectId', created.projectId)
      if (created.projectName) {
        query.set('projectName', created.projectName)
      }
      if (Number.isFinite(created.finProjectId) && created.finProjectId > 0) {
        query.set('finProjectId', String(created.finProjectId))
      }
      router.navigate(`/finance?${query.toString()}`)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to create finance project from capture.',
      )
    } finally {
      setIsCreatingFinanceProject(false)
    }
  }, [capturedProperty, isCreatingFinanceProject, router])

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
      {/* ========== MAP-DOMINANT CAPTURE SECTION ========== */}
      <div className="site-acquisition__map-dominant">
        {/* Floating Command Bar */}
        <CommandBar
          address={address}
          setAddress={setAddress}
          latitude={latitude}
          setLatitude={setLatitude}
          longitude={longitude}
          setLongitude={setLongitude}
          selectedScenarios={selectedScenarios}
          isCapturing={isCapturing}
          isGeocoding={isGeocoding}
          onCapture={handleCapture}
          onAddressBlur={handleAddressBlur}
        />

        {/* Main Content: Map + Sidebar */}
        <div className="site-acquisition__map-content">
          {/* Map Viewport - Hero Element */}
          <div className="site-acquisition__map-viewport">
            <PropertyLocationMap
              latitude={latitude}
              longitude={longitude}
              onCoordinatesChange={(lat, lon) => {
                setLatitude(lat)
                setLongitude(lon)
              }}
              address={capturedProperty?.address?.fullAddress}
              district={capturedProperty?.address?.district}
              zoningCode={capturedProperty?.uraZoning?.zoneCode ?? undefined}
              nearbyAmenities={mapAmenities}
              heritageFeatures={heritageFeatures}
              interactive={!isCapturing}
              height="calc(var(--ob-size-controls-min) + var(--ob-space-300) + var(--ob-space-250) + var(--ob-space-075))"
              showAmenities={hasAmenityCoordinates}
              showHeritage={!!capturedProperty?.heritageContext?.flag}
              propertyId={capturedProperty?.propertyId}
              status={
                isCapturing ? 'capturing' : capturedProperty ? 'live' : 'idle'
              }
              showHud={true}
            />

            {/* Error Message Overlay */}
            {error && (
              <div className="site-acquisition__error-overlay">{error}</div>
            )}

            {/* Success Message Overlay */}
            {capturedProperty && (
              <div className="site-acquisition__success-overlay">
                <strong>Property captured</strong>
                <span>
                  {capturedProperty.address.fullAddress} •{' '}
                  {capturedProperty.address.district}
                </span>
              </div>
            )}
          </div>

          {/* Condensed Sidebar - Heuristic Instrument Panel */}
          <div className="site-acquisition__sidebar--condensed">
            {/* Scenario Selection - Compact Grid (placed near Capture button per UX feedback) */}
            <div className="site-acquisition__scenario-selector">
              <div className="site-acquisition__scenario-header">
                <span className="site-acquisition__scenario-label">
                  DEVELOPMENT SCENARIOS
                </span>
                <span className="site-acquisition__scenario-count">
                  {selectedScenarios.length} selected
                </span>
              </div>
              <div className="site-acquisition__scenario-grid">
                {SCENARIO_OPTIONS.map((scenario) => {
                  const isSelected = selectedScenarios.includes(scenario.value)
                  return (
                    <button
                      key={scenario.value}
                      type="button"
                      onClick={() => toggleScenario(scenario.value)}
                      className={`site-acquisition__scenario-chip ${isSelected ? 'site-acquisition__scenario-chip--selected' : ''}`}
                    >
                      <span className="site-acquisition__scenario-chip-icon">
                        {scenario.icon}
                      </span>
                      <span className="site-acquisition__scenario-chip-label">
                        {scenario.label}
                      </span>
                      {isSelected && (
                        <span className="site-acquisition__scenario-chip-check">
                          ✓
                        </span>
                      )}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Voice Capture Module */}
            <VoiceObservationsPanel
              propertyId={capturedProperty?.propertyId ?? null}
              latitude={latitude ? parseFloat(latitude) : undefined}
              longitude={longitude ? parseFloat(longitude) : undefined}
              disabled={isCapturing}
            />

            {/* AI Intelligence Card */}
            <OptimalIntelligenceCard
              insight={
                capturedProperty?.quickAnalysis?.scenarios?.[0]?.headline ??
                null
              }
              hasProperty={!!capturedProperty}
            />

            {/* Quick Actions - New Capture / Finance (appears after capture) */}
            {capturedProperty && (
              <div className="site-acquisition__quick-actions">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleNewCapture}
                  className="site-acquisition__action-btn"
                >
                  New Capture
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleCreateFinanceProject}
                  disabled={isCreatingFinanceProject}
                  className="site-acquisition__action-btn"
                >
                  {isCreatingFinanceProject ? 'Creating...' : 'Finance →'}
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ========== POST-CAPTURE CONTENT ========== */}
      {/* Section-to-section gap: 48px per Spacing Hierarchy */}
      <Stack spacing="var(--ob-space-300)" sx={{ mt: 'var(--ob-space-200)' }}>
        {capturedProperty && (
          <>
            {/* Property Overview - Content vs Context pattern */}
            <Box>
              {/* Header on background */}
              <Box sx={{ mb: 'var(--ob-space-200)' }}>
                <Typography variant="h5" fontWeight={600} gutterBottom>
                  Property Overview
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Captured property data and development metrics
                </Typography>
              </Box>

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
                    {/* Header */}
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

                    {/* Split view: 3D Viewer + Asset Mix (tokenized gap, responsive) */}
                    <Box
                      sx={{
                        display: 'grid',
                        gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' },
                        gap: 'var(--ob-space-150)',
                        alignItems: 'stretch',
                      }}
                    >
                      <Box
                        sx={{
                          minHeight: 'var(--ob-size-controls-min)',
                          bgcolor: 'var(--ob-color-bg-root)',
                          borderRadius: 'var(--ob-radius-sm)',
                          overflow: 'hidden',
                        }}
                      >
                        <Preview3DViewer
                          previewUrl={previewJob.previewUrl}
                          metadataUrl={previewViewerMetadataUrl}
                          status={previewJob.status}
                          thumbnailUrl={previewJob.thumbnailUrl}
                          layerVisibility={previewLayerVisibility}
                          focusLayerId={previewFocusLayerId}
                        />
                      </Box>

                      <AssetMixChart
                        data={assetMixData}
                        title="Asset Allocation"
                        sx={{
                          minHeight: 'var(--ob-size-controls-min)',
                        }}
                      />
                    </Box>

                    {/* Controls bar - full width below */}
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
                        <FormControl
                          size="small"
                          sx={{ minWidth: 'var(--ob-size-input-sm)' }}
                        >
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
                          variant="secondary"
                          size="sm"
                          onClick={handleRefreshPreview}
                          disabled={isRefreshingPreview}
                        >
                          <Refresh
                            className={isRefreshingPreview ? 'fa-spin' : ''}
                            sx={{
                              fontSize: 'var(--ob-font-size-base)',
                              mr: 'var(--ob-space-050)',
                            }}
                          />
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

                {/* Master Table - Single Source of Truth for all layer data and controls */}
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
                    // Integrated legend editor props (replaces standalone ColorLegendEditor)
                    legendEntries={colorLegendEntries}
                    onLegendChange={handleLegendEntryChange}
                    legendHasPendingChanges={legendHasPendingChanges}
                    onLegendReset={handleLegendReset}
                  />
                )}
                {/* Removed redundant components:
                    - ColorLegendEditor (now inline in table accordion)
                    - MassingLayersPanel (visibility controls now in table)
                    - LayerBreakdownCards (data shown in table columns)
                */}
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
            {/* NOTE: Scenario filtering now handled by ScenarioFocusSection above */}
            <DueDiligenceChecklistSection
              capturedProperty={capturedProperty}
              checklistItems={checklistItems}
              filteredChecklistItems={filteredChecklistItems}
              displaySummary={displaySummary}
              activeScenario={activeScenario}
              activeScenarioDetails={activeScenarioDetails}
              selectedCategory={selectedCategory}
              isLoadingChecklist={isLoadingChecklist}
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
