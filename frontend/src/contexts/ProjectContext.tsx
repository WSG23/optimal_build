import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'

import { ApiError, isAbortError } from '../api/utils/request'
import { createProject, getProject, listProjects } from '../api/projects'
import { useRouterParams } from '../router'
import {
  ProjectContext,
  ProjectError,
  type ProjectSummary,
} from './projectContextDef'

const STORAGE_KEY = 'ob_current_project'

function readStoredProject(): ProjectSummary | null {
  if (typeof window === 'undefined') {
    return null
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as ProjectSummary
    if (!parsed?.id || !parsed?.name) {
      return null
    }
    return parsed
  } catch {
    return null
  }
}

function persistProject(project: ProjectSummary | null): void {
  if (typeof window === 'undefined') {
    return
  }
  if (!project) {
    window.localStorage.removeItem(STORAGE_KEY)
    return
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(project))
}

function normaliseProject(payload: {
  id: string
  name: string
  status?: string | null
}): ProjectSummary {
  return {
    id: payload.id,
    name: payload.name,
    status: payload.status ?? undefined,
  }
}

function mapProjectError(error: unknown): ProjectError {
  if (error instanceof ApiError) {
    if (error.status === 404) {
      return { type: 'not_found', message: 'Project not found.' }
    }
    if (error.status === 403) {
      return { type: 'forbidden', message: 'No access to this project.' }
    }
    if (error.status === 400 || error.status === 422) {
      return { type: 'invalid', message: 'Invalid project ID.' }
    }
  }
  return {
    type: 'unknown',
    message: error instanceof Error ? error.message : 'Unable to load project.',
  }
}

export function ProjectProvider({ children }: { children: ReactNode }) {
  const params = useRouterParams()
  const [currentProject, setCurrentProjectState] =
    useState<ProjectSummary | null>(() => readStoredProject())
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [isProjectLoading, setIsProjectLoading] = useState(false)
  const [projectError, setProjectError] = useState<ProjectError | null>(null)
  const loadController = useRef<AbortController | null>(null)

  const refreshProjects = useCallback(async () => {
    setIsProjectLoading(true)
    setProjectError(null)
    try {
      const payload = await listProjects()
      setProjects(payload.map(normaliseProject))
    } catch (error) {
      if (isAbortError(error)) {
        return
      }
      setProjectError(mapProjectError(error))
    } finally {
      setIsProjectLoading(false)
    }
  }, [])

  const setCurrentProject = useCallback((project: ProjectSummary) => {
    setCurrentProjectState(project)
    setProjectError(null)
    persistProject(project)
  }, [])

  const clearProject = useCallback(() => {
    setCurrentProjectState(null)
    setProjectError(null)
    persistProject(null)
  }, [])

  const loadProjectById = useCallback(async (projectId: string) => {
    if (!projectId) {
      return
    }
    loadController.current?.abort()
    const controller = new AbortController()
    loadController.current = controller
    setIsProjectLoading(true)
    setProjectError(null)
    try {
      const payload = await getProject(projectId)
      if (controller.signal.aborted) {
        return
      }
      const project = normaliseProject(payload)
      setCurrentProjectState(project)
      persistProject(project)
    } catch (error) {
      if (isAbortError(error)) {
        return
      }
      setProjectError(mapProjectError(error))
      setCurrentProjectState(null)
      persistProject(null)
    } finally {
      if (!controller.signal.aborted) {
        setIsProjectLoading(false)
      }
      if (loadController.current === controller) {
        loadController.current = null
      }
    }
  }, [])

  const handleCreateProject = useCallback(
    async (payload: { name: string; description?: string }) => {
      setIsProjectLoading(true)
      setProjectError(null)
      try {
        const created = await createProject(payload)
        const project = normaliseProject(created)
        setCurrentProjectState(project)
        persistProject(project)
        await refreshProjects()
        return project
      } catch (error) {
        setProjectError(mapProjectError(error))
        throw error
      } finally {
        setIsProjectLoading(false)
      }
    },
    [refreshProjects],
  )

  useEffect(() => {
    void refreshProjects()
  }, [refreshProjects])

  useEffect(() => {
    if (!params.projectId) {
      return
    }
    if (params.projectId === currentProject?.id) {
      return
    }
    void loadProjectById(params.projectId)
  }, [currentProject?.id, loadProjectById, params.projectId])

  const contextValue = useMemo(
    () => ({
      currentProject,
      projects,
      isProjectLoading,
      projectError,
      setCurrentProject,
      clearProject,
      refreshProjects,
      createProject: handleCreateProject,
    }),
    [
      currentProject,
      projects,
      isProjectLoading,
      projectError,
      setCurrentProject,
      clearProject,
      refreshProjects,
      handleCreateProject,
    ],
  )

  return (
    <ProjectContext.Provider value={contextValue}>
      {children}
    </ProjectContext.Provider>
  )
}
