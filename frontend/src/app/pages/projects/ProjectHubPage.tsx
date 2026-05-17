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
import TrendingUp from '@mui/icons-material/TrendingUp'
import AccountBalance from '@mui/icons-material/AccountBalance'
import Group from '@mui/icons-material/Group'
import Gavel from '@mui/icons-material/Gavel'
import ArrowForward from '@mui/icons-material/ArrowForward'
import MoreVert from '@mui/icons-material/MoreVert'
import Construction from '@mui/icons-material/Construction'
import Map from '@mui/icons-material/Map'
import PieChart from '@mui/icons-material/PieChart'
import Settings from '@mui/icons-material/Settings'

import { useProjectScope } from '../../../contexts/useProjectScope'
import { useRouterController } from '../../../router'
import { MetricTile } from '../../../components/canonical/MetricTile'
import { Card } from '../../../components/canonical/Card'
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
  const { currentProject, isProjectLoading, projectError, projectId } =
    useProjectScope()
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
    if (projectId) {
      fetchDashboard(projectId)
    }
  }, [fetchDashboard, projectId])

  if (!currentProject) {
    return (
      <Box sx={{ width: '100%' }}>
        {isProjectLoading ? (
          <Typography color="text.secondary">Loading project...</Typography>
        ) : (
          <>
            <Typography variant="h5" sx={{ mb: 'var(--ob-space-050)' }}>
              No project selected
            </Typography>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mb: 'var(--ob-space-100)' }}
            >
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

  // Render KPI skeleton using MetricTile loading state for exact sizing match
  const renderKPISkeleton = () => (
    <Grid container spacing="var(--ob-space-150)" mb="var(--ob-space-250)">
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
    <Grid container spacing="var(--ob-space-150)" mb="var(--ob-space-250)">
      {kpis.map((kpi) => (
        <Grid
          item
          xs={12}
          sm={6}
          md={3}
          key={kpi.label}
          sx={{ display: 'flex' }}
        >
          <MetricTile
            label={kpi.label}
            value={kpi.value}
            variant="default"
            trend={kpi.trend ?? undefined}
            sx={{ width: '100%', height: '100%' }}
          />
        </Grid>
      ))}
    </Grid>
  )

  // Render modules from API data
  const renderModules = (modules: DashboardModule[]) => (
    <Grid container spacing="var(--ob-space-150)">
      {modules
        .filter((m) => m.enabled)
        .map((item) => {
          const key = item.path.split('/').pop() || 'unknown'
          const color = getModuleColor(key, theme)
          // Use path from API directly
          return (
            <Grid item xs={12} md={6} lg={4} key={item.path}>
              <Card
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
              >
                <Stack
                  direction="row"
                  justifyContent="space-between"
                  alignItems="flex-start"
                  mb="var(--ob-space-100)"
                >
                  <Box
                    sx={{
                      p: 'var(--ob-space-075)',
                      borderRadius: 'var(--ob-radius-sm)',
                      bgcolor: alpha(color, 0.1),
                      color: color,
                    }}
                  >
                    {moduleIcons[key] || <Construction fontSize="large" />}
                  </Box>
                  <IconButton
                    size="small"
                    aria-label={`Open ${item.label}`}
                    tabIndex={-1}
                  >
                    <ArrowForward />
                  </IconButton>
                </Stack>
                <Typography
                  variant="h6"
                  component="h5"
                  fontWeight={600}
                  gutterBottom
                >
                  {item.label}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {item.description}
                </Typography>
              </Card>
            </Grid>
          )
        })}
    </Grid>
  )

  const renderModuleSkeleton = () => (
    <Grid container spacing="var(--ob-space-150)">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <Grid item xs={12} md={6} lg={4} key={i}>
          <Card sx={{ height: '100%' }}>
            <Stack
              direction="row"
              justifyContent="space-between"
              mb="var(--ob-space-100)"
            >
              <Skeleton
                variant="rectangular"
                width={48}
                height={48}
                sx={{ borderRadius: 'var(--ob-radius-sm)' }}
              />
            </Stack>
            <Skeleton
              variant="text"
              width="60%"
              height={32}
              sx={{ mb: 'var(--ob-space-050)' }}
            />
            <Skeleton variant="text" width="80%" />
          </Card>
        </Grid>
      ))}
    </Grid>
  )

  return (
    <Box sx={{ width: '100%', pb: 'var(--ob-space-250)' }}>
      {/* Header Section */}
      <Box
        sx={{
          mb: 'var(--ob-space-200)',
          pb: 'var(--ob-space-150)',
          borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
        }}
      >
        <Stack
          direction={{ xs: 'column', md: 'row' }}
          justifyContent="space-between"
          alignItems={{ xs: 'stretch', md: 'flex-start' }}
          spacing="var(--ob-space-150)"
        >
          <Stack spacing="var(--ob-space-050)" sx={{ minWidth: 0 }}>
            <Typography variant="h3" fontWeight={700}>
              {currentProject.name}
            </Typography>
            <Stack
              direction="row"
              spacing="var(--ob-space-050)"
              alignItems="center"
              flexWrap="wrap"
              useFlexGap
            >
              <Chip
                label={currentProject.status}
                color="success"
                size="small"
                variant="outlined"
              />
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{
                  fontFamily: 'var(--ob-font-family-mono)',
                  fontSize: 'var(--ob-font-size-xs)',
                  wordBreak: 'break-all',
                }}
              >
                Project ID: {currentProject.id}
              </Typography>
            </Stack>
          </Stack>
          <Stack
            direction="row"
            spacing="var(--ob-space-100)"
            sx={{ flexShrink: 0 }}
          >
            <Button
              variant="outlined"
              startIcon={<MoreVert />}
              sx={{ whiteSpace: 'nowrap' }}
            >
              Options
            </Button>
            <Button
              variant="contained"
              startIcon={<Settings />}
              sx={{ whiteSpace: 'nowrap' }}
            >
              Edit Settings
            </Button>
          </Stack>
        </Stack>
      </Box>

      {/* Dashboard Error */}
      {dashboardError && (
        <Alert
          severity="warning"
          sx={{ mb: 'var(--ob-space-150)' }}
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
      <Typography
        variant="h5"
        component="h4"
        fontWeight={600}
        gutterBottom
        sx={{ mb: 'var(--ob-space-150)' }}
      >
        Project Modules
      </Typography>
      {dashboardLoading
        ? renderModuleSkeleton()
        : renderModules(dashboard?.modules || [])}
    </Box>
  )
}
