import { useMemo, useState } from 'react'
import { ViewportFrame } from '@/components/layout/ViewportFrame'
import Panel from '@/components/layout/Panel'
import { PanelBody } from '@/components/layout/PanelBody'
import { IncidentAlertsPanel } from '@/shared/components/app/security/IncidentAlertsPanel'
import type { Ticket, TicketsByStatus } from '@/shared/components/app/security/types'
import { TID } from '@/testing/testids'

const sampleTickets: Ticket[] = [
  {
    id: 'TCK-2001',
    title: 'Access control alert',
    description: 'Door forced on Level 3 vestibule.',
    status: 'open',
    location: 'Level 3 Vestibule',
    category: 'Access',
  },
  {
    id: 'TCK-2002',
    title: 'Thermal anomaly',
    description: 'Temperature spike detected in Lab 2.',
    status: 'locked',
    location: 'Lab 2',
    category: 'Thermal',
  },
]

function groupTickets(tickets: Ticket[]): TicketsByStatus {
  return tickets.reduce<TicketsByStatus>(
    (acc, ticket) => {
      acc[ticket.status].push(ticket)
      return acc
    },
    {
      open: [],
      locked: [],
      resolved_harmful: [],
      resolved_malfunction: [],
      resolved_normal: [],
      dismissed: [],
    },
  )
}

export default function TicketingPage() {
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null)
  const ticketsByStatus = useMemo(() => groupTickets(sampleTickets), [])

  return (
    <div className="bg-neutral-950 text-white" data-testid={TID.page.ticketing}>
      <ViewportFrame className="flex h-full flex-col gap-6">
        <Panel title="Ticketing Queue" className="h-full">
          <PanelBody className="h-full overflow-y-auto p-3">
            <IncidentAlertsPanel
              ticketsByStatus={ticketsByStatus}
              selectedTicket={selectedTicket}
              onTicketSelect={setSelectedTicket}
            />
          </PanelBody>
        </Panel>
      </ViewportFrame>
    </div>
  )
}
