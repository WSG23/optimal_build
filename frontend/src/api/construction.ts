/**
 * Construction Management API Client (Phase 2G)
 *
 * Provides type-safe access to:
 * - Contractor management
 * - Quality inspections
 * - Safety incidents
 * - Drawdown requests
 */

import { api } from './client'

// Enums matching backend
export type ContractorType =
  | 'general_contractor'
  | 'sub_contractor'
  | 'specialist'
  | 'consultant'
  | 'supplier'

export type InspectionStatus =
  | 'scheduled'
  | 'passed'
  | 'failed'
  | 'passed_with_conditions'
  | 'rectification_required'

export type SeverityLevel =
  | 'near_miss'
  | 'minor'
  | 'moderate'
  | 'severe'
  | 'fatal'

export type DrawdownStatus =
  | 'draft'
  | 'submitted'
  | 'verified_qs'
  | 'approved_architect'
  | 'approved_lender'
  | 'paid'
  | 'rejected'

// Response Types
export interface Contractor {
  id: string
  project_id: string
  company_name: string
  contractor_type: ContractorType
  contact_person: string | null
  email: string | null
  phone: string | null
  contract_value: number | null
  contract_date: string | null
  is_active: boolean
  metadata: Record<string, unknown>
  created_at: string
  updated_at: string | null
}

export interface QualityInspection {
  id: string
  project_id: string
  development_phase_id: number | null
  inspection_date: string
  inspector_name: string
  location: string | null
  status: InspectionStatus
  defects_found: Record<string, unknown>
  photos_url: string[]
  notes: string | null
  created_at: string
}

export interface SafetyIncident {
  id: string
  project_id: string
  incident_date: string
  severity: SeverityLevel
  title: string
  description: string | null
  location: string | null
  reported_by: string | null
  is_resolved: boolean
  resolution_notes: string | null
  created_at: string
}

export interface DrawdownRequest {
  id: string
  project_id: string
  request_name: string
  request_date: string
  amount_requested: number
  amount_approved: number | null
  status: DrawdownStatus
  contractor_id: string | null
  supporting_docs: string[]
  notes: string | null
  created_at: string
  updated_at: string | null
}

// Create Types
export interface ContractorCreate {
  project_id: string
  company_name: string
  contractor_type?: ContractorType
  contact_person?: string
  email?: string
  phone?: string
  contract_value?: number
  contract_date?: string
  is_active?: boolean
  metadata?: Record<string, unknown>
}

export interface QualityInspectionCreate {
  project_id: string
  development_phase_id?: number
  inspection_date: string
  inspector_name: string
  location?: string
  status?: InspectionStatus
  defects_found?: Record<string, unknown>
  photos_url?: string[]
  notes?: string
}

export interface SafetyIncidentCreate {
  project_id: string
  incident_date: string
  severity: SeverityLevel
  title: string
  description?: string
  location?: string
  reported_by?: string
  is_resolved?: boolean
  resolution_notes?: string
}

export interface DrawdownRequestCreate {
  project_id: string
  request_name: string
  request_date: string
  amount_requested: number
  amount_approved?: number
  status?: DrawdownStatus
  contractor_id?: string
  supporting_docs?: string[]
  notes?: string
}

// Update Types
export interface ContractorUpdate {
  company_name?: string
  contractor_type?: ContractorType
  contact_person?: string
  email?: string
  phone?: string
  contract_value?: number
  contract_date?: string
  is_active?: boolean
  metadata?: Record<string, unknown>
}

export interface QualityInspectionUpdate {
  inspection_date?: string
  inspector_name?: string
  location?: string
  status?: InspectionStatus
  defects_found?: Record<string, unknown>
  photos_url?: string[]
  notes?: string
}

export interface SafetyIncidentUpdate {
  incident_date?: string
  severity?: SeverityLevel
  title?: string
  description?: string
  location?: string
  reported_by?: string
  is_resolved?: boolean
  resolution_notes?: string
}

export interface DrawdownRequestUpdate {
  request_name?: string
  request_date?: string
  amount_requested?: number
  amount_approved?: number
  status?: DrawdownStatus
  contractor_id?: string
  supporting_docs?: string[]
  notes?: string
}

// API Functions
export const constructionApi = {
  // Contractors
  async listContractors(
    projectId: string,
    type?: ContractorType,
  ): Promise<Contractor[]> {
    const params = type ? `?type=${type}` : ''
    return api.get<Contractor[]>(
      `/api/v1/projects/${projectId}/contractors${params}`,
    )
  },

  async createContractor(data: ContractorCreate): Promise<Contractor> {
    return api.post<Contractor>(
      `/api/v1/projects/${data.project_id}/contractors`,
      data,
    )
  },

  async updateContractor(
    contractorId: string,
    data: ContractorUpdate,
  ): Promise<Contractor> {
    return api.patch<Contractor>(
      `/api/v1/projects/contractors/${contractorId}`,
      data,
    )
  },

  // Quality Inspections
  async listInspections(
    projectId: string,
    status?: InspectionStatus,
  ): Promise<QualityInspection[]> {
    const params = status ? `?status=${status}` : ''
    return api.get<QualityInspection[]>(
      `/api/v1/projects/${projectId}/inspections${params}`,
    )
  },

  async createInspection(
    data: QualityInspectionCreate,
  ): Promise<QualityInspection> {
    return api.post<QualityInspection>(
      `/api/v1/projects/${data.project_id}/inspections`,
      data,
    )
  },

  async updateInspection(
    inspectionId: string,
    data: QualityInspectionUpdate,
  ): Promise<QualityInspection> {
    return api.patch<QualityInspection>(
      `/api/v1/projects/inspections/${inspectionId}`,
      data,
    )
  },

  // Safety Incidents
  async listIncidents(
    projectId: string,
    unresolvedOnly?: boolean,
  ): Promise<SafetyIncident[]> {
    const params = unresolvedOnly ? '?unresolved=true' : ''
    return api.get<SafetyIncident[]>(
      `/api/v1/projects/${projectId}/incidents${params}`,
    )
  },

  async createIncident(data: SafetyIncidentCreate): Promise<SafetyIncident> {
    return api.post<SafetyIncident>(
      `/api/v1/projects/${data.project_id}/incidents`,
      data,
    )
  },

  async updateIncident(
    incidentId: string,
    data: SafetyIncidentUpdate,
  ): Promise<SafetyIncident> {
    return api.patch<SafetyIncident>(
      `/api/v1/projects/incidents/${incidentId}`,
      data,
    )
  },

  // Drawdown Requests
  async listDrawdowns(
    projectId: string,
    status?: DrawdownStatus,
  ): Promise<DrawdownRequest[]> {
    const params = status ? `?status=${status}` : ''
    return api.get<DrawdownRequest[]>(
      `/api/v1/projects/${projectId}/drawdowns${params}`,
    )
  },

  async createDrawdown(data: DrawdownRequestCreate): Promise<DrawdownRequest> {
    return api.post<DrawdownRequest>(
      `/api/v1/projects/${data.project_id}/drawdowns`,
      data,
    )
  },

  async updateDrawdown(
    drawdownId: string,
    data: DrawdownRequestUpdate,
  ): Promise<DrawdownRequest> {
    return api.patch<DrawdownRequest>(
      `/api/v1/projects/drawdowns/${drawdownId}`,
      data,
    )
  },

  async approveDrawdown(
    drawdownId: string,
    approvedAmount?: number,
  ): Promise<DrawdownRequest> {
    const params = approvedAmount ? `?approved_amount=${approvedAmount}` : ''
    return api.post<DrawdownRequest>(
      `/api/v1/projects/drawdowns/${drawdownId}/approve${params}`,
      {},
    )
  },
}

// Status display helpers
export const contractorTypeLabels: Record<ContractorType, string> = {
  general_contractor: 'General Contractor',
  sub_contractor: 'Sub-Contractor',
  specialist: 'Specialist',
  consultant: 'Consultant',
  supplier: 'Supplier',
}

export const inspectionStatusLabels: Record<InspectionStatus, string> = {
  scheduled: 'Scheduled',
  passed: 'Passed',
  failed: 'Failed',
  passed_with_conditions: 'Passed with Conditions',
  rectification_required: 'Rectification Required',
}

export const severityLabels: Record<SeverityLevel, string> = {
  near_miss: 'Near Miss',
  minor: 'Minor',
  moderate: 'Moderate',
  severe: 'Severe',
  fatal: 'Fatal',
}

export const drawdownStatusLabels: Record<DrawdownStatus, string> = {
  draft: 'Draft',
  submitted: 'Submitted',
  verified_qs: 'QS Verified',
  approved_architect: 'Architect Approved',
  approved_lender: 'Lender Approved',
  paid: 'Paid',
  rejected: 'Rejected',
}

export const inspectionStatusColors: Record<
  InspectionStatus,
  'default' | 'success' | 'error' | 'warning' | 'info'
> = {
  scheduled: 'info',
  passed: 'success',
  failed: 'error',
  passed_with_conditions: 'warning',
  rectification_required: 'error',
}

export const severityColors: Record<
  SeverityLevel,
  'default' | 'success' | 'error' | 'warning' | 'info'
> = {
  near_miss: 'info',
  minor: 'default',
  moderate: 'warning',
  severe: 'error',
  fatal: 'error',
}

export const drawdownStatusColors: Record<
  DrawdownStatus,
  'default' | 'success' | 'error' | 'warning' | 'info'
> = {
  draft: 'default',
  submitted: 'info',
  verified_qs: 'info',
  approved_architect: 'warning',
  approved_lender: 'success',
  paid: 'success',
  rejected: 'error',
}
