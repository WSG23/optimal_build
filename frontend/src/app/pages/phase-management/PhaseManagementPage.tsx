import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Skeleton,
  Stack,
  Tab,
  Tabs,
  Typography,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import TimelineIcon from '@mui/icons-material/Timeline'
import AccountBalanceIcon from '@mui/icons-material/AccountBalance'
import PeopleIcon from '@mui/icons-material/People'
import BarChartIcon from '@mui/icons-material/BarChart'
import { PremiumMetricCard, EmptyState } from '@/components/canonical'
import { GanttChart } from './components/GanttChart'
import { PhaseEditor } from './components/PhaseEditor'
import { TenantRelocationDashboard } from './components/TenantRelocationDashboard'
import { CriticalPathView } from './components/CriticalPathView'
import { HeritageView } from './components/HeritageView'
import {
  DemoGanttChart,
  DemoCriticalPath,
  DemoHeritageView,
  DemoTenantCoordination,
} from './components/DemoPhaseData'
import {
  fetchGanttChart,
  fetchCriticalPath,
  fetchHeritageTracker,
  fetchTenantCoordination,
  createPhase,
  updatePhase,
  type GanttChart as GanttChartData,
  type CriticalPathResult,
  type HeritageTracker,
  type TenantCoordinationSummary,
  type DevelopmentPhase,
  type CreatePhasePayload,
  type UpdatePhasePayload,
} from '../../../api/development'
import { useProjectScope } from '../../../contexts/useProjectScope'
import { Link, useRouterController } from '../../../router'
import '../../../styles/phase-management.css'

interface TabPanelProps {
  children?: React.ReactNode
  value: number
  index: number
}

function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <Box
      role="tabpanel"
      hidden={value !== index}
      id={`phase-tabpanel-${index}`}
      aria-labelledby={`phase-tab-${index}`}
      sx={{ pt: 3 }}
    >
      {value === index && children}
    </Box>
  )
}

export function PhaseManagementPage() {
  const navigate = useRouterController().navigate
  const { currentProject, isProjectLoading, projectError, projectId } =
    useProjectScope()
  const [activeTab, setActiveTab] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Data states
  const [ganttData, setGanttData] = useState<GanttChartData | null>(null)
  const [criticalPath, setCriticalPath] = useState<CriticalPathResult | null>(
    null,
  )
  const [heritageData, setHeritageData] = useState<HeritageTracker | null>(null)
  const [tenantData, setTenantData] =
    useState<TenantCoordinationSummary | null>(null)

  // UI states
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)
  const [editorOpen, setEditorOpen] = useState(false)
  const [editingPhase, setEditingPhase] = useState<DevelopmentPhase | null>(
    null,
  )

  // Load all data
  const loadData = useCallback(
    async (controller?: AbortController) => {
      if (!projectId) {
        setLoading(false)
        return
      }
      const signal = controller?.signal
      setLoading(true)
      setError(null)

      try {
        const [gantt, critical, heritage, tenant] = await Promise.all([
          fetchGanttChart(projectId, signal).catch(() => null),
          fetchCriticalPath(projectId, signal).catch(() => null),
          fetchHeritageTracker(projectId, signal).catch(() => null),
          fetchTenantCoordination(projectId, signal).catch(() => null),
        ])

        if (signal?.aborted) return

        setGanttData(gantt)
        setCriticalPath(critical)
        setHeritageData(heritage)
        setTenantData(tenant)
      } catch (err) {
        if ((err as { name?: string }).name === 'AbortError') return
        console.error('Failed to load phase data', err)
        setError(
          'Failed to load project phase data. The API may not be available yet.',
        )
      } finally {
        if (!signal?.aborted) {
          setLoading(false)
        }
      }
    },
    [projectId],
  )

  useEffect(() => {
    const controller = new AbortController()
    loadData(controller)
    return () => controller.abort()
  }, [loadData])

  const handleTabChange = useCallback(
    (_: React.SyntheticEvent, newValue: number) => {
      setActiveTab(newValue)
    },
    [],
  )

  const handleTaskClick = useCallback((taskId: string) => {
    setSelectedTaskId(taskId)
  }, [])

  const handleAddPhase = useCallback(() => {
    setEditingPhase(null)
    setEditorOpen(true)
  }, [])

  const handleSavePhase = useCallback(
    async (data: CreatePhasePayload | UpdatePhasePayload, isNew: boolean) => {
      if (!projectId) {
        return
      }
      if (isNew) {
        await createPhase(projectId, data as CreatePhasePayload)
      } else if (editingPhase) {
        await updatePhase(
          projectId,
          editingPhase.id,
          data as UpdatePhasePayload,
        )
      }
      // Reload data after save
      await loadData()
    },
    [editingPhase, loadData, projectId],
  )

  const handleCloseEditor = useCallback(() => {
    setEditorOpen(false)
    setEditingPhase(null)
  }, [])

  // Calculate summary stats
  const stats = useMemo(() => {
    if (!ganttData) {
      return {
        totalPhases: 0,
        criticalPhases: 0,
        heritagePhases: 0,
        tenantPhases: 0,
        totalDuration: 0,
        criticalDuration: 0,
      }
    }

    return {
      totalPhases: ganttData.tasks.length,
      criticalPhases: ganttData.tasks.filter((t) => t.isCritical).length,
      heritagePhases: ganttData.tasks.filter((t) => t.isHeritage).length,
      tenantPhases: ganttData.tasks.filter((t) => t.hasTenantCoordination)
        .length,
      totalDuration: ganttData.totalDuration,
      criticalDuration: ganttData.criticalPathDuration,
    }
  }, [ganttData])

  if (!projectId) {
    return (
      <Box sx={{ width: '100%' }}>
        {isProjectLoading ? (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-100)',
            }}
          >
            <Skeleton
              variant="rectangular"
              height={48}
              sx={{ borderRadius: 'var(--ob-radius-sm)' }}
            />
            <Skeleton
              variant="rectangular"
              height={300}
              sx={{ borderRadius: 'var(--ob-radius-sm)' }}
            />
          </Box>
        ) : (
          <EmptyState
            title="Select a project to manage development phases"
            description={
              projectError?.message ??
              'Phase plans, sequencing, and relocation workflows are tied to a project context.'
            }
            actionLabel="Go to projects"
            onAction={() => navigate('/projects')}
            size="md"
            sx={{ alignItems: 'flex-start', textAlign: 'left' }}
          />
        )}
      </Box>
    )
  }

  if (loading) {
    return (
      <Box sx={{ width: '100%' }}>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--ob-space-100)',
          }}
        >
          <Skeleton
            variant="rectangular"
            height={48}
            sx={{ borderRadius: 'var(--ob-radius-sm)' }}
          />
          <Skeleton
            variant="rectangular"
            height={300}
            sx={{ borderRadius: 'var(--ob-radius-sm)' }}
          />
        </Box>
      </Box>
    )
  }

  return (
    <Box className="phase-management-page" sx={{ width: '100%' }}>
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
            Phase Management
          </Typography>
          <Typography
            variant="body2"
            sx={{ color: 'text.secondary', mt: 'var(--ob-space-025)' }}
          >
            Project timeline, critical path analysis, and coordination tracking
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
        <Stack direction="row" spacing={1} flexWrap="wrap">
          {projectId && (
            <>
              <Button
                component={Link}
                to={`/projects/${projectId}/capture`}
                size="small"
                variant="outlined"
              >
                Capture Results
              </Button>
              <Button
                component={Link}
                to={`/projects/${projectId}/feasibility`}
                size="small"
                variant="outlined"
              >
                Feasibility
              </Button>
              <Button
                component={Link}
                to={`/projects/${projectId}/finance`}
                size="small"
                variant="outlined"
              >
                Finance
              </Button>
              <Button
                component={Link}
                to={`/projects/${projectId}/team`}
                size="small"
                variant="outlined"
              >
                Team
              </Button>
              <Button
                component={Link}
                to={`/projects/${projectId}/regulatory`}
                size="small"
                variant="outlined"
              >
                Regulatory
              </Button>
            </>
          )}
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleAddPhase}
            size="small"
          >
            Add Phase
          </Button>
        </Stack>
      </Box>

      {error && (
        <Alert severity="info" sx={{ mb: 'var(--ob-space-200)' }}>
          {error} Demo data is shown below.
        </Alert>
      )}

      {/* KPI Metrics - Depth 1 (Glass Card with brand edge) */}
      <Box className="ob-card-module ob-section-gap">
        <Typography
          variant="subtitle2"
          sx={{
            color: 'text.secondary',
            mb: 'var(--ob-space-200)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}
        >
          Project Overview
        </Typography>
        <Box
          sx={{ display: 'flex', gap: 'var(--ob-space-200)', flexWrap: 'wrap' }}
        >
          <PremiumMetricCard
            icon={<TimelineIcon sx={{ fontSize: 28 }} />}
            value={stats.totalPhases}
            label="Total Phases"
            progress={75}
            compact
            sx={{ minWidth: 160, flex: 1 }}
          />
          <PremiumMetricCard
            icon={<BarChartIcon sx={{ fontSize: 28 }} />}
            value={stats.criticalPhases}
            label="Critical Path"
            status={stats.criticalPhases > 0 ? 'error' : 'success'}
            compact
            sx={{ minWidth: 160, flex: 1 }}
          />
          <PremiumMetricCard
            icon={<AccountBalanceIcon sx={{ fontSize: 28 }} />}
            value={stats.heritagePhases}
            label="Heritage Phases"
            progress={45}
            compact
            sx={{ minWidth: 160, flex: 1 }}
          />
          <PremiumMetricCard
            icon={<PeopleIcon sx={{ fontSize: 28 }} />}
            value={stats.tenantPhases}
            label="Tenant Coord"
            progress={60}
            compact
            sx={{ minWidth: 160, flex: 1 }}
          />
          <PremiumMetricCard
            value={`${stats.totalDuration}d`}
            label="Total Days"
            progress={35}
            compact
            sx={{ minWidth: 160, flex: 1 }}
          />
          <PremiumMetricCard
            value={`${stats.criticalDuration}d`}
            label="Critical Days"
            status="error"
            compact
            sx={{ minWidth: 160, flex: 1 }}
          />
        </Box>
      </Box>

      {/* Tabs - Depth 0 (Direct on Grid) */}
      <Box
        sx={{
          borderBottom: 1,
          borderColor: 'divider',
          mb: 'var(--ob-space-300)',
        }}
      >
        <Tabs value={activeTab} onChange={handleTabChange}>
          <Tab
            label="Gantt Chart"
            icon={<TimelineIcon />}
            iconPosition="start"
          />
          <Tab
            label="Critical Path"
            icon={<BarChartIcon />}
            iconPosition="start"
          />
          <Tab
            label="Heritage Tracking"
            icon={<AccountBalanceIcon />}
            iconPosition="start"
          />
          <Tab
            label="Tenant Coordination"
            icon={<PeopleIcon />}
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Tab Content - Depth 1 (Glass Card with brand edge) */}
      <Box className="ob-card-module" sx={{ overflow: 'hidden' }}>
        {/* Gantt Chart Tab */}
        <TabPanel value={activeTab} index={0}>
          {ganttData ? (
            <GanttChart
              data={ganttData}
              onTaskClick={handleTaskClick}
              selectedTaskId={selectedTaskId}
            />
          ) : (
            <DemoGanttChart
              onTaskClick={handleTaskClick}
              selectedTaskId={selectedTaskId}
            />
          )}
        </TabPanel>

        {/* Critical Path Tab */}
        <TabPanel value={activeTab} index={1}>
          {criticalPath ? (
            <CriticalPathView data={criticalPath} />
          ) : (
            <DemoCriticalPath />
          )}
        </TabPanel>

        {/* Heritage Tracking Tab */}
        <TabPanel value={activeTab} index={2}>
          {heritageData ? (
            <HeritageView data={heritageData} />
          ) : (
            <DemoHeritageView />
          )}
        </TabPanel>

        {/* Tenant Coordination Tab */}
        <TabPanel value={activeTab} index={3}>
          {tenantData ? (
            <TenantRelocationDashboard data={tenantData} />
          ) : (
            <DemoTenantCoordination />
          )}
        </TabPanel>
      </Box>

      {/* Phase Editor Dialog */}
      <PhaseEditor
        open={editorOpen}
        phase={editingPhase}
        projectId={projectId}
        onClose={handleCloseEditor}
        onSave={handleSavePhase}
      />
    </Box>
  )
}
