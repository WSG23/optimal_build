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
}
