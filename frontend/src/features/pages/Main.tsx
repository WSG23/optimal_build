import { useCallback, useEffect, useMemo, useState } from 'react'

import logoSrc from '@/shared/media/optimal-build-logo' // TODO: Replace with proper logo asset
import { ViewportFrame } from '@/components/layout/ViewportFrame'
import Panel from '@/components/layout/Panel'
import { PanelBody } from '@/components/layout/PanelBody'
import PageMiniNav from '@/components/layout/PageMiniNav'
import ClockTicker from '@/shared/components/app/security/ClockTicker'
import { useNoBodyScroll } from '@/shared/hooks/useNoBodyScroll'
import LiveFeedPanel from '@/shared/components/app/security/LiveFeedPanel'
import LeftSidebar from '@/shared/components/app/security/LeftSidebar'
import { IncidentMapView } from '@/shared/components/app/security/IncidentMapView'
import { IncidentDetectionBreakdown } from '@/shared/components/app/security/IncidentDetectionBreakdown'
import IncidentAlertsPanel from '@/shared/components/app/security/IncidentAlertsPanel'
import IncidentResponsePanel from '@/shared/components/app/security/IncidentResponsePanel'
import type {
  Ticket,
  TicketsByStatus,
  ThreatData,
} from '@/shared/components/app/security/types'
import { getSecurityOverview, updateSecurityTicketStatus } from '@/api/security'

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
  const [facilityLabel, setFacilityLabel] = useState<string | null>(null)
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [threatData, setThreatData] = useState<ThreatData | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [selectedLocation, setSelectedLocation] = useState<string | null>(null)

  const refreshOverview = useCallback(
    async (options: { signal?: AbortSignal; showLoading?: boolean } = {}) => {
      const { signal, showLoading = true } = options
      if (showLoading) {
        setLoading(true)
      }
      setLoadError(null)
      try {
        const overview = await getSecurityOverview(undefined, { signal })
        setFacilityLabel(overview.facilityLabel)
        setTickets(overview.tickets)
        setThreatData(overview.threat)
      } catch (error) {
        if (signal?.aborted) {
          return
        }
        console.error('Failed to load security overview', error)
        setLoadError('Unable to load security feed. Please retry.')
      } finally {
        if (showLoading) {
          setLoading(false)
        }
      }
    },
    [],
  )

  useEffect(() => {
    const controller = new AbortController()
    void refreshOverview({ signal: controller.signal })
    return () => controller.abort()
  }, [refreshOverview])

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

  const handleResolve = async (ticket: Ticket) => {
    try {
      const updated = await updateSecurityTicketStatus(
        ticket.id,
        'resolved_harmful',
      )
      setTickets((prev) =>
        prev.map((item) => (item.id === updated.id ? updated : item)),
      )
      void refreshOverview({ showLoading: false })
    } catch (error) {
      console.error('Failed to resolve ticket', error)
    }
  }

  const handleDismiss = async (ticket: Ticket) => {
    try {
      const updated = await updateSecurityTicketStatus(ticket.id, 'dismissed')
      setTickets((prev) =>
        prev.map((item) => (item.id === updated.id ? updated : item)),
      )
      void refreshOverview({ showLoading: false })
    } catch (error) {
      console.error('Failed to dismiss ticket', error)
    }
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

  const facilityHeading = facilityLabel
    ? `Logged in as ${facilityLabel}`
    : 'Facility context unavailable'

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
              {facilityHeading}
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
        {loading && (
          <div className="rounded-md border border-white/10 bg-white/5 px-4 py-2 text-xs uppercase tracking-wide text-white/60">
            Loading security feed…
          </div>
        )}

        <div className="grid flex-1 min-h-0 gap-6 grid-cols-[320px_minmax(0,1fr)_420px] grid-rows-[minmax(0,1fr)_320px]">
          <div className="min-h-0 col-start-1 row-start-1 row-span-2">
            <LeftSidebar
              facilityLabel={facilityLabel ?? 'Facility'}
              threatScore={threatData?.headline_score ?? 0}
              ticketsByStatus={ticketsByStatus}
            />
          </div>

          <section className="min-h-0 col-start-2 row-start-1">
            <Panel title="Floorplan Activity" className="h-full">
              <PanelBody className="h-full p-0">
                {loadError ? (
                  <div className="p-4 text-sm text-red-300">{loadError}</div>
                ) : (
                  <IncidentMapView
                    tickets={tickets}
                    selectedTicket={selectedTicket}
                    onLocationClick={handleLocationClick}
                    selectedLocation={selectedLocation}
                  />
                )}
              </PanelBody>
            </Panel>
          </section>

          <section className="min-h-0 col-start-3 row-start-1">
            <Panel title="Weak-Signal Live Feed" className="h-full">
              <PanelBody className="h-full overflow-y-auto p-3">
                <LiveFeedPanel />
              </PanelBody>
            </Panel>
          </section>

          <section className="min-h-0 col-start-2 col-span-2 row-start-2">
            <div className="grid h-full gap-6 grid-cols-[minmax(0,2.2fr)_minmax(0,1.2fr)]">
              <Panel title="Incident Detection Breakdown" className="h-full">
                <PanelBody className="h-full overflow-y-auto p-4">
                  {loadError ? (
                    <div className="text-sm text-red-300">{loadError}</div>
                  ) : (
                    <IncidentDetectionBreakdown
                      locationFilter={selectedLocation}
                      selectedCategory={selectedCategory}
                      onCategoryClick={handleCategoryClick}
                      ticketId={selectedTicket?.id ?? null}
                      ticketLabel={selectedTicket?.title ?? null}
                      tickets={tickets}
                    />
                  )}
                </PanelBody>
              </Panel>

              <Panel title="Respond & Resolve" className="h-full">
                <PanelBody className="h-full p-3">
                  {loadError ? (
                    <div className="text-sm text-red-300">{loadError}</div>
                  ) : selectedTicket ? (
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
                {loadError ? (
                  <div className="text-sm text-red-300">{loadError}</div>
                ) : (
                  <IncidentAlertsPanel
                    ticketsByStatus={ticketsByStatus}
                    selectedTicket={selectedTicket}
                    onTicketSelect={handleSelectTicket}
                  />
                )}
              </PanelBody>
            </Panel>
          </div>

          <div className="col-span-6">
            <Panel title="Threat Score Breakdown" className="h-full">
              <PanelBody className="h-full p-4">
                <div className="text-5xl font-semibold text-white">
                  {threatData?.headline_score ?? 0}
                </div>
                <p className="mt-2 text-sm text-white/60">
                  {threatData?.entity_id
                    ? `Entity ${threatData.entity_id}`
                    : 'No active entity'}
                </p>
              </PanelBody>
            </Panel>
          </div>
        </section>
      </ViewportFrame>
    </div>
  )
}
