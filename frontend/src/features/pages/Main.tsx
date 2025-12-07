import { useMemo, useState } from 'react'

import logoSrc from '@/shared/media/yosai-logo' // TODO: Replace with proper logo asset
import { ViewportFrame } from '@/components/layout/ViewportFrame'
import Panel from '@/components/layout/Panel'
import { PanelBody } from '@/components/layout/PanelBody'
import PageMiniNav from '@/components/layout/PageMiniNav'
import ClockTicker from '@/shared/components/app/security/ClockTicker'
import { useNoBodyScroll } from '@/shared/hooks/useNoBodyScroll'
import { useFacilityLabel } from '@/shared/hooks/useFacilityLabel'
import LiveFeedPanel from '@/shared/components/app/security/LiveFeedPanel'
import LeftSidebar from '@/shared/components/app/security/LeftSidebar'
import { IncidentMapView } from '@/shared/components/app/security/IncidentMapView'
import { IncidentDetectionBreakdown } from '@/shared/components/app/security/IncidentDetectionBreakdown'
import IncidentAlertsPanel from '@/shared/components/app/security/IncidentAlertsPanel'
import IncidentResponsePanel from '@/shared/components/app/security/IncidentResponsePanel'
import type {
  Ticket,
  TicketsByStatus,
} from '@/shared/components/app/security/types'

const initialTickets: Ticket[] = [
  {
    id: 'TCK-1001',
    title: 'Loading Dock Access',
    description: 'Unauthorized badge scan detected at loading dock B.',
    status: 'open',
    location: 'Loading Dock B',
    category: 'Access Control',
  },
  {
    id: 'TCK-1002',
    title: 'Server Room Motion',
    description: 'Motion sensor triggered after hours in server room.',
    status: 'locked',
    location: 'Server Room',
    category: 'Motion',
  },
  {
    id: 'TCK-1003',
    title: 'Thermal Spike',
    description: 'Thermal anomaly detected in Laboratory 4.',
    status: 'resolved_malfunction',
    location: 'Laboratory 4',
    category: 'Environmental',
  },
  {
    id: 'TCK-1004',
    title: 'Fire Door Forced',
    description: 'Fire door on Level 2 forced open for 90 seconds.',
    status: 'resolved_normal',
    location: 'Level 2 - Fire Exit',
    category: 'Access Control',
  },
  {
    id: 'TCK-1005',
    title: 'Network Intrusion Alert',
    description: 'IDS flagged suspicious outbound traffic.',
    status: 'dismissed',
    location: 'Operations Center',
    category: 'Network',
  },
]

function computeTicketsByStatus(tickets: Ticket[]): TicketsByStatus {
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

export default function Main() {
  useNoBodyScroll()
  const facilityLabel = useFacilityLabel()
  const [tickets, setTickets] = useState<Ticket[]>(initialTickets)
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [selectedLocation, setSelectedLocation] = useState<string | null>(null)

  const ticketsByStatus = useMemo(
    () => computeTicketsByStatus(tickets),
    [tickets],
  )
  const selectedTicket =
    tickets.find((ticket) => ticket.id === selectedTicketId) ?? null

  const handleSelectTicket = (ticket: Ticket) => {
    setSelectedTicketId(ticket.id)
    setSelectedLocation(ticket.location)
    setSelectedCategory(ticket.category)
  }

  const handleResolve = (ticket: Ticket) => {
    setTickets((prev) =>
      prev.map((item) =>
        item.id === ticket.id ? { ...item, status: 'resolved_harmful' } : item,
      ),
    )
  }

  const handleDismiss = (ticket: Ticket) => {
    setTickets((prev) =>
      prev.map((item) =>
        item.id === ticket.id ? { ...item, status: 'dismissed' } : item,
      ),
    )
  }

  const handleClose = () => {
    setSelectedTicketId(null)
  }

  const handleLocationClick = (location: string) => {
    setSelectedLocation((current) => (current === location ? null : location))
  }

  const handleCategoryClick = (category: string) => {
    setSelectedCategory((current) => (current === category ? null : category))
  }

  const threatData = {
    entity_id: 'ENTITY-001',
    headline_score: 72,
  }

  return (
    <div className="bg-neutral-950 text-white">
      <ViewportFrame className="flex h-full flex-col gap-6">
        <header className="mb-4 grid grid-cols-12 items-center gap-6">
          <div className="col-span-3 flex items-center gap-3">
            <img
              src={logoSrc}
              alt="Optimal Build"
              className="h-7 select-none"
            />
          </div>
          <div className="col-span-6">
            <h1 className="text-center text-2xl font-semibold">
              Logged in as {facilityLabel}
            </h1>
          </div>
          <div className="col-span-3 flex items-center justify-end gap-4">
            <PageMiniNav
              items={[
                { label: 'Export', to: '/export' },
                { label: 'Mission Control', to: '/mission' },
                { label: 'Mapping', to: '/mapping' },
                { label: 'Compliance', to: '/compliance' },
                { label: 'Settings', to: '/settings' },
                { label: 'Reports', to: '/reports' },
              ]}
            />
            <ClockTicker />
          </div>
        </header>

        <div
          className="grid flex-1 min-h-0 gap-6"
          style={{
            gridTemplateColumns: '320px minmax(0,1fr) 420px',
            gridTemplateRows: 'minmax(0,1fr) 320px',
          }}
        >
          <div
            className="min-h-0"
            style={{ gridColumn: '1', gridRow: '1 / span 2' }}
          >
            <LeftSidebar
              facilityLabel={facilityLabel}
              threatScore={threatData.headline_score}
              ticketsByStatus={ticketsByStatus}
            />
          </div>

          <section
            className="min-h-0"
            style={{ gridColumn: '2', gridRow: '1' }}
          >
            <Panel title="Floorplan Activity" className="h-full">
              <PanelBody className="h-full p-0">
                <IncidentMapView
                  tickets={tickets}
                  selectedTicket={selectedTicket}
                  onLocationClick={handleLocationClick}
                  selectedLocation={selectedLocation}
                />
              </PanelBody>
            </Panel>
          </section>

          <section
            className="min-h-0"
            style={{ gridColumn: '3', gridRow: '1' }}
          >
            <Panel title="Weak-Signal Live Feed" className="h-full">
              <PanelBody className="h-full overflow-y-auto p-3">
                <LiveFeedPanel />
              </PanelBody>
            </Panel>
          </section>

          <section
            className="min-h-0"
            style={{ gridColumn: '2 / span 2', gridRow: '2' }}
          >
            <div
              className="grid h-full gap-6"
              style={{ gridTemplateColumns: 'minmax(0,2.2fr) minmax(0,1.2fr)' }}
            >
              <Panel title="Incident Detection Breakdown" className="h-full">
                <PanelBody className="h-full overflow-y-auto p-4">
                  <IncidentDetectionBreakdown
                    locationFilter={selectedLocation}
                    selectedCategory={selectedCategory}
                    onCategoryClick={handleCategoryClick}
                    ticketId={selectedTicket?.id ?? null}
                    ticketLabel={selectedTicket?.title ?? null}
                    tickets={tickets}
                  />
                </PanelBody>
              </Panel>

              <Panel title="Respond & Resolve" className="h-full">
                <PanelBody className="h-full p-3">
                  {selectedTicket ? (
                    <IncidentResponsePanel
                      ticket={selectedTicket}
                      onResolve={handleResolve}
                      onDismiss={handleDismiss}
                      onClose={handleClose}
                    />
                  ) : (
                    <div className="text-sm text-white/60">
                      Select a ticket to coordinate a response.
                    </div>
                  )}
                </PanelBody>
              </Panel>
            </div>
          </section>
        </div>

        <section className="grid min-h-0 grid-cols-12 gap-6">
          <div className="col-span-6">
            <Panel title="Incident Alerts" className="h-full">
              <PanelBody className="h-full overflow-y-auto p-3">
                <IncidentAlertsPanel
                  ticketsByStatus={ticketsByStatus}
                  selectedTicket={selectedTicket}
                  onTicketSelect={handleSelectTicket}
                />
              </PanelBody>
            </Panel>
          </div>

          <div className="col-span-6">
            <Panel title="Threat Score Breakdown" className="h-full">
              <PanelBody className="h-full p-4">
                <div className="text-5xl font-semibold text-white">
                  {threatData.headline_score}
                </div>
                <p className="mt-2 text-sm text-white/60">
                  Entity {threatData.entity_id}
                </p>
              </PanelBody>
            </Panel>
          </div>
        </section>
      </ViewportFrame>
    </div>
  )
}
