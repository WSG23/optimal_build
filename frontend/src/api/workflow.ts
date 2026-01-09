import { ApiClient } from './client'

const apiClient = new ApiClient()

export type WorkflowStatus =
  | 'draft'
  | 'in_progress'
  | 'approved'
  | 'rejected'
  | 'cancelled'

export type StepStatus =
  | 'pending'
  | 'in_review'
  | 'approved'
  | 'rejected'
  | 'skipped'

export interface ApprovalStep {
  id: string
  name: string
  order: number // Backend returns 'order' (aliased from sequence_order)
  status: StepStatus
  approver_role?: string // Backend returns 'approver_role' (aliased from required_role)
  approved_by_id?: string
  approved_at?: string // Backend returns 'approved_at' (aliased from decision_at)
  comments?: string
  // Legacy fields for mock data compatibility
  workflow_id?: string
  sequence_order?: number
  decision_at?: string
}

export interface ApprovalWorkflow {
  id: string
  project_id: string
  name: string // Backend returns 'name' (aliased from title in DB)
  description?: string
  workflow_type: string
  status: WorkflowStatus
  current_step_order: number
  created_at: string
  updated_at?: string
  steps: ApprovalStep[]
  // Legacy fields for mock data compatibility
  title?: string
  created_by_id?: string
}

export interface CreateWorkflowParams {
  name: string // Backend expects 'name' not 'title'
  description?: string
  workflow_type: string
  steps: {
    name: string
    order: number // Backend requires 'order'
    approver_role: string // Backend expects 'approver_role' not 'required_role'
  }[]
}

export const workflowApi = {
  createWorkflow: async (
    projectId: string,
    params: CreateWorkflowParams,
  ): Promise<ApprovalWorkflow> => {
    const { data } = await apiClient.post<ApprovalWorkflow>(
      'api/v1/workflow/',
      params,
      { params: { project_id: projectId } },
    )
    return data
  },

  getWorkflow: async (workflowId: string): Promise<ApprovalWorkflow> => {
    const { data } = await apiClient.get<ApprovalWorkflow>(
      `api/v1/workflow/${workflowId}`,
    )
    return data
  },

  approveStep: async (
    stepId: string,
    approved: boolean,
    comments?: string,
  ): Promise<ApprovalStep> => {
    const { data } = await apiClient.post<ApprovalStep>(
      `api/v1/workflow/steps/${stepId}/approve`,
      { approved, comments },
    )
    return data
  },
}
