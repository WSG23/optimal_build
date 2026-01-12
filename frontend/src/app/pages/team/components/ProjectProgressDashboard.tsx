/**
 * Project Progress Dashboard - Cross-team visibility dashboard.
 * Shows project progress across phases, team activity, and pending actions.
 */

import React, { useState, useEffect } from 'react'
import {
  Box,
  Chip,
  Grid,
  IconButton,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Typography,
  Avatar,
  Tooltip,
} from '@mui/material'
import {
  TrendingUp as TrendingUpIcon,
  CheckCircle as CheckCircleIcon,
  HourglassEmpty as HourglassIcon,
  Warning as WarningIcon,
  People as PeopleIcon,
  Assignment as AssignmentIcon,
  Timeline as TimelineIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import { GlassCard } from '../../../../components/canonical/GlassCard'
import {
  getMockPhases,
  type ProjectPhase,
  type TeamMemberActivity,
  type PendingApproval,
} from './projectProgressMockData'
import {
  getProjectProgress,
  type ProjectProgressApproval,
  type ProjectProgressPhase,
  type ProjectProgressTeamActivity,
} from '../../../../api/projects'

// Types are re-exported from projectProgressMockData.ts for backward compatibility
// Import types from './projectProgressMockData' directly

interface ProjectProgressDashboardProps {
  projectId: string
  projectName?: string
}

const PHASES_STORAGE_PREFIX = 'ob_project_phases'
const ACTIVITY_STORAGE_PREFIX = 'ob_team_activity'

function getStatusIcon(status: ProjectPhase['status']) {
  switch (status) {
    case 'completed':
      return <CheckCircleIcon color="success" />
    case 'in_progress':
      return <HourglassIcon color="primary" />
    case 'delayed':
      return <WarningIcon color="error" />
    default:
      return <HourglassIcon color="disabled" />
  }
}

function getStatusColor(status: ProjectPhase['status']) {
  switch (status) {
    case 'completed':
      return 'success'
    case 'in_progress':
      return 'primary'
    case 'delayed':
      return 'error'
    case 'not_started':
      return 'info'
    default:
      return 'primary' // Use 'primary' as fallback (works for both Chip and LinearProgress)
  }
}

function getPriorityColor(priority: PendingApproval['priority']) {
  switch (priority) {
    case 'urgent':
      return 'error'
    case 'high':
      return 'warning'
    case 'normal':
      return 'info' // Normal priority = informational, not brand/selection
    default:
      return 'default'
  }
}

function buildStorageKey(prefix: string, projectId: string) {
  return `${prefix}:${projectId}`
}

function loadStoredPhases(projectId: string): ProjectPhase[] {
  if (typeof window === 'undefined' || !projectId) {
    return []
  }
  const raw = window.localStorage.getItem(
    buildStorageKey(PHASES_STORAGE_PREFIX, projectId),
  )
  if (!raw) {
    return []
  }
  try {
    const parsed = JSON.parse(raw) as ProjectPhase[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function persistPhases(projectId: string, phases: ProjectPhase[]) {
  if (typeof window === 'undefined' || !projectId) {
    return
  }
  window.localStorage.setItem(
    buildStorageKey(PHASES_STORAGE_PREFIX, projectId),
    JSON.stringify(phases),
  )
}

function loadStoredActivity(projectId: string): TeamMemberActivity[] {
  if (typeof window === 'undefined' || !projectId) {
    return []
  }
  const raw = window.localStorage.getItem(
    buildStorageKey(ACTIVITY_STORAGE_PREFIX, projectId),
  )
  if (!raw) {
    return []
  }
  try {
    const parsed = JSON.parse(raw) as TeamMemberActivity[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function persistActivity(projectId: string, activity: TeamMemberActivity[]) {
  if (typeof window === 'undefined' || !projectId) {
    return
  }
  window.localStorage.setItem(
    buildStorageKey(ACTIVITY_STORAGE_PREFIX, projectId),
    JSON.stringify(activity),
  )
}

function hashProjectId(projectId: string) {
  let hash = 0
  for (let index = 0; index < projectId.length; index += 1) {
    hash = (hash << 5) - hash + projectId.charCodeAt(index)
    hash |= 0
  }
  return Math.abs(hash)
}

function seedPhases(projectId: string): ProjectPhase[] {
  const basePhases = getMockPhases()
  const seed = hashProjectId(projectId)
  return basePhases.map((phase, index) => {
    const offset = ((seed + index * 13) % 21) - 10
    const progress = Math.min(
      100,
      Math.max(0, Math.round(phase.progress + offset)),
    )
    const status: ProjectPhase['status'] =
      progress >= 100
        ? 'completed'
        : progress > 0
          ? 'in_progress'
          : 'not_started'
    return {
      ...phase,
      progress,
      status,
    }
  })
}

export const ProjectProgressDashboard: React.FC<
  ProjectProgressDashboardProps
> = ({ projectId, projectName = 'Project' }) => {
  const [phases, setPhases] = useState<ProjectPhase[]>([])
  const [teamActivity, setTeamActivity] = useState<TeamMemberActivity[]>([])
  const [pendingApprovals, setPendingApprovals] = useState<PendingApproval[]>(
    [],
  )
  const [loading, setLoading] = useState(true)

  const mapPhases = (
    phases: ProjectProgressPhase[],
    projectIdValue: string,
  ): ProjectPhase[] => {
    if (phases.length === 0) {
      return seedPhases(projectIdValue)
    }
    return phases.map((phase) => ({
      id: String(phase.id),
      name: phase.name,
      progress: Math.round(Number(phase.progress ?? 0)),
      status: (phase.status as ProjectPhase['status']) ?? 'not_started',
      startDate: phase.start_date ?? undefined,
      endDate: phase.end_date ?? undefined,
      milestones: [],
    }))
  }

  const mapActivity = (
    activity: ProjectProgressTeamActivity[],
  ): TeamMemberActivity[] =>
    activity.map((member) => ({
      id: member.id,
      name: member.name,
      email: member.email,
      role: member.role,
      lastActive: member.last_active_at
        ? new Date(member.last_active_at).toLocaleString()
        : '—',
      pendingTasks: member.pending_tasks,
      completedTasks: member.completed_tasks,
    }))

  const mapApprovals = (
    approvals: ProjectProgressApproval[],
  ): PendingApproval[] =>
    approvals.map((approval) => ({
      id: approval.id,
      title: approval.title,
      workflowName: approval.workflow_name,
      requiredBy: approval.required_by,
      priority: 'normal' as const,
    }))

  const fetchData = async () => {
    setLoading(true)
    const storedPhases = loadStoredPhases(projectId)
    const storedActivity = loadStoredActivity(projectId)
    try {
      const progress = await getProjectProgress(projectId)
      const mappedPhases = mapPhases(progress.phases, projectId)
      setPhases(mappedPhases)
      persistPhases(projectId, mappedPhases)
      const mappedActivity = mapActivity(progress.team_activity)
      setTeamActivity(mappedActivity)
      persistActivity(projectId, mappedActivity)
      setPendingApprovals(mapApprovals(progress.pending_approvals))
      setLoading(false)
      return
    } catch (error) {
      console.error('Failed to fetch project progress:', error)
      const basePhases =
        storedPhases.length > 0 ? storedPhases : seedPhases(projectId)
      setPhases(basePhases)
      persistPhases(projectId, basePhases)
      if (storedActivity.length > 0) {
        setTeamActivity(storedActivity)
      } else {
        setTeamActivity([])
      }
      setPendingApprovals([])
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId])

  const overallProgress =
    phases.length > 0
      ? Math.round(
          phases.reduce((acc, p) => acc + p.progress, 0) / phases.length,
        )
      : 0

  const totalPendingTasks = teamActivity.reduce(
    (acc, t) => acc + t.pendingTasks,
    0,
  )
  const totalCompletedTasks = teamActivity.reduce(
    (acc, t) => acc + t.completedTasks,
    0,
  )

  if (loading) {
    return (
      <Box sx={{ p: 'var(--ob-space-400)', textAlign: 'center' }}>
        <Typography>Loading project progress...</Typography>
        <LinearProgress
          sx={{ mt: 'var(--ob-space-200)', maxWidth: 300, mx: 'auto' }}
        />
      </Box>
    )
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-300)',
      }}
    >
      {/* Section header on background (not in card) */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Typography
          variant="subtitle2"
          sx={{
            color: 'text.secondary',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}
        >
          {projectName} - Progress Dashboard
        </Typography>
        <Tooltip title="Refresh">
          <IconButton onClick={fetchData} size="small">
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* KPI Cards - 4-column grid for metrics (atomic data) */}
      <Grid container spacing="var(--ob-space-150)">
        <Grid item xs={12} sm={6} md={3}>
          <GlassCard
            sx={{
              p: 'var(--ob-space-150)',
              background:
                'linear-gradient(135deg, var(--ob-brand-700) 0%, var(--ob-brand-400) 100%)',
              color: 'white',
            }}
          >
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-100)',
              }}
            >
              <TrendingUpIcon />
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-2xs)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.1em',
                }}
              >
                Overall Progress
              </Typography>
            </Box>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-3xl)',
                fontWeight: 700,
                mt: 'var(--ob-space-050)',
              }}
            >
              {overallProgress}%
            </Typography>
            <LinearProgress
              variant="determinate"
              value={overallProgress}
              sx={{
                mt: 'var(--ob-space-100)',
                bgcolor: 'rgba(255,255,255,0.3)',
                '& .MuiLinearProgress-bar': { bgcolor: 'white' },
              }}
            />
          </GlassCard>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <GlassCard
            sx={{
              p: 'var(--ob-space-150)',
              background:
                'linear-gradient(135deg, var(--ob-success-700) 0%, var(--ob-success-400) 100%)',
              color: 'white',
            }}
          >
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-100)',
              }}
            >
              <CheckCircleIcon />
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-2xs)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.1em',
                }}
              >
                Completed Tasks
              </Typography>
            </Box>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-3xl)',
                fontWeight: 700,
                mt: 'var(--ob-space-050)',
              }}
            >
              {totalCompletedTasks}
            </Typography>
          </GlassCard>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <GlassCard
            sx={{
              p: 'var(--ob-space-150)',
              background:
                'linear-gradient(135deg, var(--ob-warning-700) 0%, var(--ob-warning-400) 100%)',
              color: 'white',
            }}
          >
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-100)',
              }}
            >
              <HourglassIcon />
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-2xs)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.1em',
                }}
              >
                Pending Tasks
              </Typography>
            </Box>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-3xl)',
                fontWeight: 700,
                mt: 'var(--ob-space-050)',
              }}
            >
              {totalPendingTasks}
            </Typography>
          </GlassCard>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <GlassCard
            sx={{
              p: 'var(--ob-space-150)',
              background:
                'linear-gradient(135deg, var(--ob-info-700) 0%, var(--ob-info-400) 100%)',
              color: 'white',
            }}
          >
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-100)',
              }}
            >
              <PeopleIcon />
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-2xs)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.1em',
                }}
              >
                Team Members
              </Typography>
            </Box>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-3xl)',
                fontWeight: 700,
                mt: 'var(--ob-space-050)',
              }}
            >
              {teamActivity.length}
            </Typography>
          </GlassCard>
        </Grid>
      </Grid>

      {/* Phase Progress & Pending Approvals - Master-Detail layout */}
      <Grid container spacing="var(--ob-space-150)">
        {/* Phase Progress Timeline */}
        <Grid item xs={12} md={8}>
          {/* Section header on background */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--ob-space-100)',
              mb: 'var(--ob-space-150)',
            }}
          >
            <TimelineIcon color="primary" />
            <Typography variant="h6">Phase Progress</Typography>
          </Box>
          {/* Data in GlassCard */}
          <GlassCard sx={{ p: 'var(--ob-space-200)' }}>
            {phases.map((phase, index) => (
              <Box
                key={phase.id}
                sx={{
                  mb: index < phases.length - 1 ? 'var(--ob-space-300)' : 0,
                }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    mb: 'var(--ob-space-100)',
                  }}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 'var(--ob-space-100)',
                    }}
                  >
                    {getStatusIcon(phase.status)}
                    <Typography variant="subtitle1" fontWeight="medium">
                      {phase.name}
                    </Typography>
                  </Box>
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 'var(--ob-space-100)',
                    }}
                  >
                    <Chip
                      label={phase.status.replace('_', ' ')}
                      color={
                        getStatusColor(phase.status) as
                          | 'default'
                          | 'primary'
                          | 'secondary'
                          | 'error'
                          | 'info'
                          | 'success'
                          | 'warning'
                      }
                      size="small"
                      sx={{ textTransform: 'capitalize' }}
                    />
                    <Typography variant="body2" color="text.secondary">
                      {phase.progress}%
                    </Typography>
                  </Box>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={phase.progress}
                  sx={{
                    height: 8,
                    borderRadius: 'var(--ob-radius-sm)',
                    mb: 'var(--ob-space-100)',
                  }}
                  color={
                    getStatusColor(phase.status) as
                      | 'inherit'
                      | 'primary'
                      | 'secondary'
                      | 'error'
                      | 'info'
                      | 'success'
                      | 'warning'
                  }
                />
                <Box
                  sx={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: 'var(--ob-space-050)',
                  }}
                >
                  {phase.milestones.map((m, idx) => (
                    <Chip
                      key={idx}
                      label={m.name}
                      size="small"
                      variant={m.completed ? 'filled' : 'outlined'}
                      color={m.completed ? 'success' : 'default'}
                      sx={{ fontSize: 'var(--ob-font-size-xs)' }}
                    />
                  ))}
                </Box>
              </Box>
            ))}
          </GlassCard>
        </Grid>

        {/* Pending Approvals */}
        <Grid item xs={12} md={4}>
          {/* Section header on background */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--ob-space-100)',
              mb: 'var(--ob-space-150)',
            }}
          >
            <AssignmentIcon color="warning" />
            <Typography variant="h6">Pending Approvals</Typography>
            <Chip
              label={pendingApprovals.length}
              size="small"
              color="warning"
            />
          </Box>
          {/* Data in GlassCard */}
          <GlassCard sx={{ p: 'var(--ob-space-200)' }}>
            <List dense disablePadding>
              {pendingApprovals.map((approval) => (
                <ListItem
                  key={approval.id}
                  sx={{
                    borderRadius: 'var(--ob-radius-sm)',
                    mb: 'var(--ob-space-100)',
                    bgcolor: 'action.hover',
                    cursor: 'pointer',
                    '&:hover': { bgcolor: 'action.selected' },
                  }}
                >
                  <ListItemText
                    primary={
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 'var(--ob-space-100)',
                        }}
                      >
                        <Typography variant="body2" fontWeight="medium">
                          {approval.title}
                        </Typography>
                        <Chip
                          label={approval.priority}
                          size="small"
                          color={
                            getPriorityColor(approval.priority) as
                              | 'default'
                              | 'primary'
                              | 'secondary'
                              | 'error'
                              | 'info'
                              | 'success'
                              | 'warning'
                          }
                          sx={{
                            fontSize: 'var(--ob-font-size-2xs)',
                            height: 'var(--ob-space-200)',
                          }}
                        />
                      </Box>
                    }
                    secondary={
                      <>
                        <Typography variant="caption" display="block">
                          {approval.workflowName}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Assigned to: {approval.requiredBy}
                        </Typography>
                      </>
                    }
                  />
                </ListItem>
              ))}
              {pendingApprovals.length === 0 && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  textAlign="center"
                >
                  No pending approvals
                </Typography>
              )}
            </List>
          </GlassCard>
        </Grid>
      </Grid>

      {/* Team Activity - Section header on background, data in card */}
      <Box>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--ob-space-100)',
            mb: 'var(--ob-space-150)',
          }}
        >
          <PeopleIcon color="primary" />
          <Typography variant="h6">Team Activity</Typography>
        </Box>
        {/* Team member cards as siblings (no nested container) */}
        <Grid container spacing="var(--ob-space-150)">
          {teamActivity.map((member) => (
            <Grid item xs={12} sm={6} md={3} key={member.id}>
              <GlassCard sx={{ p: 'var(--ob-space-150)', height: '100%' }}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--ob-space-150)',
                    mb: 'var(--ob-space-200)',
                  }}
                >
                  <Avatar sx={{ bgcolor: 'primary.main' }}>
                    {member.name.charAt(0)}
                  </Avatar>
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography variant="subtitle2" noWrap>
                      {member.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" noWrap>
                      {member.role}
                    </Typography>
                  </Box>
                </Box>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                  }}
                >
                  <Box>
                    <Typography
                      sx={{
                        fontSize: 'var(--ob-font-size-2xs)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.1em',
                        color: 'text.secondary',
                      }}
                    >
                      Pending
                    </Typography>
                    <Typography variant="h6" color="warning.main">
                      {member.pendingTasks}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography
                      sx={{
                        fontSize: 'var(--ob-font-size-2xs)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.1em',
                        color: 'text.secondary',
                      }}
                    >
                      Completed
                    </Typography>
                    <Typography variant="h6" color="success.main">
                      {member.completedTasks}
                    </Typography>
                  </Box>
                </Box>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ display: 'block', mt: 'var(--ob-space-100)' }}
                >
                  Active {member.lastActive}
                </Typography>
              </GlassCard>
            </Grid>
          ))}
        </Grid>
      </Box>
    </Box>
  )
}
