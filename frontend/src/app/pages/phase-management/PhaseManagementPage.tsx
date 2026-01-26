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
        p: 'var(--ob-space-200)',
        borderRadius: 'var(--ob-radius-md)',
        background: 'rgba(30, 30, 30, 0.6)',
        backdropFilter: 'blur(var(--ob-blur-md))',
        border: '1px solid var(--ob-color-action-hover)',
        boxShadow: '0 8px 32px 0 var(--ob-color-overlay-backdrop-light)',
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--ob-space-200)',
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow:
            '0 12px 40px 0 var(--ob-color-overlay-backdrop), 0 0 20px var(--ob-color-action-selected)',
          border: '1px solid var(--ob-color-surface-overlay-medium)',
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
              sx={{ color: 'var(--ob-color-surface-overlay)' }}
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
                top: '0',
                left: 0,
                bottom: '0',
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
          icon && <Box sx={{ p: 'var(--ob-space-100)' }}>{icon}</Box>
        )}
      </Box>

      <Box>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 700,
            color: 'var(--ob-color-bg-default)',
            textShadow: '0 2px 10px var(--ob-color-overlay-backdrop)',
            fontSize: '1.75rem',
            lineHeight: 1,
            mb: 'var(--ob-space-50)',
          }}
        >
          {value}
          {suffix && (
            <Typography
              component="span"
              variant="h6"
              sx={{ ml: 'var(--ob-space-50)', opacity: 0.7 }}
            >
              {suffix}
            </Typography>
          )}
        </Typography>
        <Stack
          direction="row"
          alignItems="center"
          spacing="var(--ob-space-100)"
        >
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
      sx={{ pt: 'var(--ob-space-300)' }}
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
        const results = await Promise.allSettled([
          fetchGanttChart(projectId, signal),
          fetchCriticalPath(projectId, signal),
          fetchHeritageTracker(projectId, signal),
          fetchTenantCoordination(projectId, signal),
        ])

        if (signal?.aborted) return

        const [ganttResult, criticalResult, heritageResult, tenantResult] =
          results

        setGanttData(
          ganttResult.status === 'fulfilled' ? ganttResult.value : null,
        )
        setCriticalPath(
          criticalResult.status === 'fulfilled' ? criticalResult.value : null,
        )
        setHeritageData(
          heritageResult.status === 'fulfilled' ? heritageResult.value : null,
        )
        setTenantData(
          tenantResult.status === 'fulfilled' ? tenantResult.value : null,
        )

        const failedRequests: string[] = []
        if (ganttResult.status === 'rejected')
          failedRequests.push('Gantt chart')
        if (criticalResult.status === 'rejected')
          failedRequests.push('Critical path')
        if (heritageResult.status === 'rejected')
          failedRequests.push('Heritage tracking')
        if (tenantResult.status === 'rejected')
          failedRequests.push('Tenant coordination')

        if (failedRequests.length > 0) {
          setError(
            `Failed to load: ${failedRequests.join(
              ', ',
            )}. Please verify the phase APIs are available.`,
          )
        }
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
        completionPct: 0,
        heritageCompletionPct: 0,
        tenantCompletionPct: 0,
      }
    }

    const heritageTasks = ganttData.tasks.filter((t) => t.isHeritage)
    const tenantTasks = ganttData.tasks.filter((t) => t.hasTenantCoordination)
    const heritageCompletionPct =
      heritageTasks.length > 0
        ? (heritageTasks.reduce((acc, t) => acc + t.progress, 0) /
            heritageTasks.length) *
          100
        : 0
    const tenantCompletionPct =
      tenantTasks.length > 0
        ? (tenantTasks.reduce((acc, t) => acc + t.progress, 0) /
            tenantTasks.length) *
          100
        : 0

    return {
      totalPhases: ganttData.tasks.length,
      criticalPhases: ganttData.tasks.filter((t) => t.isCritical).length,
      heritagePhases: heritageTasks.length,
      tenantPhases: tenantTasks.length,
      totalDuration: ganttData.totalDuration,
      criticalDuration: ganttData.criticalPathDuration,
      completionPct: ganttData.completionPct,
      heritageCompletionPct,
      tenantCompletionPct,
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
        <Stack alignItems="center" spacing="var(--ob-space-200)">
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
        <Stack direction="row" spacing="var(--ob-space-100)" flexWrap="wrap">
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
          {error}
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
            icon={
              <TimelineIcon
                sx={{ fontSize: 28, color: 'var(--ob-color-neon-cyan)' }}
              />
            }
            value={stats.totalPhases}
            label="Total Phases"
            progress={stats.completionPct}
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
              <AccountBalanceIcon
                sx={{ fontSize: 28, color: 'var(--ob-color-warning)' }}
              />
            }
            value={stats.heritagePhases}
            label="Heritage Phases"
            progress={stats.heritageCompletionPct}
            color="#f59e0b"
          />
          <HolographicCard
            icon={<PeopleIcon sx={{ fontSize: 28, color: '#a855f7' }} />}
            value={stats.tenantPhases}
            label="Tenant Coord"
            progress={stats.tenantCompletionPct}
            color="#a855f7"
          />
          <HolographicCard
            value={stats.totalDuration}
            label="Total Days"
            suffix="d"
            progress={stats.completionPct}
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
          borderBottom: 'var(--ob-space-100)',
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
            <Alert severity="info">
              No Gantt data available for this project yet.
            </Alert>
          )}
        </TabPanel>

        {/* Critical Path Tab */}
        <TabPanel value={activeTab} index={1}>
          {criticalPath ? (
            <CriticalPathView data={criticalPath} />
          ) : (
            <Alert severity="info">
              Critical path analysis is unavailable for this project.
            </Alert>
          )}
        </TabPanel>

        {/* Heritage Tracking Tab */}
        <TabPanel value={activeTab} index={2}>
          {heritageData ? (
            <HeritageView data={heritageData} />
          ) : (
            <Alert severity="info">
              Heritage tracking is unavailable for this project.
            </Alert>
          )}
        </TabPanel>

        {/* Tenant Coordination Tab */}
        <TabPanel value={activeTab} index={3}>
          {tenantData ? (
            <TenantRelocationDashboard data={tenantData} />
          ) : (
            <Alert severity="info">
              Tenant coordination data is unavailable for this project.
            </Alert>
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

function CriticalPathView({ data }: { data: CriticalPathResult }) {
  return (
    <Stack spacing="var(--ob-space-300)">
      <Paper variant="outlined" sx={{ p: 'var(--ob-space-300)' }}>
        <Typography variant="h6" sx={{ mb: 'var(--ob-space-200)' }}>
          Critical Path Analysis
        </Typography>
        <Typography variant="body1" sx={{ mb: 'var(--ob-space-200)' }}>
          Total Duration: <strong>{data.totalDuration} days</strong>
        </Typography>
        <Typography variant="body2" color="text.secondary">
          The critical path represents the longest sequence of dependent phases
          that determines the minimum project duration. Any delay in critical
          phases will delay the entire project.
        </Typography>
      </Paper>

      <Grid container spacing="var(--ob-space-200)">
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 'var(--ob-space-200)' }}>
            <Typography
              variant="subtitle1"
              sx={{
                fontWeight: 600,
                mb: 'var(--ob-space-200)',
                color: 'error.main',
              }}
            >
              Critical Phases ({data.criticalPhases.length})
            </Typography>
            <Stack spacing="var(--ob-space-100)">
              {data.criticalPhases.map((phase) => (
                <Box
                  key={phase.phaseId}
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    p: 'var(--ob-space-100)',
                    backgroundColor: '#fef2f2',
                    borderRadius: 'var(--ob-radius-sm)',
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
          <Paper variant="outlined" sx={{ p: 'var(--ob-space-200)' }}>
            <Typography
              variant="subtitle1"
              sx={{
                fontWeight: 600,
                mb: 'var(--ob-space-200)',
                color: 'success.main',
              }}
            >
              Non-Critical Phases ({data.nonCriticalPhases.length})
            </Typography>
            <Stack spacing="var(--ob-space-100)">
              {data.nonCriticalPhases.map((phase) => (
                <Box
                  key={phase.phaseId}
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    p: 'var(--ob-space-100)',
                    backgroundColor: '#f0fdf4',
                    borderRadius: 'var(--ob-radius-sm)',
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

function HeritageView({ data }: { data: HeritageTracker }) {
  return (
    <Stack spacing="var(--ob-space-300)">
      <Paper variant="outlined" sx={{ p: 'var(--ob-space-300)' }}>
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          sx={{ mb: 'var(--ob-space-200)' }}
        >
          <Typography variant="h6">Heritage Preservation Status</Typography>
          <Typography
            variant="body2"
            sx={{
              px: 'var(--ob-space-200)',
              py: 'var(--ob-space-50)',
              backgroundColor:
                data.overallApprovalStatus === 'approved'
                  ? '#dcfce7'
                  : data.overallApprovalStatus === 'pending'
                    ? '#fef3c7'
                    : 'var(--ob-color-error-muted)',
              borderRadius: 'var(--ob-radius-sm)',
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

      <Grid container spacing="var(--ob-space-200)">
        <Grid item xs={12} md={4}>
          <Paper variant="outlined" sx={{ p: 'var(--ob-space-200)' }}>
            <Typography
              variant="subtitle2"
              sx={{ fontWeight: 600, mb: 'var(--ob-space-200)' }}
            >
              Required Approvals
            </Typography>
            <Stack spacing="var(--ob-space-100)">
              {data.requiredApprovals.map((approval, idx) => (
                <Typography key={idx} variant="body2">
                  • {approval}
                </Typography>
              ))}
            </Stack>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper variant="outlined" sx={{ p: 'var(--ob-space-200)' }}>
            <Typography
              variant="subtitle2"
              sx={{
                fontWeight: 600,
                mb: 'var(--ob-space-200)',
                color: 'warning.main',
              }}
            >
              Preservation Risks
            </Typography>
            <Stack spacing="var(--ob-space-100)">
              {data.preservationRisks.map((risk, idx) => (
                <Typography key={idx} variant="body2">
                  • {risk}
                </Typography>
              ))}
            </Stack>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper variant="outlined" sx={{ p: 'var(--ob-space-200)' }}>
            <Typography
              variant="subtitle2"
              sx={{
                fontWeight: 600,
                mb: 'var(--ob-space-200)',
                color: 'info.main',
              }}
            >
              Recommendations
            </Typography>
            <Stack spacing="var(--ob-space-100)">
              {data.recommendations.map((rec, idx) => (
                <Typography key={idx} variant="body2">
                  • {rec}
                </Typography>
              ))}
            </Stack>
          </Paper>
        </Grid>
      </Grid>

      <Paper variant="outlined" sx={{ p: 'var(--ob-space-200)' }}>
        <Typography
          variant="subtitle1"
          sx={{ fontWeight: 600, mb: 'var(--ob-space-200)' }}
        >
          Heritage Phases
        </Typography>
        <Divider sx={{ mb: 'var(--ob-space-200)' }} />
        <Stack spacing="var(--ob-space-200)">
          {data.phases.map((phase) => (
            <Box
              key={phase.phaseId}
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                p: 'var(--ob-space-150)',
                backgroundColor: phase.approvalRequired
                  ? '#fefce8'
                  : 'var(--ob-color-bg-muted)',
                borderRadius: 'var(--ob-radius-sm)',
                border: '1px solid var(--ob-color-border-subtle)',
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
                    px: 'var(--ob-space-150)',
                    py: 'var(--ob-space-50)',
                    backgroundColor:
                      phase.approvalStatus === 'approved'
                        ? '#dcfce7'
                        : '#fef3c7',
                    borderRadius: 'var(--ob-radius-sm)',
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
