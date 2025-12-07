import { ApiClient } from './client'

const apiClient = new ApiClient()

export interface TeamMember {
  id: string
  project_id: string
  user_id: string
  role: string
  is_active: boolean
  joined_at: string
  user?: {
    full_name: string
    email: string
    [key: string]: unknown
  }
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
    const { data } = await apiClient.get<TeamMember[]>('/team/members', {
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
      '/team/invite',
      { email, role },
      { params: { project_id: projectId } },
    )
    return data
  },

  removeMember: async (projectId: string, userId: string): Promise<boolean> => {
    const { data } = await apiClient.delete<boolean>(
      `/team/members/${userId}`,
      {
        params: { project_id: projectId },
      },
    )
    return data
  },

  acceptInvitation: async (token: string): Promise<TeamMember> => {
    const { data } = await apiClient.post<TeamMember>(
      `/team/invitations/${token}/accept`,
    )
    return data
  },
}
