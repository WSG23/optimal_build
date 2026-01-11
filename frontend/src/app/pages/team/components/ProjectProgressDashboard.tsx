/**
 * Project Progress Dashboard - Cross-team visibility dashboard.
 * Shows project progress across phases, team activity, and pending actions.
 */

import React, { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Chip,
  Divider,
  Grid,
  IconButton,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Paper,
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
import {
  getMockPhases,
  getMockTeamActivity,
  getMockPendingApprovals,
  type ProjectPhase,
  type TeamMemberActivity,
  type PendingApproval,
} from './projectProgressMockData'
import { workflowApi, type ApprovalWorkflow } from '../../../../api/workflow'

// Types are re-exported from projectProgressMockData.ts for backward compatibility
// Import types from './projectProgressMockData' directly

interface ProjectProgressDashboardProps {
  projectId: string
  projectName?: string
}

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

export const ProjectProgressDashboard: React.FC<
  ProjectProgressDashboardProps
> = ({ projectId, projectName = 'Project' }) => {
  const [phases, setPhases] = useState<ProjectPhase[]>([])
  const [teamActivity, setTeamActivity] = useState<TeamMemberActivity[]>([])
  const [pendingApprovals, setPendingApprovals] = useState<PendingApproval[]>(
    [],
  )
  const [loading, setLoading] = useState(true)

  // Convert workflows to pending approvals format
  const extractPendingApprovals = (
    workflows: ApprovalWorkflow[],
  ): PendingApproval[] => {
    const approvals: PendingApproval[] = []
    workflows.forEach((workflow) => {
      workflow.steps
        .filter((step) => step.status === 'in_review')
        .forEach((step) => {
          approvals.push({
            id: step.id,
            title: step.name,
            workflowName: workflow.name,
            requiredBy: step.approver_role || 'Any team member',
            priority: 'normal' as const,
          })
        })
    })
    return approvals
  }

  const fetchData = async () => {
    setLoading(true)
    try {
      // Fetch real workflows for pending approvals
      const workflows = await workflowApi.listWorkflows(projectId)
      const realApprovals = extractPendingApprovals(workflows)

      // Use real pending approvals if available, otherwise fall back to mock
      if (realApprovals.length > 0) {
        setPendingApprovals(realApprovals)
      } else {
        setPendingApprovals(getMockPendingApprovals())
      }
    } catch (error) {
      console.error('Failed to fetch workflows:', error)
      // Fallback to mock data on error
      setPendingApprovals(getMockPendingApprovals())
    }

    // Still use mock data for phases and team activity (would need separate APIs)
    setPhases(getMockPhases())
    setTeamActivity(getMockTeamActivity())
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
    <Box>
      {/* Header with overall progress */}
      <Box sx={{ mb: 'var(--ob-space-400)' }}>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 'var(--ob-space-200)',
          }}
        >
          <Typography variant="h5" fontWeight="bold">
            {projectName} - Progress Dashboard
          </Typography>
          <Tooltip title="Refresh">
            <IconButton onClick={fetchData}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>

        {/* KPI Cards */}
        <Grid container spacing="var(--ob-space-200)">
          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                background:
                  'linear-gradient(135deg, var(--ob-brand-700) 0%, var(--ob-brand-400) 100%)',
                color: 'white',
              }}
            >
              <CardContent>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--ob-space-100)',
                  }}
                >
                  <TrendingUpIcon />
                  <Typography variant="caption">Overall Progress</Typography>
                </Box>
                <Typography variant="h4" fontWeight="bold">
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
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                background:
                  'linear-gradient(135deg, var(--ob-success-700) 0%, var(--ob-success-400) 100%)',
                color: 'white',
              }}
            >
              <CardContent>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--ob-space-100)',
                  }}
                >
                  <CheckCircleIcon />
                  <Typography variant="caption">Completed Tasks</Typography>
                </Box>
                <Typography variant="h4" fontWeight="bold">
                  {totalCompletedTasks}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                background:
                  'linear-gradient(135deg, var(--ob-warning-700) 0%, var(--ob-warning-400) 100%)',
                color: 'white',
              }}
            >
              <CardContent>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--ob-space-100)',
                  }}
                >
                  <HourglassIcon />
                  <Typography variant="caption">Pending Tasks</Typography>
                </Box>
                <Typography variant="h4" fontWeight="bold">
                  {totalPendingTasks}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                background:
                  'linear-gradient(135deg, var(--ob-info-700) 0%, var(--ob-info-400) 100%)',
                color: 'white',
              }}
            >
              <CardContent>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--ob-space-100)',
                  }}
                >
                  <PeopleIcon />
                  <Typography variant="caption">Team Members</Typography>
                </Box>
                <Typography variant="h4" fontWeight="bold">
                  {teamActivity.length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      <Grid container spacing="var(--ob-space-300)">
        {/* Phase Progress Timeline */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 'var(--ob-space-200)' }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-100)',
                mb: 'var(--ob-space-200)',
              }}
            >
              <TimelineIcon color="primary" />
              <Typography variant="h6">Phase Progress</Typography>
            </Box>
            <Divider sx={{ mb: 'var(--ob-space-200)' }} />

            {phases.map((phase) => (
              <Box key={phase.id} sx={{ mb: 'var(--ob-space-300)' }}>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    mb: 1,
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
          </Paper>
        </Grid>

        {/* Pending Approvals */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 'var(--ob-space-200)' }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-100)',
                mb: 'var(--ob-space-200)',
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
            <Divider sx={{ mb: 'var(--ob-space-200)' }} />

            <List dense disablePadding>
              {pendingApprovals.map((approval) => (
                <ListItem
                  key={approval.id}
                  sx={{
                    borderRadius: 1,
                    mb: 1,
                    bgcolor: 'action.hover',
                    cursor: 'pointer',
                    '&:hover': { bgcolor: 'action.selected' },
                  }}
                >
                  <ListItemText
                    primary={
                      <Box
                        sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
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
                            height: 18,
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
          </Paper>
        </Grid>

        {/* Team Activity */}
        <Grid item xs={12}>
          <Paper sx={{ p: 'var(--ob-space-200)' }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-100)',
                mb: 'var(--ob-space-200)',
              }}
            >
              <PeopleIcon color="primary" />
              <Typography variant="h6">Team Activity</Typography>
            </Box>
            <Divider sx={{ mb: 'var(--ob-space-200)' }} />

            <Grid container spacing="var(--ob-space-200)">
              {teamActivity.map((member) => (
                <Grid item xs={12} sm={6} md={3} key={member.id}>
                  <Card variant="outlined" sx={{ height: '100%' }}>
                    <CardContent>
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 'var(--ob-space-200)',
                          mb: 2,
                        }}
                      >
                        <Avatar sx={{ bgcolor: 'primary.main' }}>
                          {member.name.charAt(0)}
                        </Avatar>
                        <Box sx={{ flex: 1, minWidth: 0 }}>
                          <Typography variant="subtitle2" noWrap>
                            {member.name}
                          </Typography>
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            noWrap
                          >
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
                          <Typography variant="caption" color="text.secondary">
                            Pending
                          </Typography>
                          <Typography variant="h6" color="warning.main">
                            {member.pendingTasks}
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="caption" color="text.secondary">
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
                        sx={{ display: 'block', mt: 1 }}
                      >
                        Active {member.lastActive}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
