import type { AuditEvent } from '../../api/client'
import { useTranslation } from '../../i18n'

interface AuditTimelinePanelProps {
  events: AuditEvent[]
  loading?: boolean
}

export function AuditTimelinePanel({ events, loading = false }: AuditTimelinePanelProps) {
  const { t } = useTranslation()
  const fallbackDash = t('common.fallback.dash')

  return (
    <section className="cad-panel">
      <h3>{t('panels.auditTitle')}</h3>
      {loading && <p>{t('common.loading')}</p>}
      {!loading && events.length === 0 && <p>{fallbackDash}</p>}
      {!loading && events.length > 0 && (
        <ol className="cad-timeline">
          {events.map((event) => (
            <li key={event.ruleId}>
              <p>
                <strong>#{event.ruleId}</strong> {event.updated}
              </p>
              <p className="cad-timeline__baseline">{event.baseline}</p>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}

export default AuditTimelinePanel
