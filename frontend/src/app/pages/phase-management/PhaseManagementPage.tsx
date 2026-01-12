import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Divider,
  Grid,
  Paper,
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
import { GanttChart } from './components/GanttChart'
import { PhaseEditor } from './components/PhaseEditor'
import { TenantRelocationDashboard } from './components/TenantRelocationDashboard'
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
import { useProject } from '../../../contexts/useProject'
import { Link } from '../../../router'

// Custom Holographic Card Component
function HolographicCard({
  icon,
  value,
  label,
  progress,
  status,
  color = '#fff',
  suffix,
}: {
  icon?: React.ReactNode
  value: number | string
  label: string
  progress?: number
  status?: 'good' | 'alert'
  color?: string
  suffix?: string
}) {
  return (
    <Box
      sx={{
        position: 'relative',
        minWidth: 160,
        flex: 1,
        p: 2,
        borderRadius: 3,
        background: 'rgba(30, 30, 30, 0.6)',
        backdropFilter: 'blur(var(--ob-blur-md))',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
        display: 'flex',
        alignItems: 'center',
        gap: 2,
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow:
            '0 12px 40px 0 rgba(0, 0, 0, 0.4), 0 0 20px rgba(0, 243, 255, 0.1)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
        },
      }}
    >
      {/* Progress Ring or Icon Container */}
      <Box sx={{ position: 'relative', display: 'flex' }}>
        {progress !== undefined ? (
          <Box sx={{ position: 'relative', display: 'inline-flex' }}>
            <CircularProgress
              variant="determinate"
              value={100}
              size={52}
              thickness={4}
              sx={{ color: 'rgba(255, 255, 255, 0.1)' }}
            />
            <CircularProgress
              variant="determinate"
              value={progress}
              size={52}
              thickness={4}
              sx={{
                color: color,
                position: 'absolute',
                left: 0,
                // Add a glow effect to the progress bar
                filter: `drop-shadow(0 0 4px ${color})`,
                '& .MuiCircularProgress-circle': { strokeLinecap: 'round' },
              }}
            />
            <Box
              sx={{
                top: 0,
                left: 0,
                bottom: 0,
                right: 0,
                position: 'absolute',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {icon}
            </Box>
          </Box>
        ) : (
          icon && <Box sx={{ p: 1 }}>{icon}</Box>
        )}
      </Box>

      <Box>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 700,
            color: '#fff',
            textShadow: '0 2px 10px rgba(0,0,0,0.5)',
            fontSize: '1.75rem',
            lineHeight: 1,
            mb: 0.5,
          }}
        >
          {value}
          {suffix && (
            <Typography
              component="span"
              variant="h6"
              sx={{ ml: 0.5, opacity: 0.7 }}
            >
              {suffix}
            </Typography>
          )}
        </Typography>
        <Stack direction="row" alignItems="center" spacing={1}>
          <Typography
            variant="body2"
            sx={{
              color: 'rgba(255, 255, 255, 0.6)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              fontWeight: 500,
              fontSize: '0.7rem',
            }}
          >
            {label}
          </Typography>
          {status && (
            <Box
              sx={{
                width: 6,
                height: 6,
                borderRadius: '50%',
                bgcolor: status === 'good' ? '#00ff9d' : '#ff3366',
                boxShadow: `0 0 8px ${status === 'good' ? '#00ff9d' : '#ff3366'}`,
                animation: 'pulse 2s infinite',
                '@keyframes pulse': {
                  '0%': { opacity: 1, transform: 'scale(1)' },
                  '50%': { opacity: 0.5, transform: 'scale(1.2)' },
                  '100%': { opacity: 1, transform: 'scale(1)' },
                },
              }}
            />
          )}
        </Stack>
      </Box>
    </Box>
  )
}

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
  const { currentProject, isProjectLoading, projectError } = useProject()
  const projectId = currentProject?.id ?? ''
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
          <CircularProgress />
        ) : (
          <Alert severity={projectError ? 'error' : 'info'}>
            {projectError?.message ??
              'Select a project to manage development phases.'}
          </Alert>
        )}
      </Box>
    )
  }

  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: 400,
        }}
      >
        <Stack alignItems="center" spacing={2}>
          <CircularProgress />
          <Typography color="text.secondary">
            Loading project phases...
          </Typography>
        </Stack>
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

      {/* KPI Metrics - Depth 1 (Glass Card with cyan edge) */}
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
          <HolographicCard
            icon={<TimelineIcon sx={{ fontSize: 28, color: '#00f3ff' }} />}
            value={stats.totalPhases}
            label="Total Phases"
            progress={75} // Example progress
            color="#00f3ff"
          />
          <HolographicCard
            icon={
              <BarChartIcon
                sx={{
                  fontSize: 28,
                  color: stats.criticalPhases > 0 ? '#ff3366' : '#00ff9d',
                }}
              />
            }
            value={stats.criticalPhases}
            label="Critical Path"
            status={stats.criticalPhases > 0 ? 'alert' : 'good'}
            color={stats.criticalPhases > 0 ? '#ff3366' : '#00ff9d'}
          />
          <HolographicCard
            icon={
              <AccountBalanceIcon sx={{ fontSize: 28, color: '#f59e0b' }} />
            }
            value={stats.heritagePhases}
            label="Heritage Phases"
            progress={45}
            color="#f59e0b"
          />
          <HolographicCard
            icon={<PeopleIcon sx={{ fontSize: 28, color: '#a855f7' }} />}
            value={stats.tenantPhases}
            label="Tenant Coord"
            progress={60}
            color="#a855f7"
          />
          <HolographicCard
            value={stats.totalDuration}
            label="Total Days"
            suffix="d"
            progress={35} // Just an example, ideally calculated (elapsed / total)
            color="#fff"
          />
          <HolographicCard
            value={stats.criticalDuration}
            label="Critical Days"
            suffix="d"
            color="#ff3366"
            status="alert"
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

      {/* Tab Content - Depth 1 (Glass Card with cyan edge) */}
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

// Demo components for when API is not available
function DemoGanttChart({
  onTaskClick,
  selectedTaskId,
}: {
  onTaskClick: (id: string) => void
  selectedTaskId: string | null
}) {
  const demoData: GanttChartData = {
    projectId: 'demo-project',
    projectName: 'Heritage Mixed-Use Development',
    generatedAt: new Date().toISOString(),
    tasks: [
      {
        id: '1',
        name: 'Site Preparation',
        phaseType: 'site_preparation',
        status: 'completed',
        startDate: '2025-01-01',
        endDate: '2025-01-30',
        duration: 30,
        progress: 1.0,
        dependencies: [],
        isCritical: true,
        isHeritage: false,
        hasTenantCoordination: false,
        color: '#10b981',
        budgetAmount: 500000,
        actualCostAmount: 480000,
      },
      {
        id: '2',
        name: 'Heritage Facade Restoration',
        phaseType: 'heritage_restoration',
        status: 'in_progress',
        startDate: '2025-02-01',
        endDate: '2025-04-15',
        duration: 74,
        progress: 0.45,
        dependencies: ['1'],
        isCritical: true,
        isHeritage: true,
        hasTenantCoordination: false,
        color: '#f59e0b',
        budgetAmount: 2000000,
        actualCostAmount: null,
      },
      {
        id: '3',
        name: 'Tenant Relocation Phase 1',
        phaseType: 'tenant_renovation',
        status: 'in_progress',
        startDate: '2025-02-15',
        endDate: '2025-03-31',
        duration: 45,
        progress: 0.6,
        dependencies: ['1'],
        isCritical: false,
        isHeritage: false,
        hasTenantCoordination: true,
        color: '#3b82f6',
        budgetAmount: 300000,
        actualCostAmount: null,
      },
      {
        id: '4',
        name: 'Structure Reinforcement',
        phaseType: 'structure',
        status: 'planning',
        startDate: '2025-04-16',
        endDate: '2025-06-30',
        duration: 76,
        progress: 0,
        dependencies: ['2'],
        isCritical: true,
        isHeritage: false,
        hasTenantCoordination: false,
        color: '#94a3b8',
        budgetAmount: 3500000,
        actualCostAmount: null,
      },
      {
        id: '5',
        name: 'MEP Installation',
        phaseType: 'mep_rough_in',
        status: 'not_started',
        startDate: '2025-07-01',
        endDate: '2025-09-15',
        duration: 77,
        progress: 0,
        dependencies: ['4'],
        isCritical: true,
        isHeritage: false,
        hasTenantCoordination: false,
        color: '#94a3b8',
        budgetAmount: 2500000,
        actualCostAmount: null,
      },
      {
        id: '6',
        name: 'Interior Fit-Out',
        phaseType: 'interior_fit_out',
        status: 'not_started',
        startDate: '2025-09-16',
        endDate: '2025-11-30',
        duration: 76,
        progress: 0,
        dependencies: ['5'],
        isCritical: false,
        isHeritage: false,
        hasTenantCoordination: true,
        color: '#94a3b8',
        budgetAmount: 1800000,
        actualCostAmount: null,
      },
    ],
    projectStartDate: '2025-01-01',
    projectEndDate: '2025-11-30',
    totalDuration: 334,
    criticalPathDuration: 257,
  }

  return (
    <GanttChart
      data={demoData}
      onTaskClick={onTaskClick}
      selectedTaskId={selectedTaskId}
    />
  )
}

function CriticalPathView({ data }: { data: CriticalPathResult }) {
  return (
    <Stack spacing={3}>
      <Paper variant="outlined" sx={{ p: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Critical Path Analysis
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Total Duration: <strong>{data.totalDuration} days</strong>
        </Typography>
        <Typography variant="body2" color="text.secondary">
          The critical path represents the longest sequence of dependent phases
          that determines the minimum project duration. Any delay in critical
          phases will delay the entire project.
        </Typography>
      </Paper>

      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography
              variant="subtitle1"
              sx={{ fontWeight: 600, mb: 2, color: 'error.main' }}
            >
              Critical Phases ({data.criticalPhases.length})
            </Typography>
            <Stack spacing={1}>
              {data.criticalPhases.map((phase) => (
                <Box
                  key={phase.phaseId}
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    p: 1,
                    backgroundColor: '#fef2f2',
                    borderRadius: 1,
                  }}
                >
                  <Typography variant="body2">{phase.name}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Float: {phase.float} days
                  </Typography>
                </Box>
              ))}
            </Stack>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography
              variant="subtitle1"
              sx={{ fontWeight: 600, mb: 2, color: 'success.main' }}
            >
              Non-Critical Phases ({data.nonCriticalPhases.length})
            </Typography>
            <Stack spacing={1}>
              {data.nonCriticalPhases.map((phase) => (
                <Box
                  key={phase.phaseId}
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    p: 1,
                    backgroundColor: '#f0fdf4',
                    borderRadius: 1,
                  }}
                >
                  <Typography variant="body2">{phase.name}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Float: {phase.float} days
                  </Typography>
                </Box>
              ))}
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Stack>
  )
}

function DemoCriticalPath() {
  const demoData: CriticalPathResult = {
    projectId: 'demo-project',
    criticalPath: ['1', '2', '4', '5'],
    totalDuration: 257,
    criticalPhases: [
      {
        phaseId: 1,
        name: 'Site Preparation',
        earlyStart: 0,
        earlyFinish: 30,
        lateStart: 0,
        lateFinish: 30,
        float: 0,
      },
      {
        phaseId: 2,
        name: 'Heritage Facade Restoration',
        earlyStart: 31,
        earlyFinish: 104,
        lateStart: 31,
        lateFinish: 104,
        float: 0,
      },
      {
        phaseId: 4,
        name: 'Structure Reinforcement',
        earlyStart: 105,
        earlyFinish: 180,
        lateStart: 105,
        lateFinish: 180,
        float: 0,
      },
      {
        phaseId: 5,
        name: 'MEP Installation',
        earlyStart: 181,
        earlyFinish: 257,
        lateStart: 181,
        lateFinish: 257,
        float: 0,
      },
    ],
    nonCriticalPhases: [
      { phaseId: 3, name: 'Tenant Relocation Phase 1', float: 30 },
      { phaseId: 6, name: 'Interior Fit-Out', float: 15 },
    ],
  }
  return <CriticalPathView data={demoData} />
}

function HeritageView({ data }: { data: HeritageTracker }) {
  return (
    <Stack spacing={3}>
      <Paper variant="outlined" sx={{ p: 3 }}>
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          sx={{ mb: 2 }}
        >
          <Typography variant="h6">Heritage Preservation Status</Typography>
          <Typography
            variant="body2"
            sx={{
              px: 2,
              py: 0.5,
              backgroundColor:
                data.overallApprovalStatus === 'approved'
                  ? '#dcfce7'
                  : data.overallApprovalStatus === 'pending'
                    ? '#fef3c7'
                    : '#fee2e2',
              borderRadius: 1,
            }}
          >
            {data.overallApprovalStatus}
          </Typography>
        </Stack>
        <Typography variant="body2" color="text.secondary">
          Classification:{' '}
          <strong>{data.heritageClassification.replace(/_/g, ' ')}</strong>
        </Typography>
      </Paper>

      <Grid container spacing={2}>
        <Grid item xs={12} md={4}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>
              Required Approvals
            </Typography>
            <Stack spacing={1}>
              {data.requiredApprovals.map((approval, idx) => (
                <Typography key={idx} variant="body2">
                  • {approval}
                </Typography>
              ))}
            </Stack>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography
              variant="subtitle2"
              sx={{ fontWeight: 600, mb: 2, color: 'warning.main' }}
            >
              Preservation Risks
            </Typography>
            <Stack spacing={1}>
              {data.preservationRisks.map((risk, idx) => (
                <Typography key={idx} variant="body2">
                  • {risk}
                </Typography>
              ))}
            </Stack>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography
              variant="subtitle2"
              sx={{ fontWeight: 600, mb: 2, color: 'info.main' }}
            >
              Recommendations
            </Typography>
            <Stack spacing={1}>
              {data.recommendations.map((rec, idx) => (
                <Typography key={idx} variant="body2">
                  • {rec}
                </Typography>
              ))}
            </Stack>
          </Paper>
        </Grid>
      </Grid>

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
          Heritage Phases
        </Typography>
        <Divider sx={{ mb: 2 }} />
        <Stack spacing={2}>
          {data.phases.map((phase) => (
            <Box
              key={phase.phaseId}
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                p: 1.5,
                backgroundColor: phase.approvalRequired ? '#fefce8' : '#f9fafb',
                borderRadius: 1,
                border: '1px solid #e5e7eb',
              }}
            >
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {phase.name}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {phase.heritageClassification.replace(/_/g, ' ')}
                </Typography>
              </Box>
              {phase.approvalRequired && (
                <Typography
                  variant="caption"
                  sx={{
                    px: 1.5,
                    py: 0.5,
                    backgroundColor:
                      phase.approvalStatus === 'approved'
                        ? '#dcfce7'
                        : '#fef3c7',
                    borderRadius: 1,
                  }}
                >
                  {phase.approvalStatus ?? 'Pending'}
                </Typography>
              )}
            </Box>
          ))}
        </Stack>
      </Paper>
    </Stack>
  )
}

function DemoHeritageView() {
  const demoData: HeritageTracker = {
    projectId: 'demo-project',
    heritageClassification: 'conservation_building',
    overallApprovalStatus: 'pending',
    phases: [
      {
        phaseId: 2,
        name: 'Heritage Facade Restoration',
        heritageClassification: 'conservation_building',
        approvalRequired: true,
        approvalStatus: 'approved',
        specialConsiderations: [
          'Original materials must be preserved',
          'Historical facade elements protected',
        ],
      },
      {
        phaseId: 4,
        name: 'Structure Reinforcement',
        heritageClassification: 'conservation_building',
        approvalRequired: true,
        approvalStatus: 'pending',
        specialConsiderations: ['Non-invasive reinforcement methods required'],
      },
    ],
    requiredApprovals: [
      'URA Conservation approval',
      'National Heritage Board review',
      'Structural engineer heritage certification',
    ],
    preservationRisks: [
      'Original facade materials may be fragile',
      'Hidden structural issues in heritage elements',
      'Limited documentation of original construction',
    ],
    recommendations: [
      'Engage heritage architect for facade work',
      'Conduct detailed photogrammetry before work',
      'Prepare contingency for material sourcing',
    ],
  }
  return <HeritageView data={demoData} />
}

function DemoTenantCoordination() {
  const demoData: TenantCoordinationSummary = {
    projectId: 'demo-project',
    totalTenants: 8,
    statusBreakdown: {
      pending_notification: 1,
      notified: 2,
      confirmed: 2,
      in_progress: 1,
      relocated: 2,
    },
    relocations: [
      {
        id: 1,
        phaseId: 3,
        tenantName: 'ABC Trading Co.',
        currentUnit: '#01-01',
        relocationType: 'temporary',
        status: 'relocated',
        notificationDate: '2024-12-01',
        plannedMoveDate: '2025-02-15',
        actualMoveDate: '2025-02-14',
        temporaryLocation: '#05-01 (Temp)',
        compensationAmount: 15000,
        notes: null,
      },
      {
        id: 2,
        phaseId: 3,
        tenantName: 'XYZ Retail',
        currentUnit: '#01-02',
        relocationType: 'temporary',
        status: 'relocated',
        notificationDate: '2024-12-01',
        plannedMoveDate: '2025-02-20',
        actualMoveDate: '2025-02-19',
        temporaryLocation: '#05-02 (Temp)',
        compensationAmount: 12000,
        notes: null,
      },
      {
        id: 3,
        phaseId: 3,
        tenantName: 'Golden Restaurant',
        currentUnit: '#02-01',
        relocationType: 'permanent',
        status: 'in_progress',
        notificationDate: '2025-01-15',
        plannedMoveDate: '2025-03-15',
        actualMoveDate: null,
        temporaryLocation: null,
        compensationAmount: 50000,
        notes: 'Requires special kitchen equipment moving',
      },
      {
        id: 4,
        phaseId: 6,
        tenantName: 'Tech Startup Inc.',
        currentUnit: '#03-01',
        relocationType: 'temporary',
        status: 'confirmed',
        notificationDate: '2025-02-01',
        plannedMoveDate: '2025-09-01',
        actualMoveDate: null,
        temporaryLocation: '#06-01 (Temp)',
        compensationAmount: 8000,
        notes: null,
      },
      {
        id: 5,
        phaseId: 6,
        tenantName: 'Design Studio',
        currentUnit: '#03-02',
        relocationType: 'temporary',
        status: 'confirmed',
        notificationDate: '2025-02-01',
        plannedMoveDate: '2025-09-15',
        actualMoveDate: null,
        temporaryLocation: '#06-02 (Temp)',
        compensationAmount: 6000,
        notes: null,
      },
    ],
    upcomingMoves: [
      {
        id: 3,
        phaseId: 3,
        tenantName: 'Golden Restaurant',
        currentUnit: '#02-01',
        relocationType: 'permanent',
        status: 'in_progress',
        notificationDate: '2025-01-15',
        plannedMoveDate: '2025-03-15',
        actualMoveDate: null,
        temporaryLocation: null,
        compensationAmount: 50000,
        notes: null,
      },
    ],
    overdueNotifications: [],
    timeline: [
      {
        date: '2025-02-19',
        event: 'Move completed',
        tenantName: 'XYZ Retail',
        status: 'relocated',
      },
      {
        date: '2025-02-14',
        event: 'Move completed',
        tenantName: 'ABC Trading Co.',
        status: 'relocated',
      },
      {
        date: '2025-02-01',
        event: 'Notification sent',
        tenantName: 'Design Studio',
        status: 'notified',
      },
      {
        date: '2025-02-01',
        event: 'Notification sent',
        tenantName: 'Tech Startup Inc.',
        status: 'notified',
      },
      {
        date: '2025-01-15',
        event: 'Notification sent',
        tenantName: 'Golden Restaurant',
        status: 'notified',
      },
    ],
    warnings: [],
  }
  return <TenantRelocationDashboard data={demoData} />
}
