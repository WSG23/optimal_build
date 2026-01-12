import React, { useState, useEffect, useRef } from 'react'
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
} from '@mui/material'
import {
  Add as AddIcon,
  Person as PersonIcon,
  Task as TaskIcon,
  Dashboard as DashboardIcon,
} from '@mui/icons-material'
import { Button } from '../../../components/canonical/Button'
import { GlassCard } from '../../../components/canonical/GlassCard'
import { teamApi, TeamMember } from '../../../api/team'
import { WorkflowDashboard } from './components/WorkflowDashboard'
import { ProjectProgressDashboard } from './components/ProjectProgressDashboard'
import { useProject } from '../../../contexts/useProject'

const STORAGE_PREFIX = 'ob_team_members'

const buildStorageKey = (pid: string) => `${STORAGE_PREFIX}:${pid}`

const loadStoredMembers = (pid: string): TeamMember[] => {
  if (typeof window === 'undefined' || !pid) {
    return []
  }
  const raw = window.localStorage.getItem(buildStorageKey(pid))
  if (!raw) {
    return []
  }
  try {
    const parsed = JSON.parse(raw) as TeamMember[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

const persistMembers = (pid: string, data: TeamMember[]) => {
  if (typeof window === 'undefined' || !pid) {
    return
  }
  window.localStorage.setItem(buildStorageKey(pid), JSON.stringify(data))
}
// If not using react-router params for project ID, we might need to get it from context or props.
// For now, I'll assume we grab it from URL or a hardcoded one for dev if not available.
// Actually, let's try to get it from context/store if typical, or just use a placeholder if we can't find it.
// Wait, the page is likely routed with /projects/:projectId/team or similar?
// Let's assume useParams() works or we need to pass a prop.
// To be safe I will use a hook if I can find one, or just assume useParams() has it or a prop.
// checking imports... I don't see useParams in original file. The original file didn't use props either.
// Maybe it's a top level page that gets the project from a global store.
// Let's assume for now we might need to extract it or pass it.
// I'll add `projectId` as a prop but also try to get it from useParams.

export const TeamManagementPage: React.FC = () => {
  const { currentProject, isProjectLoading, projectError } = useProject()
  const projectId = currentProject?.id ?? ''

  const [activeTab, setActiveTab] = useState(0)
  const [members, setMembers] = useState<TeamMember[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [removingMemberId, setRemovingMemberId] = useState<string | null>(null)

  const [inviteOpen, setInviteOpen] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('consultant')
  const [inviting, setInviting] = useState(false)

  // Ref to prevent multiple fetches and track if we've already loaded data
  const hasFetchedRef = useRef(false)
  const isFetchingRef = useRef(false)

  useEffect(() => {
    hasFetchedRef.current = false
    isFetchingRef.current = false
    setMembers([])
  }, [projectId])

  useEffect(() => {
    if (!projectId) {
      return
    }
    // Only fetch if we're on the team members tab, haven't fetched yet, and not currently fetching
    if (activeTab !== 0 || hasFetchedRef.current || isFetchingRef.current) {
      return
    }

    const fetchMembers = async () => {
      isFetchingRef.current = true
      setLoading(true)
      setError(null)
      const storedMembers = loadStoredMembers(projectId)
      try {
        const data = await teamApi.listMembers(projectId)
        if (data.length > 0) {
          setMembers(data)
          persistMembers(projectId, data)
        } else if (storedMembers.length > 0) {
          setMembers(storedMembers)
        } else {
          setMembers([])
        }
        hasFetchedRef.current = true
      } catch (err) {
        console.error(err)
        if (storedMembers.length > 0) {
          setMembers(storedMembers)
        } else {
          setMembers([])
        }
        hasFetchedRef.current = true // Mark as fetched even on error to prevent infinite retries
      } finally {
        setLoading(false)
        isFetchingRef.current = false
      }
    }

    void fetchMembers()
  }, [activeTab, projectId])

  const handleInvite = async () => {
    if (!projectId) {
      return
    }
    setInviting(true)
    setError(null)
    try {
      await teamApi.inviteMember(projectId, inviteEmail, inviteRole)
      const pendingMember: TeamMember = {
        id: `invite-${Date.now()}`,
        project_id: projectId,
        user_id: `invite-${Date.now()}`,
        role: inviteRole,
        is_active: false,
        joined_at: new Date().toISOString(),
        user: {
          full_name: inviteEmail.split('@')[0] ?? inviteEmail,
          email: inviteEmail,
        },
      }
      setMembers((prev) => {
        const next = [pendingMember, ...prev]
        persistMembers(projectId, next)
        return next
      })
      setInviteOpen(false)
      setInviteEmail('')
      // Ideally refresh members list if they show up immediately (pending),
      // but standard invitation flow usually means they don't show up in 'members' until accepted
      // unless we list invitations separately.
      // For now, let's just show a success message or re-fetch.
      alert('Invitation sent!')
    } catch (err) {
      console.error(err)
      setError('Failed to send invitation')
    } finally {
      setInviting(false)
    }
  }

  const handleRemoveMember = async (member: TeamMember) => {
    if (!projectId) {
      return
    }
    if (member.user_id.startsWith('invite-')) {
      setMembers((prev) => {
        const next = prev.filter((item) => item.id !== member.id)
        persistMembers(projectId, next)
        return next
      })
      return
    }
    setRemovingMemberId(member.id)
    setError(null)
    try {
      await teamApi.removeMember(projectId, member.user_id)
      setMembers((prev) => {
        const next = prev.filter((item) => item.id !== member.id)
        persistMembers(projectId, next)
        return next
      })
    } catch (err) {
      console.error(err)
      setError('Failed to remove member')
    } finally {
      setRemovingMemberId(null)
    }
  }

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue)
  }

  if (!projectId) {
    return (
      <Box sx={{ width: '100%' }}>
        {isProjectLoading ? (
          <CircularProgress />
        ) : (
          <Alert severity={projectError ? 'error' : 'info'}>
            {projectError?.message ??
              'Select a project to manage team coordination.'}
          </Alert>
        )}
      </Box>
    )
  }

  return (
    <Box sx={{ width: '100%' }}>
      {/* Compact Page Header - TIGHT layout with animation */}
      <Box
        component="header"
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 'var(--ob-space-100)',
          mb: 'var(--ob-space-150)',
          animation:
            'ob-slide-down-fade var(--ob-motion-header-duration) var(--ob-motion-header-ease) both',
        }}
      >
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
            Team Management
          </Typography>
          <Typography
            variant="body2"
            sx={{ color: 'text.secondary', mt: 'var(--ob-space-025)' }}
          >
            Manage project team members and workflow approvals
          </Typography>
          {currentProject && (
            <Typography
              variant="body2"
              sx={{ color: 'text.secondary', mt: 'var(--ob-space-025)' }}
            >
              Project: {currentProject.name}
            </Typography>
          )}
        </Box>
        {activeTab === 0 && (
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setInviteOpen(true)}
          >
            <AddIcon sx={{ fontSize: '1rem', mr: 'var(--ob-space-050)' }} />
            Invite Member
          </Button>
        )}
      </Box>

      {/* Tabs - Direct on Grid */}
      <Box
        sx={{
          borderBottom: 1,
          borderColor: 'divider',
          mb: 'var(--ob-space-200)',
        }}
      >
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          aria-label="team management tabs"
        >
          <Tab
            icon={<PersonIcon />}
            iconPosition="start"
            label="Team Members"
          />
          <Tab
            icon={<TaskIcon />}
            iconPosition="start"
            label="Approvals & Workflows"
          />
          <Tab
            icon={<DashboardIcon />}
            iconPosition="start"
            label="Progress Dashboard"
          />
        </Tabs>
      </Box>

      {error && (
        <Alert
          severity="error"
          sx={{ mb: 'var(--ob-space-300)' }}
          onClose={() => setError(null)}
        >
          {error}
        </Alert>
      )}

      {/* Tab 0: Team Members - Content vs Context: header on background, data in card */}
      {activeTab === 0 && (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--ob-space-150)',
          }}
        >
          {/* Section header on background (not in card) */}
          <Typography
            variant="subtitle2"
            sx={{
              color: 'text.secondary',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            Team Members
          </Typography>
          {/* Data table in GlassCard */}
          <GlassCard sx={{ p: 'var(--ob-space-150)' }}>
            <TableContainer sx={{ width: '100%', overflowX: 'auto' }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Email</TableCell>
                    <TableCell>Role</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell
                        colSpan={5}
                        align="center"
                        sx={{ py: 'var(--ob-space-400)' }}
                      >
                        <CircularProgress size={24} />
                        <Typography
                          variant="body2"
                          sx={{
                            mt: 'var(--ob-space-100)',
                            color: 'text.secondary',
                          }}
                        >
                          Loading team...
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : members.length === 0 ? (
                    <TableRow>
                      <TableCell
                        colSpan={5}
                        align="center"
                        sx={{ py: 'var(--ob-space-400)' }}
                      >
                        <Typography variant="body2" color="text.secondary">
                          No team members found.
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    members.map((member) => {
                      const isPendingInvite =
                        member.user_id.startsWith('invite-')
                      return (
                        <TableRow key={member.id} hover>
                          <TableCell sx={{ fontWeight: 500 }}>
                            {member.user?.full_name || 'Unknown'}
                          </TableCell>
                          <TableCell>
                            {member.user?.email || 'No email'}
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={member.role}
                              size="small"
                              sx={{
                                textTransform: 'capitalize',
                                bgcolor:
                                  member.role === 'developer'
                                    ? 'primary.main'
                                    : 'default',
                              }}
                            />
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={
                                isPendingInvite
                                  ? 'Pending'
                                  : member.is_active
                                    ? 'Active'
                                    : 'Inactive'
                              }
                              size="small"
                              color={
                                isPendingInvite
                                  ? 'warning'
                                  : member.is_active
                                    ? 'success'
                                    : 'default'
                              }
                              variant="outlined"
                              sx={{ textTransform: 'capitalize' }}
                            />
                          </TableCell>
                          <TableCell align="right">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleRemoveMember(member)}
                              disabled={removingMemberId === member.id}
                              sx={{ color: 'error.main' }}
                            >
                              {removingMemberId === member.id
                                ? 'Removing...'
                                : 'Remove'}
                            </Button>
                          </TableCell>
                        </TableRow>
                      )
                    })
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </GlassCard>
        </Box>
      )}

      {/* Tab 1: Approvals & Workflows - No wrapper, component manages own layout */}
      {activeTab === 1 && <WorkflowDashboard projectId={projectId} />}

      {/* Tab 2: Progress Dashboard - No wrapper, component manages own layout */}
      {activeTab === 2 && (
        <ProjectProgressDashboard
          projectId={projectId}
          projectName={currentProject?.name ?? 'Project'}
        />
      )}

      {/* Invite Dialog */}
      <Dialog
        open={inviteOpen}
        onClose={() => setInviteOpen(false)}
        PaperProps={{ className: 'team-invite-dialog' }}
      >
        <DialogTitle>Invite New Member</DialogTitle>
        <DialogContent>
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-200)',
              mt: 'var(--ob-space-100)',
            }}
          >
            <TextField
              label="Email Address"
              fullWidth
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              disabled={inviting}
            />
            <TextField
              select
              label="Role"
              fullWidth
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
              disabled={inviting}
            >
              <MenuItem value="consultant">Consultant</MenuItem>
              <MenuItem value="architect">Architect</MenuItem>
              <MenuItem value="engineer">Engineer</MenuItem>
              <MenuItem value="viewer">Viewer</MenuItem>
            </TextField>
          </Box>
        </DialogContent>
        <DialogActions
          sx={{ p: 'var(--ob-space-200)', gap: 'var(--ob-space-100)' }}
        >
          <Button
            variant="ghost"
            onClick={() => setInviteOpen(false)}
            disabled={inviting}
          >
            Cancel
          </Button>
          <Button variant="primary" onClick={handleInvite} disabled={inviting}>
            {inviting ? 'Sending...' : 'Send Invitation'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
