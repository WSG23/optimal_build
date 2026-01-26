import type {
  Ticket,
  TicketStatus,
  ThreatData,
} from '../shared/components/app/security/types'
import { getJson, patchJson, type RequestOptions } from './utils/request'

interface SecurityOverviewResponse {
  facility_label?: string | null
  project_id?: string | null
  tickets?: Ticket[]
  threat?: ThreatData
}

interface SecurityTicketResponse {
  id: string
  project_id?: string | null
  title: string
  description: string
  status: TicketStatus
  location: string
  category: string
  created_at: string
  updated_at: string
}

export interface SecurityOverview {
  facilityLabel: string | null
  projectId: string | null
  tickets: Ticket[]
  threat: ThreatData
}

function mapTicket(payload: SecurityTicketResponse): Ticket {
  return {
    id: String(payload.id ?? '').trim(),
    title: payload.title ?? '',
    description: payload.description ?? '',
    status: payload.status,
    location: payload.location ?? '',
    category: payload.category ?? '',
  }
}

export async function getSecurityOverview(
  projectId?: string,
  options: RequestOptions = {},
): Promise<SecurityOverview> {
  const params = new URLSearchParams()
  if (projectId) {
    params.set('project_id', projectId)
  }
  const path = params.toString()
    ? `/api/v1/security/overview?${params.toString()}`
    : '/api/v1/security/overview'

  const payload = await getJson<SecurityOverviewResponse>(path, options)
  const threat = payload.threat ?? { entity_id: null, headline_score: 0 }
  return {
    facilityLabel: payload.facility_label ?? null,
    projectId: payload.project_id ?? null,
    tickets: (payload.tickets ?? []).map(mapTicket),
    threat,
  }
}

export async function updateSecurityTicketStatus(
  ticketId: string,
  status: TicketStatus,
): Promise<Ticket> {
  const payload = await patchJson<SecurityTicketResponse>(
    `/api/v1/security/tickets/${ticketId}`,
    { status },
  )
  return mapTicket(payload)
}
