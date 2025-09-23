import type {
  BuildableScreeningResponse,
  ClauseRecord,
  DiffRecord,
  DocumentRecord,
  ErgonomicsMetric,
  EntLegalInstrument,
  EntRoadmapItem,
  EntStakeholder,
  EntStudy,
  ProductRecord,
  RuleRecord,
  SourceRecord
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL ?? '/api/v1';

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

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
    fetchJson<{ items: EntRoadmapItem[]; total: number }>(
      `/entitlements/roadmap/${projectId}?limit=100`
    ),
  getStudies: (projectId: number) =>
    fetchJson<{ items: EntStudy[]; total: number }>(
      `/entitlements/studies/${projectId}?limit=100`
    ),
  getStakeholders: (projectId: number) =>
    fetchJson<{ items: EntStakeholder[]; total: number }>(
      `/entitlements/stakeholders/${projectId}?limit=100`
    ),
  getLegal: (projectId: number) =>
    fetchJson<{ items: EntLegalInstrument[]; total: number }>(
      `/entitlements/legal/${projectId}?limit=100`
    )
};
