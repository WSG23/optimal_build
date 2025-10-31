import type { CommissionEntry, DealSnapshot, StageEvent } from '../types'

interface DealInsightsPanelProps {
  deal: DealSnapshot | null
  timeline: StageEvent[]
  commissions: CommissionEntry[]
}

export function DealInsightsPanel({
  deal,
  timeline,
  commissions,
}: DealInsightsPanelProps) {
  if (!deal) {
    return (
      <div className="bp-deal-panel bp-deal-panel--empty">
        <h2>Select a deal to inspect</h2>
        <p>
          Choose any card in the pipeline to review stage history, commission
          records, and audit metadata.
        </p>
      </div>
    )
  }

  return (
    <div className="bp-deal-panel">
      <header className="bp-deal-panel__header">
        <h2>{deal.title ?? deal.id}</h2>
        <div className="bp-deal-panel__meta">
          <span>Assigned to: {deal.agentName}</span>
          {deal.leadSource && <span>Source: {deal.leadSource}</span>}
          {deal.expectedCloseDate && (
            <span>Expected close: {deal.expectedCloseDate}</span>
          )}
        </div>
      </header>

      <section className="bp-deal-panel__section">
        <h3>Stage timeline</h3>
        <ol className="bp-deal-panel__timeline">
          {timeline.length === 0 && (
            <li className="bp-deal-panel__timeline-empty">
              No stage events yet.
            </li>
          )}
          {timeline.map((event) => (
            <li key={event.id}>
              <div className="bp-deal-panel__timeline-stage">
                <span>{event.toStage.replace('_', ' ')}</span>
                <time>{event.recordedAt}</time>
              </div>
              <div className="bp-deal-panel__timeline-body">
                {event.durationSeconds !== null &&
                  event.durationSeconds !== undefined && (
                    <span>
                      Duration{' '}
                      {Math.round(event.durationSeconds / 3600).toFixed(0)}h
                    </span>
                  )}
                {event.changedBy && <span>By {event.changedBy}</span>}
                {event.note && <p>{event.note}</p>}
                {(event.auditHash || event.auditSignature) && (
                  <p className="bp-deal-panel__timeline-audit">
                    Audit hash: {event.auditHash ?? '—'} <br />
                    Signature: {event.auditSignature ?? '—'}
                  </p>
                )}
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="bp-deal-panel__section">
        <h3>Commission ledger</h3>
        <div className="bp-commission-table">
          <div className="bp-commission-table__header">
            <span>Type</span>
            <span>Status</span>
            <span>Amount</span>
            <span>Updated</span>
          </div>
          {commissions.length === 0 && (
            <div className="bp-commission-table__empty">
              No commission records yet.
            </div>
          )}
          {commissions.map((commission) => (
            <div className="bp-commission-table__row" key={commission.id}>
              <span>{commission.type}</span>
              <span className={`bp-status bp-status--${commission.status}`}>
                {commission.status}
              </span>
              <span>
                {commission.amount !== null
                  ? `${commission.currency} ${commission.amount.toLocaleString()}`
                  : '—'}
              </span>
              <span>{commission.confirmedAt ?? commission.disputedAt ?? '—'}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
