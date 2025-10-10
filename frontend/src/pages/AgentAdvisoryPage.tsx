import { FormEvent, useEffect, useMemo, useState } from 'react'

import { AppLayout } from '../App'
import {
  AdvisoryFeedbackItem,
  AdvisoryFeedbackPayload,
  AdvisorySummary,
  fetchAdvisorySummary,
  submitAdvisoryFeedback,
} from '../api/advisory'
import { useRouterLocation } from '../router'

function usePropertyIdFromQuery(): string {
  const { search } = useRouterLocation()
  return useMemo(() => {
    try {
      const params = new URLSearchParams(search)
      return params.get('propertyId') ?? ''
    } catch (error) {
      console.warn('Failed to parse query string', error)
      return ''
    }
  }, [search])
}

export function AgentAdvisoryPage() {
  const propertyId = usePropertyIdFromQuery()
  const [summary, setSummary] = useState<AdvisorySummary | null>(null)
  const [feedback, setFeedback] = useState<AdvisoryFeedbackItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [feedbackNotes, setFeedbackNotes] = useState('')
  const [feedbackSentiment, setFeedbackSentiment] = useState('positive')
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (!propertyId) {
      return
    }
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    fetchAdvisorySummary(propertyId, controller.signal)
      .then((data) => {
        setSummary(data)
        setFeedback(data.feedback)
      })
      .catch((err) => {
        if (err instanceof Error) {
          setError(err.message)
        } else {
          setError('Failed to load advisory insights')
        }
      })
      .finally(() => setLoading(false))

    return () => controller.abort()
  }, [propertyId])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!propertyId || feedbackNotes.trim() === '') {
      return
    }

    const payload: AdvisoryFeedbackPayload = {
      sentiment: feedbackSentiment,
      notes: feedbackNotes.trim(),
    }
    setIsSubmitting(true)
    try {
      const record = await submitAdvisoryFeedback(propertyId, payload)
      setFeedback((existing) => [record, ...existing])
      setFeedbackNotes('')
      setFeedbackSentiment('positive')
    } catch (err) {
      console.error('Failed to record feedback', err)
      setError(err instanceof Error ? err.message : 'Failed to submit feedback')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AppLayout
      title="Development advisory toolkit"
      subtitle="Blend site analysis with market intelligence to recommend positioning, velocity, and next steps."
    >
      {!propertyId && (
        <div className="advisory__notice">
          Provide a `propertyId` query parameter to load advisory insights.
        </div>
      )}

      {error && <div className="advisory__error">{error}</div>}

      {loading && <div className="advisory__loading">Loading advisory insights…</div>}

      {summary && (
        <div className="advisory">
          <section className="advisory__panel">
            <h2>Asset mix strategy</h2>
            <p>
              Total programmable GFA:{' '}
              {summary.asset_mix.total_programmable_gfa_sqm != null
                ? `${summary.asset_mix.total_programmable_gfa_sqm.toLocaleString()} sqm`
                : '—'}
            </p>
            <table className="advisory__table">
              <thead>
                <tr>
                  <th>Use</th>
                  <th>Allocation</th>
                  <th>Target GFA (sqm)</th>
                  <th>Rationale</th>
                </tr>
              </thead>
              <tbody>
                {summary.asset_mix.mix_recommendations.map((segment) => (
                  <tr key={segment.use}>
                    <td>{segment.use}</td>
                    <td>{segment.allocation_pct}%</td>
                    <td>
                      {segment.target_gfa_sqm != null
                        ? segment.target_gfa_sqm.toLocaleString()
                        : '—'}
                    </td>
                    <td>{segment.rationale}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {summary.asset_mix.notes.length > 0 && (
              <ul className="advisory__notes">
                {summary.asset_mix.notes.map((note, index) => (
                  <li key={`mix-note-${index}`}>{note}</li>
                ))}
              </ul>
            )}
          </section>

          <section className="advisory__panel">
            <h2>Market positioning</h2>
            <p>Tier: {summary.market_positioning.market_tier}</p>
            <div className="advisory__pricing">
              <strong>Pricing guidance</strong>
              <ul>
                {Object.entries(summary.market_positioning.pricing_guidance).map(
                  ([key, range]) => (
                    <li key={key}>
                      {key}: {range.target_min.toLocaleString()} –{' '}
                      {range.target_max.toLocaleString()}
                    </li>
                  ),
                )}
              </ul>
            </div>
            <div className="advisory__segments">
              <strong>Target segments</strong>
              <ul>
                {summary.market_positioning.target_segments.map((segment, index) => (
                  <li key={`segment-${index}`}>
                    {String(segment.segment || 'Segment')} –{' '}
                    {segment.weight_pct != null ? `${segment.weight_pct}%` : ''}
                  </li>
                ))}
              </ul>
            </div>
            <ul className="advisory__messaging">
              {summary.market_positioning.messaging.map((message, index) => (
                <li key={`message-${index}`}>{message}</li>
              ))}
            </ul>
          </section>

          <section className="advisory__panel">
            <h2>Absorption forecast</h2>
            <p>
              Expected stabilisation in{' '}
              {summary.absorption_forecast.expected_months_to_stabilize} months at a
              target velocity of {summary.absorption_forecast.monthly_velocity_target}{' '}
              units per month.
            </p>
            <table className="advisory__table">
              <thead>
                <tr>
                  <th>Milestone</th>
                  <th>Month</th>
                  <th>Absorption</th>
                </tr>
              </thead>
              <tbody>
                {summary.absorption_forecast.timeline.map((milestone, index) => (
                  <tr key={`timeline-${index}`}>
                    <td>{milestone.milestone}</td>
                    <td>{milestone.month}</td>
                    <td>{milestone.expected_absorption_pct}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="advisory__panel">
            <h2>Feedback loop</h2>
            <form className="advisory__form" onSubmit={handleSubmit}>
              <label>
                Sentiment
                <select
                  value={feedbackSentiment}
                  onChange={(event) => setFeedbackSentiment(event.target.value)}
                  disabled={isSubmitting}
                >
                  <option value="positive">Positive</option>
                  <option value="neutral">Neutral</option>
                  <option value="negative">Negative</option>
                </select>
              </label>
              <label>
                Notes
                <textarea
                  value={feedbackNotes}
                  onChange={(event) => setFeedbackNotes(event.target.value)}
                  disabled={isSubmitting}
                  rows={3}
                />
              </label>
              <button type="submit" disabled={isSubmitting || feedbackNotes.trim() === ''}>
                {isSubmitting ? 'Submitting…' : 'Record feedback'}
              </button>
            </form>

            <h3>Recent feedback</h3>
            {feedback.length === 0 ? (
              <p className="advisory__empty">No feedback captured yet.</p>
            ) : (
              <ul className="advisory__feedback-list">
                {feedback.map((item) => (
                  <li key={item.id}>
                    <strong>{item.sentiment}</strong> – {item.notes}
                    <div className="advisory__feedback-meta">
                      {new Date(item.created_at).toLocaleString()}{' '}
                      {item.channel ? `· ${item.channel}` : ''}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </AppLayout>
  )
}

export default AgentAdvisoryPage
