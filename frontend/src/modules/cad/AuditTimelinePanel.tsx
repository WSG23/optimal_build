import type { AuditEvent } from '../../api/client'
import { useTranslation } from '../../i18n'

interface AuditTimelinePanelProps {
  events: AuditEvent[]
  loading?: boolean
}

export function AuditTimelinePanel({
  events,
  loading = false,
}: AuditTimelinePanelProps) {
  const { t } = useTranslation()
  const fallbackDash = t('common.fallback.dash')

  const formatContext = (context: Record<string, unknown> | undefined) => {
    if (!context || Object.keys(context).length === 0) {
      return fallbackDash
    }
    const decisionContext = context as {
      decision?: unknown
      suggestion_id?: unknown
    }
    if (typeof decisionContext.decision === 'string') {
      const identifier = decisionContext.suggestion_id
        ? ` #${decisionContext.suggestion_id}`
        : ''
      return `${decisionContext.decision}${identifier}`
    }
    return Object.entries(context)
      .map(([key, value]) => {
        if (value === null || value === undefined) {
          return `${key}: ${fallbackDash}`
        }
        if (typeof value === 'object') {
          try {
            return `${key}: ${JSON.stringify(value)}`
          } catch (error) {
            return `${key}: ${String(value)}`
          }
        }
        return `${key}: ${String(value)}`
      })
      .join(', ')
  }

  return (
    <section className="cad-panel">
      <h3>{t('panels.auditTitle')}</h3>
      {loading && <p>{t('common.loading')}</p>}
      {!loading && events.length === 0 && <p>{fallbackDash}</p>}
      {!loading && events.length > 0 && (
        <ol className="cad-timeline">
          {events.map((event) => (
            <li key={event.id}>
              <p>
                <strong>{event.eventType}</strong> #{event.id}
              </p>
              <p className="cad-timeline__baseline">
                {event.baselineSeconds !== null
                  ? t('detection.auditBaseline', {
                      minutes: Math.round(event.baselineSeconds / 60),
                    })
                  : t('detection.auditBaseline', { minutes: fallbackDash })}
              </p>
              <p className="cad-timeline__baseline">
                {event.actualSeconds !== null
                  ? t('detection.auditActual', {
                      minutes: Math.round(event.actualSeconds / 60),
                    })
                  : t('detection.auditActual', { minutes: fallbackDash })}
              </p>
              <p className="cad-timeline__baseline">
                {t('detection.auditContext', {
                  text: formatContext(event.context),
                })}
              </p>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}

export default AuditTimelinePanel
