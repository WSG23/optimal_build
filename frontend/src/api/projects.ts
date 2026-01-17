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

export interface ProjectProgressPhase {
  id: string
  name: string
  progress: number
  status: string
  start_date?: string | null
  end_date?: string | null
  source?: string
}

export interface ProjectProgressApproval {
  id: string
  title: string
  workflow_name: string
  required_by: string
  status: string
}

export interface ProjectProgressTeamActivity {
  id: string
  name: string
  email: string
  role: string
  last_active_at?: string | null
  pending_tasks: number
  completed_tasks: number
}

export interface ProjectProgressSummary {
  total_steps: number
  approved_steps: number
  pending_steps: number
}

export interface ProjectProgressResponse {
  project: {
    id: string
    name: string
    current_phase?: string | null
  }
  phases: ProjectProgressPhase[]
  workflow_summary: ProjectProgressSummary
  pending_approvals: ProjectProgressApproval[]
  team_activity: ProjectProgressTeamActivity[]
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

export async function getProjectProgress(
  projectId: string,
): Promise<ProjectProgressResponse> {
  return getJson<ProjectProgressResponse>(
    `/api/v1/projects/${projectId}/progress`,
  )
}

export interface DashboardKPI {
  label: string
  value: string
  sub_value?: string | null
  trend?: string | null
  trend_direction?: 'up' | 'down' | 'neutral' | null
}

export interface DashboardModule {
  label: string
  path: string
  enabled: boolean
  description?: string | null
}

export interface ProjectDashboardResponse {
  kpis: DashboardKPI[]
  modules: DashboardModule[]
}

export async function getProjectDashboard(
  projectId: string,
): Promise<ProjectDashboardResponse> {
  return getJson<ProjectDashboardResponse>(
    `/api/v1/projects/${projectId}/dashboard`,
  )
}
