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

// Asset types for compliance paths
export type AssetType =
  | 'office'
  | 'retail'
  | 'residential'
  | 'industrial'
  | 'hospitality'
  | 'mixed_use'
  | 'heritage'

export type SubmissionType =
  | 'planning_permission'
  | 'development_control'
  | 'building_plan'
  | 'structural_plan'
  | 'fire_safety'
  | 'environmental'
  | 'heritage_conservation'
  | 'change_of_use'
  | 'csc_application'
  | 'top_application'

// Compliance path for regulatory timeline
export interface AssetCompliancePath {
  id: string
  asset_type: AssetType
  submission_type: SubmissionType
  agency_id: string
  sequence_order: number
  is_mandatory: boolean
  description?: string
  typical_duration_days?: number
  created_at: string
}

// Change of use application
export interface ChangeOfUseApplication {
  id: string
  project_id: string
  current_use: AssetType
  proposed_use: AssetType
  justification?: string
  status: 'draft' | 'submitted' | 'in_review' | 'approved' | 'rejected'
  ura_reference?: string
  requires_dc_amendment: boolean
  requires_planning_permission: boolean
  submitted_at?: string
  approved_at?: string
  created_at: string
  updated_at: string
}

export interface ChangeOfUseCreateRequest {
  project_id: string
  current_use: AssetType
  proposed_use: AssetType
  justification?: string
}

export interface ChangeOfUseUpdateRequest {
  status?: string
  justification?: string
  ura_reference?: string
  requires_dc_amendment?: boolean
}

// Heritage submission
export interface HeritageSubmission {
  id: string
  project_id: string
  conservation_status: string
  original_construction_year?: number
  heritage_elements?: string
  proposed_interventions?: string
  status: 'draft' | 'submitted' | 'in_review' | 'approved' | 'rejected'
  stb_reference?: string
  conservation_plan_attached: boolean
  submitted_at?: string
  approved_at?: string
  created_at: string
  updated_at: string
}

export interface HeritageSubmissionCreateRequest {
  project_id: string
  conservation_status: string
  original_construction_year?: number
  heritage_elements?: string
  proposed_interventions?: string
}

export interface HeritageSubmissionUpdateRequest {
  status?: string
  stb_reference?: string
  heritage_elements?: string
  proposed_interventions?: string
  conservation_plan_attached?: boolean
}

export const regulatoryApi = {
  // Submissions
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

  // Compliance Paths
  getCompliancePaths: async (
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

  // Change of Use
  createChangeOfUse: async (
    request: ChangeOfUseCreateRequest,
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

  updateChangeOfUse: async (
    applicationId: string,
    request: ChangeOfUseUpdateRequest,
  ): Promise<ChangeOfUseApplication> => {
    const { data } = await apiClient.patch<ChangeOfUseApplication>(
      `/regulatory/change-of-use/${applicationId}`,
      request,
    )
    return data
  },

  // Heritage Submissions
  createHeritageSubmission: async (
    request: HeritageSubmissionCreateRequest,
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

  updateHeritageSubmission: async (
    submissionId: string,
    request: HeritageSubmissionUpdateRequest,
  ): Promise<HeritageSubmission> => {
    const { data } = await apiClient.patch<HeritageSubmission>(
      `/regulatory/heritage/${submissionId}`,
      request,
    )
    return data
  },

  submitToSTB: async (submissionId: string): Promise<HeritageSubmission> => {
    const { data } = await apiClient.post<HeritageSubmission>(
      `/regulatory/heritage/${submissionId}/submit`,
      {},
    )
    return data
  },
}
