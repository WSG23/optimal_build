import { getJson, postJson } from './utils/request'

export interface ProjectResponse {
  id: string
  name: string
  description?: string | null
  status?: string | null
}

export interface ProjectCreateRequest {
  name: string
  description?: string
}

function mapProject(payload: ProjectResponse): ProjectResponse {
  return {
    id: String(payload.id ?? '').trim(),
    name: String(payload.name ?? '').trim(),
    description:
      typeof payload.description === 'string' ? payload.description : null,
    status: typeof payload.status === 'string' ? payload.status : null,
  }
}

export async function listProjects(): Promise<ProjectResponse[]> {
  const payload = await getJson<ProjectResponse[]>('/api/v1/projects/list')
  return payload.map(mapProject).filter((project) => project.id && project.name)
}

export async function getProject(projectId: string): Promise<ProjectResponse> {
  const payload = await getJson<ProjectResponse>(
    `/api/v1/projects/${projectId}`,
  )
  return mapProject(payload)
}

export async function createProject(
  request: ProjectCreateRequest,
): Promise<ProjectResponse> {
  const payload = await postJson<ProjectResponse>(
    '/api/v1/projects/create',
    request,
  )
  return mapProject(payload)
}
