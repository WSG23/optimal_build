import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
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

// Demo project ID - in production this would come from route params or context
const DEMO_PROJECT_ID = 1

export function PhaseManagementPage() {
  const [activeTab, setActiveTab] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Data states
  const [ganttData, setGanttData] = useState<GanttChartData | null>(null)
  const [criticalPath, setCriticalPath] = useState<CriticalPathResult | null>(null)
  const [heritageData, setHeritageData] = useState<HeritageTracker | null>(null)
  const [tenantData, setTenantData] = useState<TenantCoordinationSummary | null>(null)

  // UI states
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)
  const [editorOpen, setEditorOpen] = useState(false)
  const [editingPhase, setEditingPhase] = useState<DevelopmentPhase | null>(null)

  // Load all data
  const loadData = useCallback(async (controller?: AbortController) => {
    const signal = controller?.signal
    setLoading(true)
    setError(null)

    try {
      const [gantt, critical, heritage, tenant] = await Promise.all([
        fetchGanttChart(DEMO_PROJECT_ID, signal).catch(() => null),
        fetchCriticalPath(DEMO_PROJECT_ID, signal).catch(() => null),
        fetchHeritageTracker(DEMO_PROJECT_ID, signal).catch(() => null),
        fetchTenantCoordination(DEMO_PROJECT_ID, signal).catch(() => null),
      ])

      if (signal?.aborted) return

      setGanttData(gantt)
      setCriticalPath(critical)
      setHeritageData(heritage)
      setTenantData(tenant)
    } catch (err) {
      if ((err as { name?: string }).name === 'AbortError') return
      console.error('Failed to load phase data', err)
      setError('Failed to load project phase data. The API may not be available yet.')
    } finally {
      if (!signal?.aborted) {
        setLoading(false)
      }
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    loadData(controller)
    return () => controller.abort()
  }, [loadData])

  const handleTabChange = useCallback((_: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue)
  }, [])

  const handleTaskClick = useCallback((taskId: string) => {
    setSelectedTaskId(taskId)
  }, [])

  const handleAddPhase = useCallback(() => {
    setEditingPhase(null)
    setEditorOpen(true)
  }, [])

  const handleSavePhase = useCallback(
    async (data: CreatePhasePayload | UpdatePhasePayload, isNew: boolean) => {
      if (isNew) {
        await createPhase(DEMO_PROJECT_ID, data as CreatePhasePayload)
      } else if (editingPhase) {
        await updatePhase(DEMO_PROJECT_ID, editingPhase.id, data as UpdatePhasePayload)
      }
      // Reload data after save
      await loadData()
    },
    [editingPhase, loadData],
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
      tenantPhases: ganttData.tasks.filter((t) => t.hasTenantCoordination).length,
      totalDuration: ganttData.totalDuration,
      criticalDuration: ganttData.criticalPathDuration,
    }
  }, [ganttData])

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <Stack alignItems="center" spacing={2}>
          <CircularProgress />
          <Typography color="text.secondary">Loading project phases...</Typography>
        </Stack>
      </Box>
    )
  }

  return (
    <Box className="phase-management-page">
      {error && (
        <Alert severity="info" sx={{ mb: 3 }}>
          {error} Demo data is shown below.
        </Alert>
      )}

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} md={2}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center' }}>
              <TimelineIcon sx={{ fontSize: 32, color: 'primary.main', mb: 1 }} />
              <Typography variant="h4" sx={{ fontWeight: 600 }}>
                {stats.totalPhases}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Phases
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} md={2}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center' }}>
              <BarChartIcon sx={{ fontSize: 32, color: 'error.main', mb: 1 }} />
              <Typography variant="h4" sx={{ fontWeight: 600 }}>
                {stats.criticalPhases}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Critical Path
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} md={2}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center' }}>
              <AccountBalanceIcon sx={{ fontSize: 32, color: 'warning.main', mb: 1 }} />
              <Typography variant="h4" sx={{ fontWeight: 600 }}>
                {stats.heritagePhases}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Heritage Phases
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} md={2}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center' }}>
              <PeopleIcon sx={{ fontSize: 32, color: 'info.main', mb: 1 }} />
              <Typography variant="h4" sx={{ fontWeight: 600 }}>
                {stats.tenantPhases}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Tenant Coordination
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} md={2}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 600, color: 'text.primary' }}>
                {stats.totalDuration}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Days
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} md={2}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 600, color: 'error.main' }}>
                {stats.criticalDuration}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Critical Days
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content with Tabs */}
      <Paper elevation={0} sx={{ border: '1px solid #e0e0e0' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider', px: 2 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Tabs value={activeTab} onChange={handleTabChange}>
              <Tab label="Gantt Chart" icon={<TimelineIcon />} iconPosition="start" />
              <Tab label="Critical Path" icon={<BarChartIcon />} iconPosition="start" />
              <Tab label="Heritage Tracking" icon={<AccountBalanceIcon />} iconPosition="start" />
              <Tab label="Tenant Coordination" icon={<PeopleIcon />} iconPosition="start" />
            </Tabs>

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

        <Box sx={{ p: 2 }}>
          {/* Gantt Chart Tab */}
          <TabPanel value={activeTab} index={0}>
            {ganttData ? (
              <GanttChart
                data={ganttData}
                onTaskClick={handleTaskClick}
                selectedTaskId={selectedTaskId}
              />
            ) : (
              <DemoGanttChart onTaskClick={handleTaskClick} selectedTaskId={selectedTaskId} />
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
      </Paper>

      {/* Phase Editor Dialog */}
      <PhaseEditor
        open={editorOpen}
        phase={editingPhase}
        projectId={DEMO_PROJECT_ID}
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
    projectId: 1,
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

  return <GanttChart data={demoData} onTaskClick={onTaskClick} selectedTaskId={selectedTaskId} />
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
          The critical path represents the longest sequence of dependent phases that determines the
          minimum project duration. Any delay in critical phases will delay the entire project.
        </Typography>
      </Paper>

      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2, color: 'error.main' }}>
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
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2, color: 'success.main' }}>
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
    projectId: 1,
    criticalPath: ['1', '2', '4', '5'],
    totalDuration: 257,
    criticalPhases: [
      { phaseId: 1, name: 'Site Preparation', earlyStart: 0, earlyFinish: 30, lateStart: 0, lateFinish: 30, float: 0 },
      { phaseId: 2, name: 'Heritage Facade Restoration', earlyStart: 31, earlyFinish: 104, lateStart: 31, lateFinish: 104, float: 0 },
      { phaseId: 4, name: 'Structure Reinforcement', earlyStart: 105, earlyFinish: 180, lateStart: 105, lateFinish: 180, float: 0 },
      { phaseId: 5, name: 'MEP Installation', earlyStart: 181, earlyFinish: 257, lateStart: 181, lateFinish: 257, float: 0 },
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
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
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
          Classification: <strong>{data.heritageClassification.replace(/_/g, ' ')}</strong>
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
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2, color: 'warning.main' }}>
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
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2, color: 'info.main' }}>
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
                      phase.approvalStatus === 'approved' ? '#dcfce7' : '#fef3c7',
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
    projectId: 1,
    heritageClassification: 'conservation_building',
    overallApprovalStatus: 'pending',
    phases: [
      {
        phaseId: 2,
        name: 'Heritage Facade Restoration',
        heritageClassification: 'conservation_building',
        approvalRequired: true,
        approvalStatus: 'approved',
        specialConsiderations: ['Original materials must be preserved', 'Historical facade elements protected'],
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
    projectId: 1,
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
      { date: '2025-02-19', event: 'Move completed', tenantName: 'XYZ Retail', status: 'relocated' },
      { date: '2025-02-14', event: 'Move completed', tenantName: 'ABC Trading Co.', status: 'relocated' },
      { date: '2025-02-01', event: 'Notification sent', tenantName: 'Design Studio', status: 'notified' },
      { date: '2025-02-01', event: 'Notification sent', tenantName: 'Tech Startup Inc.', status: 'notified' },
      { date: '2025-01-15', event: 'Notification sent', tenantName: 'Golden Restaurant', status: 'notified' },
    ],
    warnings: [],
  }
  return <TenantRelocationDashboard data={demoData} />
}
