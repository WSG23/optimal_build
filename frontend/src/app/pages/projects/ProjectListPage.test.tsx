import type { ReactElement } from 'react'

import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import {
  ProjectContext,
  type ProjectContextValue,
} from '../../../contexts/projectContextDef'
import { ProjectListPage } from './ProjectListPage'

function createMockProjectContext(
  overrides: Partial<ProjectContextValue> = {},
): ProjectContextValue {
  return {
    currentProject: null,
    projects: [],
    isProjectLoading: false,
    projectError: null,
    setCurrentProject: vi.fn(),
    clearProject: vi.fn(),
    refreshProjects: vi.fn().mockResolvedValue(undefined),
    createProject: vi.fn().mockResolvedValue({
      id: 'project-1',
      name: 'Project 1',
      status: 'active',
    }),
    ...overrides,
  }
}

function renderWithProviders(
  ui: ReactElement,
  contextValue: ProjectContextValue = createMockProjectContext(),
) {
  return render(
    <ProjectContext.Provider value={contextValue}>
      {ui}
    </ProjectContext.Provider>,
  )
}

describe('ProjectListPage', () => {
  it('renders the canonical empty state and opens the create dialog from its CTA', async () => {
    const contextValue = createMockProjectContext()
    const user = userEvent.setup()

    renderWithProviders(<ProjectListPage />, contextValue)

    await waitFor(() => {
      expect(contextValue.refreshProjects).toHaveBeenCalled()
    })

    expect(screen.getByText('No projects yet')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Create a project to start feasibility, finance, and intelligence workflows.',
      ),
    ).toBeInTheDocument()

    const createButtons = screen.getAllByRole('button', {
      name: /create project/i,
    })
    await user.click(createButtons[1])

    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('Create Project')).toBeInTheDocument()
  })
})
