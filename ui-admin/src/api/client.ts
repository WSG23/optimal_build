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
  SourceRecord
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL ?? '/api/v1';

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const defaultHeaders: Record<string, string> = { 'Content-Type': 'application/json' };
  let headers: HeadersInit = defaultHeaders;
  if (init?.headers) {
    if (init.headers instanceof Headers) {
      const merged = new Headers(defaultHeaders);
      init.headers.forEach((value, key) => merged.set(key, value));
      headers = merged;
    } else {
      headers = { ...defaultHeaders, ...(init.headers as Record<string, string>) };
    }
  }
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

const ADMIN_HEADERS = { 'X-Role': 'admin' };

export const ReviewAPI = {
  getSources: () => fetchJson<{ items: SourceRecord[] }>('/review/sources'),
  getDocuments: (sourceId?: number) =>
    fetchJson<{ items: DocumentRecord[] }>(
      sourceId ? `/review/documents?source_id=${sourceId}` : '/review/documents'
    ),
  getClauses: (documentId?: number) =>
    fetchJson<{ items: ClauseRecord[] }>(
      documentId ? `/review/clauses?document_id=${documentId}` : '/review/clauses'
    ),
  getRules: () => fetchJson<{ items: RuleRecord[] }>('/rules'),
  reviewRule: (ruleId: number, action: 'approve' | 'reject' | 'publish', notes?: string) =>
    fetchJson<{ item: RuleRecord }>(`/rules/${ruleId}/review`, {
      method: 'POST',
      body: JSON.stringify({ action, notes })
    }),
  getDiffs: (ruleId?: number) =>
    fetchJson<{ items: DiffRecord[] }>(ruleId ? `/review/diffs?rule_id=${ruleId}` : '/review/diffs'),
  screenBuildable: (payload: { address?: string; geometry?: object; defaults?: object }) =>
    fetchJson<BuildableScreeningResponse>('/screen/buildable', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  getProducts: () => fetchJson<{ items: ProductRecord[] }>('/products/'),
  getErgonomics: () => fetchJson<{ items: ErgonomicsMetric[] }>('/ergonomics/')
};

export const EntitlementsAPI = {
  getRoadmap: (projectId: number) =>
    fetchJson<PaginatedResponse<EntRoadmapItemRecord>>(
      `/entitlements/${projectId}/roadmap?limit=200`
    ),
  updateRoadmap: (projectId: number, itemId: number, payload: Partial<EntRoadmapItemRecord>) =>
    fetchJson<EntRoadmapItemRecord>(`/entitlements/${projectId}/roadmap/${itemId}`, {
      method: 'PUT',
      headers: ADMIN_HEADERS,
      body: JSON.stringify(payload)
    }),
  getStudies: (projectId: number) =>
    fetchJson<PaginatedResponse<EntStudyRecord>>(`/entitlements/${projectId}/studies?limit=200`),
  createStudy: (projectId: number, payload: Partial<EntStudyRecord>) =>
    fetchJson<EntStudyRecord>(`/entitlements/${projectId}/studies`, {
      method: 'POST',
      headers: ADMIN_HEADERS,
      body: JSON.stringify(payload)
    }),
  updateStudy: (projectId: number, studyId: number, payload: Partial<EntStudyRecord>) =>
    fetchJson<EntStudyRecord>(`/entitlements/${projectId}/studies/${studyId}`, {
      method: 'PUT',
      headers: ADMIN_HEADERS,
      body: JSON.stringify(payload)
    }),
  getStakeholders: (projectId: number) =>
    fetchJson<PaginatedResponse<EntEngagementRecord>>(
      `/entitlements/${projectId}/stakeholders?limit=200`
    ),
  createStakeholder: (projectId: number, payload: Partial<EntEngagementRecord>) =>
    fetchJson<EntEngagementRecord>(`/entitlements/${projectId}/stakeholders`, {
      method: 'POST',
      headers: ADMIN_HEADERS,
      body: JSON.stringify(payload)
    }),
  updateStakeholder: (
    projectId: number,
    stakeholderId: number,
    payload: Partial<EntEngagementRecord>
  ) =>
    fetchJson<EntEngagementRecord>(
      `/entitlements/${projectId}/stakeholders/${stakeholderId}`,
      {
        method: 'PUT',
        headers: ADMIN_HEADERS,
        body: JSON.stringify(payload)
      }
    ),
  getLegalInstruments: (projectId: number) =>
    fetchJson<PaginatedResponse<EntLegalInstrumentRecord>>(
      `/entitlements/${projectId}/legal?limit=200`
    ),
  createLegalInstrument: (projectId: number, payload: Partial<EntLegalInstrumentRecord>) =>
    fetchJson<EntLegalInstrumentRecord>(`/entitlements/${projectId}/legal`, {
      method: 'POST',
      headers: ADMIN_HEADERS,
      body: JSON.stringify(payload)
    }),
  updateLegalInstrument: (
    projectId: number,
    instrumentId: number,
    payload: Partial<EntLegalInstrumentRecord>
  ) =>
    fetchJson<EntLegalInstrumentRecord>(
      `/entitlements/${projectId}/legal/${instrumentId}`,
      {
        method: 'PUT',
        headers: ADMIN_HEADERS,
        body: JSON.stringify(payload)
      }
    )
};
