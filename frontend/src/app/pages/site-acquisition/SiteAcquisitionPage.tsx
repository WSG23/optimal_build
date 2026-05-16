import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
// createPortal is used by modal components
import {
  capturePropertyForDevelopment,
  type DevelopmentScenario,
  type SiteAcquisitionResult,
} from '../../../api/siteAcquisition'
import { forwardGeocodeAddress } from '../../../api/geocoding'
import { useFeaturePreferences } from '../../../hooks/useFeaturePreferences'

// Extracted types, constants, utils, and hooks
import type { QuickAnalysisEntry } from './types'
import { SCENARIO_OPTIONS } from './constants'
import { buildPropertyOverviewCards, buildFeasibilitySignals } from './utils'
import { usePreviewJob } from './hooks/usePreviewJob'
import { useCaptureScenarioComparison } from './hooks/useCaptureScenarioComparison'
import {
  PropertyOverviewSection,
  type LayerAction,
} from './components/property-overview'
import { ScenarioFocusSection } from './components/scenario-focus'
import { MultiScenarioComparisonSection } from './components/multi-scenario-comparison'
import { VoiceObservationsPanel } from './components/VoiceObservationsPanel'
import { OptimalIntelligenceCard } from './components/OptimalIntelligenceCard'
import { CommandBar } from './components/CommandBar'
import { ConceptPreviewSection } from './components/ConceptPreviewSection'
import {
  PropertyLocationMap,
  type HeritageFeature,
  type NearbyAmenity,
} from './components/map'

// MUI & Canonical Components
import { Box, Stack, Typography } from '@mui/material'
import { Button } from '../../../components/canonical/Button'
import { useRouterController } from '../../../router'

// Storage keys for property persistence
const CAPTURED_PROPERTY_STORAGE_KEY = 'site-acquisition:captured-property'

/**
 * Legacy developer capture page retained as an internal fallback while the
 * unified capture workspace is the active route.
 *
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
  const [activeScenario, setActiveScenario] = useState<
    DevelopmentScenario | 'all'
  >('all')
  const [isCapturing, setIsCapturing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [capturedProperty, setCapturedProperty] =
    useState<SiteAcquisitionResult | null>(null)
  const [isGeocoding, setIsGeocoding] = useState(false)
  const hasRestoredCapturedPropertyRef = useRef(false)

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
      console.warn('Forward geocoding failed:', err)
      setError(
        err instanceof Error
          ? err.message
          : 'Geocoding failed. You can enter coordinates manually.',
      )
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
    if (hasRestoredCapturedPropertyRef.current) return
    hasRestoredCapturedPropertyRef.current = true

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
  }, [setPreviewJob])

  const scenarioLookup = useMemo(
    () => new Map(SCENARIO_OPTIONS.map((option) => [option.value, option])),
    [],
  )

  const currencySymbol = capturedProperty?.currencySymbol || 'S$'

  const {
    quickAnalysisScenarios,
    comparisonScenarios,
    scenarioComparisonData,
    scenarioComparisonVisible,
    activeScenarioSummary,
    quickAnalysisHistory,
    formatScenarioLabel,
    formatNumberMetric,
  } = useCaptureScenarioComparison({
    capturedProperty,
    activeScenario,
    currencySymbol,
  })

  const [isQuickAnalysisHistoryOpen, setQuickAnalysisHistoryOpen] =
    useState(false)
  const dueDiligencePath = '/app/due-diligence'
  useEffect(() => {
    if (quickAnalysisHistory.length === 0 && isQuickAnalysisHistoryOpen) {
      setQuickAnalysisHistoryOpen(false)
    }
  }, [quickAnalysisHistory.length, isQuickAnalysisHistoryOpen])

  const scenarioFilterOptions = useMemo(() => {
    const collected = new Set<DevelopmentScenario>()
    selectedScenarios.forEach((scenario) => collected.add(scenario))
    quickAnalysisScenarios.forEach((scenario) =>
      collected.add(scenario.scenario as DevelopmentScenario),
    )
    return Array.from(collected)
  }, [quickAnalysisScenarios, selectedScenarios])

  const scenarioFocusOptions = useMemo(
    () =>
      ['all', ...scenarioFilterOptions] as Array<'all' | DevelopmentScenario>,
    [scenarioFilterOptions],
  )

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

  useEffect(() => {
    if (activeScenario === 'all') {
      return
    }
    if (scenarioFilterOptions.includes(activeScenario)) {
      return
    }
    setActiveScenario(scenarioFilterOptions[0] ?? 'all')
  }, [activeScenario, scenarioFilterOptions])

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
  const propertyOverviewCards = useMemo(() => {
    if (!capturedProperty) {
      return []
    }
    return buildPropertyOverviewCards({
      capturedProperty,
      previewJob,
      colorLegendEntries,
      formatters: {
        formatNumber: formatNumberMetric,
        formatCurrency: () => '—',
        formatTimestamp,
      },
    })
  }, [
    capturedProperty,
    previewJob,
    colorLegendEntries,
    formatNumberMetric,
    formatTimestamp,
  ])

  const captureInsight = useMemo(() => {
    if (!capturedProperty) {
      return null
    }
    const envelope = capturedProperty.buildEnvelope
    const analysisPoints = [
      envelope.allowablePlotRatio != null
        ? `plot ratio ${formatNumberMetric(envelope.allowablePlotRatio, {
            maximumFractionDigits: 2,
          })}`
        : null,
      envelope.maxBuildableGfaSqm != null
        ? `max buildable GFA ${formatNumberMetric(envelope.maxBuildableGfaSqm, {
            maximumFractionDigits: 0,
          })} sqm`
        : null,
      envelope.buildingHeightLimitM != null
        ? `height limit ${formatNumberMetric(envelope.buildingHeightLimitM, {
            maximumFractionDigits: 0,
          })} m`
        : null,
      envelope.siteCoveragePct != null
        ? `site coverage ${formatNumberMetric(envelope.siteCoveragePct, {
            maximumFractionDigits: 0,
          })}%`
        : null,
    ].filter(Boolean)
    const previewStatus =
      capturedProperty.visualization?.status
        ?.replace(/_/g, ' ')
        .toLowerCase() ?? 'pending'
    const isFallbackCapture =
      capturedProperty.visualization?.status?.toLowerCase() === 'placeholder' ||
      envelope.buildingHeightLimitM == null ||
      envelope.siteCoveragePct == null
    const summary =
      analysisPoints.length > 0
        ? analysisPoints.slice(0, 3).join(', ')
        : 'zoning and envelope controls are still resolving'
    const scopeNote = isFallbackCapture
      ? 'This is a preliminary capture: scalar controls only, with no setback or floor-by-floor compliance modelling.'
      : 'Capture reflects the currently resolved scalar controls for this site, without setback or floor-by-floor compliance modelling.'
    return `Instant capture analysis highlights ${summary}. Preview status: ${previewStatus}. ${scopeNote}`
  }, [capturedProperty, formatNumberMetric])

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

  const formatRecordedTimestamp = useCallback((timestamp?: string | null) => {
    if (!timestamp) {
      return '—'
    }
    const parsed = new Date(timestamp)
    if (Number.isNaN(parsed.getTime())) {
      return timestamp
    }
    return parsed.toLocaleString()
  }, [])

  function toggleScenario(scenario: DevelopmentScenario) {
    setSelectedScenarios((prev) =>
      prev.includes(scenario)
        ? prev.filter((s) => s !== scenario)
        : [...prev, scenario],
    )
  }

  // Persist optimization outputs so downstream feasibility views can hydrate.
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
          console.warn(
            'Unable to persist feasibility handoff snapshot',
            storageError,
          )
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

            {/* Voice notes */}
            <VoiceObservationsPanel
              propertyId={capturedProperty?.propertyId ?? null}
              latitude={latitude ? parseFloat(latitude) : undefined}
              longitude={longitude ? parseFloat(longitude) : undefined}
              disabled={isCapturing}
            />

            {/* AI Intelligence Card */}
            <OptimalIntelligenceCard
              insight={captureInsight}
              hasProperty={!!capturedProperty}
            />

            {/* Quick Actions - New Capture only (appears after capture) */}
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
                  <ConceptPreviewSection
                    previewJob={previewJob}
                    previewViewerMetadataUrl={previewViewerMetadataUrl}
                    previewDetailLevel={previewDetailLevel}
                    setPreviewDetailLevel={setPreviewDetailLevel}
                    isRefreshingPreview={isRefreshingPreview}
                    handleRefreshPreview={handleRefreshPreview}
                    previewLayerVisibility={previewLayerVisibility}
                    previewFocusLayerId={previewFocusLayerId}
                    previewLayerMetadata={previewLayerMetadata}
                    hiddenLayerCount={hiddenLayerCount}
                    isPreviewMetadataLoading={isPreviewMetadataLoading}
                    previewMetadataError={previewMetadataError}
                    onLayerAction={handleLayerAction}
                    onShowAllLayers={handleShowAllLayers}
                    onResetLayerFocus={handleResetLayerFocus}
                    formatNumberMetric={formatNumberMetric}
                    colorLegendEntries={colorLegendEntries}
                    onLegendChange={handleLegendEntryChange}
                    legendHasPendingChanges={legendHasPendingChanges}
                    onLegendReset={handleLegendReset}
                  />
                )}
              </Box>
            </Box>

            {/* Scenario Focus - Depth 1 */}
            {scenarioFocusOptions.length > 0 && (
              <ScenarioFocusSection
                scenarioFocusOptions={scenarioFocusOptions}
                scenarioLookup={scenarioLookup}
                activeScenario={activeScenario}
                activeScenarioSummary={activeScenarioSummary}
                quickAnalysisHistoryCount={quickAnalysisHistory.length}
                scenarioComparisonVisible={scenarioComparisonVisible}
                setActiveScenario={setActiveScenario}
                onCompareScenarios={handleScenarioComparisonScroll}
                onOpenQuickAnalysisHistory={() =>
                  setQuickAnalysisHistoryOpen(true)
                }
                onOpenDueDiligence={() => router.navigate(dueDiligencePath)}
                formatScenarioLabel={formatScenarioLabel}
              />
            )}

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
              setActiveScenario={setActiveScenario}
              formatRecordedTimestamp={formatRecordedTimestamp}
            />

            <Box
              sx={{
                display: 'flex',
                justifyContent: 'center',
                py: 'var(--ob-space-100)',
              }}
            >
              <Button
                variant="secondary"
                size="lg"
                onClick={() => router.navigate(dueDiligencePath)}
              >
                View Due Diligence →
              </Button>
            </Box>
          </>
        )}
      </Stack>
    </Box>
  )
}
