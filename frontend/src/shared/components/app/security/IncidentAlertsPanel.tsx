import type { FC } from 'react'
import type { Ticket, TicketsByStatus } from './types'

export interface IncidentAlertsPanelProps {
  ticketsByStatus: TicketsByStatus
  selectedTicket: Ticket | null
  onTicketSelect: (ticket: Ticket) => void
}

export const IncidentAlertsPanel: FC<IncidentAlertsPanelProps> = ({
  ticketsByStatus,
  selectedTicket,
  onTicketSelect,
}) => {
  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-2">
      {Object.entries(ticketsByStatus).map(([status, tickets]) => (
        <div key={status}>
          <h3 className="text-xs uppercase tracking-wide text-white/50">
            {status.replace(/_/g, ' ')}
          </h3>
          <ul className="mt-2 space-y-2">
            {tickets.map((ticket) => {
              const isSelected = selectedTicket?.id === ticket.id
              return (
                <li key={ticket.id}>
                  <button
                    type="button"
                    className={`w-full rounded-md border border-white/10 bg-white/5 p-3 text-left text-sm transition-colors hover:bg-white/10 ${
                      isSelected ? 'ring-2 ring-emerald-400/60' : ''
                    }`}
                    onClick={() => onTicketSelect(ticket)}
                  >
                    <div className="font-medium text-white/90">
                      {ticket.title}
                    </div>
                    <div className="text-xs text-white/60">
                      {ticket.description}
                    </div>
                    <div className="mt-1 text-[10px] uppercase tracking-wide text-white/40">
                      {ticket.location}
                    </div>
                  </button>
                </li>
              )
            })}
          </ul>
        </div>
      ))}
    </div>
  )
}

export type { TicketsByStatus }
export default IncidentAlertsPanel
