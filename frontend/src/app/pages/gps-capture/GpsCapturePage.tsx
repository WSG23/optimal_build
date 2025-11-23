import {
  useCallback,
  useMemo,
  useState,
  type FormEvent,
} from 'react'
import {
  DEFAULT_SCENARIO_ORDER,
  fetchPropertyMarketIntelligence,
  generateProfessionalPack,
  logPropertyByGps,
  type DevelopmentScenario,
  type GpsCaptureSummary,
  type MarketIntelligenceSummary,
  type ProfessionalPackSummary,
  type ProfessionalPackType,
} from '../../../api/agents'

export function GpsCapturePage() {
  const [latitude, setLatitude] = useState<string>('1.3000')
  const [longitude, setLongitude] = useState<string>('103.8500')
  const [jurisdictionCode, setJurisdictionCode] = useState<string>('SG')
  const [selectedScenarios, setSelectedScenarios] = useState<
    DevelopmentScenario[]
  >([...DEFAULT_SCENARIO_ORDER])

  const [captureLoading, setCaptureLoading] = useState(false)
  const [captureError, setCaptureError] = useState<string | null>(null)
  const [captureSummary, setCaptureSummary] =
    useState<GpsCaptureSummary | null>(null)

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

  const today = useMemo(
    () => new Date().toLocaleString(undefined, { dateStyle: 'medium' }),
    [],
  )

  const handleScenarioToggle = useCallback(
    (scenario: DevelopmentScenario) => {
      setSelectedScenarios((prev) => {
        if (prev.includes(scenario)) {
          return prev.filter((item) => item !== scenario)
        }
        return [...prev, scenario]
      })
    },
    [],
  )

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
        const summary = await logPropertyByGps({
          latitude: parsedLat,
          longitude: parsedLon,
          developmentScenarios:
            selectedScenarios.length > 0 ? selectedScenarios : undefined,
          jurisdictionCode: jurisdictionCode || undefined,
        })
        setCaptureSummary(summary)
        setCapturedSites((prev) => [
          {
            propertyId: summary.propertyId,
            address: summary.address.fullAddress.startsWith('Mocked Address')
              ? `Captured site (${parsedLat.toFixed(5)}, ${parsedLon.toFixed(5)})`
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
    [latitude, longitude, jurisdictionCode, selectedScenarios],
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
                  District:{' '}
                  <strong>{captureSummary.address.district}</strong>
                </p>
              )}
            </div>
          )}
        </div>
        <div className="gps-card gps-card--map">
          <h2>Site preview</h2>
          <p>
            Map (Mapbox) preview placeholder. The production implementation will
            show coordinates, reverse-geocoded address, and draw radius overlays.
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
                            <dd>{formatMetricValue(metricValue)}</dd>
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
                  <dd>{extractReportValue(marketSummary.report, 'property_type')}</dd>
                </div>
                <div>
                  <dt>Location</dt>
                  <dd>{extractReportValue(marketSummary.report, 'location')}</dd>
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
              benchmarks, and absorption trends returned by the market intelligence
              service after capture.
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
            Generate professional packs for developers and investors. The UI will
            integrate with the pack generator once APIs are finalised.
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
                  <li key={`${pack.propertyId}-${pack.packType}-${pack.generatedAt}`}>
                    <strong>{formatPackLabel(pack.packType)}</strong> •{' '}
                    {new Date(pack.generatedAt).toLocaleString()} —{' '}
                    {pack.downloadUrl ? (
                      <a href={pack.downloadUrl}>Download</a>
                    ) : pack.isFallback ? (
                      <span title={pack.warning ?? 'Preview pack generated offline'}>
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
                      {site.scenario
                        ? formatScenarioLabel(site.scenario)
                        : '—'}
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
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function formatMetricValue(value: unknown) {
  if (value === null || value === undefined) {
    return '—'
  }
  if (typeof value === 'number') {
    return Number.isInteger(value) ? value.toString() : value.toFixed(2)
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
