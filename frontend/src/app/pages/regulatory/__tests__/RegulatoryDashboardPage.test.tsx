import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react'
import React from 'react'

import { RegulatoryDashboardPage } from '../RegulatoryDashboardPage'
import {
  ProjectContext,
  type ProjectContextValue,
} from '../../../../contexts/projectContextDef'
import type {
  AuthoritySubmission,
  ChangeOfUseApplication,
  HeritageSubmission,
} from '../../../../api/regulatory'

// Mock the API modules
vi.mock('../../../../api/regulatory', () => ({
  regulatoryApi: {
    listSubmissions: vi.fn(),
    listChangeOfUseApplications: vi.fn(),
    listHeritageSubmissions: vi.fn(),
    getSubmissionStatus: vi.fn(),
    createSubmission: vi.fn(),
    getCompliancePaths: vi.fn(),
    getCorenetCapability: vi.fn(),
  },
}))

// Import mocked modules
import { regulatoryApi } from '../../../../api/regulatory'

const mockSubmissions: AuthoritySubmission[] = [
  {
    id: 'submission-1',
    project_id: 'project-1',
    agency_id: 'URA',
    agency_code: 'URA',
    agency_name: 'Urban Redevelopment Authority',
    submission_type: 'DC',
    submission_no: 'URA-2025-001',
    status: 'APPROVED',
    title: 'Development Control Application',
    description: 'Main DC submission',
    submitted_at: '2025-01-01T00:00:00Z',
    approved_at: '2025-01-15T00:00:00Z',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-15T00:00:00Z',
  },
  {
    id: 'submission-2',
    project_id: 'project-1',
    agency_id: 'BCA',
    agency_code: 'BCA',
    agency_name: 'Building & Construction Authority',
    submission_type: 'BP',
    status: 'IN_REVIEW',
    title: 'Building Plan Submission',
    created_at: '2025-01-10T00:00:00Z',
    updated_at: '2025-01-10T00:00:00Z',
  },
  {
    id: 'submission-3',
    project_id: 'project-1',
    agency_id: 'SCDF',
    agency_code: 'SCDF',
    agency_name: 'Singapore Civil Defence Force',
    submission_type: 'CONSULTATION',
    status: 'REJECTED',
    title: 'Fire Safety Consultation',
    created_at: '2025-01-05T00:00:00Z',
    updated_at: '2025-01-08T00:00:00Z',
  },
]

const mockChangeOfUseApps: ChangeOfUseApplication[] = [
  {
    id: 'cou-1',
    project_id: 'project-1',
    current_use: 'office',
    proposed_use: 'retail',
    justification: 'Market demand for retail space',
    status: 'draft',
    requires_dc_amendment: true,
    requires_planning_permission: true,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
]

const mockHeritageSubmissions: HeritageSubmission[] = [
  {
    id: 'heritage-1',
    project_id: 'project-1',
    conservation_status: 'national_monument',
    original_construction_year: 1920,
    heritage_elements: 'Original facade, internal timber structure',
    proposed_interventions: 'Facade restoration, internal modernization',
    status: 'draft',
    stb_reference: undefined,
    conservation_plan_attached: false,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
]

const mockProject = {
  id: 'project-1',
  name: 'Test Regulatory Project',
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

describe('RegulatoryDashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Setup default mock returns
    vi.mocked(regulatoryApi.listSubmissions).mockResolvedValue(mockSubmissions)
    vi.mocked(regulatoryApi.listChangeOfUseApplications).mockResolvedValue(
      mockChangeOfUseApps,
    )
    vi.mocked(regulatoryApi.listHeritageSubmissions).mockResolvedValue(
      mockHeritageSubmissions,
    )
    vi.mocked(regulatoryApi.getCompliancePaths).mockResolvedValue([])
    vi.mocked(regulatoryApi.getCorenetCapability).mockResolvedValue({
      submission_mode_default: 'submission_prep',
      live_submission_available: false,
      package_status: 'not_ready',
      package_requirements: [],
      delivery_blockers: [],
      integration_status: {
        provider: 'test',
        state: 'mock',
        synthetic: true,
      },
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
        <RegulatoryDashboardPage />,
        createMockProjectContext({ currentProject: null }),
      )

      expect(
        screen.getByText(/Select a project to manage regulatory submissions/i),
      ).toBeInTheDocument()
    })

    it('shows loading state while project is loading', () => {
      const { container } = renderWithProviders(
        <RegulatoryDashboardPage />,
        createMockProjectContext({
          currentProject: null,
          isProjectLoading: true,
        }),
      )

      expect(container.querySelector('.MuiSkeleton-root')).toBeInTheDocument()
    })

    it('shows error when project error exists', () => {
      renderWithProviders(
        <RegulatoryDashboardPage />,
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
      renderWithProviders(<RegulatoryDashboardPage />)

      expect(screen.getByText(/Regulatory Dashboard/i)).toBeInTheDocument()
      expect(
        screen.getByText(/Project: Test Regulatory Project/i),
      ).toBeInTheDocument()
    })

    it('renders two tabs', () => {
      renderWithProviders(<RegulatoryDashboardPage />)

      expect(
        screen.getByRole('tab', { name: /Submissions/i }),
      ).toBeInTheDocument()
      expect(
        screen.getByRole('tab', { name: /Compliance Path/i }),
      ).toBeInTheDocument()
    })

    it('shows New Submission button', () => {
      renderWithProviders(<RegulatoryDashboardPage />)

      expect(screen.getByText(/New Submission/i)).toBeInTheDocument()
    })

    it('shows Check Status button', () => {
      renderWithProviders(<RegulatoryDashboardPage />)

      expect(screen.getByText(/Check Status/i)).toBeInTheDocument()
    })
  })

  describe('Quick Actions section', () => {
    it('displays Change of Use action card', async () => {
      renderWithProviders(<RegulatoryDashboardPage />)

      expect(
        screen.getByRole('button', { name: /Start change of use/i }),
      ).toBeInTheDocument()
    })

    it('displays Heritage Submission action card', async () => {
      renderWithProviders(<RegulatoryDashboardPage />)

      expect(
        screen.getByRole('button', { name: /heritage submission/i }),
      ).toBeInTheDocument()
    })

    it('displays Compliance Timeline action card', async () => {
      renderWithProviders(<RegulatoryDashboardPage />)

      expect(
        screen.getByRole('button', { name: /View compliance path/i }),
      ).toBeInTheDocument()
    })
  })

  describe('Submissions tab', () => {
    it('displays agency labels in the submissions table', async () => {
      renderWithProviders(<RegulatoryDashboardPage />)

      await waitFor(() => {
        expect(
          screen.getByText('Urban Redevelopment Authority'),
        ).toBeInTheDocument()
      })

      expect(
        screen.getByText('Building & Construction Authority'),
      ).toBeInTheDocument()
      expect(
        screen.getByText('Singapore Civil Defence Force'),
      ).toBeInTheDocument()
    })

    it('displays submissions table with data', async () => {
      renderWithProviders(<RegulatoryDashboardPage />)

      await waitFor(() => {
        expect(
          screen.getByText('Development Control Application'),
        ).toBeInTheDocument()
      })

      expect(screen.getByText('Building Plan Submission')).toBeInTheDocument()
    })

    it('displays correct status chips for submissions', async () => {
      renderWithProviders(<RegulatoryDashboardPage />)

      await waitFor(() => {
        expect(screen.getByText(/APPROVED/i)).toBeInTheDocument()
      })

      expect(screen.getByText(/IN_REVIEW/i)).toBeInTheDocument()
      expect(screen.getByText(/REJECTED/i)).toBeInTheDocument()
    })

    it('displays refresh buttons for submissions', async () => {
      renderWithProviders(<RegulatoryDashboardPage />)

      await waitFor(() => {
        const refreshButtons = screen.getAllByText(/Refresh/i)
        expect(refreshButtons.length).toBeGreaterThan(0)
      })
    })

    it('shows empty state when no submissions', async () => {
      vi.mocked(regulatoryApi.listSubmissions).mockResolvedValue([])
      vi.mocked(regulatoryApi.listChangeOfUseApplications).mockResolvedValue([])
      vi.mocked(regulatoryApi.listHeritageSubmissions).mockResolvedValue([])

      renderWithProviders(<RegulatoryDashboardPage />)

      await waitFor(() => {
        expect(screen.getByText(/No submissions yet/i)).toBeInTheDocument()
      })
    })
  })

  describe('Change of Use Applications section', () => {
    it('displays change of use applications', async () => {
      renderWithProviders(<RegulatoryDashboardPage />)

      await waitFor(() => {
        expect(screen.getByText(/office to retail/i)).toBeInTheDocument()
      })
    })

    it('shows empty state when no change of use applications', async () => {
      vi.mocked(regulatoryApi.listChangeOfUseApplications).mockResolvedValue([])

      renderWithProviders(<RegulatoryDashboardPage />)

      await waitFor(() => {
        expect(
          screen.getByText(/No change-of-use applications yet/i),
        ).toBeInTheDocument()
      })
    })

    it('displays Edit button for draft applications', async () => {
      renderWithProviders(<RegulatoryDashboardPage />)

      await waitFor(() => {
        // Find Edit button in the change of use section
        const editButtons = screen.getAllByText(/Edit/i)
        expect(editButtons.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Heritage Submissions section', () => {
    it('displays heritage submissions', async () => {
      renderWithProviders(<RegulatoryDashboardPage />)

      await waitFor(() => {
        expect(screen.getByText(/national_monument/i)).toBeInTheDocument()
      })
    })

    it('shows empty state when no heritage submissions', async () => {
      vi.mocked(regulatoryApi.listHeritageSubmissions).mockResolvedValue([])

      renderWithProviders(<RegulatoryDashboardPage />)

      await waitFor(() => {
        expect(
          screen.getByText(/No heritage submissions yet/i),
        ).toBeInTheDocument()
      })

      expect(screen.getByText(/New heritage submission/i)).toBeInTheDocument()
    })
  })

  describe('Tab navigation', () => {
    it('switches to Compliance Path tab', async () => {
      vi.mocked(regulatoryApi.getCompliancePaths).mockResolvedValue([])

      renderWithProviders(<RegulatoryDashboardPage />)

      fireEvent.click(screen.getByRole('tab', { name: /Compliance Path/i }))

      await waitFor(() => {
        expect(
          screen.getByText(/Compliance Path Timeline/i),
        ).toBeInTheDocument()
      })
    })
  })

  describe('API interactions', () => {
    it('calls listSubmissions with project ID on mount', async () => {
      renderWithProviders(<RegulatoryDashboardPage />)

      await waitFor(() => {
        expect(regulatoryApi.listSubmissions).toHaveBeenCalledWith('project-1')
      })
    })

    it('calls listChangeOfUseApplications with project ID on mount', async () => {
      renderWithProviders(<RegulatoryDashboardPage />)

      await waitFor(() => {
        expect(regulatoryApi.listChangeOfUseApplications).toHaveBeenCalledWith(
          'project-1',
        )
      })
    })

    it('calls listHeritageSubmissions with project ID on mount', async () => {
      renderWithProviders(<RegulatoryDashboardPage />)

      await waitFor(() => {
        expect(regulatoryApi.listHeritageSubmissions).toHaveBeenCalledWith(
          'project-1',
        )
      })
    })

    it('refreshes submissions when Check Status button is clicked', async () => {
      renderWithProviders(<RegulatoryDashboardPage />)

      await waitFor(() => {
        expect(
          screen.getByText('Development Control Application'),
        ).toBeInTheDocument()
      })

      // Clear mock call count
      vi.mocked(regulatoryApi.listSubmissions).mockClear()

      fireEvent.click(screen.getByText(/Check Status/i))

      await waitFor(() => {
        expect(regulatoryApi.listSubmissions).toHaveBeenCalledWith('project-1')
      })
    })
  })

  describe('Error handling', () => {
    it('shows error message when API fails', async () => {
      vi.mocked(regulatoryApi.listSubmissions).mockRejectedValue(
        new Error('API Error'),
      )
      vi.mocked(regulatoryApi.listChangeOfUseApplications).mockRejectedValue(
        new Error('API Error'),
      )
      vi.mocked(regulatoryApi.listHeritageSubmissions).mockRejectedValue(
        new Error('API Error'),
      )

      renderWithProviders(<RegulatoryDashboardPage />)

      await waitFor(() => {
        expect(
          screen.getByText(/Failed to load submissions/i),
        ).toBeInTheDocument()
      })
    })
  })
})
