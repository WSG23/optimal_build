import { useMemo, useState } from 'react'
import { ViewportFrame } from '@/components/layout/ViewportFrame'
import Panel from '@/components/layout/Panel'
import { PanelBody } from '@/components/layout/PanelBody'
import { IncidentAlertsPanel } from '@/shared/components/app/security/IncidentAlertsPanel'
import type { Ticket, TicketsByStatus } from '@/shared/components/app/security/types'
import { ZenPageHeader } from './components/ZenPageHeader'
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

  const openCount = ticketsByStatus.open.length
  const lockedCount = ticketsByStatus.locked.length
  const resolvedCount =
    ticketsByStatus.resolved_harmful.length +
    ticketsByStatus.resolved_malfunction.length +
    ticketsByStatus.resolved_normal.length

  return (
    <div className="bg-neutral-950 text-white" data-testid={TID.page.ticketing}>
      <ViewportFrame className="flex h-full flex-col gap-6">
        <ZenPageHeader title="Ticketing" />
        <div
          className="grid flex-1 min-h-0 gap-6"
          style={{ gridTemplateColumns: 'minmax(0,1fr) minmax(0,1.4fr) minmax(0,1fr)' }}
        >
          <div className="min-h-0" style={{ gridColumn: '1', gridRow: '1' }}>
            <Panel title="Queue Overview" className="h-full">
              <PanelBody className="flex h-full flex-col gap-3 p-4 text-sm text-white/70">
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs">
                  <p className="font-semibold text-white/80">Open</p>
                  <p>{openCount}</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs">
                  <p className="font-semibold text-white/80">Locked</p>
                  <p>{lockedCount}</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs">
                  <p className="font-semibold text-white/80">Resolved (24h)</p>
                  <p>{resolvedCount}</p>
                </div>
                <p className="mt-auto text-xs">
                  Ticket transitions respect host-defined workflows and escalate automatically to compliance when tagged.
                </p>
              </PanelBody>
            </Panel>
          </div>
          <div className="min-h-0" style={{ gridColumn: '2', gridRow: '1 / span 2' }}>
            <Panel title="Ticketing Queue" className="h-full">
              <PanelBody className="h-full overflow-y-auto p-3">
                <IncidentAlertsPanel
                  ticketsByStatus={ticketsByStatus}
                  selectedTicket={selectedTicket}
                  onTicketSelect={setSelectedTicket}
                />
              </PanelBody>
            </Panel>
          </div>
          <div className="min-h-0" style={{ gridColumn: '1', gridRow: '2' }}>
            <Panel title="Resolution Playbooks" className="h-full">
              <PanelBody className="grid h-full grid-cols-1 gap-3 p-4 text-xs text-white/70">
                <div className="rounded border border-white/10 bg-white/5 p-3">
                  <p className="font-semibold text-white/80">Access Control</p>
                  <p>Lockdown + manual badge audit triggered when severity ≥ medium.</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3">
                  <p className="font-semibold text-white/80">Thermal</p>
                  <p>Notify facilities team and cross-check with mission logs.</p>
                </div>
              </PanelBody>
            </Panel>
          </div>
          <div className="min-h-0" style={{ gridColumn: '3', gridRow: '1 / span 2' }}>
            <Panel title="Linked Workstreams" className="h-full">
              <PanelBody className="flex h-full flex-col gap-3 p-4 text-sm text-white/70">
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs">
                  <p className="font-semibold text-white/80">Mission Control</p>
                  <p>Live incident cards mirrored in operations view.</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs">
                  <p className="font-semibold text-white/80">Compliance</p>
                  <p>Flagged tickets sync to violations dashboard when policy tags present.</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs">
                  <p className="font-semibold text-white/80">Analytics</p>
                  <p>Resolution times contribute to SLA tracking.</p>
                </div>
              </PanelBody>
            </Panel>
          </div>
        </div>
      </ViewportFrame>
    </div>
  )
}
