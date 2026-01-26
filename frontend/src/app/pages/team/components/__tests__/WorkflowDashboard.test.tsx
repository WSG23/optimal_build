import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react'
import React from 'react'

import { WorkflowDashboard } from '../WorkflowDashboard'
import type { ApprovalWorkflow } from '../../../../../api/workflow'

// Mock the API modules
vi.mock('../../../../../api/workflow', () => ({
  workflowApi: {
    listWorkflows: vi.fn(),
    createWorkflow: vi.fn(),
    approveStep: vi.fn(),
  },
}))

// Import mocked modules
import { workflowApi } from '../../../../../api/workflow'

const mockWorkflows: ApprovalWorkflow[] = [
  {
    id: 'workflow-1',
    project_id: 'project-1',
    name: 'Design Review Workflow',
    title: 'Design Review Workflow',
    description: 'Review workflow for design approvals',
    workflow_type: 'design_review',
    status: 'in_progress',
    created_at: '2025-01-01T00:00:00Z',
    steps: [
      {
        id: 'step-1',
        workflow_id: 'workflow-1',
        name: 'Initial Review',
        order: 1,
        status: 'approved',
        approver_role: 'consultant',
        approved_at: '2025-01-02T00:00:00Z',
      },
      {
        id: 'step-2',
        workflow_id: 'workflow-1',
        name: 'Final Approval',
        order: 2,
        status: 'in_review',
        approver_role: 'architect',
      },
    ],
  },
  {
    id: 'workflow-2',
    project_id: 'project-1',
    name: 'Budget Approval Workflow',
    title: 'Budget Approval Workflow',
    description: 'Workflow for budget sign-off',
    workflow_type: 'budget_approval',
    status: 'approved',
    created_at: '2025-01-03T00:00:00Z',
    steps: [
      {
        id: 'step-3',
        workflow_id: 'workflow-2',
        name: 'Budget Review',
        order: 1,
        status: 'approved',
        approver_role: 'developer',
        approved_at: '2025-01-04T00:00:00Z',
      },
    ],
  },
]

describe('WorkflowDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Setup default mock returns
    vi.mocked(workflowApi.listWorkflows).mockResolvedValue(mockWorkflows)
    vi.mocked(workflowApi.createWorkflow).mockResolvedValue(mockWorkflows[0])
    vi.mocked(workflowApi.approveStep).mockResolvedValue(true)
  })

  afterEach(() => {
    cleanup()
  })

  describe('rendering', () => {
    it('renders the section header', async () => {
      render(<WorkflowDashboard projectId="project-1" />)

      expect(screen.getByText(/Approval Workflows/i)).toBeInTheDocument()
    })

    it('renders New Workflow button', async () => {
      render(<WorkflowDashboard projectId="project-1" />)

      expect(screen.getByText(/New Workflow/i)).toBeInTheDocument()
    })

    it('shows loading state initially', () => {
      vi.mocked(workflowApi.listWorkflows).mockImplementation(
        () => new Promise(() => {}), // Never resolves
      )

      render(<WorkflowDashboard projectId="project-1" />)

      expect(screen.getByRole('progressbar')).toBeInTheDocument()
    })
  })

  describe('workflow display', () => {
    it('displays workflows after loading', async () => {
      render(<WorkflowDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText('Design Review Workflow')).toBeInTheDocument()
      })

      expect(screen.getByText('Budget Approval Workflow')).toBeInTheDocument()
    })

    it('displays workflow descriptions', async () => {
      render(<WorkflowDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(
          screen.getByText('Review workflow for design approvals'),
        ).toBeInTheDocument()
      })
    })

    it('displays workflow types', async () => {
      render(<WorkflowDashboard projectId="project-1" />)

      await waitFor(() => {
        // Look for "Type:" text - there may be multiple workflows showing this
        const typeLabels = screen.getAllByText(/Type:/i)
        expect(typeLabels.length).toBeGreaterThan(0)
      })
    })

    it('displays workflow steps', async () => {
      render(<WorkflowDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText('Initial Review')).toBeInTheDocument()
      })

      expect(screen.getByText('Final Approval')).toBeInTheDocument()
    })

    it('displays step approver roles', async () => {
      render(<WorkflowDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText(/consultant/i)).toBeInTheDocument()
      })
    })

    it('shows empty state when no workflows', async () => {
      vi.mocked(workflowApi.listWorkflows).mockResolvedValue([])

      render(<WorkflowDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(
          screen.getByText(/No active workflows. Create one to get started./i),
        ).toBeInTheDocument()
      })
    })
  })

  describe('workflow status chips', () => {
    it('displays status chips for workflows', async () => {
      render(<WorkflowDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText('in progress')).toBeInTheDocument()
      })
    })
  })

  describe('workflow card expansion', () => {
    it('collapses workflow card when clicking header', async () => {
      render(<WorkflowDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText('Initial Review')).toBeInTheDocument()
      })

      // Find the workflow card header (with the workflow name) and click it
      const workflowHeader = screen.getByText('Design Review Workflow')
      fireEvent.click(workflowHeader.closest('[class*="MuiBox"]')!)

      // Steps should be hidden after collapse
      await waitFor(() => {
        expect(screen.queryByText('Initial Review')).not.toBeVisible()
      })
    })
  })

  describe('approve step', () => {
    it('shows approve button for in_review steps', async () => {
      render(<WorkflowDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText('Final Approval')).toBeInTheDocument()
      })

      expect(
        screen.getByRole('button', { name: /Approve/i }),
      ).toBeInTheDocument()
    })

    it('calls approveStep API when clicking Approve button', async () => {
      render(<WorkflowDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /Approve/i }),
        ).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /Approve/i }))

      await waitFor(() => {
        expect(workflowApi.approveStep).toHaveBeenCalledWith(
          'step-2',
          true,
          'Approved from dashboard',
        )
      })
    })
  })

  describe('create workflow dialog', () => {
    it('opens create dialog when clicking New Workflow button', async () => {
      render(<WorkflowDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText(/New Workflow/i)).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText(/New Workflow/i))

      expect(screen.getByText(/Create Approval Workflow/i)).toBeInTheDocument()
    })

    it('closes create dialog when clicking Cancel', async () => {
      render(<WorkflowDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText(/New Workflow/i)).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText(/New Workflow/i))
      expect(screen.getByText(/Create Approval Workflow/i)).toBeInTheDocument()

      fireEvent.click(screen.getByText(/Cancel/i))

      await waitFor(() => {
        expect(
          screen.queryByText(/Create Approval Workflow/i),
        ).not.toBeInTheDocument()
      })
    })
  })

  describe('API error handling', () => {
    it('shows empty state when API fails and no localStorage', async () => {
      vi.mocked(workflowApi.listWorkflows).mockRejectedValue(
        new Error('API Error'),
      )

      render(<WorkflowDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(
          screen.getByText(/No active workflows. Create one to get started./i),
        ).toBeInTheDocument()
      })
    })
  })
})
