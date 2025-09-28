import type {
  BuildableScreeningResponse,
  ClauseRecord,
  DiffRecord,
  DocumentRecord,
  EntEngagementRecord,
  EntLegalInstrumentRecord,
  EntRoadmapItemRecord,
  EntStudyRecord,
  ErgonomicsMetric,
  PaginatedResponse,
  ProductRecord,
  RuleRecord,
  SourceRecord,
} from '../types'

const API_BASE = import.meta.env.VITE_API_URL ?? '/api/v1'

const encodeParam = (value: number | string): string =>
  encodeURIComponent(String(value))

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const defaultHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  const headers = new Headers(defaultHeaders)
  if (init?.headers) {
    if (init.headers instanceof Headers) {
      init.headers.forEach((value, key) => {
        headers.set(key, value)
      })
    } else if (Array.isArray(init.headers)) {
      for (const [key, value] of init.headers) {
        headers.set(key, value)
      }
    } else {
      for (const [key, value] of Object.entries(init.headers)) {
        if (typeof value === 'string') {
          headers.set(key, value)
        }
      }
    }
  }
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  })
  if (!response.ok) {
    const message = await response.text()
    throw new Error(
      message || `Request failed with status ${response.status.toString()}`,
    )
  }
  return response.json() as Promise<T>
}

const ADMIN_HEADERS = { 'X-Role': 'admin' }

export const ReviewAPI = {
  getSources: () => fetchJson<{ items: SourceRecord[] }>('/review/sources'),
  getDocuments: (sourceId?: number) =>
    fetchJson<{ items: DocumentRecord[] }>(
      sourceId
        ? `/review/documents?source_id=${encodeParam(sourceId)}`
        : '/review/documents',
    ),
  getClauses: (documentId?: number) =>
    fetchJson<{ items: ClauseRecord[] }>(
      documentId
        ? `/review/clauses?document_id=${encodeParam(documentId)}`
        : '/review/clauses',
    ),
  getRules: () => fetchJson<{ items: RuleRecord[] }>('/rules'),
  reviewRule: (
    ruleId: number,
    action: 'approve' | 'reject' | 'publish',
    notes?: string,
  ) =>
    fetchJson<{ item: RuleRecord }>(`/rules/${encodeParam(ruleId)}/review`, {
      method: 'POST',
      body: JSON.stringify({ action, notes }),
    }),
  getDiffs: (ruleId?: number) =>
    fetchJson<{ items: DiffRecord[] }>(
      ruleId ? `/review/diffs?rule_id=${encodeParam(ruleId)}` : '/review/diffs',
    ),
  screenBuildable: (payload: {
    address?: string
    geometry?: object
    defaults?: object
  }) =>
    fetchJson<BuildableScreeningResponse>('/screen/buildable', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  getProducts: () => fetchJson<{ items: ProductRecord[] }>('/products/'),
  getErgonomics: () => fetchJson<{ items: ErgonomicsMetric[] }>('/ergonomics/'),
}

export const EntitlementsAPI = {
  getRoadmap: (projectId: number) =>
    fetchJson<PaginatedResponse<EntRoadmapItemRecord>>(
      `/entitlements/${encodeParam(projectId)}/roadmap?limit=200`,
    ),
  updateRoadmap: (
    projectId: number,
    itemId: number,
    payload: Partial<EntRoadmapItemRecord>,
  ) =>
    fetchJson<EntRoadmapItemRecord>(
      `/entitlements/${encodeParam(projectId)}/roadmap/${encodeParam(itemId)}`,
      {
        method: 'PUT',
        headers: ADMIN_HEADERS,
        body: JSON.stringify(payload),
      },
    ),
  getStudies: (projectId: number) =>
    fetchJson<PaginatedResponse<EntStudyRecord>>(
      `/entitlements/${encodeParam(projectId)}/studies?limit=200`,
    ),
  createStudy: (projectId: number, payload: Partial<EntStudyRecord>) =>
    fetchJson<EntStudyRecord>(
      `/entitlements/${encodeParam(projectId)}/studies`,
      {
        method: 'POST',
        headers: ADMIN_HEADERS,
        body: JSON.stringify(payload),
      },
    ),
  updateStudy: (
    projectId: number,
    studyId: number,
    payload: Partial<EntStudyRecord>,
  ) =>
    fetchJson<EntStudyRecord>(
      `/entitlements/${encodeParam(projectId)}/studies/${encodeParam(studyId)}`,
      {
        method: 'PUT',
        headers: ADMIN_HEADERS,
        body: JSON.stringify(payload),
      },
    ),
  getStakeholders: (projectId: number) =>
    fetchJson<PaginatedResponse<EntEngagementRecord>>(
      `/entitlements/${encodeParam(projectId)}/stakeholders?limit=200`,
    ),
  createStakeholder: (
    projectId: number,
    payload: Partial<EntEngagementRecord>,
  ) =>
    fetchJson<EntEngagementRecord>(
      `/entitlements/${encodeParam(projectId)}/stakeholders`,
      {
        method: 'POST',
        headers: ADMIN_HEADERS,
        body: JSON.stringify(payload),
      },
    ),
  updateStakeholder: (
    projectId: number,
    stakeholderId: number,
    payload: Partial<EntEngagementRecord>,
  ) =>
    fetchJson<EntEngagementRecord>(
      `/entitlements/${encodeParam(projectId)}/stakeholders/${encodeParam(
        stakeholderId,
      )}`,
      {
        method: 'PUT',
        headers: ADMIN_HEADERS,
        body: JSON.stringify(payload),
      },
    ),
  getLegalInstruments: (projectId: number) =>
    fetchJson<PaginatedResponse<EntLegalInstrumentRecord>>(
      `/entitlements/${encodeParam(projectId)}/legal?limit=200`,
    ),
  createLegalInstrument: (
    projectId: number,
    payload: Partial<EntLegalInstrumentRecord>,
  ) =>
    fetchJson<EntLegalInstrumentRecord>(
      `/entitlements/${encodeParam(projectId)}/legal`,
      {
        method: 'POST',
        headers: ADMIN_HEADERS,
        body: JSON.stringify(payload),
      },
    ),
  updateLegalInstrument: (
    projectId: number,
    instrumentId: number,
    payload: Partial<EntLegalInstrumentRecord>,
  ) =>
    fetchJson<EntLegalInstrumentRecord>(
      `/entitlements/${encodeParam(projectId)}/legal/${encodeParam(
        instrumentId,
      )}`,
      {
        method: 'PUT',
        headers: ADMIN_HEADERS,
        body: JSON.stringify(payload),
      },
    ),
}
