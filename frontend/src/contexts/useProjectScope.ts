import { useRouterParams } from '../router'
import { useProject } from './useProject'

export function useProjectScope() {
  const { projectId: routeProjectId } = useRouterParams()
  const projectState = useProject()

  const projectId = routeProjectId ?? projectState.currentProject?.id ?? ''
  const projectName =
    routeProjectId && routeProjectId !== projectState.currentProject?.id
      ? routeProjectId
      : (projectState.currentProject?.name ?? routeProjectId ?? null)

  return {
    ...projectState,
    projectId,
    projectName,
    routeProjectId: routeProjectId ?? null,
    hasProject: projectId.length > 0,
  }
}
