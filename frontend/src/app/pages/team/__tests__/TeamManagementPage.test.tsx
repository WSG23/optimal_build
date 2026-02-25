import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react'
import React from 'react'

import { TeamManagementPage } from '../TeamManagementPage'
import {
  ProjectContext,
  type ProjectContextValue,
} from '../../../../contexts/projectContextDef'
import type { TeamMember } from '../../../../api/team'

// Mock the API modules
vi.mock('../../../../api/team', () => ({
  teamApi: {
    listMembers: vi.fn(),
    inviteMember: vi.fn(),
    removeMember: vi.fn(),
  },
}))

vi.mock('../../../../api/workflow', () => ({
  workflowApi: {
    listWorkflows: vi.fn(),
    createWorkflow: vi.fn(),
    approveStep: vi.fn(),
  },
}))

vi.mock('../../../../api/projects', () => ({
  getProjectProgress: vi.fn(),
}))

// Import mocked modules
import { teamApi } from '../../../../api/team'
import { workflowApi } from '../../../../api/workflow'
import { getProjectProgress } from '../../../../api/projects'

const mockTeamMembers: TeamMember[] = [
  {
    id: 'member-1',
    project_id: 'project-1',
    user_id: 'user-1',
    role: 'developer',
    is_active: true,
    joined_at: '2025-01-01T00:00:00Z',
    user: {
      full_name: 'John Smith',
      email: 'john@example.com',
    },
  },
  {
    id: 'member-2',
    project_id: 'project-1',
    user_id: 'user-2',
    role: 'consultant',
    is_active: false,
    joined_at: '2025-01-02T00:00:00Z',
    user: {
      full_name: 'Jane Doe',
      email: 'jane@example.com',
    },
  },
]

const mockProject = {
  id: 'project-1',
  name: 'Test Project',
  status: 'active',
}

function createMockProjectContext(
  overrides: Partial<ProjectContextValue> = {},
): ProjectContextValue {
  return {
    currentProject: mockProject,
    projects: [mockProject],
    isProjectLoading: false,
    projectError: null,
    setCurrentProject: vi.fn(),
    clearProject: vi.fn(),
    refreshProjects: vi.fn().mockResolvedValue(undefined),
    createProject: vi.fn().mockResolvedValue(mockProject),
    ...overrides,
  }
}

function renderWithProviders(
  ui: React.ReactElement,
  contextValue: ProjectContextValue = createMockProjectContext(),
) {
  return render(
    <ProjectContext.Provider value={contextValue}>
      {ui}
    </ProjectContext.Provider>,
  )
}

describe('TeamManagementPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Setup default mock returns
    vi.mocked(teamApi.listMembers).mockResolvedValue(mockTeamMembers)
    vi.mocked(workflowApi.listWorkflows).mockResolvedValue([])
    vi.mocked(getProjectProgress).mockResolvedValue({
      phases: [],
      team_activity: [],
      pending_approvals: [],
    })
    // Clear localStorage
    window.localStorage.clear()
  })

  afterEach(() => {
    cleanup()
    window.localStorage.clear()
  })

  describe('when no project is selected', () => {
    it('shows message to select a project', () => {
      renderWithProviders(
        <TeamManagementPage />,
        createMockProjectContext({ currentProject: null }),
      )

      expect(
        screen.getByText(/Select a project to manage team coordination/i),
      ).toBeInTheDocument()
    })

    it('shows loading state while project is loading', () => {
      renderWithProviders(
        <TeamManagementPage />,
        createMockProjectContext({
          currentProject: null,
          isProjectLoading: true,
        }),
      )

      expect(screen.getByRole('progressbar')).toBeInTheDocument()
    })

    it('shows error when project error exists', () => {
      renderWithProviders(
        <TeamManagementPage />,
        createMockProjectContext({
          currentProject: null,
          projectError: { type: 'not_found', message: 'Project not found' },
        }),
      )

      expect(screen.getByText(/Project not found/i)).toBeInTheDocument()
    })
  })

  describe('when project is selected', () => {
    it('renders page header with project name', async () => {
      renderWithProviders(<TeamManagementPage />)
      await waitFor(() => {
        expect(teamApi.listMembers).toHaveBeenCalledWith('project-1')
      })

      expect(screen.getByText(/Team Management/i)).toBeInTheDocument()
      expect(screen.getByText(/Project: Test Project/i)).toBeInTheDocument()
    })

    it('renders three tabs', async () => {
      renderWithProviders(<TeamManagementPage />)
      await waitFor(() => {
        expect(teamApi.listMembers).toHaveBeenCalledWith('project-1')
      })

      expect(
        screen.getByRole('tab', { name: /Team Members/i }),
      ).toBeInTheDocument()
      expect(
        screen.getByRole('tab', { name: /Approvals & Workflows/i }),
      ).toBeInTheDocument()
      expect(
        screen.getByRole('tab', { name: /Progress Dashboard/i }),
      ).toBeInTheDocument()
    })

    it('shows Invite Member button on Team Members tab', async () => {
      renderWithProviders(<TeamManagementPage />)
      await waitFor(() => {
        expect(teamApi.listMembers).toHaveBeenCalledWith('project-1')
      })

      expect(screen.getByText(/Invite Member/i)).toBeInTheDocument()
    })
  })

  describe('Team Members tab', () => {
    it('displays team members after loading', async () => {
      renderWithProviders(<TeamManagementPage />)

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument()
      })

      expect(screen.getByText('john@example.com')).toBeInTheDocument()
      expect(screen.getByText('Jane Doe')).toBeInTheDocument()
      expect(screen.getByText('jane@example.com')).toBeInTheDocument()
    })

    it('displays member roles', async () => {
      renderWithProviders(<TeamManagementPage />)

      await waitFor(() => {
        expect(screen.getByText('developer')).toBeInTheDocument()
      })

      expect(screen.getByText('consultant')).toBeInTheDocument()
    })

    it('displays member status', async () => {
      renderWithProviders(<TeamManagementPage />)

      await waitFor(() => {
        expect(screen.getByText('Active')).toBeInTheDocument()
      })

      expect(screen.getByText('Inactive')).toBeInTheDocument()
    })

    it('shows empty state when no members', async () => {
      vi.mocked(teamApi.listMembers).mockResolvedValue([])

      renderWithProviders(<TeamManagementPage />)

      await waitFor(() => {
        expect(screen.getByText(/No team members found/i)).toBeInTheDocument()
      })
    })

    it('shows loading state while fetching members', () => {
      // Create a promise that doesn't resolve immediately
      vi.mocked(teamApi.listMembers).mockImplementation(
        () => new Promise(() => {}), // Never resolves
      )

      renderWithProviders(<TeamManagementPage />)

      expect(screen.getByText(/Loading team/i)).toBeInTheDocument()
    })
  })

  describe('Invite Member dialog', () => {
    it('opens dialog when clicking Invite Member button', async () => {
      renderWithProviders(<TeamManagementPage />)

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText(/Invite Member/i))

      expect(screen.getByText(/Invite New Member/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Role/i)).toBeInTheDocument()
    })

    it('closes dialog when clicking Cancel', async () => {
      renderWithProviders(<TeamManagementPage />)

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText(/Invite Member/i))
      expect(screen.getByText(/Invite New Member/i)).toBeInTheDocument()

      fireEvent.click(screen.getByText(/Cancel/i))

      await waitFor(() => {
        expect(screen.queryByText(/Invite New Member/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('Tab navigation', () => {
    it('switches to Approvals & Workflows tab', async () => {
      renderWithProviders(<TeamManagementPage />)

      fireEvent.click(
        screen.getByRole('tab', { name: /Approvals & Workflows/i }),
      )

      await waitFor(() => {
        expect(screen.getByText(/Approval Workflows/i)).toBeInTheDocument()
      })
    })

    it('switches to Progress Dashboard tab', async () => {
      renderWithProviders(<TeamManagementPage />)

      fireEvent.click(screen.getByRole('tab', { name: /Progress Dashboard/i }))

      await waitFor(() => {
        expect(screen.getByText(/Progress Dashboard/i)).toBeInTheDocument()
      })
    })

    it('hides Invite Member button on other tabs', async () => {
      renderWithProviders(<TeamManagementPage />)

      // Initially visible
      expect(screen.getByText(/Invite Member/i)).toBeInTheDocument()

      // Switch to Workflows tab
      fireEvent.click(
        screen.getByRole('tab', { name: /Approvals & Workflows/i }),
      )

      await waitFor(() => {
        expect(screen.queryByText(/Invite Member/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('Remove member', () => {
    it('calls removeMember API when clicking Remove button', async () => {
      vi.mocked(teamApi.removeMember).mockResolvedValue(true)

      renderWithProviders(<TeamManagementPage />)

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument()
      })

      const removeButtons = screen.getAllByText(/Remove/i)
      fireEvent.click(removeButtons[0])

      await waitFor(() => {
        expect(teamApi.removeMember).toHaveBeenCalledWith('project-1', 'user-1')
      })
    })
  })
})
