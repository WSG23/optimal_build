import { useState } from 'react'
import type {
  AdvisorySummary,
  AdvisoryFeedbackPayload,
} from '../../../api/advisory'
import {
  fetchAdvisorySummary,
  submitAdvisoryFeedback,
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
          Advisory Services
        </h1>
        <p
          style={{
            fontSize: '1.25rem',
            color: '#6e6e73',
            fontWeight: 400,
            margin: 0,
            letterSpacing: '-0.01em',
          }}
        >
          Development strategy insights and market positioning
        </p>
      </header>

      {/* Property ID Input */}
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
            fontSize: '1.25rem',
            fontWeight: 600,
            margin: '0 0 1.5rem',
            letterSpacing: '-0.01em',
          }}
        >
          Load property analysis
        </h2>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <label
              htmlFor="property-id"
              style={{
                display: 'block',
                fontSize: '0.875rem',
                fontWeight: 500,
                color: '#1d1d1f',
                marginBottom: '0.5rem',
                letterSpacing: '-0.005em',
              }}
            >
              Property ID
            </label>
            <input
              id="property-id"
              type="text"
              placeholder="Enter property identifier"
              value={propertyId}
              onChange={(e) => setPropertyId(e.target.value)}
              disabled={loading}
              style={{
                width: '100%',
                padding: '0.875rem 1rem',
                fontSize: '1rem',
                border: '1px solid #d2d2d7',
                borderRadius: '12px',
                outline: 'none',
                transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
                background: loading ? '#f5f5f7' : 'white',
                fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, monospace',
                letterSpacing: '-0.005em',
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = '#1d1d1f'
                e.currentTarget.style.boxShadow = '0 0 0 4px rgba(0, 0, 0, 0.04)'
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = '#d2d2d7'
                e.currentTarget.style.boxShadow = 'none'
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleLoad()
              }}
            />
          </div>
          <button
            type="button"
            onClick={handleLoad}
            disabled={loading || !propertyId.trim()}
            style={{
              padding: '0.875rem 2rem',
              fontSize: '1.0625rem',
              fontWeight: 500,
              color: 'white',
              background: loading || !propertyId.trim() ? '#d2d2d7' : '#1d1d1f',
              border: 'none',
              borderRadius: '12px',
              cursor: loading || !propertyId.trim() ? 'not-allowed' : 'pointer',
              transition: 'background 0.2s ease',
              letterSpacing: '-0.005em',
              whiteSpace: 'nowrap',
            }}
            onMouseEnter={(e) => {
              if (!loading && propertyId.trim()) {
                e.currentTarget.style.background = '#424245'
              }
            }}
            onMouseLeave={(e) => {
              if (!loading && propertyId.trim()) {
                e.currentTarget.style.background = '#1d1d1f'
              }
            }}
          >
            {loading ? 'Loading...' : 'Load'}
          </button>
        </div>

        {error && (
          <div
            style={{
              marginTop: '1rem',
              padding: '0.875rem 1rem',
              background: '#fff5f5',
              border: '1px solid #ffe0e0',
              borderRadius: '12px',
              color: '#d70015',
              fontSize: '0.9375rem',
              letterSpacing: '-0.005em',
            }}
          >
            {error}
          </div>
        )}
      </section>

      {/* Advisory Content */}
      {summary && (
        <>
          {/* Asset Mix Strategy */}
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
                fontSize: '1.75rem',
                fontWeight: 600,
                letterSpacing: '-0.01em',
                margin: '0 0 1.5rem',
              }}
            >
              Asset Mix Strategy
            </h2>
            {summary.asset_mix.total_programmable_gfa_sqm && (
              <div
                style={{
                  fontSize: '0.9375rem',
                  color: '#6e6e73',
                  marginBottom: '1.5rem',
                  letterSpacing: '-0.005em',
                }}
              >
                Total programmable GFA:{' '}
                <strong style={{ color: '#1d1d1f' }}>
                  {summary.asset_mix.total_programmable_gfa_sqm.toLocaleString()} m²
                </strong>
              </div>
            )}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {summary.asset_mix.mix_recommendations.map((segment, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '1.25rem',
                    background: '#f5f5f7',
                    borderRadius: '12px',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'baseline',
                      marginBottom: '0.5rem',
                    }}
                  >
                    <h3
                      style={{
                        fontSize: '1.0625rem',
                        fontWeight: 600,
                        margin: 0,
                        letterSpacing: '-0.005em',
                        textTransform: 'capitalize',
                      }}
                    >
                      {segment.use}
                    </h3>
                    <span
                      style={{
                        fontSize: '1.5rem',
                        fontWeight: 600,
                        color: '#1d1d1f',
                        letterSpacing: '-0.015em',
                      }}
                    >
                      {(segment.allocation_pct * 100).toFixed(0)}%
                    </span>
                  </div>
                  {segment.target_gfa_sqm && (
                    <div
                      style={{
                        fontSize: '0.875rem',
                        color: '#6e6e73',
                        marginBottom: '0.5rem',
                        letterSpacing: '-0.005em',
                      }}
                    >
                      Target GFA: {segment.target_gfa_sqm.toLocaleString()} m²
                    </div>
                  )}
                  <p
                    style={{
                      fontSize: '0.9375rem',
                      color: '#6e6e73',
                      margin: 0,
                      lineHeight: 1.5,
                      letterSpacing: '-0.005em',
                    }}
                  >
                    {segment.rationale}
                  </p>
                </div>
              ))}
            </div>
            {summary.asset_mix.notes.length > 0 && (
              <div
                style={{
                  marginTop: '1.5rem',
                  padding: '1rem',
                  background: '#fff9e6',
                  border: '1px solid #ffe8b3',
                  borderRadius: '12px',
                }}
              >
                <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>
                  {summary.asset_mix.notes.map((note, idx) => (
                    <li
                      key={idx}
                      style={{
                        fontSize: '0.9375rem',
                        color: '#996600',
                        lineHeight: 1.6,
                        letterSpacing: '-0.005em',
                      }}
                    >
                      {note}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>

          {/* Market Positioning */}
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
                fontSize: '1.75rem',
                fontWeight: 600,
                letterSpacing: '-0.01em',
                margin: '0 0 1.5rem',
              }}
            >
              Market Positioning
            </h2>
            <div
              style={{
                display: 'inline-block',
                padding: '0.5rem 1rem',
                background: '#f5f5f7',
                borderRadius: '8px',
                fontSize: '0.9375rem',
                fontWeight: 500,
                marginBottom: '1.5rem',
                letterSpacing: '-0.005em',
              }}
            >
              Market Tier: {summary.market_positioning.market_tier}
            </div>

            <h3
              style={{
                fontSize: '1.125rem',
                fontWeight: 600,
                margin: '0 0 1rem',
                letterSpacing: '-0.005em',
              }}
            >
              Pricing Guidance
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
              {Object.entries(summary.market_positioning.pricing_guidance).map(
                ([useType, pricing]) => (
                  <div
                    key={useType}
                    style={{
                      padding: '1.25rem',
                      background: '#f5f5f7',
                      borderRadius: '12px',
                    }}
                  >
                    <div
                      style={{
                        fontSize: '1rem',
                        fontWeight: 600,
                        marginBottom: '0.75rem',
                        textTransform: 'capitalize',
                        letterSpacing: '-0.005em',
                      }}
                    >
                      {useType}
                    </div>
                    {Object.entries(pricing).map(([key, value]) => (
                      <div
                        key={key}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          fontSize: '0.875rem',
                          color: '#6e6e73',
                          marginBottom: '0.25rem',
                          letterSpacing: '-0.005em',
                        }}
                      >
                        <span style={{ textTransform: 'capitalize' }}>{key.replace('_', ' ')}:</span>
                        <span style={{ fontWeight: 500, color: '#1d1d1f' }}>
                          ${value.toLocaleString()}
                        </span>
                      </div>
                    ))}
                  </div>
                ),
              )}
            </div>

            {summary.market_positioning.messaging.length > 0 && (
              <>
                <h3
                  style={{
                    fontSize: '1.125rem',
                    fontWeight: 600,
                    margin: '0 0 1rem',
                    letterSpacing: '-0.005em',
                  }}
                >
                  Key Messages
                </h3>
                <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>
                  {summary.market_positioning.messaging.map((msg, idx) => (
                    <li
                      key={idx}
                      style={{
                        fontSize: '0.9375rem',
                        color: '#6e6e73',
                        lineHeight: 1.6,
                        marginBottom: '0.5rem',
                        letterSpacing: '-0.005em',
                      }}
                    >
                      {msg}
                    </li>
                  ))}
                </ul>
              </>
            )}
          </section>

          {/* Absorption Forecast */}
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
                fontSize: '1.75rem',
                fontWeight: 600,
                letterSpacing: '-0.01em',
                margin: '0 0 1.5rem',
              }}
            >
              Absorption Forecast
            </h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
              <div style={{ padding: '1.25rem', background: '#f5f5f7', borderRadius: '12px' }}>
                <div style={{ fontSize: '0.875rem', color: '#6e6e73', marginBottom: '0.5rem', letterSpacing: '-0.005em' }}>
                  Time to Stabilize
                </div>
                <div style={{ fontSize: '2rem', fontWeight: 600, letterSpacing: '-0.015em' }}>
                  {summary.absorption_forecast.expected_months_to_stabilize}
                  <span style={{ fontSize: '1rem', fontWeight: 400, color: '#6e6e73', marginLeft: '0.25rem' }}>
                    months
                  </span>
                </div>
              </div>
              <div style={{ padding: '1.25rem', background: '#f5f5f7', borderRadius: '12px' }}>
                <div style={{ fontSize: '0.875rem', color: '#6e6e73', marginBottom: '0.5rem', letterSpacing: '-0.005em' }}>
                  Monthly Velocity
                </div>
                <div style={{ fontSize: '2rem', fontWeight: 600, letterSpacing: '-0.015em' }}>
                  {summary.absorption_forecast.monthly_velocity_target}
                  <span style={{ fontSize: '1rem', fontWeight: 400, color: '#6e6e73', marginLeft: '0.25rem' }}>
                    units
                  </span>
                </div>
              </div>
              <div style={{ padding: '1.25rem', background: '#f5f5f7', borderRadius: '12px' }}>
                <div style={{ fontSize: '0.875rem', color: '#6e6e73', marginBottom: '0.5rem', letterSpacing: '-0.005em' }}>
                  Confidence
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 600, textTransform: 'capitalize', letterSpacing: '-0.01em' }}>
                  {summary.absorption_forecast.confidence}
                </div>
              </div>
            </div>

            <h3
              style={{
                fontSize: '1.125rem',
                fontWeight: 600,
                margin: '0 0 1rem',
                letterSpacing: '-0.005em',
              }}
            >
              Timeline
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {summary.absorption_forecast.timeline.map((milestone, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1rem',
                    padding: '1rem',
                    background: '#f5f5f7',
                    borderRadius: '12px',
                  }}
                >
                  <div
                    style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '50%',
                      background: '#1d1d1f',
                      color: 'white',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '1rem',
                      fontWeight: 600,
                      flexShrink: 0,
                      letterSpacing: '-0.005em',
                    }}
                  >
                    M{milestone.month}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '1rem', fontWeight: 500, marginBottom: '0.25rem', letterSpacing: '-0.005em' }}>
                      {milestone.milestone}
                    </div>
                    <div style={{ fontSize: '0.875rem', color: '#6e6e73', letterSpacing: '-0.005em' }}>
                      {(milestone.expected_absorption_pct * 100).toFixed(0)}% absorbed
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Feedback Loop */}
          <section
            style={{
              background: 'white',
              border: '1px solid #d2d2d7',
              borderRadius: '18px',
              padding: '2rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2
                style={{
                  fontSize: '1.75rem',
                  fontWeight: 600,
                  letterSpacing: '-0.01em',
                  margin: 0,
                }}
              >
                Market Feedback
              </h2>
              <button
                type="button"
                onClick={() => setFeedbackOpen(!feedbackOpen)}
                style={{
                  padding: '0.5rem 1.25rem',
                  fontSize: '0.9375rem',
                  fontWeight: 500,
                  color: '#1d1d1f',
                  background: 'transparent',
                  border: '1px solid #d2d2d7',
                  borderRadius: '10px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  letterSpacing: '-0.005em',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = '#1d1d1f'
                  e.currentTarget.style.color = 'white'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'transparent'
                  e.currentTarget.style.color = '#1d1d1f'
                }}
              >
                {feedbackOpen ? 'Cancel' : 'Add Feedback'}
              </button>
            </div>

            {feedbackOpen && (
              <form onSubmit={handleSubmitFeedback} style={{ marginBottom: '2rem' }}>
                <div style={{ marginBottom: '1rem' }}>
                  <label
                    style={{
                      display: 'block',
                      fontSize: '0.875rem',
                      fontWeight: 500,
                      color: '#1d1d1f',
                      marginBottom: '0.5rem',
                      letterSpacing: '-0.005em',
                    }}
                  >
                    Sentiment
                  </label>
                  <select
                    value={feedbackForm.sentiment}
                    onChange={(e) => setFeedbackForm({ ...feedbackForm, sentiment: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '0.75rem 1rem',
                      fontSize: '1rem',
                      border: '1px solid #d2d2d7',
                      borderRadius: '12px',
                      outline: 'none',
                      background: 'white',
                      letterSpacing: '-0.005em',
                    }}
                  >
                    <option value="positive">Positive</option>
                    <option value="neutral">Neutral</option>
                    <option value="negative">Negative</option>
                  </select>
                </div>
                <div style={{ marginBottom: '1rem' }}>
                  <label
                    style={{
                      display: 'block',
                      fontSize: '0.875rem',
                      fontWeight: 500,
                      color: '#1d1d1f',
                      marginBottom: '0.5rem',
                      letterSpacing: '-0.005em',
                    }}
                  >
                    Notes
                  </label>
                  <textarea
                    value={feedbackForm.notes}
                    onChange={(e) => setFeedbackForm({ ...feedbackForm, notes: e.target.value })}
                    placeholder="Enter your feedback..."
                    rows={4}
                    style={{
                      width: '100%',
                      padding: '0.875rem 1rem',
                      fontSize: '1rem',
                      border: '1px solid #d2d2d7',
                      borderRadius: '12px',
                      outline: 'none',
                      background: 'white',
                      resize: 'vertical',
                      letterSpacing: '-0.005em',
                      fontFamily: '-apple-system, BlinkMacSystemFont, system-ui, sans-serif',
                    }}
                  />
                </div>
                <div style={{ marginBottom: '1.5rem' }}>
                  <label
                    style={{
                      display: 'block',
                      fontSize: '0.875rem',
                      fontWeight: 500,
                      color: '#1d1d1f',
                      marginBottom: '0.5rem',
                      letterSpacing: '-0.005em',
                    }}
                  >
                    Channel (optional)
                  </label>
                  <input
                    type="text"
                    value={feedbackForm.channel}
                    onChange={(e) => setFeedbackForm({ ...feedbackForm, channel: e.target.value })}
                    placeholder="e.g., phone call, site visit"
                    style={{
                      width: '100%',
                      padding: '0.75rem 1rem',
                      fontSize: '1rem',
                      border: '1px solid #d2d2d7',
                      borderRadius: '12px',
                      outline: 'none',
                      background: 'white',
                      letterSpacing: '-0.005em',
                    }}
                  />
                </div>
                <button
                  type="submit"
                  disabled={submitting || !feedbackForm.notes.trim()}
                  style={{
                    padding: '0.875rem 2rem',
                    fontSize: '1.0625rem',
                    fontWeight: 500,
                    color: 'white',
                    background: submitting || !feedbackForm.notes.trim() ? '#d2d2d7' : '#1d1d1f',
                    border: 'none',
                    borderRadius: '12px',
                    cursor: submitting || !feedbackForm.notes.trim() ? 'not-allowed' : 'pointer',
                    letterSpacing: '-0.005em',
                  }}
                >
                  {submitting ? 'Submitting...' : 'Submit Feedback'}
                </button>
              </form>
            )}

            {summary.feedback.length === 0 ? (
              <div
                style={{
                  padding: '3rem 2rem',
                  textAlign: 'center',
                  background: '#f5f5f7',
                  borderRadius: '12px',
                }}
              >
                <p style={{ fontSize: '0.9375rem', color: '#6e6e73', margin: 0, letterSpacing: '-0.005em' }}>
                  No feedback recorded yet
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {summary.feedback.map((item) => (
                  <div
                    key={item.id}
                    style={{
                      padding: '1.25rem',
                      background: '#f5f5f7',
                      borderRadius: '12px',
                    }}
                  >
                    <div style={{ display: 'flex', gap: '1rem', marginBottom: '0.75rem' }}>
                      <span
                        style={{
                          padding: '0.25rem 0.75rem',
                          background: item.sentiment === 'positive' ? '#dcfce7' : item.sentiment === 'negative' ? '#fee2e2' : '#f5f5f7',
                          color: item.sentiment === 'positive' ? '#047857' : item.sentiment === 'negative' ? '#b91c1c' : '#6e6e73',
                          borderRadius: '6px',
                          fontSize: '0.8125rem',
                          fontWeight: 500,
                          textTransform: 'capitalize',
                          letterSpacing: '-0.005em',
                        }}
                      >
                        {item.sentiment}
                      </span>
                      {item.channel && (
                        <span style={{ fontSize: '0.875rem', color: '#6e6e73', letterSpacing: '-0.005em' }}>
                          via {item.channel}
                        </span>
                      )}
                    </div>
                    <p style={{ fontSize: '0.9375rem', color: '#1d1d1f', margin: '0 0 0.75rem', lineHeight: 1.6, letterSpacing: '-0.005em' }}>
                      {item.notes}
                    </p>
                    <div style={{ fontSize: '0.8125rem', color: '#86868b', letterSpacing: '-0.005em' }}>
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
        <div
          style={{
            padding: '4rem 2rem',
            textAlign: 'center',
            background: 'white',
            border: '1px solid #d2d2d7',
            borderRadius: '18px',
          }}
        >
          <div
            style={{
              width: '60px',
              height: '60px',
              margin: '0 auto 1.5rem',
              background: '#f5f5f7',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.5rem',
            }}
          >
            📊
          </div>
          <p
            style={{
              fontSize: '1.125rem',
              fontWeight: 500,
              color: '#1d1d1f',
              marginBottom: '0.5rem',
              letterSpacing: '-0.01em',
            }}
          >
            No advisory data loaded
          </p>
          <p
            style={{
              fontSize: '0.9375rem',
              color: '#6e6e73',
              margin: 0,
              letterSpacing: '-0.005em',
            }}
          >
            Enter a property ID above to view development insights
          </p>
        </div>
      )}
    </div>
  )
}
