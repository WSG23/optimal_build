import { useState } from 'react'
import type {
  AdvisorySummary,
  AdvisoryFeedbackPayload,
  SalesVelocityResponse,
} from '../../../api/advisory'
import {
  fetchAdvisorySummary,
  submitAdvisoryFeedback,
  computeSalesVelocity,
} from '../../../api/advisory'

export function AdvisoryPage() {
  const [propertyId, setPropertyId] = useState('')
  const [summary, setSummary] = useState<AdvisorySummary | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [feedbackOpen, setFeedbackOpen] = useState(false)
  const [feedbackForm, setFeedbackForm] = useState<AdvisoryFeedbackPayload>({
    sentiment: 'neutral',
    notes: '',
    channel: '',
  })
  const [submitting, setSubmitting] = useState(false)
  const [velocityInput, setVelocityInput] = useState<{
    jurisdiction: string;
    asset_type: string;
    price_band: string;
    units_planned: number | null;
    launch_window: string;
    inventory_months: string;
    recent_absorption: string;
  }>({
    jurisdiction: 'SG',
    asset_type: 'residential',
    price_band: '1800-2200_psf',
    units_planned: 200,
    launch_window: '2025-Q2',
    inventory_months: '',
    recent_absorption: '',
  })
  const [velocityResult, setVelocityResult] = useState<SalesVelocityResponse | null>(null)
  const [velocityError, setVelocityError] = useState<string | null>(null)
  const [velocityLoading, setVelocityLoading] = useState(false)

  const parseNumber = (value: string): number | null => {
    const trimmed = value.trim()
    if (trimmed === '') return null
    const parsed = Number(trimmed)
    return Number.isFinite(parsed) ? parsed : null
  }

  async function handleLoad() {
    if (!propertyId.trim()) return

    setLoading(true)
    setError(null)
    try {
      const data = await fetchAdvisorySummary(propertyId.trim())
      setSummary(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load advisory data')
      setSummary(null)
    } finally {
      setLoading(false)
    }
  }

  async function handleSubmitFeedback(e: React.FormEvent) {
    e.preventDefault()
    if (!propertyId.trim() || !feedbackForm.notes.trim()) return

    setSubmitting(true)
    try {
      const newFeedback = await submitAdvisoryFeedback(propertyId.trim(), feedbackForm)
      if (summary) {
        setSummary({
          ...summary,
          feedback: [newFeedback, ...summary.feedback],
        })
      }
      setFeedbackForm({ sentiment: 'neutral', notes: '', channel: '' })
      setFeedbackOpen(false)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to submit feedback')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleComputeVelocity() {
    setVelocityLoading(true)
    setVelocityError(null)
    try {
      const payload = {
        jurisdiction: velocityInput.jurisdiction,
        asset_type: velocityInput.asset_type,
        price_band: velocityInput.price_band || null,
        units_planned: velocityInput.units_planned || null,
        launch_window: velocityInput.launch_window || null,
        inventory_months: parseNumber(velocityInput.inventory_months),
        recent_absorption: parseNumber(velocityInput.recent_absorption),
      }
      const result = await computeSalesVelocity(payload)
      setVelocityResult(result)
    } catch (err) {
      setVelocityError(
        err instanceof Error ? err.message : 'Failed to compute sales velocity',
      )
      setVelocityResult(null)
    } finally {
      setVelocityLoading(false)
    }
  }

  return (
    <div className="page">
      {/* Header */}
      <header className="page__header">
        <h1 className="page__title">Advisory Services</h1>
        <p className="page__subtitle">
          Development strategy insights and market positioning
        </p>
      </header>

      {/* Property ID Input */}
      <section className="page__section">
        <h2 className="page__section-title">Load property analysis</h2>
        <div className="page__form-row">
          <div className="page__form-group" style={{ flex: 1, marginBottom: 0 }}>
            <label htmlFor="property-id" className="page__label">
              Property ID
            </label>
            <input
              id="property-id"
              type="text"
              className="page__input page__input--mono"
              placeholder="Enter property identifier"
              value={propertyId}
              onChange={(e) => setPropertyId(e.target.value)}
              disabled={loading}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleLoad()
              }}
            />
          </div>
          <button
            type="button"
            className="page__btn page__btn--primary"
            onClick={handleLoad}
            disabled={loading || !propertyId.trim()}
          >
            {loading ? 'Loading...' : 'Load'}
          </button>
        </div>

        {error && (
          <div className="page__alert page__alert--error">{error}</div>
        )}
      </section>

      {/* Advisory Content */}
      {summary && (
        <>
          {/* Asset Mix Strategy */}
          <section className="page__section">
            <h2 className="page__section-title">Asset Mix Strategy</h2>
            {summary.asset_mix.total_programmable_gfa_sqm && (
              <div className="advisory__gfa-info">
                Total programmable GFA:{' '}
                <span className="advisory__gfa-value">
                  {summary.asset_mix.total_programmable_gfa_sqm.toLocaleString()} m²
                </span>
              </div>
            )}
            <div className="page__grid page__grid--auto">
              {summary.asset_mix.mix_recommendations.map((segment, idx) => (
                <div key={idx} className="advisory__segment">
                  <div className="advisory__segment-header">
                    <h3 className="advisory__segment-title">{segment.use}</h3>
                    <span className="advisory__segment-value">
                      {(segment.allocation_pct * 100).toFixed(0)}%
                    </span>
                  </div>
                  {segment.target_gfa_sqm && (
                    <div className="advisory__segment-meta">
                      Target GFA: {segment.target_gfa_sqm.toLocaleString()} m²
                    </div>
                  )}
                  <p className="advisory__segment-rationale">{segment.rationale}</p>
                </div>
              ))}
            </div>
            {summary.asset_mix.notes.length > 0 && (
              <div className="advisory__notes">
                <ul>
                  {summary.asset_mix.notes.map((note, idx) => (
                    <li key={idx}>{note}</li>
                  ))}
                </ul>
              </div>
            )}
          </section>

          {/* Market Positioning */}
          <section className="page__section">
            <h2 className="page__section-title">Market Positioning</h2>
            <div className="advisory__tier-badge">
              Market Tier: {summary.market_positioning.market_tier}
            </div>

            <h3 className="page__section-title">Pricing Guidance</h3>
            <div className="page__grid page__grid--auto">
              {Object.entries(summary.market_positioning.pricing_guidance).map(
                ([useType, pricing]) => (
                  <div key={useType} className="advisory__pricing-card">
                    <div className="advisory__pricing-title">{useType}</div>
                    {Object.entries(pricing).map(([key, value]) => (
                      <div key={key} className="advisory__pricing-row">
                        <span>{key.replace('_', ' ')}:</span>
                        <span>${value.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                ),
              )}
            </div>

            {summary.market_positioning.messaging.length > 0 && (
              <>
                <h3 className="page__section-title" style={{ marginTop: 'var(--ob-spacing-400)' }}>
                  Key Messages
                </h3>
                <ul className="advisory__messages">
                  {summary.market_positioning.messaging.map((msg, idx) => (
                    <li key={idx}>{msg}</li>
                  ))}
                </ul>
              </>
            )}
          </section>

          {/* Absorption Forecast */}
          <section className="page__section">
            <h2 className="page__section-title">Absorption Forecast</h2>
            <div className="advisory__metrics">
              <div className="advisory__metric-card">
                <div className="advisory__metric-label">Time to Stabilize</div>
                <div className="advisory__metric-value">
                  {summary.absorption_forecast.expected_months_to_stabilize}
                  <span className="advisory__metric-unit">months</span>
                </div>
              </div>
              <div className="advisory__metric-card">
                <div className="advisory__metric-label">Monthly Velocity</div>
                <div className="advisory__metric-value">
                  {summary.absorption_forecast.monthly_velocity_target}
                  <span className="advisory__metric-unit">units</span>
                </div>
              </div>
              <div className="advisory__metric-card">
                <div className="advisory__metric-label">Confidence</div>
                <div className="advisory__metric-value" style={{ textTransform: 'capitalize' }}>
                  {summary.absorption_forecast.confidence}
                </div>
              </div>
            </div>

            <h3 className="page__section-title">Timeline</h3>
            <div className="advisory__timeline">
              {summary.absorption_forecast.timeline.map((milestone, idx) => (
                <div key={idx} className="advisory__timeline-item">
                  <div className="advisory__timeline-badge">M{milestone.month}</div>
                  <div className="advisory__timeline-content">
                    <div className="advisory__timeline-title">{milestone.milestone}</div>
                    <div className="advisory__timeline-meta">
                      {(milestone.expected_absorption_pct * 100).toFixed(0)}% absorbed
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Sales Velocity Model */}
          <section className="page__section">
            <div className="advisory__section-header">
              <div>
                <h2 className="page__section-title" style={{ marginBottom: 0 }}>
                  Sales Velocity Model
                </h2>
                <p className="advisory__section-description">
                  Forecast launch cadence with inventory and velocity benchmarks.
                </p>
              </div>
              <button
                type="button"
                className="page__btn page__btn--primary"
                onClick={handleComputeVelocity}
                disabled={velocityLoading}
              >
                {velocityLoading ? 'Computing...' : 'Run forecast'}
              </button>
            </div>

            <div className="page__grid page__grid--auto">
              <div className="page__form-group">
                <label className="page__label">Jurisdiction</label>
                <select
                  className="page__select"
                  value={velocityInput.jurisdiction}
                  onChange={(e) =>
                    setVelocityInput((prev) => ({ ...prev, jurisdiction: e.target.value }))
                  }
                >
                  <option value="SG">Singapore</option>
                  <option value="SEA">Seattle</option>
                  <option value="TOR">Toronto</option>
                  <option value="NZ">New Zealand</option>
                  <option value="HK">Hong Kong</option>
                </select>
              </div>
              <div className="page__form-group">
                <label className="page__label">Asset type</label>
                <select
                  className="page__select"
                  value={velocityInput.asset_type}
                  onChange={(e) =>
                    setVelocityInput((prev) => ({ ...prev, asset_type: e.target.value }))
                  }
                >
                  <option value="residential">Residential</option>
                  <option value="office">Office</option>
                  <option value="retail">Retail</option>
                  <option value="mixed_use">Mixed-use</option>
                  <option value="industrial">Industrial</option>
                </select>
              </div>
              <div className="page__form-group">
                <label className="page__label">Price band</label>
                <input
                  type="text"
                  className="page__input"
                  value={velocityInput.price_band}
                  onChange={(e) =>
                    setVelocityInput((prev) => ({ ...prev, price_band: e.target.value }))
                  }
                  placeholder="e.g. 1800-2200_psf"
                />
              </div>
              <div className="page__form-group">
                <label className="page__label">Units planned</label>
                <input
                  type="number"
                  className="page__input"
                  value={velocityInput.units_planned ?? ''}
                  onChange={(e) =>
                    setVelocityInput((prev) => ({
                      ...prev,
                      units_planned: e.target.value === '' ? null : Number(e.target.value),
                    }))
                  }
                  min={0}
                />
              </div>
              <div className="page__form-group">
                <label className="page__label">Launch window</label>
                <input
                  type="text"
                  className="page__input"
                  value={velocityInput.launch_window}
                  onChange={(e) =>
                    setVelocityInput((prev) => ({ ...prev, launch_window: e.target.value }))
                  }
                  placeholder="e.g. 2025-Q2"
                />
              </div>
              <div className="page__form-group">
                <label className="page__label">Inventory (months, optional)</label>
                <input
                  type="number"
                  className="page__input"
                  value={velocityInput.inventory_months}
                  onChange={(e) =>
                    setVelocityInput((prev) => ({ ...prev, inventory_months: e.target.value }))
                  }
                  min={0}
                  step="0.1"
                />
              </div>
              <div className="page__form-group">
                <label className="page__label">Recent absorption (units/mo, optional)</label>
                <input
                  type="number"
                  className="page__input"
                  value={velocityInput.recent_absorption}
                  onChange={(e) =>
                    setVelocityInput((prev) => ({ ...prev, recent_absorption: e.target.value }))
                  }
                  min={0}
                  step="0.1"
                />
              </div>
            </div>

            {velocityError && (
              <div className="page__alert page__alert--error">{velocityError}</div>
            )}

            {velocityResult && (
              <div className="advisory__velocity-results">
                <div className="advisory__metrics">
                  <div className="advisory__metric-card">
                    <div className="advisory__metric-label">Velocity</div>
                    <div className="advisory__metric-value">
                      {velocityResult.forecast.velocity_units_per_month ?? '—'}
                      <span className="advisory__metric-unit">units/mo</span>
                    </div>
                  </div>
                  <div className="advisory__metric-card">
                    <div className="advisory__metric-label">Absorption</div>
                    <div className="advisory__metric-value">
                      {velocityResult.forecast.absorption_months ?? '—'}
                      <span className="advisory__metric-unit">months</span>
                    </div>
                  </div>
                  <div className="advisory__metric-card">
                    <div className="advisory__metric-label">Confidence</div>
                    <div className="advisory__metric-value">
                      {(velocityResult.forecast.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>

                {velocityResult.risks.length > 0 && (
                  <div className="advisory__risk-tags">
                    {velocityResult.risks.map((risk, idx) => (
                      <span
                        key={idx}
                        className={`advisory__risk-tag advisory__risk-tag--${risk.level}`}
                      >
                        {risk.label} ({risk.level})
                      </span>
                    ))}
                  </div>
                )}

                {velocityResult.recommendations.length > 0 && (
                  <div>
                    <h3 className="page__section-title">Recommendations</h3>
                    <ul className="advisory__recommendations">
                      {velocityResult.recommendations.map((rec, idx) => (
                        <li key={idx}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div>
                  <h3 className="page__section-title">Benchmarks</h3>
                  <div className="advisory__benchmarks">
                    <div className="advisory__benchmark-card">
                      <div className="advisory__benchmark-label">Inventory</div>
                      <div className="advisory__benchmark-value">
                        {velocityResult.benchmarks.inventory_months ?? '—'} months
                      </div>
                    </div>
                    <div className="advisory__benchmark-card">
                      <div className="advisory__benchmark-label">Velocity p25 / p50 / p75</div>
                      <div className="advisory__benchmark-value">
                        {[velocityResult.benchmarks.velocity_p25, velocityResult.benchmarks.velocity_median, velocityResult.benchmarks.velocity_p75]
                          .map((v) => (v == null ? '—' : v))
                          .join(' / ')}{' '}
                        units/mo
                      </div>
                    </div>
                    <div className="advisory__benchmark-card">
                      <div className="advisory__benchmark-label">Median PSF</div>
                      <div className="advisory__benchmark-value">
                        {velocityResult.benchmarks.median_psf ?? '—'}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </section>

          {/* Feedback Loop */}
          <section className="page__section">
            <div className="advisory__section-header">
              <h2 className="page__section-title" style={{ marginBottom: 0 }}>
                Market Feedback
              </h2>
              <button
                type="button"
                className="page__btn page__btn--secondary"
                onClick={() => setFeedbackOpen(!feedbackOpen)}
              >
                {feedbackOpen ? 'Cancel' : 'Add Feedback'}
              </button>
            </div>

            {feedbackOpen && (
              <form onSubmit={handleSubmitFeedback}>
                <div className="page__form-group">
                  <label className="page__label">Sentiment</label>
                  <select
                    className="page__select"
                    value={feedbackForm.sentiment}
                    onChange={(e) => setFeedbackForm({ ...feedbackForm, sentiment: e.target.value })}
                  >
                    <option value="positive">Positive</option>
                    <option value="neutral">Neutral</option>
                    <option value="negative">Negative</option>
                  </select>
                </div>
                <div className="page__form-group">
                  <label className="page__label">Notes</label>
                  <textarea
                    className="page__textarea"
                    value={feedbackForm.notes}
                    onChange={(e) => setFeedbackForm({ ...feedbackForm, notes: e.target.value })}
                    placeholder="Enter your feedback..."
                    rows={4}
                  />
                </div>
                <div className="page__form-group">
                  <label className="page__label">Channel (optional)</label>
                  <input
                    type="text"
                    className="page__input"
                    value={feedbackForm.channel}
                    onChange={(e) => setFeedbackForm({ ...feedbackForm, channel: e.target.value })}
                    placeholder="e.g., phone call, site visit"
                  />
                </div>
                <button
                  type="submit"
                  className="page__btn page__btn--primary"
                  disabled={submitting || !feedbackForm.notes.trim()}
                >
                  {submitting ? 'Submitting...' : 'Submit Feedback'}
                </button>
              </form>
            )}

            <div className="page__divider" />

            {summary.feedback.length === 0 ? (
              <div className="page__empty">
                <p className="page__empty-description">No feedback recorded yet</p>
              </div>
            ) : (
              <div className="advisory__feedback-list">
                {summary.feedback.map((item) => (
                  <div key={item.id} className="advisory__feedback-item">
                    <div className="advisory__feedback-header">
                      <span className={`advisory__sentiment advisory__sentiment--${item.sentiment}`}>
                        {item.sentiment}
                      </span>
                      {item.channel && (
                        <span className="advisory__feedback-channel">via {item.channel}</span>
                      )}
                    </div>
                    <p className="advisory__feedback-notes">{item.notes}</p>
                    <div className="advisory__feedback-meta">
                      {item.submitted_by && <span>{item.submitted_by} · </span>}
                      {new Date(item.created_at).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </>
      )}

      {/* Empty State */}
      {!summary && !loading && (
        <section className="page__section">
          <div className="page__empty">
            <div className="advisory__empty-icon">📊</div>
            <h3 className="page__empty-title">No advisory data loaded</h3>
            <p className="page__empty-description">
              Enter a property ID above to view development insights
            </p>
          </div>
        </section>
      )}
    </div>
  )
}
