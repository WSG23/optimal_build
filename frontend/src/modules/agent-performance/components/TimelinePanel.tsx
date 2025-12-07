import type { DealStage, DealTimelineEvent } from '../types'
import { formatDate, formatDuration } from '../utils/formatters'

interface TimelinePanelProps {
  events: DealTimelineEvent[]
  loading: boolean
  locale: string
  fallbackText: string
  loadingText: string
  auditLabel: string
  durationLabel: string
  changedByLabel: string
  noteLabel: string
  hashLabel: string
  signatureLabel: string
  stageLabelFor: (stage: DealStage) => string
}

export function TimelinePanel({
  events,
  loading,
  locale,
  fallbackText,
  loadingText,
  auditLabel,
  durationLabel,
  changedByLabel,
  noteLabel,
  hashLabel,
  signatureLabel,
  stageLabelFor,
}: TimelinePanelProps) {
  if (loading) {
    return <p className="agent-performance__timeline-loading">{loadingText}</p>
  }

  if (events.length === 0) {
    return <p className="agent-performance__timeline-empty">{fallbackText}</p>
  }

  return (
    <ol className="agent-performance__timeline-list">
      {events.map((event) => (
        <li key={event.id} className="agent-performance__timeline-item">
          <header>
            <span className="agent-performance__timeline-stage">
              {stageLabelFor(event.toStage)}
            </span>
            <span className="agent-performance__timeline-date">
              {formatDate(event.recordedAt, locale) || fallbackText}
            </span>
          </header>
          <dl>
            <div>
              <dt>{durationLabel}</dt>
              <dd>{formatDuration(event.durationSeconds, fallbackText)}</dd>
            </div>
            <div>
              <dt>{changedByLabel}</dt>
              <dd>{event.changedBy ?? fallbackText}</dd>
            </div>
            <div>
              <dt>{noteLabel}</dt>
              <dd>{event.note ?? fallbackText}</dd>
            </div>
            <div>
              <dt>{auditLabel}</dt>
              <dd>
                {event.auditLog ? (
                  <div className="agent-performance__audit">
                    <p>
                      <strong>{hashLabel}</strong>{' '}
                      <span>{event.auditLog.hash}</span>
                    </p>
                    <p>
                      <strong>{signatureLabel}</strong>{' '}
                      <span>{event.auditLog.signature}</span>
                    </p>
                  </div>
                ) : (
                  fallbackText
                )}
              </dd>
            </div>
          </dl>
        </li>
      ))}
    </ol>
  )
}
