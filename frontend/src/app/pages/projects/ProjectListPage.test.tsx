// @vitest-environment jsdom

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
  it('renders Singapore-first onboarding actions and opens the create dialog', async () => {
    const contextValue = createMockProjectContext()
    const user = userEvent.setup()

    renderWithProviders(<ProjectListPage />, contextValue)

    await waitFor(() => {
      expect(contextValue.refreshProjects).toHaveBeenCalled()
    })

    expect(
      screen.getByText('Singapore developer workspace'),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /open deal calculator/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /start workbook intake/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /open sample project/i }),
    ).toBeInTheDocument()
    expect(screen.getByText('No projects yet')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Start with the deal calculator, import an existing workbook, or open the seeded Singapore sample project.',
      ),
    ).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /create project/i }))

    expect(await screen.findByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('Create Project')).toBeInTheDocument()
  })
})
