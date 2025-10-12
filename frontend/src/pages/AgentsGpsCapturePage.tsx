import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'

import mapboxgl from 'mapbox-gl'

const isNodeTestEnv =
  typeof process !== 'undefined' && process.env?.NODE_ENV === 'test'

if (typeof window !== 'undefined' && !isNodeTestEnv) {
  void import('mapbox-gl/dist/mapbox-gl.css')
}

import { AppLayout } from '../App'
import {
  DEFAULT_SCENARIO_ORDER,
  type DevelopmentScenario,
  type GpsCaptureSummary,
  type MarketIntelligenceSummary,
  type MetricValue,
  type QuickAnalysisScenarioSummary,
  type ProfessionalPackSummary,
  type ProfessionalPackType,
  logPropertyByGps,
  fetchPropertyMarketIntelligence,
  generateProfessionalPack,
} from '../api/agents'
import { useTranslation } from '../i18n'
import { Link } from '../router'

const MAPBOX_ENV =
  typeof import.meta !== 'undefined' && import.meta
    ? (import.meta as ImportMeta).env
    : undefined
const MAPBOX_TOKEN = MAPBOX_ENV?.VITE_MAPBOX_ACCESS_TOKEN ?? ''
if (MAPBOX_TOKEN) {
  mapboxgl.accessToken = MAPBOX_TOKEN
}

const DEFAULT_LATITUDE = '1.3000'
const DEFAULT_LONGITUDE = '103.8500'

interface ScenarioOption {
  value: DevelopmentScenario
  labelKey: string
  descriptionKey: string
}

const SCENARIO_OPTIONS: readonly ScenarioOption[] = [
  {
    value: 'raw_land',
    labelKey: 'agentsCapture.scenarios.rawLand.title',
    descriptionKey: 'agentsCapture.scenarios.rawLand.description',
  },
  {
    value: 'existing_building',
    labelKey: 'agentsCapture.scenarios.existingBuilding.title',
    descriptionKey: 'agentsCapture.scenarios.existingBuilding.description',
  },
  {
    value: 'heritage_property',
    labelKey: 'agentsCapture.scenarios.heritageProperty.title',
    descriptionKey: 'agentsCapture.scenarios.heritageProperty.description',
  },
  {
    value: 'underused_asset',
    labelKey: 'agentsCapture.scenarios.underusedAsset.title',
    descriptionKey: 'agentsCapture.scenarios.underusedAsset.description',
  },
] as const

interface PackOption {
  value: ProfessionalPackType
  labelKey: string
  descriptionKey: string
}

const PACK_OPTIONS: readonly PackOption[] = [
  {
    value: 'universal',
    labelKey: 'agentsCapture.pack.options.universal.title',
    descriptionKey: 'agentsCapture.pack.options.universal.description',
  },
  {
    value: 'investment',
    labelKey: 'agentsCapture.pack.options.investment.title',
    descriptionKey: 'agentsCapture.pack.options.investment.description',
  },
  {
    value: 'sales',
    labelKey: 'agentsCapture.pack.options.sales.title',
    descriptionKey: 'agentsCapture.pack.options.sales.description',
  },
  {
    value: 'lease',
    labelKey: 'agentsCapture.pack.options.lease.title',
    descriptionKey: 'agentsCapture.pack.options.lease.description',
  },
] as const

function formatDateDisplay(value: unknown, locale: string): string | null {
  if (typeof value !== 'string' || value.trim() === '') {
    return null
  }
  const timestamp = Date.parse(value)
  if (Number.isNaN(timestamp)) {
    return value
  }
  return new Date(timestamp).toLocaleDateString(locale)
}

function renderMarketReport(
  summary: MarketIntelligenceSummary,
  translate: ReturnType<typeof useTranslation>['t'],
  locale: string,
) {
  const report = summary.report ?? {}
  const comparables = (report.comparables_analysis as Record<string, unknown>) ?? {}
  const transactions =
    typeof comparables.transaction_count === 'number'
      ? comparables.transaction_count
      : null
  const propertyType =
    typeof report.property_type === 'string' ? report.property_type : null
  const location = typeof report.location === 'string' ? report.location : null
  const periodData = report.period as
    | { start?: string | null; end?: string | null }
    | undefined
  const periodStart = formatDateDisplay(periodData?.start, locale)
  const periodEnd = formatDateDisplay(periodData?.end, locale)
  const generatedAt = formatDateDisplay(report.generated_at, locale)

  const metrics = [
    {
      key: 'propertyType',
      label: translate('agentsCapture.market.propertyType'),
      value: propertyType ?? '—',
    },
    {
      key: 'location',
      label: translate('agentsCapture.market.location'),
      value: location ?? '—',
    },
    {
      key: 'period',
      label: translate('agentsCapture.market.period'),
      value:
        periodStart && periodEnd
          ? `${periodStart} – ${periodEnd}`
          : periodStart ?? periodEnd ?? '—',
    },
    {
      key: 'transactions',
      label: translate('agentsCapture.market.transactions'),
      value:
        transactions !== null
          ? new Intl.NumberFormat(locale).format(transactions)
          : '—',
    },
  ]

  return (
    <>
      <dl className="agents-capture__market-metrics">
        {metrics.map(({ key, label, value }) => (
          <div key={key} className="agents-capture__market-row">
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
      {generatedAt && (
        <p className="agents-capture__status">
          {translate('agentsCapture.market.generatedAt', { timestamp: generatedAt })}
        </p>
      )}
    </>
  )
}

function QuickAnalysisMap({ coordinates }: { coordinates: CoordinatePair }) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<mapboxgl.Map | null>(null)
  const { t } = useTranslation()

  const canRender = MAPBOX_TOKEN !== '' && typeof window !== 'undefined'

  useEffect(() => {
    if (!canRender || !containerRef.current) {
      return
    }

    if (mapRef.current) {
      mapRef.current.remove()
    }

    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: 'mapbox://styles/mapbox/light-v11',
      center: [coordinates.longitude, coordinates.latitude],
      zoom: 15,
    })

    map.addControl(new mapboxgl.NavigationControl({ showCompass: false }))
    new mapboxgl.Marker({ color: '#2563eb' })
      .setLngLat([coordinates.longitude, coordinates.latitude])
      .addTo(map)

    mapRef.current = map
    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [coordinates.latitude, coordinates.longitude, canRender])

  if (!canRender) {
    return (
      <div className="agents-capture__map-fallback">
        {t('agentsCapture.context.mapFallback')}
      </div>
    )
  }

  return <div ref={containerRef} className="agents-capture__map-canvas" />
}

function formatMetricLabel(key: string, translate: ReturnType<typeof useTranslation>['t']): string {
  const lookup: Record<string, string> = {
    site_area_sqm: translate('agentsCapture.metrics.siteArea'),
    plot_ratio: translate('agentsCapture.metrics.plotRatio'),
    potential_gfa_sqm: translate('agentsCapture.metrics.potentialGfa'),
    approved_gfa_sqm: translate('agentsCapture.metrics.approvedGfa'),
    scenario_gfa_sqm: translate('agentsCapture.metrics.scenarioGfa'),
    gfa_uplift_sqm: translate('agentsCapture.metrics.gfaUplift'),
    near_by_mrt_count: translate('agentsCapture.metrics.nearbyMrtCount'),
    nearby_mrt_count: translate('agentsCapture.metrics.nearbyMrtCount'),
    current_use: translate('agentsCapture.metrics.currentUse'),
    building_height_m: translate('agentsCapture.metrics.buildingHeight'),
    nearby_development_count: translate(
      'agentsCapture.metrics.nearbyDevelopmentCount',
    ),
    nearest_completion: translate('agentsCapture.metrics.nearestCompletion'),
    recent_transaction_count: translate(
      'agentsCapture.metrics.recentTransactionCount',
    ),
    average_psf_price: translate('agentsCapture.metrics.averagePsfPrice'),
    average_monthly_rent: translate(
      'agentsCapture.metrics.averageMonthlyRent',
    ),
    rental_comparable_count: translate(
      'agentsCapture.metrics.rentalComparableCount',
    ),
    property_type: translate('agentsCapture.metrics.propertyType'),
    completion_year: translate('agentsCapture.metrics.completionYear'),
    heritage_risk: translate('agentsCapture.metrics.heritageRisk'),
  }

  if (lookup[key]) {
    return lookup[key]
  }
  const cleaned = key.replace(/_/g, ' ')
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1)
}

function formatMetricValue(value: MetricValue, locale: string): string {
  if (value === null) {
    return '—'
  }
  if (typeof value === 'number') {
    return new Intl.NumberFormat(locale, {
      maximumFractionDigits: Number.isInteger(value) ? 0 : 2,
    }).format(value)
  }
  return value
}

function formatFileSize(bytes: number | null, locale: string): string {
  if (bytes == null || Number.isNaN(bytes)) {
    return '—'
  }
  if (bytes < 1024) {
    return `${new Intl.NumberFormat(locale).format(bytes)} B`
  }
  const units = ['KB', 'MB', 'GB'] as const
  let value = bytes / 1024
  let index = 0
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024
    index += 1
  }
  return `${new Intl.NumberFormat(locale, { maximumFractionDigits: 1 }).format(value)} ${units[index]}`
}

function scenarioTitle(
  scenario: DevelopmentScenario,
  translate: ReturnType<typeof useTranslation>['t'],
): string {
  switch (scenario) {
    case 'raw_land':
      return translate('agentsCapture.scenarios.rawLand.title')
    case 'existing_building':
      return translate('agentsCapture.scenarios.existingBuilding.title')
    case 'heritage_property':
      return translate('agentsCapture.scenarios.heritageProperty.title')
    case 'underused_asset':
      return translate('agentsCapture.scenarios.underusedAsset.title')
    default:
      return scenario
  }
}

function scenarioDescription(
  scenario: DevelopmentScenario,
  translate: ReturnType<typeof useTranslation>['t'],
): string {
  switch (scenario) {
    case 'raw_land':
      return translate('agentsCapture.scenarios.rawLand.description')
    case 'existing_building':
      return translate('agentsCapture.scenarios.existingBuilding.description')
    case 'heritage_property':
      return translate('agentsCapture.scenarios.heritageProperty.description')
    case 'underused_asset':
      return translate('agentsCapture.scenarios.underusedAsset.description')
    default:
      return ''
  }
}

function ScenarioCard({
  scenario,
  locale,
}: {
  scenario: QuickAnalysisScenarioSummary
  locale: string
}) {
  const { t } = useTranslation()

  const entries = useMemo(() => Object.entries(scenario.metrics), [scenario.metrics])

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
  const [selectedScenarios, setSelectedScenarios] = useState<
    Set<DevelopmentScenario>
  >(() => new Set(DEFAULT_SCENARIO_ORDER))
  const [result, setResult] = useState<GpsCaptureSummary | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [marketReport, setMarketReport] =
    useState<MarketIntelligenceSummary | null>(null)
  const [marketLoading, setMarketLoading] = useState(false)
  const [marketError, setMarketError] = useState<string | null>(null)
  const [packType, setPackType] = useState<ProfessionalPackType>('universal')
  const [packSummary, setPackSummary] = useState<ProfessionalPackSummary | null>(
    null,
  )
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

  const selectedPackOption = useMemo(
    () => PACK_OPTIONS.find((option) => option.value === packType) ?? PACK_OPTIONS[0],
    [packType],
  )

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
        err instanceof Error ? err.message : t('agentsCapture.pack.errorFallback')
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
                  <label key={option.value} className="agents-capture__scenario-option">
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

          <p className="agents-capture__note">{t('agentsCapture.form.helper')}</p>
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
              <Link to="/finance" className="agents-capture__cta-link">
                {t('agentsCapture.results.openFinance')}
              </Link>
            </div>

            <footer className="agents-capture__footer">
              <p>
                {t('agentsCapture.results.generatedAt', {
                  timestamp: new Date(result.quickAnalysis.generatedAt).toLocaleString(
                    locale,
                  ),
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
          <section className="agents-capture__context">
            <div className="agents-capture__map">
              <h4>{t('agentsCapture.context.mapTitle')}</h4>
              <QuickAnalysisMap coordinates={result.coordinates} />
            </div>
            {result.nearbyAmenities && (
              <aside className="agents-capture__amenities">
                <h4>{t('agentsCapture.context.amenitiesTitle')}</h4>
                <ul>
                  {(
                    [
                      {
                        key: 'mrtStations' as const,
                        label: t('agentsCapture.context.amenities.mrt'),
                      },
                      {
                        key: 'busStops' as const,
                        label: t('agentsCapture.context.amenities.bus'),
                      },
                      {
                        key: 'schools' as const,
                        label: t('agentsCapture.context.amenities.schools'),
                      },
                      {
                        key: 'shoppingMalls' as const,
                        label: t('agentsCapture.context.amenities.malls'),
                      },
                      {
                        key: 'parks' as const,
                        label: t('agentsCapture.context.amenities.parks'),
                      },
                    ]
                  ).map(({ key, label }) => {
                    const items = result.nearbyAmenities?.[key] ?? []
                    if (!items.length) {
                      return null
                    }
                    const nearest = items[0]
                    return (
                      <li key={key}>
                        <strong>{label}</strong>
                        {nearest.distanceM != null
                          ? t('agentsCapture.context.amenities.itemWithDistance', {
                              name: nearest.name,
                              distance: new Intl.NumberFormat(locale, {
                                maximumFractionDigits: 0,
                              }).format(nearest.distanceM),
                            })
                          : t('agentsCapture.context.amenities.item', {
                              name: nearest.name,
                            })}
                      </li>
                    )
                  })}
                </ul>
              </aside>
            )}
            <aside className="agents-capture__market">
              <h4>{t('agentsCapture.market.title')}</h4>
              {marketLoading && (
                <p className="agents-capture__status">
                  {t('agentsCapture.market.loading')}
                </p>
              )}
              {marketError && (
                <p className="agents-capture__error agents-capture__error--inline">
                  {t('agentsCapture.market.error', { message: marketError })}
                </p>
              )}
              {marketReport && renderMarketReport(marketReport, t, locale)}
            </aside>
            <aside className="agents-capture__pack">
              <h4>{t('agentsCapture.pack.title')}</h4>
              <p className="agents-capture__status">
                {t('agentsCapture.pack.subtitle')}
              </p>
              <form className="agents-capture__pack-form" onSubmit={handlePackSubmit}>
                <label className="agents-capture__pack-field">
                  <span>{t('agentsCapture.pack.selectLabel')}</span>
                  <select
                    value={packType}
                    onChange={(event) =>
                      setPackType(event.target.value as ProfessionalPackType)
                    }
                  >
                    {PACK_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {t(option.labelKey)}
                      </option>
                    ))}
                  </select>
                </label>
                <p className="agents-capture__pack-description">
                  {t(selectedPackOption.descriptionKey)}
                </p>
                <button
                  type="submit"
                  className="agents-capture__pack-button"
                  disabled={packLoading}
                >
                  {packLoading
                    ? t('agentsCapture.pack.generateLoading')
                    : t('agentsCapture.pack.generate')}
                </button>
              </form>
              {packError && (
                <p className="agents-capture__error agents-capture__error--inline">
                  {t('agentsCapture.pack.error', { message: packError })}
                </p>
              )}
              {packSummary && (
                <div className="agents-capture__pack-result">
                  <p className="agents-capture__status">
                    {t('agentsCapture.pack.generatedAt', {
                      timestamp: new Date(packSummary.generatedAt).toLocaleString(
                        locale,
                      ),
                    })}
                  </p>
                  <p className="agents-capture__status">
                    {t('agentsCapture.pack.size', {
                      size: formatFileSize(packSummary.sizeBytes, locale),
                    })}
                  </p>
                  {packSummary.downloadUrl ? (
                    <a
                      href={packSummary.downloadUrl}
                      className="agents-capture__pack-download"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {t('agentsCapture.pack.downloadCta', {
                        filename: packSummary.filename,
                      })}
                    </a>
                  ) : (
                    <p className="agents-capture__status">
                      {t('agentsCapture.pack.noDownload')}
                    </p>
                  )}
                  {packNotice && (
                    <p className="agents-capture__status">{packNotice}</p>
                  )}
                </div>
              )}
            </aside>
          </section>
        )}
      </section>
    </AppLayout>
  )
}

export default AgentsGpsCapturePage
