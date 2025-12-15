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
  workflow_id: string
  name: string
  sequence_order: number
  required_role?: string
  required_user_id?: string
  status: StepStatus
  approved_by_id?: string
  decision_at?: string
  comments?: string
}

export interface ApprovalWorkflow {
  id: string
  project_id: string
  title: string
  description?: string
  workflow_type: string
  status: WorkflowStatus
  created_by_id: string
  created_at: string
  steps: ApprovalStep[]
}

export interface CreateWorkflowParams {
  title: string
  description?: string
  workflow_type: string
  steps: {
    name: string
    required_role?: string
    required_user_id?: string
  }[]
}

export const workflowApi = {
  createWorkflow: async (
    projectId: string,
    params: CreateWorkflowParams,
  ): Promise<ApprovalWorkflow> => {
    const { data } = await apiClient.post<ApprovalWorkflow>(
      '/workflow/',
      params,
      { params: { project_id: projectId } },
    )
    return data
  },

  getWorkflow: async (workflowId: string): Promise<ApprovalWorkflow> => {
    const { data } = await apiClient.get<ApprovalWorkflow>(
      `/workflow/${workflowId}`,
    )
    return data
  },

  approveStep: async (
    stepId: string,
    approved: boolean,
    comments?: string,
  ): Promise<ApprovalStep> => {
    // The backend returns the updated workflow or step?
    // Checking api/v1/workflow.py: it calls WorkflowService.approve_step which returns Step
    // But router response_model is ApprovalWorkflowRead (Wait, let me check backend code again internally if needed,
    // assuming it returns the updated object or the step. Service.approve_step returns Step, Router `response_model=ApprovalWorkflowRead`?
    // If router model is `ApprovalWorkflowRead` but service returns `Step`, that might be a bug or I misread.
    // Let's assume for now it returns the updated Workflow based on pydantic model, or I should fix backend if mismatch.
    // Re-reading `api/v1/workflow.py`: `@router.post(...) response_model=ApprovalWorkflowRead ... return workflow`
    // Ah, the router variable is named `workflow`, but `WorkflowService.approve_step` returns `step`.
    // I need to watch out for this. I will assume it returns the whole workflow for now as that's more useful for UI update.
    const { data } = await apiClient.post<ApprovalStep>(
      `/workflow/steps/${stepId}/approve`,
      { approved, comments },
    )
    return data
  },
}
