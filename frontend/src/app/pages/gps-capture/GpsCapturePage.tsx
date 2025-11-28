import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  lazy,
  Suspense,
  type FormEvent,
} from 'react'
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
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'

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
  const [marketError, setMarketError] = useState<string | null>(null)

  const [packs, setPacks] = useState<ProfessionalPackSummary[]>([])
  const [packError, setPackError] = useState<string | null>(null)
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
  const mapContainerRef = useRef<HTMLDivElement | null>(null)
  const mapInstanceRef = useRef<mapboxgl.Map | null>(null)
  const mapMarkerRef = useRef<mapboxgl.Marker | null>(null)

  const today = useMemo(
    () => new Date().toLocaleString(undefined, { dateStyle: 'medium' }),
    [],
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
        mapInstanceRef.current.setCenter([result.longitude, result.latitude])
        mapMarkerRef.current.setLngLat([result.longitude, result.latitude])
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

  useEffect(() => {
    const token = import.meta.env.VITE_MAPBOX_TOKEN
    if (!token) {
      setMapError('Mapbox token not set; map preview disabled.')
      return
    }
    if (mapInstanceRef.current || !mapContainerRef.current) {
      return
    }
    mapboxgl.accessToken = token
    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: 'mapbox://styles/mapbox/streets-v12',
      center: [Number(longitude) || 103.85, Number(latitude) || 1.3],
      zoom: 12,
    })
    const marker = new mapboxgl.Marker({ draggable: true })
      .setLngLat([Number(longitude) || 103.85, Number(latitude) || 1.3])
      .addTo(map)
    marker.on('dragend', () => {
      const lngLat = marker.getLngLat()
      setLatitude(lngLat.lat.toFixed(6))
      setLongitude(lngLat.lng.toFixed(6))
    })
    map.on('click', (event) => {
      const { lng, lat } = event.lngLat
      setLatitude(lat.toFixed(6))
      setLongitude(lng.toFixed(6))
      marker.setLngLat([lng, lat])
    })
    mapInstanceRef.current = map
    mapMarkerRef.current = marker
    return () => {
      map.remove()
    }
  }, [latitude, longitude])

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
        setCaptureError(null)
        setMarketSummary(null)
        setMarketError(null)
        setDeveloperFeatures(null)

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

  return (
    <div className="gps-page">
      <section className="gps-page__summary">
        <div className="gps-card">
          <h2>Capture a property</h2>
          <p>
            Enter GPS coordinates or drop a pin on the map to capture a site.
            Add photos and field notes before sending to developers.
          </p>
          <form className="gps-form" onSubmit={handleCapture}>
            <div className="gps-form__group">
              <label htmlFor="address">Address (optional)</label>
              <div className="gps-form__address-row">
                <input
                  id="address"
                  name="address"
                  value={address}
                  onChange={(event) => setAddress(event.target.value)}
                  placeholder="123 Main Street, Singapore"
                />
                <div className="gps-form__address-actions">
                  <button type="button" onClick={handleForwardGeocode}>
                    Geocode address
                  </button>
                  <button type="button" onClick={handleReverseGeocode}>
                    Reverse geocode
                  </button>
                </div>
              </div>
              {geocodeError && <p className="gps-error">{geocodeError}</p>}
            </div>
            <div className="gps-form__group">
              <label htmlFor="latitude">Latitude</label>
              <input
                id="latitude"
                name="latitude"
                value={latitude}
                onChange={(event) => setLatitude(event.target.value)}
                required
              />
            </div>
            <div className="gps-form__group">
              <label htmlFor="longitude">Longitude</label>
              <input
                id="longitude"
                name="longitude"
                value={longitude}
                onChange={(event) => setLongitude(event.target.value)}
                required
              />
            </div>
            <div className="gps-form__group">
              <label htmlFor="jurisdictionCode">Jurisdiction</label>
              <select
                id="jurisdictionCode"
                name="jurisdictionCode"
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
            <div className="gps-form__group">
              <label>Development scenarios</label>
              <div className="gps-form__scenarios">
                {DEFAULT_SCENARIO_ORDER.map((scenario) => (
                  <label key={scenario}>
                    <input
                      type="checkbox"
                      checked={selectedScenarios.includes(scenario)}
                      onChange={() => handleScenarioToggle(scenario)}
                    />
                    <span>{formatScenarioLabel(scenario)}</span>
                  </label>
                ))}
              </div>
            </div>
            <FeatureTogglePanel
              preferences={featurePreferences}
              entitlements={featureEntitlements}
              onToggle={toggleFeature}
              onUnlock={unlockFeature}
              disabled={captureLoading}
            />
            <button
              type="submit"
              className="gps-form__submit"
              disabled={captureLoading}
            >
              {captureLoading ? 'Capturing…' : 'Capture site'}
            </button>
          </form>
          {captureError && <p className="gps-error">{captureError}</p>}
          {captureSummary && (
            <div className="gps-capture-meta">
              <p>
                Last captured:{' '}
                <strong>
                  {new Date(captureSummary.timestamp).toLocaleString()}
                </strong>
              </p>
              <p>
                Address: <strong>{captureSummary.address.fullAddress}</strong>
              </p>
              {captureSummary.address.district && (
                <p>
                  District: <strong>{captureSummary.address.district}</strong>
                </p>
              )}
              {captureSummary.uraZoning?.zoneCode && (
                <p>
                  Zoning: <strong>{captureSummary.uraZoning.zoneCode}</strong>
                </p>
              )}
            </div>
          )}
        </div>
        <div className="gps-card gps-card--map">
          <h2>Site preview</h2>
          {mapError ? (
            <p className="gps-error">{mapError}</p>
          ) : (
            <div
              className="gps-map"
              ref={mapContainerRef}
              aria-label="Map preview"
              style={{
                height: '320px',
                borderRadius: '12px',
                overflow: 'hidden',
              }}
            />
          )}
          <p className="gps-map__hint">
            Click on the map or drag the marker to update coordinates. Geocoding
            uses Google Maps; set <code>VITE_GOOGLE_MAPS_API_KEY</code> and
            <code>VITE_MAPBOX_TOKEN</code> in your environment.
          </p>
        </div>
      </section>

      <section className="gps-page__panels">
        <div className="gps-panel">
          <h3>Quick analysis scenarios</h3>
          <p className="gps-panel__timestamp">
            {quickAnalysis
              ? `Generated ${new Date(
                  quickAnalysis.generatedAt,
                ).toLocaleString()}`
              : 'Capture a property to view quick analysis.'}
          </p>
          {quickAnalysis ? (
            <ul className="gps-panel__list">
              {quickAnalysis.scenarios.map((scenario) => (
                <li key={scenario.scenario}>
                  <div className="gps-panel__headline">
                    <strong>{formatScenarioLabel(scenario.scenario)}</strong>
                    <span>{scenario.headline}</span>
                  </div>
                  {Object.keys(scenario.metrics).length > 0 && (
                    <dl className="gps-panel__metrics">
                      {Object.entries(scenario.metrics).map(
                        ([metricKey, metricValue]) => (
                          <div key={metricKey}>
                            <dt>{humanizeMetricKey(metricKey)}</dt>
                            <dd>
                              {formatMetricValue(
                                metricValue,
                                metricKey,
                                captureSummary?.currencySymbol,
                              )}
                            </dd>
                          </div>
                        ),
                      )}
                    </dl>
                  )}
                  {scenario.notes.length > 0 && (
                    <ul className="gps-panel__notes">
                      {scenario.notes.map((note, index) => (
                        <li key={index}>{note}</li>
                      ))}
                    </ul>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p>
              See plot ratio, GFA potential, heritage considerations, and
              repositioning opportunities once capture is complete.
            </p>
          )}
        </div>
        <div className="gps-panel">
          <h3>Market intelligence</h3>
          {marketLoading && <p>Loading market intelligence…</p>}
          {marketError && <p className="gps-error">{marketError}</p>}
          {marketSummary ? (
            <>
              <dl className="gps-panel__metrics">
                <div>
                  <dt>Property type</dt>
                  <dd>
                    {extractReportValue(marketSummary.report, 'property_type')}
                  </dd>
                </div>
                <div>
                  <dt>Location</dt>
                  <dd>
                    {extractReportValue(marketSummary.report, 'location')}
                  </dd>
                </div>
                <div>
                  <dt>Period analysed</dt>
                  <dd>{extractPeriod(marketSummary.report)}</dd>
                </div>
                <div>
                  <dt>Transactions</dt>
                  <dd>{extractTransactions(marketSummary.report)}</dd>
                </div>
              </dl>
              <p>
                Additional insights: comparables, supply dynamics, absorption,
                and yield benchmarks will be rendered from the full report.
              </p>
            </>
          ) : (
            <p>
              This panel will display comparables, supply dynamics, yield
              benchmarks, and absorption trends returned by the market
              intelligence service after capture.
            </p>
          )}
          <p>
            Generated:{' '}
            <strong>
              {marketSummary
                ? today
                : captureSummary
                  ? 'fetching…'
                  : 'pending capture'}
            </strong>
          </p>
        </div>
        <div className="gps-panel">
          <h3>Marketing packs</h3>
          <p>
            Generate professional packs for developers and investors. The UI
            will integrate with the pack generator once APIs are finalised.
          </p>
          <div className="gps-pack-options">
            {PACK_TYPES.map((packType) => (
              <button
                key={packType}
                type="button"
                disabled={packLoadingType === packType}
                onClick={() => handleGeneratePack(packType)}
              >
                {packLoadingType === packType
                  ? 'Generating…'
                  : formatPackLabel(packType)}
              </button>
            ))}
          </div>
          <div className="gps-pack-history">
            {packError && <p className="gps-error">{packError}</p>}
            {packs.length === 0 ? (
              <p>No packs generated yet.</p>
            ) : (
              <ul>
                {packs.map((pack) => (
                  <li
                    key={`${pack.propertyId}-${pack.packType}-${pack.generatedAt}`}
                  >
                    <strong>{formatPackLabel(pack.packType)}</strong> •{' '}
                    {new Date(pack.generatedAt).toLocaleString()} —{' '}
                    {pack.downloadUrl ? (
                      <a href={pack.downloadUrl}>Download</a>
                    ) : pack.isFallback ? (
                      <span
                        title={pack.warning ?? 'Preview pack generated offline'}
                      >
                        Preview only
                      </span>
                    ) : (
                      'Download link unavailable'
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </section>

      {/* Developer features section - shown when any feature is enabled and data exists */}
      {developerFeatures && (
        <section className="gps-page__developer-features">
          {/* 3D Preview Viewer */}
          {featurePreferences.preview3D && developerFeatures.visualization && (
            <div className="gps-panel gps-panel--preview">
              <h3>3D Preview</h3>
              <Suspense
                fallback={
                  <div className="gps-panel__loading">Loading 3D viewer...</div>
                }
              >
                <Preview3DViewer
                  previewUrl={developerFeatures.visualization.conceptMeshUrl}
                  metadataUrl={
                    developerFeatures.visualization.previewMetadataUrl
                  }
                  status={developerFeatures.visualization.status}
                  thumbnailUrl={developerFeatures.visualization.thumbnailUrl}
                />
              </Suspense>
              {developerFeatures.visualization.notes.length > 0 && (
                <ul className="gps-panel__notes">
                  {developerFeatures.visualization.notes.map((note, index) => (
                    <li key={index}>{note}</li>
                  ))}
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

      <section className="gps-page__captures">
        <div className="gps-panel">
          <h3>Recent captures</h3>
          {capturedSites.length === 0 ? (
            <p>Capture sites to build a running history.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Property</th>
                  <th>District</th>
                  <th>Primary scenario</th>
                  <th>Captured</th>
                  <th>Pack status</th>
                </tr>
              </thead>
              <tbody>
                {capturedSites.map((site) => (
                  <tr key={`${site.propertyId}-${site.capturedAt}`}>
                    <td>{site.address}</td>
                    <td>{site.district ?? '—'}</td>
                    <td>
                      {site.scenario ? formatScenarioLabel(site.scenario) : '—'}
                    </td>
                    <td>{new Date(site.capturedAt).toLocaleString()}</td>
                    <td>
                      {packs.find((pack) => pack.propertyId === site.propertyId)
                        ? 'Pack generated'
                        : 'Pending'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>
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

function extractPeriod(report: Record<string, unknown>) {
  const period = report.period
  if (
    period &&
    typeof period === 'object' &&
    ('start' in period || 'end' in period)
  ) {
    const { start, end } = period as { start?: string; end?: string }
    const formattedStart = start ? new Date(start).toLocaleDateString() : null
    const formattedEnd = end ? new Date(end).toLocaleDateString() : null
    if (formattedStart && formattedEnd) {
      return `${formattedStart} – ${formattedEnd}`
    }
    return formattedStart ?? formattedEnd ?? '—'
  }
  return '—'
}
