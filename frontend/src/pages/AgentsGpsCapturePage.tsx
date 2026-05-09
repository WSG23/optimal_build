import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'

import { colors } from '@ob/tokens'

import { AppLayout } from '../App'
import {
  DEFAULT_SCENARIO_ORDER,
  type DevelopmentScenario,
  type GpsCaptureSummary,
  type MarketIntelligenceSummary,
  type MetricValue,
  type CoordinatePair,
  type QuickAnalysisScenarioSummary,
  type ProfessionalPackSummary,
  type ProfessionalPackType,
  logPropertyByGps,
  fetchPropertyMarketIntelligence,
  generateProfessionalPack,
} from '../api/agents'
import { forwardGeocodeAddress, reverseGeocodeCoords } from '../api/geocoding'
import { useTranslation } from '../i18n'
import { Link } from '../router'
import '../styles/agents-capture.css'
import {
  SCENARIO_OPTIONS,
  DEFAULT_LATITUDE,
  DEFAULT_LONGITUDE,
  formatMetricLabel,
  formatMetricValue,
  scenarioTitle,
  scenarioDescription,
} from './agentsCaptureUtils'
import { AgentsCaptureContextPanel } from './AgentsCaptureContextPanel'

const GOOGLE_MAPS_ENV =
  typeof import.meta !== 'undefined' && import.meta
    ? (import.meta as ImportMeta).env
    : undefined
const GOOGLE_MAPS_API_KEY = GOOGLE_MAPS_ENV?.VITE_GOOGLE_MAPS_API_KEY ?? ''

let googleMapsPromise: Promise<void> | null = null

function loadGoogleMapsScript(apiKey: string): Promise<void> {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('Window is not available.'))
  }
  if (googleMapsPromise) {
    return googleMapsPromise
  }

  googleMapsPromise = (async () => {
    if (!window.google?.maps) {
      await new Promise<void>((resolve, reject) => {
        const script = document.createElement('script')
        script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&loading=async`
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

// Constants and utilities imported from agentsCaptureUtils

function QuickAnalysisMap({ coordinates }: { coordinates: CoordinatePair }) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<google.maps.Map | null>(null)
  const markerRef = useRef<google.maps.marker.AdvancedMarkerElement | null>(
    null,
  )
  const [mapError, setMapError] = useState<string | null>(null)
  const { t } = useTranslation()

  const canRender = GOOGLE_MAPS_API_KEY !== '' && typeof window !== 'undefined'

  useEffect(() => {
    if (!canRender || !containerRef.current) {
      return
    }

    let cancelled = false

    void loadGoogleMapsScript(GOOGLE_MAPS_API_KEY)
      .then(() => {
        if (
          cancelled ||
          !containerRef.current ||
          typeof google === 'undefined'
        ) {
          return
        }
        const center = {
          lat: coordinates.latitude,
          lng: coordinates.longitude,
        }

        if (!mapRef.current) {
          mapRef.current = new google.maps.Map(containerRef.current, {
            center,
            zoom: 15,
            mapId: 'agents_gps_map',
            mapTypeControl: false,
            streetViewControl: false,
            fullscreenControl: false,
          })
        } else {
          mapRef.current.setCenter(center)
        }

        if (!markerRef.current) {
          const pinSvg = document.createElement('div')
          pinSvg.innerHTML = `<svg width="20" height="20" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
            <circle cx="10" cy="10" r="8" fill="${colors.brand[600]}" stroke="white" stroke-width="2"/>
          </svg>`
          markerRef.current = new google.maps.marker.AdvancedMarkerElement({
            position: center,
            map: mapRef.current,
            content: pinSvg,
          })
        } else {
          markerRef.current.position = center
          markerRef.current.map = mapRef.current
        }
      })
      .catch((error) => {
        if (!cancelled) {
          setMapError(
            error instanceof Error
              ? error.message
              : 'Unable to load map preview.',
          )
        }
      })

    return () => {
      cancelled = true
      if (markerRef.current) {
        markerRef.current.map = null
        markerRef.current = null
      }
      mapRef.current = null
    }
  }, [coordinates.latitude, coordinates.longitude, canRender])

  if (!canRender || mapError) {
    return (
      <div className="agents-capture__map-fallback">
        {mapError ?? t('agentsCapture.context.mapFallback')}
      </div>
    )
  }

  return <div ref={containerRef} className="agents-capture__map-canvas" />
}

// Formatting functions imported from agentsCaptureUtils

function ScenarioCard({
  scenario,
  locale,
}: {
  scenario: QuickAnalysisScenarioSummary
  locale: string
}) {
  const { t } = useTranslation()

  const entries = useMemo(
    () =>
      Object.entries(scenario.metrics).filter(
        ([key]) => key !== 'accuracy_bands',
      ) as [string, MetricValue | undefined][],
    [scenario.metrics],
  )

  return (
    <article className="agents-capture__scenario-card">
      <header>
        <h3>{scenarioTitle(scenario.scenario, t)}</h3>
        <p>{scenarioDescription(scenario.scenario, t)}</p>
      </header>
      <p className="agents-capture__scenario-headline">{scenario.headline}</p>
      {entries.length > 0 && (
        <dl className="agents-capture__metrics">
          {entries.map(([key, value]) => (
            <div key={key} className="agents-capture__metric-row">
              <dt>{formatMetricLabel(key, t)}</dt>
              <dd>{formatMetricValue(value, locale)}</dd>
            </div>
          ))}
        </dl>
      )}
      {scenario.notes.length > 0 && (
        <ul className="agents-capture__notes">
          {scenario.notes.map((note, index) => (
            <li key={`${scenario.scenario}-note-${index}`}>{note}</li>
          ))}
        </ul>
      )}
    </article>
  )
}

interface AgentsGpsCapturePageProps {
  logPropertyFn?: typeof logPropertyByGps
  fetchMarketIntelligenceFn?: typeof fetchPropertyMarketIntelligence
  generatePackFn?: typeof generateProfessionalPack
}

export function AgentsGpsCapturePage({
  logPropertyFn = logPropertyByGps,
  fetchMarketIntelligenceFn = fetchPropertyMarketIntelligence,
  generatePackFn = generateProfessionalPack,
}: AgentsGpsCapturePageProps = {}) {
  const { t, i18n } = useTranslation()
  const locale = i18n.language ?? 'en'
  const [latitude, setLatitude] = useState<string>(DEFAULT_LATITUDE)
  const [longitude, setLongitude] = useState<string>(DEFAULT_LONGITUDE)
  const [address, setAddress] = useState<string>('')
  const [selectedScenarios, setSelectedScenarios] = useState<
    Set<DevelopmentScenario>
  >(() => new Set(DEFAULT_SCENARIO_ORDER))
  const [result, setResult] = useState<GpsCaptureSummary | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [geocodeError, setGeocodeError] = useState<string | null>(null)
  const [marketReport, setMarketReport] =
    useState<MarketIntelligenceSummary | null>(null)
  const [marketLoading, setMarketLoading] = useState(false)
  const [marketError, setMarketError] = useState<string | null>(null)
  const [packType, setPackType] = useState<ProfessionalPackType>('universal')
  const [packSummary, setPackSummary] =
    useState<ProfessionalPackSummary | null>(null)
  const [packLoading, setPackLoading] = useState(false)
  const [packError, setPackError] = useState<string | null>(null)
  const [packNotice, setPackNotice] = useState<string | null>(null)

  const toggleScenario = (scenario: DevelopmentScenario) => {
    setSelectedScenarios((current) => {
      const next = new Set(current)
      if (next.has(scenario)) {
        next.delete(scenario)
      } else {
        next.add(scenario)
      }
      return next
    })
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    setGeocodeError(null)

    const lat = Number.parseFloat(latitude)
    const lon = Number.parseFloat(longitude)

    if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
      setError(t('agentsCapture.errors.coordinatesInvalid'))
      return
    }

    const scenarios = Array.from(selectedScenarios)

    setLoading(true)
    try {
      const payload = await logPropertyFn({
        latitude: lat,
        longitude: lon,
        developmentScenarios: scenarios.length > 0 ? scenarios : undefined,
      })
      setResult(payload)
    } catch (err) {
      const message =
        err instanceof Error ? err.message : t('agentsCapture.errors.generic')
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const scenarioOrder = useMemo(
    () => result?.quickAnalysis.scenarios ?? [],
    [result],
  )
  const scenarioKeys = useMemo(
    () => new Set(scenarioOrder.map((item) => item.scenario)),
    [scenarioOrder],
  )
  const disclaimers = useMemo(() => {
    const messages: string[] = []
    if (scenarioKeys.has('raw_land') || scenarioKeys.has('underused_asset')) {
      messages.push(t('agentsCapture.disclaimers.preDevelopment'))
    }
    if (
      scenarioKeys.has('existing_building') ||
      scenarioKeys.has('heritage_property')
    ) {
      messages.push(t('agentsCapture.disclaimers.salesLeasing'))
    }
    if (messages.length === 0) {
      messages.push(t('agentsCapture.disclaimers.default'))
    }
    return messages
  }, [scenarioKeys, t])

  useEffect(() => {
    setPackSummary(null)
    setPackError(null)
    setPackNotice(null)
    setPackLoading(false)
    setPackType('universal')
  }, [result?.propertyId])

  useEffect(() => {
    if (!result) {
      setMarketReport(null)
      return undefined
    }

    const controller = new AbortController()
    let cancelled = false

    setMarketLoading(true)
    setMarketError(null)

    fetchMarketIntelligenceFn(result.propertyId, 12, controller.signal)
      .then((report) => {
        if (!cancelled) {
          setMarketReport(report)
          setMarketError(report.warning ?? null)
        }
      })
      .catch((err) => {
        if (cancelled || err?.name === 'AbortError') {
          return
        }
        const fallbackMessage =
          err instanceof Error ? err.message : t('agentsCapture.errors.market')
        setMarketError(fallbackMessage)
      })
      .finally(() => {
        if (!cancelled) {
          setMarketLoading(false)
        }
      })

    return () => {
      cancelled = true
      controller.abort()
    }
  }, [fetchMarketIntelligenceFn, result, t])

  const handlePackSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!result) {
      setPackError(t('agentsCapture.pack.missingProperty'))
      return
    }

    setPackLoading(true)
    setPackError(null)
    setPackNotice(null)

    try {
      const summary = await generatePackFn(result.propertyId, packType)
      setPackSummary(summary)
      setPackNotice(summary.warning ?? null)
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : t('agentsCapture.pack.errorFallback')
      setPackError(message)
      setPackNotice(null)
      setPackSummary(null)
    } finally {
      setPackLoading(false)
    }
  }

  return (
    <AppLayout
      title={t('agentsCapture.title')}
      subtitle={t('agentsCapture.subtitle')}
    >
      <section className="agents-capture">
        <form className="agents-capture__form" onSubmit={handleSubmit}>
          <div className="agents-capture__grid">
            <label className="agents-capture__field">
              <span>Address (optional)</span>
              <div className="agents-capture__address-row">
                <input
                  type="text"
                  value={address}
                  onChange={(event) => setAddress(event.target.value)}
                  placeholder="123 Main Street, Singapore"
                />
                <div className="agents-capture__address-actions">
                  <button
                    type="button"
                    onClick={async () => {
                      if (!address.trim()) {
                        setGeocodeError('Enter an address to geocode.')
                        return
                      }
                      try {
                        const result = await forwardGeocodeAddress(
                          address.trim(),
                        )
                        setLatitude(result.latitude.toString())
                        setLongitude(result.longitude.toString())
                        setGeocodeError(null)
                      } catch (err) {
                        const message =
                          err instanceof Error
                            ? err.message
                            : 'Geocoding failed.'
                        setGeocodeError(message)
                      }
                    }}
                    disabled={loading}
                  >
                    Geocode address
                  </button>
                  <button
                    type="button"
                    onClick={async () => {
                      const lat = Number.parseFloat(latitude)
                      const lon = Number.parseFloat(longitude)
                      if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
                        setGeocodeError(
                          'Enter valid coordinates to reverse geocode.',
                        )
                        return
                      }
                      try {
                        const result = await reverseGeocodeCoords(lat, lon)
                        setAddress(result.formattedAddress)
                        setGeocodeError(null)
                      } catch (err) {
                        const message =
                          err instanceof Error
                            ? err.message
                            : 'Reverse geocoding failed.'
                        setGeocodeError(message)
                      }
                    }}
                    disabled={loading}
                  >
                    Reverse geocode
                  </button>
                </div>
              </div>
            </label>
          </div>
          {geocodeError && (
            <p className="agents-capture__error">{geocodeError}</p>
          )}
          <div className="agents-capture__grid">
            <label className="agents-capture__field">
              <span>{t('agentsCapture.form.latitude')}</span>
              <input
                type="number"
                step="0.0001"
                value={latitude}
                onChange={(event) => setLatitude(event.target.value)}
                required
              />
            </label>
            <label className="agents-capture__field">
              <span>{t('agentsCapture.form.longitude')}</span>
              <input
                type="number"
                step="0.0001"
                value={longitude}
                onChange={(event) => setLongitude(event.target.value)}
                required
              />
            </label>
          </div>

          <fieldset className="agents-capture__scenarios">
            <legend>{t('agentsCapture.form.scenarioLegend')}</legend>
            <div className="agents-capture__scenario-options">
              {SCENARIO_OPTIONS.map((option) => {
                const checked = selectedScenarios.has(option.value)
                return (
                  <label
                    key={option.value}
                    className="agents-capture__scenario-option"
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleScenario(option.value)}
                    />
                    <div>
                      <span>{t(option.labelKey)}</span>
                      <p>{t(option.descriptionKey)}</p>
                    </div>
                  </label>
                )
              })}
            </div>
          </fieldset>

          <button
            type="submit"
            className="agents-capture__submit"
            disabled={loading}
          >
            {loading
              ? t('agentsCapture.form.submitLoading')
              : t('agentsCapture.form.submit')}
          </button>

          <p className="agents-capture__note">
            {t('agentsCapture.form.helper')}
          </p>
        </form>

        {error && (
          <div role="alert" className="agents-capture__error">
            {error}
          </div>
        )}

        {result ? (
          <section className="agents-capture__results">
            <header className="agents-capture__results-header">
              <div>
                <h3>{t('agentsCapture.results.title')}</h3>
                <p>{t('agentsCapture.results.subtitle')}</p>
              </div>
              <div className="agents-capture__results-meta">
                <span>
                  {t('agentsCapture.results.address', {
                    address: result.address.fullAddress,
                  })}
                </span>
                <span>
                  {t('agentsCapture.results.existingUse', {
                    use: result.existingUse,
                  })}
                </span>
                {result.uraZoning.zoneDescription && (
                  <span>
                    {t('agentsCapture.results.zone', {
                      zone: result.uraZoning.zoneDescription,
                    })}
                  </span>
                )}
              </div>
            </header>

            <div className="agents-capture__analysis">
              {scenarioOrder.length === 0 ? (
                <p>{t('agentsCapture.results.empty')}</p>
              ) : (
                scenarioOrder.map((scenario) => (
                  <ScenarioCard
                    key={scenario.scenario}
                    scenario={scenario}
                    locale={locale}
                  />
                ))
              )}
            </div>

            <div className="agents-capture__cta">
              <Link
                to={
                  result.propertyId
                    ? `/feasibility?propertyId=${encodeURIComponent(result.propertyId)}`
                    : '/feasibility'
                }
                className="agents-capture__cta-link"
              >
                {t('agentsCapture.results.viewFeasibility')}
              </Link>
              {(() => {
                const financeProjectName =
                  result.propertyInfo?.propertyName?.trim() ||
                  result.address.fullAddress?.trim() ||
                  null
                const financeLink = result.propertyId
                  ? `/developers/finance?projectId=${encodeURIComponent(result.propertyId)}${
                      financeProjectName
                        ? `&projectName=${encodeURIComponent(financeProjectName)}`
                        : ''
                    }`
                  : '/developers/finance'
                return (
                  <Link to={financeLink} className="agents-capture__cta-link">
                    {t('agentsCapture.results.openFinance')}
                  </Link>
                )
              })()}
            </div>

            <footer className="agents-capture__footer">
              <p>
                {t('agentsCapture.results.generatedAt', {
                  timestamp: new Date(
                    result.quickAnalysis.generatedAt,
                  ).toLocaleString(locale),
                })}
              </p>
              {disclaimers.map((message, index) => (
                <p key={`disclaimer-${index}`}>{message}</p>
              ))}
            </footer>
          </section>
        ) : (
          <section className="agents-capture__placeholder">
            <p>{t('agentsCapture.placeholder')}</p>
          </section>
        )}

        {result && (
          <AgentsCaptureContextPanel
            result={result}
            marketReport={marketReport}
            marketLoading={marketLoading}
            marketError={marketError}
            packSummary={packSummary}
            packLoading={packLoading}
            packError={packError}
            packNotice={packNotice}
            packType={packType}
            setPackType={setPackType}
            onPackSubmit={handlePackSubmit}
            mapElement={<QuickAnalysisMap coordinates={result.coordinates} />}
          />
        )}
      </section>
    </AppLayout>
  )
}

export default AgentsGpsCapturePage
