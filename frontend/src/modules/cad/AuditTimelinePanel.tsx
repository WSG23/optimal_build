import type { AuditEvent } from '../../api/client'
import { useLocale } from '../../i18n/LocaleContext'

interface AuditTimelinePanelProps {
  events: AuditEvent[]
  loading?: boolean
}

export function AuditTimelinePanel({ events, loading = false }: AuditTimelinePanelProps) {
  const { strings } = useLocale()

  return (
    <section className="cad-panel">
      <h3>{strings.panels.auditTitle}</h3>
      {loading && <p>Loading…</p>}
      {!loading && events.length === 0 && <p>—</p>}
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
