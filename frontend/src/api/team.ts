import { ApiClient } from './client'

const apiClient = new ApiClient()

export interface TeamMember {
  id: string
  project_id: string
  user_id: string
  role: string
  is_active: boolean
  joined_at: string
  last_active_at?: string | null
  user?: {
    full_name: string
    email: string
    [key: string]: unknown
  }
}

export interface TeamMemberActivity {
  id: string
  user_id: string
  project_id: string
  role: string
  joined_at: string
  last_active_at?: string | null
  name: string
  email: string
  pending_tasks: number
  completed_tasks: number
}

export interface TeamActivityStats {
  members: TeamMemberActivity[]
  total_pending_tasks: number
  total_completed_tasks: number
  active_members_count: number
}

export interface TeamInvitation {
  id: string
  project_id: string
  email: string
  role: string
  status: 'pending' | 'accepted' | 'expired' | 'revoked'
  token?: string // Only returned for reviewer/admin in dev mode/response
  expires_at: string
}

export const teamApi = {
  listMembers: async (projectId: string): Promise<TeamMember[]> => {
    const { data } = await apiClient.get<TeamMember[]>('api/v1/team/members', {
      params: { project_id: projectId },
    })
    return data
  },

  inviteMember: async (
    projectId: string,
    email: string,
    role: string,
  ): Promise<TeamInvitation> => {
    const { data } = await apiClient.post<TeamInvitation>(
      'api/v1/team/invite',
      { email, role },
      { params: { project_id: projectId } },
    )
    return data
  },

  removeMember: async (projectId: string, userId: string): Promise<boolean> => {
    const { data } = await apiClient.delete<boolean>(
      `api/v1/team/members/${userId}`,
      {
        params: { project_id: projectId },
      },
    )
    return data
  },

  acceptInvitation: async (token: string): Promise<TeamMember> => {
    const { data } = await apiClient.post<TeamMember>(
      `api/v1/team/invitations/${token}/accept`,
    )
    return data
  },

  getTeamActivity: async (projectId: string): Promise<TeamActivityStats> => {
    const { data } = await apiClient.get<TeamActivityStats>(
      'api/v1/team/activity',
      {
        params: { project_id: projectId },
      },
    )
    return data
  },

  updateMemberActivity: async (
    projectId: string,
    userId: string,
  ): Promise<TeamMember> => {
    const { data } = await apiClient.post<TeamMember>(
      `api/v1/team/members/${userId}/activity`,
      {},
      { params: { project_id: projectId } },
    )
    return data
  },
}
