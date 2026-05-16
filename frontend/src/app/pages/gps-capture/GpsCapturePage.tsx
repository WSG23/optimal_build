import {
  useCallback,
  useEffect,
  useRef,
  useState,
  lazy,
  Suspense,
  type FormEvent,
} from 'react'
// Import MUI Icons
import ConstructionIcon from '@mui/icons-material/Construction'
import DomainIcon from '@mui/icons-material/Domain'
import AccountBalanceIcon from '@mui/icons-material/AccountBalance'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import MapsHomeWorkIcon from '@mui/icons-material/MapsHomeWork'
import RadarIcon from '@mui/icons-material/Radar'

import {
  DEFAULT_SCENARIO_ORDER,
  fetchPropertyMarketIntelligence,
  generateProfessionalPack,
  logPropertyByGpsWithFeatures,
  type DevelopmentScenario,
  type GpsCaptureSummaryWithFeatures,
  type DeveloperFeatureData,
  type MarketIntelligenceSummary,
  type ProfessionalPackSummary,
  type ProfessionalPackType,
} from '../../../api/agents'
import {
  useFeaturePreferences,
  type UserRole,
} from '../../../hooks/useFeaturePreferences'
import {
  forwardGeocodeAddress,
  reverseGeocodeCoords,
} from '../../../api/geocoding'
import {
  FeatureTogglePanel,
  AssetOptimizationSummary,
  FinancialSummaryCard,
  HeritageContextCard,
} from '../../components/gps-capture'
import '../../../styles/gps-capture.css'
import { formatScenarioLabel, DARK_MAP_STYLE } from './gpsCaptureUtils'
import { HudWidgets } from './HudWidgets'
import { MissionLog } from './MissionLog'

const GOOGLE_MAPS_API_KEY = import.meta.env?.VITE_GOOGLE_MAPS_API_KEY ?? ''

// Track if Google Maps script is loading/loaded
let googleMapsPromise: Promise<void> | null = null

function loadGoogleMapsScript(): Promise<void> {
  if (googleMapsPromise) {
    return googleMapsPromise
  }

  googleMapsPromise = (async () => {
    if (!window.google?.maps) {
      await new Promise<void>((resolve, reject) => {
        const script = document.createElement('script')
        script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}&loading=async`
        script.async = true
        script.defer = true
        script.onload = () => resolve()
        script.onerror = () => reject(new Error('Failed to load Google Maps'))
        document.head.appendChild(script)
      })
    }

    // With loading=async, we must importLibrary to get the actual classes
    await google.maps.importLibrary('maps')
    await google.maps.importLibrary('marker')
  })()

  return googleMapsPromise
}

// Lazy load the 3D preview viewer to avoid loading THREE.js unless needed
const Preview3DViewer = lazy(() =>
  import('../../components/site-acquisition/Preview3DViewer').then((m) => ({
    default: m.Preview3DViewer,
  })),
)

export function GpsCapturePage() {
  const role: UserRole = 'agent'
  const [latitude, setLatitude] = useState<string>('1.3000')
  const [longitude, setLongitude] = useState<string>('103.8500')
  const [address, setAddress] = useState<string>('')
  const [jurisdictionCode, setJurisdictionCode] = useState<string>('SG')
  const [selectedScenarios, setSelectedScenarios] = useState<
    DevelopmentScenario[]
  >([...DEFAULT_SCENARIO_ORDER])

  const [captureLoading, setCaptureLoading] = useState(false)
  const [captureError, setCaptureError] = useState<string | null>(null)
  const [captureSummary, setCaptureSummary] =
    useState<GpsCaptureSummaryWithFeatures | null>(null)
  const [developerFeatures, setDeveloperFeatures] =
    useState<DeveloperFeatureData | null>(null)

  // Immersive Experience States
  const [isScanning, setIsScanning] = useState(false)

  // Feature preferences hook for optional developer features
  const {
    preferences: featurePreferences,
    entitlements: featureEntitlements,
    toggleFeature,
    unlockFeature,
  } = useFeaturePreferences(role)

  const [marketSummary, setMarketSummary] =
    useState<MarketIntelligenceSummary | null>(null)
  const [marketLoading, setMarketLoading] = useState(false)
  const [_marketError, setMarketError] = useState<string | null>(null)

  const [_packs, setPacks] = useState<ProfessionalPackSummary[]>([])
  const [_packError, setPackError] = useState<string | null>(null)
  const [packLoadingType, setPackLoadingType] =
    useState<ProfessionalPackType | null>(null)

  const [capturedSites, setCapturedSites] = useState<
    Array<{
      propertyId: string
      address: string
      district?: string
      scenario: DevelopmentScenario | null
      capturedAt: string
    }>
  >([])

  const [geocodeError, setGeocodeError] = useState<string | null>(null)
  const [mapError, setMapError] = useState<string | null>(null)
  const [isMapLoaded, setIsMapLoaded] = useState(false)
  const mapContainerRef = useRef<HTMLDivElement | null>(null)
  const mapInstanceRef = useRef<google.maps.Map | null>(null)
  const mapMarkerRef = useRef<google.maps.marker.AdvancedMarkerElement | null>(
    null,
  )

  const handleScenarioToggle = useCallback((scenario: DevelopmentScenario) => {
    setSelectedScenarios((prev) => {
      if (prev.includes(scenario)) {
        return prev.filter((item) => item !== scenario)
      }
      return [...prev, scenario]
    })
  }, [])

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
      setCaptureSummary((prev) =>
        prev
          ? {
              ...prev,
              address: {
                ...prev.address,
                fullAddress: result.formattedAddress,
              },
              coordinates: {
                latitude: result.latitude,
                longitude: result.longitude,
              },
            }
          : prev,
      )
      if (mapInstanceRef.current && mapMarkerRef.current) {
        mapInstanceRef.current.setCenter({
          lat: result.latitude,
          lng: result.longitude,
        })
        mapMarkerRef.current.position = {
          lat: result.latitude,
          lng: result.longitude,
        }
      }
    } catch (error) {
      console.error('Forward geocode failed', error)
      setGeocodeError(
        error instanceof Error ? error.message : 'Unable to geocode address.',
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
      setCaptureSummary((prev) =>
        prev
          ? {
              ...prev,
              address: {
                ...prev.address,
                fullAddress: result.formattedAddress,
              },
            }
          : prev,
      )
    } catch (error) {
      console.error('Reverse geocode failed', error)
      setGeocodeError(
        error instanceof Error ? error.message : 'Unable to reverse geocode.',
      )
    }
  }, [latitude, longitude])

  // Load Google Maps script
  useEffect(() => {
    if (!GOOGLE_MAPS_API_KEY) {
      setMapError('Google Maps API key not set; map preview disabled.')
      return
    }

    loadGoogleMapsScript()
      .then(() => setIsMapLoaded(true))
      .catch((err) => setMapError(err.message))
  }, [])

  // Initialize Google Map
  useEffect(() => {
    if (!isMapLoaded || !mapContainerRef.current || mapInstanceRef.current) {
      return
    }

    const initialLat = Number(latitude) || 1.3
    const initialLng = Number(longitude) || 103.85

    const map = new google.maps.Map(mapContainerRef.current, {
      center: { lat: initialLat, lng: initialLng },
      zoom: 16,
      tilt: 45, // Add tilt for 3D feel
      styles: DARK_MAP_STYLE as google.maps.MapTypeStyle[],
      mapId: 'gps_capture_map',
      mapTypeControl: false,
      streetViewControl: false,
    })

    // Create custom marker pin element
    const pinElement = document.createElement('div')
    pinElement.style.width = 'var(--ob-space-150)'
    pinElement.style.height = 'var(--ob-space-150)'
    pinElement.style.borderRadius = '50%'
    pinElement.style.backgroundColor = 'var(--ob-color-status-info, #8b5cf6)'
    pinElement.style.border = '3px solid white'
    pinElement.style.boxShadow = '0 2px 6px rgba(0,0,0,0.3)'
    pinElement.style.cursor = 'grab'

    // Create draggable marker using AdvancedMarkerElement
    const marker = new google.maps.marker.AdvancedMarkerElement({
      position: { lat: initialLat, lng: initialLng },
      map,
      gmpDraggable: true,
      content: pinElement,
    })

    // Handle marker drag
    marker.addListener('dragend', () => {
      const position = marker.position
      if (position) {
        const lat =
          typeof position.lat === 'function' ? position.lat() : position.lat
        const lng =
          typeof position.lng === 'function' ? position.lng() : position.lng
        if (lat !== null && lng !== null) {
          setLatitude(lat.toFixed(6))
          setLongitude(lng.toFixed(6))
        }
      }
    })

    // Handle map click
    map.addListener('click', (event: google.maps.MapMouseEvent) => {
      if (event.latLng) {
        const lat = event.latLng.lat()
        const lng = event.latLng.lng()
        setLatitude(lat.toFixed(6))
        setLongitude(lng.toFixed(6))
        marker.position = { lat, lng }
      }
    })

    mapInstanceRef.current = map
    mapMarkerRef.current = marker

    return () => {
      // Cleanup
      if (mapMarkerRef.current) {
        mapMarkerRef.current.map = null
      }
    }
  }, [isMapLoaded]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleCapture = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault()
      const parsedLat = Number(latitude)
      const parsedLon = Number(longitude)
      if (!Number.isFinite(parsedLat) || !Number.isFinite(parsedLon)) {
        setCaptureError('Please provide valid coordinates.')
        return
      }

      try {
        setCaptureLoading(true)
        setIsScanning(true) // Start Animation
        setCaptureError(null)
        setMarketSummary(null)
        setMarketError(null)
        setDeveloperFeatures(null)

        // Artificial delay for "Scanning" effect (1.5s) if user desires the "Wow" timing
        await new Promise((resolve) => setTimeout(resolve, 1500))

        // Use hybrid API that routes to developer endpoint when features are enabled
        const summary = await logPropertyByGpsWithFeatures({
          latitude: parsedLat,
          longitude: parsedLon,
          developmentScenarios:
            selectedScenarios.length > 0 ? selectedScenarios : undefined,
          jurisdictionCode: jurisdictionCode || undefined,
          enabledFeatures: featurePreferences,
        })
        setCaptureSummary(summary)
        setDeveloperFeatures(summary.developerFeatures)
        setCapturedSites((prev) => [
          {
            propertyId: summary.propertyId,
            address: summary.address.fullAddress.startsWith('Mocked Address')
              ? address ||
                `Captured site (${parsedLat.toFixed(5)}, ${parsedLon.toFixed(5)})`
              : summary.address.fullAddress,
            district: summary.address.district,
            scenario: summary.quickAnalysis.scenarios[0]?.scenario ?? null,
            capturedAt: summary.timestamp,
          },
          ...prev,
        ])

        setMarketLoading(true)
        try {
          const intelligence = await fetchPropertyMarketIntelligence(
            summary.propertyId,
          )
          setMarketSummary(intelligence)
          setMarketError(intelligence.warning ?? null)
        } finally {
          setMarketLoading(false)
        }
      } catch (error) {
        console.error('GPS capture failed', error)
        setCaptureError(
          error instanceof Error
            ? error.message
            : 'Unable to capture property. Please try again.',
        )
      } finally {
        setCaptureLoading(false)
        setIsScanning(false) // Stop Animation
      }
    },
    [
      address,
      latitude,
      longitude,
      jurisdictionCode,
      selectedScenarios,
      featurePreferences,
    ],
  )

  const handleGeneratePack = useCallback(
    async (packType: ProfessionalPackType) => {
      if (!captureSummary) {
        setPackError('Capture a property before generating a marketing pack.')
        return
      }
      try {
        setPackLoadingType(packType)
        setPackError(null)
        const pack = await generateProfessionalPack(
          captureSummary.propertyId,
          packType,
        )
        setPackError(pack.warning ?? null)
        setPacks((prev) => [pack, ...prev])
      } catch (error) {
        console.error('Failed to generate pack', error)
        setPackError(
          error instanceof Error
            ? error.message
            : 'Unable to generate marketing pack.',
        )
      } finally {
        setPackLoadingType(null)
      }
    },
    [captureSummary],
  )

  const quickAnalysis = captureSummary?.quickAnalysis ?? null

  // Helper to get icon for scenario
  const getScenarioIcon = (scenario: DevelopmentScenario) => {
    switch (scenario) {
      case 'raw_land':
        return <ConstructionIcon />
      case 'existing_building':
        return <DomainIcon />
      case 'heritage_property':
        return <AccountBalanceIcon />
      case 'underused_asset':
        return <TrendingUpIcon />
      case 'mixed_use_redevelopment':
        return <MapsHomeWorkIcon />
      default:
        return <DomainIcon />
    }
  }

  return (
    <div className="gps-page">
      {/* Immersive Map Background */}
      <div
        className={`gps-background-map ${isScanning ? 'scanning' : ''}`}
        ref={mapContainerRef}
        aria-label="Interactive map background"
      />
      {mapError && <div className="gps-map-error">{mapError}</div>}

      {/* Content Overlay */}
      <div className="gps-content-overlay">
        <section className="gps-page__summary">
          {/* LEFT PANEL: Glass Capture Card */}
          <div className={`capture-card-glass ${isScanning ? 'dimmed' : ''}`}>
            <div>
              <h2>Capture a property</h2>
              <p>Launch a new acquisition mission.</p>
            </div>

            <form className="gps-form" onSubmit={handleCapture}>
              {/* Address Input (Floating Ghost) */}
              <div className="gps-form__group" style={{ gridColumn: '1 / -1' }}>
                <label htmlFor="address">Target Address / Location</label>
                <div className="gps-form__address-row">
                  <input
                    id="address"
                    name="address"
                    className="gps-input-ghost"
                    value={address}
                    onChange={(event) => setAddress(event.target.value)}
                    placeholder="Enter address or drop pin..."
                    autoComplete="off"
                  />
                  <div className="gps-form__address-actions">
                    <button
                      type="button"
                      className="gps-geocode-btn"
                      onClick={handleForwardGeocode}
                    >
                      Geocode
                    </button>
                    <button
                      type="button"
                      className="gps-geocode-btn"
                      onClick={handleReverseGeocode}
                    >
                      Reverse
                    </button>
                  </div>
                </div>
                {geocodeError && <p className="gps-error">{geocodeError}</p>}
              </div>

              {/* Coordinates (Ghost) */}
              <div className="gps-form__group">
                <label htmlFor="latitude">LAT</label>
                <input
                  id="latitude"
                  name="latitude"
                  className="gps-input-ghost"
                  value={latitude}
                  onChange={(event) => setLatitude(event.target.value)}
                  required
                />
              </div>
              <div className="gps-form__group">
                <label htmlFor="longitude">LONG</label>
                <input
                  id="longitude"
                  name="longitude"
                  className="gps-input-ghost"
                  value={longitude}
                  onChange={(event) => setLongitude(event.target.value)}
                  required
                />
              </div>

              <div className="gps-form__group">
                <label htmlFor="jurisdictionCode">JURISDICTION</label>
                <select
                  id="jurisdictionCode"
                  name="jurisdictionCode"
                  className="gps-input-ghost gps-select-ghost"
                  value={jurisdictionCode}
                  onChange={(event) => setJurisdictionCode(event.target.value)}
                  required
                >
                  <option value="SG">Singapore</option>
                </select>
              </div>

              {/* Gamified Scenarios Tiles */}
              <div className="gps-form__group gps-form__group--full-width">
                <label id="mission-scenario-label">MISSION SCENARIO</label>
                <div
                  className="gps-scenarios-grid"
                  role="group"
                  aria-labelledby="mission-scenario-label"
                >
                  {DEFAULT_SCENARIO_ORDER.map((scenario) => {
                    const isSelected = selectedScenarios.includes(scenario)
                    return (
                      <div
                        key={scenario}
                        className={`gps-scenario-tile ${isSelected ? 'gps-scenario-tile--selected' : ''}`}
                        onClick={() => handleScenarioToggle(scenario)}
                      >
                        {getScenarioIcon(scenario)}
                        <span>{formatScenarioLabel(scenario)}</span>
                      </div>
                    )
                  })}
                </div>
              </div>

              <FeatureTogglePanel
                preferences={featurePreferences}
                entitlements={featureEntitlements}
                onToggle={toggleFeature}
                onUnlock={unlockFeature}
                disabled={captureLoading}
              />

              {/* Scan & Analyze Button */}
              <button
                type="submit"
                className="gps-scan-button"
                disabled={captureLoading}
              >
                {captureLoading ? (
                  <>
                    <div className="gps-spinner"></div>
                    <span>Scanning Object...</span>
                  </>
                ) : (
                  <>
                    <RadarIcon />
                    Scan & Analyze
                  </>
                )}
              </button>
            </form>

            {captureError && <p className="gps-error">{captureError}</p>}
            {captureSummary && (
              <div className="gps-capture-meta">
                <p>
                  Target Locked:{' '}
                  <strong>{captureSummary.address.fullAddress}</strong>
                </p>
                <p>
                  Captured:{' '}
                  {new Date(captureSummary.timestamp).toLocaleTimeString()}
                </p>
              </div>
            )}
          </div>

          {/* RIGHT PANEL: HUD Widgets */}
          <HudWidgets
            quickAnalysis={quickAnalysis}
            captureSummary={captureSummary}
            marketSummary={marketSummary}
            marketLoading={marketLoading}
            packLoadingType={packLoadingType}
            onGeneratePack={handleGeneratePack}
          />
        </section>

        {/* Developer features section */}
        {developerFeatures && (
          <section className="gps-page__developer-features">
            {/* 3D Preview Viewer */}
            {featurePreferences.preview3D &&
              developerFeatures.visualization && (
                <div className="gps-panel gps-panel--preview">
                  <h3>3D Preview</h3>
                  <Suspense
                    fallback={
                      <div className="gps-panel__loading">
                        Loading 3D viewer...
                      </div>
                    }
                  >
                    <Preview3DViewer
                      previewUrl={
                        developerFeatures.visualization.conceptMeshUrl
                      }
                      metadataUrl={
                        developerFeatures.visualization.previewMetadataUrl
                      }
                      status={developerFeatures.visualization.status}
                      thumbnailUrl={
                        developerFeatures.visualization.thumbnailUrl
                      }
                    />
                  </Suspense>
                  {developerFeatures.visualization.notes.length > 0 && (
                    <ul className="gps-panel__notes">
                      {developerFeatures.visualization.notes.map(
                        (note, index) => (
                          <li key={index}>{note}</li>
                        ),
                      )}
                    </ul>
                  )}
                </div>
              )}

            {/* Asset Optimization Summary */}
            {featurePreferences.assetOptimization &&
              developerFeatures.optimizations.length > 0 && (
                <div className="gps-panel">
                  <AssetOptimizationSummary
                    optimizations={developerFeatures.optimizations}
                    currencySymbol={captureSummary?.currencySymbol}
                  />
                </div>
              )}

            {/* Financial Summary */}
            {featurePreferences.financialSummary &&
              developerFeatures.financialSummary && (
                <div className="gps-panel">
                  <FinancialSummaryCard
                    summary={developerFeatures.financialSummary}
                    currencySymbol={captureSummary?.currencySymbol}
                  />
                </div>
              )}

            {/* Heritage Context */}
            {featurePreferences.heritageContext &&
              developerFeatures.heritageContext && (
                <div className="gps-panel">
                  <HeritageContextCard
                    context={developerFeatures.heritageContext}
                  />
                </div>
              )}
          </section>
        )}

        {/* Recent Captures */}
        <MissionLog capturedSites={capturedSites} />
      </div>
    </div>
  )
}

// Utility functions imported from gpsCaptureUtils
