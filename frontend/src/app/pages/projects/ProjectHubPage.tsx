import { useCallback, useEffect, useState } from 'react'
import {
  Box,
  Button,
  Grid,
  Stack,
  Typography,
  Chip,
  IconButton,
  alpha,
  useTheme,
  Alert,
  Theme,
  Skeleton,
} from '@mui/material'
import {
  TrendingUp,
  AccountBalance,
  Group,
  Gavel,
  ArrowForward,
  MoreVert,
  Construction,
  Map,
  PieChart,
  Settings,
} from '@mui/icons-material'

import { useProject } from '../../../contexts/useProject'
import { useRouterController } from '../../../router'
import { MetricTile } from '../../../components/canonical/MetricTile'
import { GlassCard } from '../../../components/canonical/GlassCard'
import {
  getProjectDashboard,
  ProjectDashboardResponse,
  DashboardKPI,
  DashboardModule,
} from '../../../api/projects'

// Map module keys to icons
const moduleIcons: Record<string, React.ReactNode> = {
  capture: <Map fontSize="large" />,
  feasibility: <PieChart fontSize="large" />,
  finance: <AccountBalance fontSize="large" />,
  phases: <TrendingUp fontSize="large" />,
  team: <Group fontSize="large" />,
  regulatory: <Gavel fontSize="large" />,
}

// Map module keys to theme colors
const getModuleColor = (key: string, theme: Theme): string => {
  const colorMap: Record<string, string> = {
    capture: theme.palette.info.main,
    feasibility: theme.palette.secondary.main,
    finance: theme.palette.success.main,
    phases: theme.palette.warning.main,
    team: theme.palette.text.secondary,
    regulatory: theme.palette.error.main,
  }
  return colorMap[key] || theme.palette.primary.main
}

export function ProjectHubPage() {
  const { navigate } = useRouterController()
  const { currentProject, isProjectLoading, projectError } = useProject()
  const theme = useTheme()

  const [dashboard, setDashboard] = useState<ProjectDashboardResponse | null>(
    null,
  )
  const [dashboardLoading, setDashboardLoading] = useState(false)
  const [dashboardError, setDashboardError] = useState<string | null>(null)

  const fetchDashboard = useCallback(async (projectId: string) => {
    setDashboardLoading(true)
    setDashboardError(null)
    try {
      const data = await getProjectDashboard(projectId)
      setDashboard(data)
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to load dashboard data'
      setDashboardError(message)
    } finally {
      setDashboardLoading(false)
    }
  }, [])

  useEffect(() => {
    if (currentProject?.id) {
      fetchDashboard(currentProject.id)
    }
  }, [currentProject?.id, fetchDashboard])

  if (!currentProject) {
    return (
      <Box sx={{ width: '100%' }}>
        {isProjectLoading ? (
          <Typography color="text.secondary">Loading project...</Typography>
        ) : (
          <>
            <Typography variant="h5" sx={{ mb: 1 }}>
              No project selected
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {projectError?.message ??
                'Select a project to view results and navigate to modules.'}
            </Typography>
            <Button variant="contained" onClick={() => navigate('/projects')}>
              Go to projects
            </Button>
          </>
        )}
      </Box>
    )
  }

  const basePath = `/projects/${currentProject.id}`

  // Render KPI skeleton using MetricTile loading state for exact sizing match
  const renderKPISkeleton = () => (
    <Grid container spacing={3} mb={5}>
      {[1, 2, 3, 4].map((i) => (
        <Grid item xs={12} sm={6} md={3} key={i} sx={{ display: 'flex' }}>
          <MetricTile
            label="Loading..."
            value="---"
            variant="default"
            loading
            sx={{ width: '100%', height: '100%' }}
          />
        </Grid>
      ))}
    </Grid>
  )

  // Render KPIs from API data
  const renderKPIs = (kpis: DashboardKPI[]) => (
    <Grid container spacing={3} mb={5}>
      {kpis.map((kpi) => (
        <Grid item xs={12} sm={6} md={3} key={kpi.label} sx={{ display: 'flex' }}>
          <MetricTile
            label={kpi.label}
            value={kpi.value}
            variant="default"
            trend={kpi.trend?.value}
            trendLabel={kpi.trend?.label}
            sx={{ width: '100%', height: '100%' }}
          />
        </Grid>
      ))}
    </Grid>
  )

  // Render modules from API data
  const renderModules = (modules: DashboardModule[]) => (
    <Grid container spacing={3}>
      {modules
        .filter((m) => m.enabled)
        .map((item) => {
          const key = item.path.split('/').pop() || 'unknown'
          const color = getModuleColor(key, theme)
          // Use path from API directly
          return (
            <Grid item xs={12} md={6} lg={4} key={item.path}>
              <GlassCard
                sx={{
                  height: '100%',
                  transition: 'all 0.2s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    borderColor: color,
                  },
                }}
                hover="lift"
                onClick={() => navigate(item.path)}
                role="button"
              >
                <Stack
                  direction="row"
                  justifyContent="space-between"
                  alignItems="flex-start"
                  mb={2}
                >
                  <Box
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      bgcolor: alpha(color, 0.1),
                      color: color,
                    }}
                  >
                    {moduleIcons[key] || <Construction fontSize="large" />}
                  </Box>
                  <IconButton size="small">
                    <ArrowForward />
                  </IconButton>
                </Stack>
                <Typography variant="h6" fontWeight={600} gutterBottom>
                  {item.label}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {item.description}
                </Typography>
              </GlassCard>
            </Grid>
          )
        })}
    </Grid>
  )

  const renderModuleSkeleton = () => (
    <Grid container spacing={3}>
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <Grid item xs={12} md={6} lg={4} key={i}>
          <GlassCard sx={{ height: '100%' }}>
            <Stack direction="row" justifyContent="space-between" mb={2}>
              <Skeleton variant="rectangular" width={48} height={48} sx={{ borderRadius: 2 }} />
            </Stack>
            <Skeleton variant="text" width="60%" height={32} sx={{ mb: 1 }} />
            <Skeleton variant="text" width="80%" />
          </GlassCard>
        </Grid>
      ))}
    </Grid>
  )

  return (
    <Box sx={{ width: '100%', pb: 5 }}>
      {/* Header Section */}
      <Box
        sx={{
          mb: 4,
          pb: 3,
          borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
        }}
      >
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="flex-start"
        >
          <Stack spacing={1}>
            <Typography variant="h3" fontWeight={700}>
              {currentProject.name}
            </Typography>
            <Stack direction="row" spacing={1} alignItems="center">
              <Chip
                label={currentProject.status}
                color="success"
                size="small"
                variant="outlined"
              />
              <Typography variant="body2" color="text.secondary">
                Project ID: {currentProject.id}
              </Typography>
            </Stack>
          </Stack>
          <Stack direction="row" spacing={2}>
            <Button variant="outlined" startIcon={<MoreVert />}>
              Options
            </Button>
            <Button variant="contained" startIcon={<Settings />}>
              Edit Settings
            </Button>
          </Stack>
        </Stack>
      </Box>

      {/* Dashboard Error */}
      {dashboardError && (
        <Alert
          severity="warning"
          sx={{ mb: 3 }}
          action={
            <Button
              color="inherit"
              size="small"
              onClick={() => fetchDashboard(currentProject.id)}
            >
              Retry
            </Button>
          }
        >
          {dashboardError}
        </Alert>
      )}

      {/* KPI Dashboard */}
      {dashboardLoading
        ? renderKPISkeleton()
        : dashboard?.kpis
          ? renderKPIs(dashboard.kpis)
          : renderKPISkeleton()}

      {/* Module Navigation Grid */}
      <Typography variant="h5" fontWeight={600} gutterBottom sx={{ mb: 3 }}>
        Project Modules
      </Typography>
      {dashboardLoading
        ? renderModuleSkeleton()
        : renderModules(dashboard?.modules || [])}
    </Box>
  )
}
