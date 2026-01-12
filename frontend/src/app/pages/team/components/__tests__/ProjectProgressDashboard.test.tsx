import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  cleanup,
  render,
  screen,
  waitFor,
  fireEvent,
} from '@testing-library/react'
import React from 'react'

import { ProjectProgressDashboard } from '../ProjectProgressDashboard'
import type {
  ProjectProgressPhase,
  ProjectProgressTeamActivity,
  ProjectProgressApproval,
} from '../../../../../api/projects'

// Mock the API modules
vi.mock('../../../../../api/projects', () => ({
  getProjectProgress: vi.fn(),
}))

// Mock the mock data module
vi.mock('../projectProgressMockData', () => ({
  getMockPhases: vi.fn(() => [
    {
      id: 'phase-1',
      name: 'Planning',
      progress: 100,
      status: 'completed',
      milestones: [{ name: 'Site Analysis', completed: true }],
    },
    {
      id: 'phase-2',
      name: 'Design',
      progress: 60,
      status: 'in_progress',
      milestones: [
        { name: 'Concept Design', completed: true },
        { name: 'Detail Design', completed: false },
      ],
    },
    {
      id: 'phase-3',
      name: 'Construction',
      progress: 0,
      status: 'not_started',
      milestones: [],
    },
  ]),
}))

// Import mocked modules
import { getProjectProgress } from '../../../../../api/projects'

const mockProgressData = {
  phases: [
    {
      id: 1,
      name: 'Feasibility',
      progress: 100,
      status: 'completed',
      start_date: '2025-01-01',
      end_date: '2025-01-15',
    },
    {
      id: 2,
      name: 'Design Development',
      progress: 75,
      status: 'in_progress',
      start_date: '2025-01-16',
      end_date: '2025-02-15',
    },
    {
      id: 3,
      name: 'Documentation',
      progress: 0,
      status: 'not_started',
      start_date: null,
      end_date: null,
    },
  ] as ProjectProgressPhase[],
  team_activity: [
    {
      id: 'member-1',
      name: 'Alice Johnson',
      email: 'alice@example.com',
      role: 'Architect',
      last_active_at: '2025-01-10T10:00:00Z',
      pending_tasks: 5,
      completed_tasks: 12,
    },
    {
      id: 'member-2',
      name: 'Bob Smith',
      email: 'bob@example.com',
      role: 'Engineer',
      last_active_at: '2025-01-10T09:30:00Z',
      pending_tasks: 3,
      completed_tasks: 8,
    },
  ] as ProjectProgressTeamActivity[],
  pending_approvals: [
    {
      id: 'approval-1',
      title: 'Design Review Sign-off',
      workflow_name: 'Design Review Workflow',
      required_by: 'Senior Architect',
    },
    {
      id: 'approval-2',
      title: 'Budget Approval',
      workflow_name: 'Budget Workflow',
      required_by: 'Finance Manager',
    },
  ] as ProjectProgressApproval[],
}

describe('ProjectProgressDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Setup default mock returns
    vi.mocked(getProjectProgress).mockResolvedValue(mockProgressData)
    // Clear localStorage
    window.localStorage.clear()
  })

  afterEach(() => {
    cleanup()
    window.localStorage.clear()
  })

  describe('loading state', () => {
    it('shows loading state initially', () => {
      vi.mocked(getProjectProgress).mockImplementation(
        () => new Promise(() => {}), // Never resolves
      )

      render(<ProjectProgressDashboard projectId="project-1" />)

      expect(screen.getByText(/Loading project progress/i)).toBeInTheDocument()
      expect(screen.getByRole('progressbar')).toBeInTheDocument()
    })
  })

  describe('header', () => {
    it('renders project name in header', async () => {
      render(
        <ProjectProgressDashboard
          projectId="project-1"
          projectName="Test Project"
        />,
      )

      await waitFor(() => {
        expect(
          screen.getByText(/Test Project - Progress Dashboard/i),
        ).toBeInTheDocument()
      })
    })

    it('renders refresh button', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /Refresh/i }),
        ).toBeInTheDocument()
      })
    })

    it('refetches data when clicking refresh', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /Refresh/i }),
        ).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /Refresh/i }))

      await waitFor(() => {
        expect(getProjectProgress).toHaveBeenCalledTimes(2)
      })
    })
  })

  describe('KPI cards', () => {
    it('displays overall progress percentage', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        // Overall progress should be average of phases (100 + 75 + 0) / 3 = 58%
        expect(screen.getByText('58%')).toBeInTheDocument()
      })
    })

    it('displays overall progress label', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText(/Overall Progress/i)).toBeInTheDocument()
      })
    })

    it('displays completed tasks count', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        // Total completed tasks: 12 + 8 = 20
        expect(screen.getByText('20')).toBeInTheDocument()
      })

      expect(screen.getByText(/Completed Tasks/i)).toBeInTheDocument()
    })

    it('displays pending tasks count', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        // Total pending tasks: 5 + 3 = 8
        // Use getAllByText since the number may appear in multiple places
        const eights = screen.getAllByText('8')
        expect(eights.length).toBeGreaterThan(0)
      })

      expect(screen.getByText(/Pending Tasks/i)).toBeInTheDocument()
    })

    it('displays team members count', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        // 2 team members - appears in KPI card and as approval count
        // Use getAllByText since the number may appear in multiple places
        const twos = screen.getAllByText('2')
        expect(twos.length).toBeGreaterThan(0)
      })

      expect(screen.getByText(/Team Members/i)).toBeInTheDocument()
    })
  })

  describe('phase progress section', () => {
    it('displays phase progress section header', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText(/Phase Progress/i)).toBeInTheDocument()
      })
    })

    it('displays phase names', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText('Feasibility')).toBeInTheDocument()
      })

      expect(screen.getByText('Design Development')).toBeInTheDocument()
      expect(screen.getByText('Documentation')).toBeInTheDocument()
    })

    it('displays phase progress percentages', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText('100%')).toBeInTheDocument()
      })

      expect(screen.getByText('75%')).toBeInTheDocument()
      expect(screen.getByText('0%')).toBeInTheDocument()
    })

    it('displays phase status chips', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText('completed')).toBeInTheDocument()
      })

      expect(screen.getByText('in progress')).toBeInTheDocument()
      expect(screen.getByText('not started')).toBeInTheDocument()
    })
  })

  describe('pending approvals section', () => {
    it('displays pending approvals section header', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText(/Pending Approvals/i)).toBeInTheDocument()
      })
    })

    it('displays pending approvals count chip', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        // Should show chip with count 2
        const chips = screen.getAllByText('2')
        expect(chips.length).toBeGreaterThan(0)
      })
    })

    it('displays approval titles', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText('Design Review Sign-off')).toBeInTheDocument()
      })

      expect(screen.getByText('Budget Approval')).toBeInTheDocument()
    })

    it('displays approval workflow names', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText('Design Review Workflow')).toBeInTheDocument()
      })

      expect(screen.getByText('Budget Workflow')).toBeInTheDocument()
    })

    it('displays assigned to information', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(
          screen.getByText(/Assigned to: Senior Architect/i),
        ).toBeInTheDocument()
      })

      expect(
        screen.getByText(/Assigned to: Finance Manager/i),
      ).toBeInTheDocument()
    })

    it('shows empty state when no pending approvals', async () => {
      vi.mocked(getProjectProgress).mockResolvedValue({
        ...mockProgressData,
        pending_approvals: [],
      })

      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText(/No pending approvals/i)).toBeInTheDocument()
      })
    })
  })

  describe('team activity section', () => {
    it('displays team activity section header', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText(/Team Activity/i)).toBeInTheDocument()
      })
    })

    it('displays team member names', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument()
      })

      expect(screen.getByText('Bob Smith')).toBeInTheDocument()
    })

    it('displays team member roles', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText('Architect')).toBeInTheDocument()
      })

      expect(screen.getByText('Engineer')).toBeInTheDocument()
    })

    it('displays team member avatars with initials', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText('A')).toBeInTheDocument() // Alice's avatar
      })

      expect(screen.getByText('B')).toBeInTheDocument() // Bob's avatar
    })

    it('displays pending task counts per member', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        // Alice has 5 pending, Bob has 3 pending
        expect(screen.getByText('5')).toBeInTheDocument()
        expect(screen.getByText('3')).toBeInTheDocument()
      })
    })

    it('displays completed task counts per member', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        // Alice has 12 completed, Bob has 8 completed
        expect(screen.getByText('12')).toBeInTheDocument()
      })
    })
  })

  describe('localStorage persistence', () => {
    it('persists phases to localStorage after fetching', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText('Feasibility')).toBeInTheDocument()
      })

      const stored = window.localStorage.getItem('ob_project_phases:project-1')
      expect(stored).not.toBeNull()
    })

    it('persists team activity to localStorage after fetching', async () => {
      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument()
      })

      const stored = window.localStorage.getItem('ob_team_activity:project-1')
      expect(stored).not.toBeNull()
    })

    it('loads phases from localStorage when API fails', async () => {
      // Pre-populate localStorage with stored phases
      window.localStorage.setItem(
        'ob_project_phases:project-1',
        JSON.stringify([
          {
            id: 'stored-phase-1',
            name: 'Stored Phase',
            progress: 50,
            status: 'in_progress',
            milestones: [],
          },
        ]),
      )

      vi.mocked(getProjectProgress).mockRejectedValue(new Error('API Error'))

      render(<ProjectProgressDashboard projectId="project-1" />)

      await waitFor(() => {
        expect(screen.getByText('Stored Phase')).toBeInTheDocument()
      })
    })
  })

  describe('API error handling', () => {
    it('uses seed phases when API fails and no localStorage', async () => {
      vi.mocked(getProjectProgress).mockRejectedValue(new Error('API Error'))

      render(<ProjectProgressDashboard projectId="project-1" />)

      // Should fall back to seeded phases from getMockPhases
      await waitFor(() => {
        expect(screen.getByText('Planning')).toBeInTheDocument()
      })

      expect(screen.getByText('Design')).toBeInTheDocument()
    })
  })

  describe('empty phases handling', () => {
    it('uses seed phases when API returns empty phases', async () => {
      vi.mocked(getProjectProgress).mockResolvedValue({
        phases: [],
        team_activity: [],
        pending_approvals: [],
      })

      render(<ProjectProgressDashboard projectId="project-1" />)

      // Should fall back to seeded phases
      await waitFor(() => {
        expect(screen.getByText('Planning')).toBeInTheDocument()
      })
    })
  })
})
