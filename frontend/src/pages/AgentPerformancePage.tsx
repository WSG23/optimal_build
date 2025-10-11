import { useEffect, useMemo, useState } from 'react'
import { AppLayout } from '../App'
import { useTranslation } from '../i18n'
import {
  DEAL_STAGE_ORDER,
  type DealStage,
  type DealSummary,
  type DealTimelineEvent,
  fetchDealTimeline,
  fetchDeals,
} from '../api/deals'

function formatDuration(seconds: number | null, fallback: string): string {
  if (seconds === null || Number.isNaN(seconds)) {
    return fallback
  }
  if (seconds < 60) {
    return `${Math.round(seconds)}s`
  }
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) {
    return `${minutes}m`
  }
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  if (hours < 24) {
    return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`
  }
  const days = Math.floor(hours / 24)
  const remainingHours = hours % 24
  return remainingHours > 0
    ? `${days}d ${remainingHours}h`
    : `${days}d`
}

function formatDate(value: string, locale: string): string {
  if (!value) {
    return ''
  }
  try {
    const formatter = new Intl.DateTimeFormat(locale, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
    return formatter.format(new Date(value))
  } catch (error) {
    console.warn('Failed to format date', error)
    return value
  }
}

const STAGE_TRANSLATION_KEYS: Record<DealStage, string> = {
  lead_captured: 'agentPerformance.stages.lead_captured',
  qualification: 'agentPerformance.stages.qualification',
  needs_analysis: 'agentPerformance.stages.needs_analysis',
  proposal: 'agentPerformance.stages.proposal',
  negotiation: 'agentPerformance.stages.negotiation',
  agreement: 'agentPerformance.stages.agreement',
  due_diligence: 'agentPerformance.stages.due_diligence',
  awaiting_closure: 'agentPerformance.stages.awaiting_closure',
  closed_won: 'agentPerformance.stages.closed_won',
  closed_lost: 'agentPerformance.stages.closed_lost',
}

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
}

function TimelinePanel({
  events,
  loading,
  locale,
  fallbackText,
  auditLabel,
  durationLabel,
  changedByLabel,
  noteLabel,
  hashLabel,
  signatureLabel,
  stageLabelFor,
}: TimelinePanelProps & {
  stageLabelFor: (stage: DealStage) => string
}) {
  if (loading) {
    return (
      <p className="agent-performance__timeline-loading">{loadingText}</p>
    )
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

function groupDealsByStage(deals: DealSummary[]): Record<DealStage, DealSummary[]> {
  return deals.reduce<Record<DealStage, DealSummary[]>>((acc, deal) => {
    const stage = deal.pipelineStage
    const bucket = acc[stage] ?? []
    bucket.push(deal)
    acc[stage] = bucket
    return acc
  }, {} as Record<DealStage, DealSummary[]>)
}

export default function AgentPerformancePage() {
  const { t, i18n } = useTranslation()
  const locale = i18n.language
  const [deals, setDeals] = useState<DealSummary[]>([])
  const [loadingDeals, setLoadingDeals] = useState<boolean>(false)
  const [dealError, setDealError] = useState<string | null>(null)
  const [selectedDealId, setSelectedDealId] = useState<string | null>(null)
  const [timeline, setTimeline] = useState<DealTimelineEvent[]>([])
  const [timelineLoading, setTimelineLoading] = useState<boolean>(false)
  const [timelineError, setTimelineError] = useState<string | null>(null)

  useEffect(() => {
    let abort = new AbortController()
    setLoadingDeals(true)
    setDealError(null)
    fetchDeals(abort.signal)
      .then((payload) => {
        setDeals(payload)
        if (payload.length > 0) {
          setSelectedDealId(payload[0].id)
        }
      })
      .catch((error: unknown) => {
        console.error('Failed to load deals', error)
        setDealError(t('agentPerformance.errors.loadDeals'))
      })
      .finally(() => {
        setLoadingDeals(false)
      })
    return () => {
      abort.abort()
    }
  }, [t])

  useEffect(() => {
    if (!selectedDealId) {
      setTimeline([])
      return
    }
    let abort = new AbortController()
    setTimelineLoading(true)
    setTimelineError(null)
    fetchDealTimeline(selectedDealId, abort.signal)
      .then((events) => {
        setTimeline(events)
      })
      .catch((error: unknown) => {
        console.error('Failed to load timeline', error)
        setTimelineError(t('agentPerformance.errors.loadTimeline'))
      })
      .finally(() => {
        setTimelineLoading(false)
      })
    return () => {
      abort.abort()
    }
  }, [selectedDealId, t])

  const groupedDeals = useMemo(() => groupDealsByStage(deals), [deals])

  const fallbackText = t('agentPerformance.common.fallback')
  const auditLabel = t('agentPerformance.timeline.auditLabel')
  const durationLabel = t('agentPerformance.timeline.durationLabel')
  const changedByLabel = t('agentPerformance.timeline.changedBy')
  const noteLabel = t('agentPerformance.timeline.note')
  const hashLabel = t('agentPerformance.timeline.hash')
  const signatureLabel = t('agentPerformance.timeline.signature')
  const loadingText = t('common.loading')

  return (
    <AppLayout
      title={t('agentPerformance.title')}
      subtitle={t('agentPerformance.subtitle')}
    >
      <div className="agent-performance">
        <section className="agent-performance__kanban">
          {dealError && (
            <p className="agent-performance__error agent-performance__error--inline">
              {dealError}
            </p>
          )}
          {DEAL_STAGE_ORDER.map((stage) => {
            const items = groupedDeals[stage] ?? []
            const label =
              t(STAGE_TRANSLATION_KEYS[stage]) ?? STAGE_TRANSLATION_KEYS[stage]
            return (
              <article key={stage} className="agent-performance__column">
                <header>
                  <h3>{label}</h3>
                  <span className="agent-performance__count">
                    {items.length}
                  </span>
                </header>
                {loadingDeals && (
                  <p className="agent-performance__column-placeholder">
                    {t('common.loading')}
                  </p>
                )}
                {!loadingDeals && items.length === 0 && (
                  <p className="agent-performance__column-placeholder">
                    {fallbackText}
                  </p>
                )}
                <ul>
                  {items.map((deal) => {
                    const isSelected = selectedDealId === deal.id
                    return (
                      <li key={deal.id}>
                        <button
                          type="button"
                          className={`agent-performance__deal${
                            isSelected
                              ? ' agent-performance__deal--selected'
                              : ''
                          }`}
                          onClick={() => setSelectedDealId(deal.id)}
                        >
                          <strong>{deal.title}</strong>
                          {deal.leadSource && (
                            <span>{deal.leadSource}</span>
                          )}
                          {deal.estimatedValueAmount !== null && (
                            <span>
                              {deal.estimatedValueCurrency}{' '}
                              {deal.estimatedValueAmount.toLocaleString(locale)}
                            </span>
                          )}
                        </button>
                      </li>
                    )
                  })}
                </ul>
              </article>
            )
          })}
        </section>
        <aside className="agent-performance__timeline">
          {dealError && (
            <p className="agent-performance__error">{dealError}</p>
          )}
          {timelineError && !timelineLoading && (
            <p className="agent-performance__error">{timelineError}</p>
          )}
          {!dealError && (
            <TimelinePanel
              events={timeline}
              loading={timelineLoading}
              locale={locale}
              fallbackText={fallbackText}
              loadingText={loadingText}
              auditLabel={auditLabel}
              durationLabel={durationLabel}
              changedByLabel={changedByLabel}
              noteLabel={noteLabel}
              hashLabel={hashLabel}
              signatureLabel={signatureLabel}
              stageLabelFor={(stage) =>
                t(STAGE_TRANSLATION_KEYS[stage]) ?? stage
              }
            />
          )}
        </aside>
      </div>
    </AppLayout>
  )
}
