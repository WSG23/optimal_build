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
import LockIcon from '@mui/icons-material/Lock'
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf'
import DescriptionIcon from '@mui/icons-material/Description'
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

const GOOGLE_MAPS_API_KEY = import.meta.env?.VITE_GOOGLE_MAPS_API_KEY ?? ''

// Track if Google Maps script is loading/loaded
let googleMapsPromise: Promise<void> | null = null

function loadGoogleMapsScript(): Promise<void> {
  if (window.google?.maps) {
    return Promise.resolve()
  }

  if (googleMapsPromise) {
    return googleMapsPromise
  }

  googleMapsPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}`
    script.async = true
    script.defer = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Failed to load Google Maps'))
    document.head.appendChild(script)
  })

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
  const mapMarkerRef = useRef<google.maps.Marker | null>(null)

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
        mapMarkerRef.current.setPosition({
          lat: result.latitude,
          lng: result.longitude,
        })
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

    // Dark mode map style
    const darkMapStyle: google.maps.MapTypeStyle[] = [
      { elementType: 'geometry', stylers: [{ color: '#242f3e' }] },
      { elementType: 'labels.text.stroke', stylers: [{ color: '#242f3e' }] },
      { elementType: 'labels.text.fill', stylers: [{ color: '#746855' }] },
      {
        featureType: 'administrative.locality',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#d59563' }],
      },
      {
        featureType: 'poi',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#d59563' }],
      },
      {
        featureType: 'poi.park',
        elementType: 'geometry',
        stylers: [{ color: '#263c3f' }],
      },
      {
        featureType: 'road',
        elementType: 'geometry',
        stylers: [{ color: '#38414e' }],
      },
      {
        featureType: 'road',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#9ca5b3' }],
      },
      {
        featureType: 'road.highway',
        elementType: 'geometry',
        stylers: [{ color: '#746855' }],
      },
      {
        featureType: 'water',
        elementType: 'geometry',
        stylers: [{ color: '#17263c' }],
      },
      {
        featureType: 'water',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#515c6d' }],
      },
    ]

    const initialLat = Number(latitude) || 1.3
    const initialLng = Number(longitude) || 103.85

    const map = new google.maps.Map(mapContainerRef.current, {
      center: { lat: initialLat, lng: initialLng },
      zoom: 16,
      tilt: 45, // Add tilt for 3D feel
      styles: darkMapStyle,
      mapTypeControl: false,
      streetViewControl: false,
    })

    // Create draggable marker using standard Marker class
    const marker = new google.maps.Marker({
      position: { lat: initialLat, lng: initialLng },
      map,
      draggable: true,
      icon: {
        path: google.maps.SymbolPath.CIRCLE,
        scale: 12,
        fillColor: '#3b82f6',
        fillOpacity: 1,
        strokeColor: 'white',
        strokeWeight: 3,
      },
    })

    // Handle marker drag
    marker.addListener('dragend', () => {
      const position = marker.getPosition()
      if (position) {
        setLatitude(position.lat().toFixed(6))
        setLongitude(position.lng().toFixed(6))
      }
    })

    // Handle map click
    map.addListener('click', (event: google.maps.MapMouseEvent) => {
      if (event.latLng) {
        const lat = event.latLng.lat()
        const lng = event.latLng.lng()
        setLatitude(lat.toFixed(6))
        setLongitude(lng.toFixed(6))
        marker.setPosition({ lat, lng })
      }
    })

    mapInstanceRef.current = map
    mapMarkerRef.current = marker

    return () => {
      // Cleanup
      if (mapMarkerRef.current) {
        mapMarkerRef.current.setMap(null)
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
        console.log('[GPS Capture] Received summary:', {
          jurisdictionCode: summary.jurisdictionCode,
          currencySymbol: summary.currencySymbol,
          hasDeveloperFeatures: summary.developerFeatures !== null,
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
                  <option value="HK">Hong Kong</option>
                  <option value="NZ">New Zealand</option>
                  <option value="SEA">Seattle / King County</option>
                  <option value="TOR">Toronto</option>
                </select>
              </div>

              {/* Gamified Scenarios Tiles */}
              <div className="gps-form__group gps-form__group--full-width">
                <label>MISSION SCENARIO</label>
                <div className="gps-scenarios-grid">
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
          <div className="gps-hud-group">
            {/* Widget 1: Quick Analysis */}
            <div className={`gps-hud-card ${!quickAnalysis ? 'locked' : ''}`}>
              <h3>
                Quick Analysis
                {!quickAnalysis && <LockIcon fontSize="small" />}
              </h3>

              {quickAnalysis ? (
                <div className="gps-hud-content">
                  <ul className="gps-panel__list">
                    {quickAnalysis.scenarios.slice(0, 1).map((scenario) => {
                      // Show only first scenario for compactness in HUD
                      const displayMetrics = Object.entries(scenario.metrics)
                        .filter(([key]) => key !== 'accuracy_bands')
                        .slice(0, 3)
                      return (
                        <li key={scenario.scenario}>
                          <div className="gps-panel__headline">
                            <strong>
                              {formatScenarioLabel(scenario.scenario)}
                            </strong>
                          </div>
                          {displayMetrics.length > 0 && (
                            <dl className="gps-panel__metrics">
                              {displayMetrics.map(([k, v]) => (
                                <div key={k}>
                                  <dt>{humanizeMetricKey(k)}</dt>
                                  <dd>
                                    {formatMetricValue(
                                      v,
                                      k,
                                      captureSummary?.currencySymbol,
                                    )}
                                  </dd>
                                </div>
                              ))}
                            </dl>
                          )}
                        </li>
                      )
                    })}
                    {quickAnalysis.scenarios.length > 1 && (
                      <p className="gps-hud-more-scenarios">
                        + {quickAnalysis.scenarios.length - 1} more scenarios
                      </p>
                    )}
                  </ul>
                </div>
              ) : (
                <div className="gps-hud-locked-overlay">
                  <span>Awaiting Scan</span>
                </div>
              )}
            </div>

            {/* Widget 2: Market Intelligence */}
            <div className={`gps-hud-card ${!marketSummary ? 'locked' : ''}`}>
              <h3>
                Market Intelligence
                {!marketSummary && <LockIcon fontSize="small" />}
              </h3>
              {marketLoading ? (
                <div className="gps-hud-loading">
                  <div className="gps-spinner gps-spinner--sm"></div>
                  Decrypting market data...
                </div>
              ) : marketSummary ? (
                <div className="gps-hud-content">
                  <dl className="gps-panel__metrics">
                    <div>
                      <dt>Type</dt>
                      <dd>
                        {extractReportValue(
                          marketSummary.report,
                          'property_type',
                        )}
                      </dd>
                    </div>
                    <div>
                      <dt>Zone</dt>
                      <dd>
                        {extractReportValue(marketSummary.report, 'location')}
                      </dd>
                    </div>
                    <div>
                      <dt>Trans</dt>
                      <dd>
                        {extractTransactions(marketSummary.report)} recent
                      </dd>
                    </div>
                  </dl>
                </div>
              ) : (
                <div className="gps-hud-locked-overlay">
                  <span>Downlink Offline</span>
                </div>
              )}
            </div>

            {/* Widget 3: Marketing Packs */}
            <div className={`gps-hud-card ${!captureSummary ? 'locked' : ''}`}>
              <h3>
                Marketing Packs
                {!captureSummary && <LockIcon fontSize="small" />}
              </h3>
              <div className="gps-pack-grid gps-hud-content">
                {PACK_TYPES.map((packType) => (
                  <button
                    key={packType}
                    type="button"
                    className="gps-pack-btn"
                    disabled={packLoadingType === packType || !captureSummary}
                    onClick={() => handleGeneratePack(packType)}
                  >
                    {packLoadingType === packType ? (
                      <div className="gps-spinner gps-spinner--xs"></div>
                    ) : packType === 'investment' || packType === 'sales' ? (
                      <PictureAsPdfIcon />
                    ) : (
                      <DescriptionIcon />
                    )}
                    <span>{formatPackLabel(packType).split(' ')[0]}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
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
        <section className="gps-page__captures">
          <div className="gps-panel">
            <h3>Mission Log</h3>
            {capturedSites.length === 0 ? (
              <p style={{ fontStyle: 'italic', color: '#94a3b8' }}>
                No prior missions.
              </p>
            ) : (
              <table style={{ color: '#ccc' }}>
                <thead>
                  <tr>
                    <th>Target</th>
                    <th>District</th>
                    <th>Scenario</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {capturedSites.map((site) => (
                    <tr key={`${site.propertyId}-${site.capturedAt}`}>
                      <td>{site.address}</td>
                      <td>{site.district ?? '-'}</td>
                      <td>
                        {site.scenario
                          ? formatScenarioLabel(site.scenario)
                          : '-'}
                      </td>
                      <td>{new Date(site.capturedAt).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}

const PACK_TYPES: ProfessionalPackType[] = [
  'universal',
  'investment',
  'sales',
  'lease',
]

function formatScenarioLabel(value: DevelopmentScenario) {
  switch (value) {
    case 'raw_land':
      return 'Raw land'
    case 'existing_building':
      return 'Existing building'
    case 'heritage_property':
      return 'Heritage property'
    case 'underused_asset':
      return 'Underused asset'
    case 'mixed_use_redevelopment':
      return 'Mixed-use redevelopment'
    default:
      return value
  }
}

function formatPackLabel(value: ProfessionalPackType) {
  switch (value) {
    case 'universal':
      return 'Universal pack'
    case 'investment':
      return 'Investment memo'
    case 'sales':
      return 'Sales brief'
    case 'lease':
      return 'Lease brochure'
    default:
      return value
  }
}

function humanizeMetricKey(key: string) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

function formatMetricValue(
  value: unknown,
  metricKey?: string,
  currencySymbol?: string,
) {
  if (value === null || value === undefined) {
    return '—'
  }
  if (typeof value === 'number') {
    const formattedNumber = Number.isInteger(value)
      ? value.toLocaleString()
      : value.toLocaleString(undefined, {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })

    // Add currency symbol if metric key suggests it's a price/financial value
    // Exclude count/number fields that happen to contain financial keywords
    const isCountField =
      metricKey &&
      (metricKey.includes('count') ||
        metricKey.includes('number') ||
        metricKey.includes('quantity') ||
        metricKey.includes('units'))

    const hasFinancialKeyword =
      metricKey &&
      !isCountField &&
      (metricKey.includes('price') ||
        metricKey.includes('noi') ||
        metricKey.includes('valuation') ||
        metricKey.includes('capex') ||
        metricKey.includes('rent') ||
        metricKey.includes('cost') ||
        metricKey.includes('value') ||
        metricKey.includes('revenue') ||
        metricKey.includes('income'))

    console.log('[formatMetricValue]', {
      metricKey,
      currencySymbol,
      isCountField,
      hasFinancialKeyword,
      willAddSymbol: !!(currencySymbol && hasFinancialKeyword),
    })

    if (currencySymbol && hasFinancialKeyword) {
      return `${currencySymbol}${formattedNumber}`
    }
    return formattedNumber
  }
  return String(value)
}

function extractReportValue(report: Record<string, unknown>, key: string) {
  const value = report[key]
  return typeof value === 'string' && value.trim() !== '' ? value : '—'
}

function extractTransactions(report: Record<string, unknown>) {
  const comparables = report.comparables_analysis
  if (
    comparables &&
    typeof comparables === 'object' &&
    'transaction_count' in comparables
  ) {
    const value = (comparables as Record<string, unknown>).transaction_count
    if (typeof value === 'number') {
      return value.toLocaleString()
    }
  }
  return '—'
}
