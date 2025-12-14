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

interface TeamMemberActivity {
  id: string
  name: string
  email: string
  role: string
  lastActive: string
  pendingTasks: number
  completedTasks: number
}

interface ProjectPhase {
  id: string
  name: string
  progress: number
  status: 'not_started' | 'in_progress' | 'completed' | 'delayed'
  startDate?: string
  endDate?: string
  milestones: {
    name: string
    completed: boolean
  }[]
}

interface PendingApproval {
  id: string
  title: string
  workflowName: string
  requiredBy: string
  dueDate?: string
  priority: 'low' | 'normal' | 'high' | 'urgent'
}

interface ProjectProgressDashboardProps {
  projectId: string
  projectName?: string
}

// Mock data for demonstration
const getMockPhases = (): ProjectPhase[] => [
  {
    id: 'phase-1',
    name: 'Site Acquisition',
    progress: 100,
    status: 'completed',
    startDate: '2025-01-15',
    endDate: '2025-03-01',
    milestones: [
      { name: 'Site Survey', completed: true },
      { name: 'Due Diligence', completed: true },
      { name: 'Purchase Agreement', completed: true },
    ],
  },
  {
    id: 'phase-2',
    name: 'Concept Design',
    progress: 75,
    status: 'in_progress',
    startDate: '2025-03-01',
    milestones: [
      { name: 'Massing Study', completed: true },
      { name: 'GFA Optimization', completed: true },
      { name: 'Financial Feasibility', completed: true },
      { name: 'Design Review', completed: false },
    ],
  },
  {
    id: 'phase-3',
    name: 'Regulatory Submission',
    progress: 30,
    status: 'in_progress',
    startDate: '2025-04-15',
    milestones: [
      { name: 'URA Outline Approval', completed: true },
      { name: 'BCA Structural Plans', completed: false },
      { name: 'SCDF Fire Safety', completed: false },
      { name: 'NEA Environmental', completed: false },
    ],
  },
  {
    id: 'phase-4',
    name: 'Construction',
    progress: 0,
    status: 'not_started',
    milestones: [
      { name: 'Foundation', completed: false },
      { name: 'Superstructure', completed: false },
      { name: 'M&E Works', completed: false },
      { name: 'Finishing', completed: false },
    ],
  },
]

const getMockTeamActivity = (): TeamMemberActivity[] => [
  {
    id: 'u1',
    name: 'John Smith',
    email: 'john.smith@example.com',
    role: 'Project Manager',
    lastActive: '2 hours ago',
    pendingTasks: 3,
    completedTasks: 12,
  },
  {
    id: 'u2',
    name: 'Sarah Chen',
    email: 'sarah.chen@example.com',
    role: 'Architect',
    lastActive: '30 mins ago',
    pendingTasks: 2,
    completedTasks: 8,
  },
  {
    id: 'u3',
    name: 'Michael Wong',
    email: 'michael.wong@example.com',
    role: 'Structural Engineer',
    lastActive: '1 hour ago',
    pendingTasks: 4,
    completedTasks: 6,
  },
  {
    id: 'u4',
    name: 'Emily Tan',
    email: 'emily.tan@example.com',
    role: 'Quantity Surveyor',
    lastActive: '3 hours ago',
    pendingTasks: 1,
    completedTasks: 5,
  },
]

const getMockPendingApprovals = (): PendingApproval[] => [
  {
    id: 'a1',
    title: 'Structural Feasibility Review',
    workflowName: 'Concept Design Sign-off',
    requiredBy: 'Michael Wong',
    dueDate: '2025-12-10',
    priority: 'high',
  },
  {
    id: 'a2',
    title: 'Cost Estimate Approval',
    workflowName: 'Financial Review',
    requiredBy: 'Emily Tan',
    priority: 'normal',
  },
  {
    id: 'a3',
    title: 'Heritage Assessment',
    workflowName: 'Regulatory Compliance',
    requiredBy: 'Sarah Chen',
    priority: 'urgent',
  },
]

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
    default:
      return 'default'
  }
}

function getPriorityColor(priority: PendingApproval['priority']) {
  switch (priority) {
    case 'urgent':
      return 'error'
    case 'high':
      return 'warning'
    case 'normal':
      return 'primary'
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

  useEffect(() => {
    // Simulate loading
    setLoading(true)
    setTimeout(() => {
      setPhases(getMockPhases())
      setTeamActivity(getMockTeamActivity())
      setPendingApprovals(getMockPendingApprovals())
      setLoading(false)
    }, 500)
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
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography>Loading project progress...</Typography>
        <LinearProgress sx={{ mt: 2, maxWidth: 300, mx: 'auto' }} />
      </Box>
    )
  }

  return (
    <Box>
      {/* Header with overall progress */}
      <Box sx={{ mb: 4 }}>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 2,
          }}
        >
          <Typography variant="h5" fontWeight="bold">
            {projectName} - Progress Dashboard
          </Typography>
          <Tooltip title="Refresh">
            <IconButton
              onClick={() => {
                setLoading(true)
                setTimeout(() => setLoading(false), 500)
              }}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>

        {/* KPI Cards */}
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                background:
                  'linear-gradient(135deg, var(--ob-brand-700) 0%, var(--ob-brand-400) 100%)',
                color: 'white',
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
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
                    mt: 1,
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
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
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
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
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
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
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

      <Grid container spacing={3}>
        {/* Phase Progress Timeline */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <TimelineIcon color="primary" />
              <Typography variant="h6">Phase Progress</Typography>
            </Box>
            <Divider sx={{ mb: 2 }} />

            {phases.map((phase) => (
              <Box key={phase.id} sx={{ mb: 3 }}>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    mb: 1,
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {getStatusIcon(phase.status)}
                    <Typography variant="subtitle1" fontWeight="medium">
                      {phase.name}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
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
                  sx={{ height: 8, borderRadius: 4, mb: 1 }}
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
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {phase.milestones.map((m, idx) => (
                    <Chip
                      key={idx}
                      label={m.name}
                      size="small"
                      variant={m.completed ? 'filled' : 'outlined'}
                      color={m.completed ? 'success' : 'default'}
                      sx={{ fontSize: '0.7rem' }}
                    />
                  ))}
                </Box>
              </Box>
            ))}
          </Paper>
        </Grid>

        {/* Pending Approvals */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <AssignmentIcon color="warning" />
              <Typography variant="h6">Pending Approvals</Typography>
              <Chip
                label={pendingApprovals.length}
                size="small"
                color="warning"
              />
            </Box>
            <Divider sx={{ mb: 2 }} />

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
                          sx={{ fontSize: '0.65rem', height: 18 }}
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
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <PeopleIcon color="primary" />
              <Typography variant="h6">Team Activity</Typography>
            </Box>
            <Divider sx={{ mb: 2 }} />

            <Grid container spacing={2}>
              {teamActivity.map((member) => (
                <Grid item xs={12} sm={6} md={3} key={member.id}>
                  <Card variant="outlined" sx={{ height: '100%' }}>
                    <CardContent>
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 2,
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
