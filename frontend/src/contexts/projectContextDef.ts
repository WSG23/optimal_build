import { createContext } from 'react'

export interface ProjectSummary {
  id: string
  name: string
  status?: string
}

export interface ProjectError {
  type: 'not_found' | 'forbidden' | 'invalid' | 'unknown'
  message: string
}

export interface ProjectContextValue {
  currentProject: ProjectSummary | null
  projects: ProjectSummary[]
  isProjectLoading: boolean
  projectError: ProjectError | null
  setCurrentProject: (project: ProjectSummary) => void
  clearProject: () => void
  refreshProjects: () => Promise<void>
  createProject: (payload: {
    name: string
    description?: string
  }) => Promise<ProjectSummary>
}

export const ProjectContext = createContext<ProjectContextValue | null>(null)
