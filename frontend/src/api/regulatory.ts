import { ApiClient } from './client'

const apiClient = new ApiClient()

export interface SubmissionDocument {
  id: number
  document_type: string
  file_name: string
  version: number
  uploaded_at: string
}

export interface AuthoritySubmission {
  id: number
  project_id: number
  agency: string
  submission_type: string
  submission_no?: string
  status: 'draft' | 'submitted' | 'in_review' | 'approved' | 'rejected' | 'rfi'
  title: string
  description?: string
  submitted_at?: string
  approved_at?: string
  agency_remarks?: string
  documents: SubmissionDocument[]
}

export interface CreateSubmissionRequest {
  project_id: number
  agency: string
  submission_type: string
}

export type AssetType =
  | 'office'
  | 'retail'
  | 'residential'
  | 'industrial'
  | 'heritage'
  | 'mixed_use'
  | 'hospitality'

export interface AssetCompliancePath {
  id: string
  asset_type: AssetType
  agency_id: string
  submission_type: string
  sequence_order: number
  is_mandatory: boolean
  description?: string
  typical_duration_days?: number
  created_at: string
}

export interface ChangeOfUseApplication {
  id: string
  project_id: string
  current_use: AssetType
  proposed_use: AssetType
  status: 'draft' | 'submitted' | 'in_review' | 'approved' | 'rejected' | 'rfi'
  justification?: string
  ura_reference?: string
  requires_dc_amendment: boolean
  requires_planning_permission: boolean
  submitted_at?: string
  approved_at?: string
  created_at: string
  updated_at: string
}

export interface CreateChangeOfUseRequest {
  project_id: string
  current_use: AssetType
  proposed_use: AssetType
  justification?: string
}

export interface HeritageSubmission {
  id: string
  project_id: string
  conservation_status: string
  stb_reference?: string
  status: 'draft' | 'submitted' | 'in_review' | 'approved' | 'rejected' | 'rfi'
  original_construction_year?: number
  heritage_elements?: string
  proposed_interventions?: string
  conservation_plan_attached: boolean
  submitted_at?: string
  approved_at?: string
  created_at: string
  updated_at: string
}

export interface CreateHeritageSubmissionRequest {
  project_id: string
  conservation_status: string
  original_construction_year?: number
  heritage_elements?: string
  proposed_interventions?: string
}

export interface RegulatoryAgency {
  id: string
  code: string
  name: string
  description?: string
}

export const regulatoryApi = {
  createSubmission: async (
    request: CreateSubmissionRequest,
  ): Promise<AuthoritySubmission> => {
    const { data } = await apiClient.post<AuthoritySubmission>(
      '/regulatory/submit',
      request,
    )
    return data
  },

  listSubmissions: async (
    projectId: string | number,
  ): Promise<AuthoritySubmission[]> => {
    const { data } = await apiClient.get<AuthoritySubmission[]>(
      `/regulatory/project/${projectId}/submissions`,
    )
    return data
  },

  getSubmissionStatus: async (
    submissionId: number | string,
  ): Promise<AuthoritySubmission> => {
    const { data } = await apiClient.get<AuthoritySubmission>(
      `/regulatory/${submissionId}/status`,
    )
    return data
  },

  // Agency endpoints
  listAgencies: async (): Promise<RegulatoryAgency[]> => {
    const { data } = await apiClient.get<RegulatoryAgency[]>(
      '/regulatory/agencies',
    )
    return data
  },

  // Compliance path endpoints
  getCompliancePathsForAsset: async (
    assetType: AssetType,
  ): Promise<AssetCompliancePath[]> => {
    const { data } = await apiClient.get<AssetCompliancePath[]>(
      `/regulatory/compliance-paths/${assetType}`,
    )
    return data
  },

  listAllCompliancePaths: async (): Promise<AssetCompliancePath[]> => {
    const { data } = await apiClient.get<AssetCompliancePath[]>(
      '/regulatory/compliance-paths',
    )
    return data
  },

  // Change of use endpoints
  createChangeOfUse: async (
    request: CreateChangeOfUseRequest,
  ): Promise<ChangeOfUseApplication> => {
    const { data } = await apiClient.post<ChangeOfUseApplication>(
      '/regulatory/change-of-use',
      request,
    )
    return data
  },

  listChangeOfUseApplications: async (
    projectId: string,
  ): Promise<ChangeOfUseApplication[]> => {
    const { data } = await apiClient.get<ChangeOfUseApplication[]>(
      `/regulatory/change-of-use/project/${projectId}`,
    )
    return data
  },

  // Heritage submission endpoints
  createHeritageSubmission: async (
    request: CreateHeritageSubmissionRequest,
  ): Promise<HeritageSubmission> => {
    const { data } = await apiClient.post<HeritageSubmission>(
      '/regulatory/heritage',
      request,
    )
    return data
  },

  listHeritageSubmissions: async (
    projectId: string,
  ): Promise<HeritageSubmission[]> => {
    const { data } = await apiClient.get<HeritageSubmission[]>(
      `/regulatory/heritage/project/${projectId}`,
    )
    return data
  },

  getHeritageSubmission: async (
    submissionId: string,
  ): Promise<HeritageSubmission> => {
    const { data } = await apiClient.get<HeritageSubmission>(
      `/regulatory/heritage/${submissionId}`,
    )
    return data
  },

  submitHeritageToSTB: async (
    submissionId: string,
  ): Promise<HeritageSubmission> => {
    const { data } = await apiClient.post<HeritageSubmission>(
      `/regulatory/heritage/${submissionId}/submit`,
      {},
    )
    return data
  },
}
