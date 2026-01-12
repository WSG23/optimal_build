import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import {
  Box,
  Button,
  Grid,
  Typography,
  Chip,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tab,
  Tabs,
  useTheme,
} from '@mui/material'
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  CheckCircle as ApprovedIcon,
  HourglassEmpty as PendingIcon,
  Error as RejectedIcon,
  QuestionAnswer as RfiIcon,
  Business as AgencyIcon,
  Timeline as TimelineIcon,
  SwapHoriz as SwapIcon,
  AccountBalance as HeritageIcon,
  Assignment as SubmissionIcon,
} from '@mui/icons-material'
import {
  regulatoryApi,
  AuthoritySubmission,
  ChangeOfUseApplication,
  HeritageSubmission,
  AssetType,
} from '../../../api/regulatory'
import { SubmissionWizard } from './components/SubmissionWizard'
import { CompliancePathTimeline } from './components/CompliancePathTimeline'
import { ChangeOfUseWizard } from './components/ChangeOfUseWizard'
import { HeritageSubmissionForm } from './components/HeritageSubmissionForm'
import { getTableSx, getPrimaryButtonSx } from '../../../utils/themeStyles'
import { useProject } from '../../../contexts/useProject'

const AGENCIES_INFO = [
  { code: 'URA', name: 'Urban Redevelopment Authority', status: 'Online' },
  { code: 'BCA', name: 'Building & Construction Authority', status: 'Online' },
  { code: 'SCDF', name: 'Singapore Civil Defence Force', status: 'Online' },
  { code: 'NEA', name: 'National Environment Agency', status: 'Online' },
]

const STORAGE_PREFIX = 'ob_regulatory'

const buildStorageKey = (projectId: string, suffix: string) =>
  `${STORAGE_PREFIX}:${projectId}:${suffix}`

const loadStoredList = <T,>(projectId: string, suffix: string): T[] => {
  if (typeof window === 'undefined' || !projectId) {
    return []
  }
  const raw = window.localStorage.getItem(buildStorageKey(projectId, suffix))
  if (!raw) {
    return []
  }
  try {
    const parsed = JSON.parse(raw) as T[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

const persistList = <T,>(projectId: string, suffix: string, items: T[]) => {
  if (typeof window === 'undefined' || !projectId) {
    return
  }
  window.localStorage.setItem(
    buildStorageKey(projectId, suffix),
    JSON.stringify(items),
  )
}

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <Box
      role="tabpanel"
      hidden={value !== index}
      id={`regulatory-tabpanel-${index}`}
      aria-labelledby={`regulatory-tab-${index}`}
      sx={{ pt: 'var(--ob-space-300)' }}
    >
      {value === index && children}
    </Box>
  )
}

export const RegulatoryDashboardPage: React.FC = () => {
  const theme = useTheme()
  const isDarkMode = theme.palette.mode === 'dark'
  const { currentProject, isProjectLoading, projectError } = useProject()
  const projectId = currentProject?.id ?? ''

  const [tabValue, setTabValue] = useState(0)
  const [submissions, setSubmissions] = useState<AuthoritySubmission[]>([])
  const [changeOfUseApps, setChangeOfUseApps] = useState<
    ChangeOfUseApplication[]
  >([])
  const [heritageSubmissions, setHeritageSubmissions] = useState<
    HeritageSubmission[]
  >([])
  const [loading, setLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [wizardOpen, setWizardOpen] = useState(false)
  const [changeOfUseOpen, setChangeOfUseOpen] = useState(false)
  const [selectedChangeOfUse, setSelectedChangeOfUse] = useState<
    ChangeOfUseApplication | undefined
  >(undefined)
  const [heritageFormOpen, setHeritageFormOpen] = useState(false)
  const [selectedHeritageSubmission, setSelectedHeritageSubmission] = useState<
    HeritageSubmission | undefined
  >(undefined)
  const [error, setError] = useState<string | null>(null)
  const previousProjectId = useRef<string | null>(null)
  const fetchRequestId = useRef(0)
  const latestHeritageSubmission = useMemo(() => {
    if (heritageSubmissions.length === 0) {
      return null
    }
    return [...heritageSubmissions].sort((a, b) => {
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    })[0]
  }, [heritageSubmissions])
  const preferredAssetType = useMemo<AssetType | undefined>(() => {
    if (heritageSubmissions.length > 0) {
      return 'heritage'
    }
    if (changeOfUseApps.length > 0) {
      const latest = changeOfUseApps[0]
      return (latest.proposed_use || latest.current_use) as AssetType
    }
    return undefined
  }, [changeOfUseApps, heritageSubmissions])

  // Theme-aware styles
  const tableSx = getTableSx(isDarkMode)

  const fetchSubmissions = useCallback(
    async (isRefresh = false) => {
      if (!projectId) {
        return
      }
      const requestId = ++fetchRequestId.current
      if (isRefresh) setRefreshing(true)
      else setLoading(true)
      setError(null)

      const storedSubmissions = loadStoredList<AuthoritySubmission>(
        projectId,
        'submissions',
      )
      const storedChangeOfUse = loadStoredList<ChangeOfUseApplication>(
        projectId,
        'change-of-use',
      )
      const storedHeritage = loadStoredList<HeritageSubmission>(
        projectId,
        'heritage',
      )

      try {
        // Fetch authority submissions
        const data = await regulatoryApi.listSubmissions(projectId)
        if (requestId !== fetchRequestId.current) {
          return
        }
        setSubmissions(data)
        persistList(projectId, 'submissions', data)

        // Fetch change of use applications
        const couApps =
          await regulatoryApi.listChangeOfUseApplications(projectId)
        if (requestId !== fetchRequestId.current) {
          return
        }
        setChangeOfUseApps(couApps)
        persistList(projectId, 'change-of-use', couApps)

        // Fetch heritage submissions
        const heritageData =
          await regulatoryApi.listHeritageSubmissions(projectId)
        if (requestId !== fetchRequestId.current) {
          return
        }
        setHeritageSubmissions(heritageData)
        persistList(projectId, 'heritage', heritageData)

        // Poll recent submissions for updates
        const pendingItems = data.filter((s) =>
          ['SUBMITTED', 'IN_REVIEW'].includes(s.status),
        )
        if (pendingItems.length > 0 && isRefresh) {
          for (const item of pendingItems) {
            await regulatoryApi.getSubmissionStatus(item.id)
          }
          const updatedData = await regulatoryApi.listSubmissions(projectId)
          if (requestId !== fetchRequestId.current) {
            return
          }
          setSubmissions(updatedData)
        }
      } catch (err) {
        if (requestId !== fetchRequestId.current) {
          return
        }
        console.error(err)
        setSubmissions(storedSubmissions)
        setChangeOfUseApps(storedChangeOfUse)
        setHeritageSubmissions(storedHeritage)
        if (
          storedSubmissions.length === 0 &&
          storedChangeOfUse.length === 0 &&
          storedHeritage.length === 0
        ) {
          setError('Failed to load submissions')
        }
      } finally {
        if (requestId === fetchRequestId.current) {
          if (isRefresh) setRefreshing(false)
          else setLoading(false)
        }
      }
    },
    [projectId],
  )

  useEffect(() => {
    fetchSubmissions()
  }, [fetchSubmissions])

  useEffect(() => {
    if (previousProjectId.current === projectId) {
      return
    }
    previousProjectId.current = projectId
    setSubmissions([])
    setChangeOfUseApps([])
    setHeritageSubmissions([])
    setSelectedChangeOfUse(undefined)
    setSelectedHeritageSubmission(undefined)
    setWizardOpen(false)
    setChangeOfUseOpen(false)
    setHeritageFormOpen(false)
    setError(null)
  }, [projectId])

  if (!projectId) {
    return (
      <Box sx={{ width: '100%' }}>
        {isProjectLoading ? (
          <CircularProgress />
        ) : (
          <Alert severity={projectError ? 'error' : 'info'}>
            {projectError?.message ??
              'Select a project to manage regulatory submissions.'}
          </Alert>
        )}
      </Box>
    )
  }

  const handleCreateSuccess = (newSubmission: AuthoritySubmission) => {
    setSubmissions((prev) => {
      const next = [
        newSubmission,
        ...prev.filter((s) => s.id !== newSubmission.id),
      ]
      persistList(projectId, 'submissions', next)
      return next
    })
    setWizardOpen(false)
  }

  const handleHeritageSuccess = (submission: HeritageSubmission) => {
    // Update or add to the list
    setHeritageSubmissions((prev) => {
      const existingIndex = prev.findIndex((s) => s.id === submission.id)
      if (existingIndex >= 0) {
        const updated = [...prev]
        updated[existingIndex] = submission
        persistList(projectId, 'heritage', updated)
        return updated
      }
      const next = [submission, ...prev]
      persistList(projectId, 'heritage', next)
      return next
    })
    // Don't close the form - let user continue editing or submit to STB
  }

  const openHeritageForm = (submission?: HeritageSubmission) => {
    setSelectedHeritageSubmission(submission)
    setHeritageFormOpen(true)
  }

  const openChangeOfUseForm = (application?: ChangeOfUseApplication) => {
    setSelectedChangeOfUse(application)
    setChangeOfUseOpen(true)
  }

  const closeHeritageForm = () => {
    setHeritageFormOpen(false)
    setSelectedHeritageSubmission(undefined)
  }

  const closeChangeOfUseForm = () => {
    setChangeOfUseOpen(false)
    setSelectedChangeOfUse(undefined)
  }

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  const getStatusColor = (status: string) => {
    switch (status.toUpperCase()) {
      case 'APPROVED':
        return 'success'
      case 'REJECTED':
        return 'error'
      case 'RFI':
        return 'warning'
      case 'IN_REVIEW':
        return 'info'
      case 'SUBMITTED':
        return 'primary'
      case 'DRAFT':
        return 'default'
      default:
        return 'default'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status.toUpperCase()) {
      case 'APPROVED':
        return <ApprovedIcon fontSize="small" />
      case 'REJECTED':
        return <RejectedIcon fontSize="small" />
      case 'RFI':
        return <RfiIcon fontSize="small" />
      case 'IN_REVIEW':
      case 'SUBMITTED':
        return <PendingIcon fontSize="small" />
      default:
        return <PendingIcon fontSize="small" />
    }
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
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--ob-space-300)',
          }}
        >
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
              Regulatory Dashboard
            </Typography>
            <Typography
              variant="body2"
              sx={{ color: 'text.secondary', mt: 'var(--ob-space-025)' }}
            >
              Manage authority submissions and compliance tracking
            </Typography>
          </Box>
          <Typography
            variant="body2"
            sx={{ color: 'text.secondary', mt: 'var(--ob-space-050)' }}
          >
            Project: {currentProject?.name ?? projectId}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 'var(--ob-space-150)' }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => fetchSubmissions(true)}
            disabled={refreshing || loading}
            size="small"
          >
            {refreshing ? 'Updating...' : 'Check Status'}
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setWizardOpen(true)}
            sx={getPrimaryButtonSx()}
            size="small"
          >
            New Submission
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 'var(--ob-space-200)' }}>
          {error}
        </Alert>
      )}

      {/* Quick Actions - Depth 1 (Glass Card with cyan edge) */}
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
          Quick Actions
        </Typography>
        <Grid container spacing="var(--ob-space-200)">
          <Grid item xs={12} sm={4}>
            <Box
              onClick={() => openChangeOfUseForm()}
              sx={{
                p: 'var(--ob-space-200)',
                cursor: 'pointer',
                borderRadius: 'var(--ob-radius-sm)',
                border: '1px solid',
                borderColor: 'divider',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-200)',
                transition: 'all 0.2s ease',
                '&:hover': {
                  borderColor: 'primary.main',
                  transform: 'translateY(-2px)',
                },
              }}
            >
              <SwapIcon color="primary" fontSize="large" />
              <Box>
                <Typography variant="subtitle1" fontWeight="bold">
                  Change of Use
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Apply for land use conversion
                </Typography>
              </Box>
            </Box>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Box
              onClick={() =>
                latestHeritageSubmission
                  ? openHeritageForm(latestHeritageSubmission)
                  : openHeritageForm()
              }
              sx={{
                p: 'var(--ob-space-200)',
                cursor: 'pointer',
                borderRadius: 'var(--ob-radius-sm)',
                border: '1px solid',
                borderColor: 'divider',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-200)',
                transition: 'all 0.2s ease',
                '&:hover': {
                  borderColor: 'primary.main',
                  transform: 'translateY(-2px)',
                },
              }}
            >
              <HeritageIcon color="primary" fontSize="large" />
              <Box>
                <Typography variant="subtitle1" fontWeight="bold">
                  Heritage Submission
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  STB conservation application
                </Typography>
                {latestHeritageSubmission ? (
                  <Box sx={{ mt: 'var(--ob-space-050)' }}>
                    <Typography variant="caption" color="text.secondary">
                      Latest draft{' '}
                      {new Date(
                        latestHeritageSubmission.created_at,
                      ).toLocaleDateString()}
                      {' • '}Click to reopen
                    </Typography>
                    <Box>
                      <Button
                        size="small"
                        variant="text"
                        onClick={(event) => {
                          event.stopPropagation()
                          openHeritageForm()
                        }}
                        sx={{ mt: 'var(--ob-space-050)', px: 0 }}
                      >
                        Start new submission
                      </Button>
                    </Box>
                  </Box>
                ) : null}
              </Box>
            </Box>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Box
              onClick={() => setTabValue(1)}
              sx={{
                p: 'var(--ob-space-200)',
                cursor: 'pointer',
                borderRadius: 'var(--ob-radius-sm)',
                border: '1px solid',
                borderColor: 'divider',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-200)',
                transition: 'all 0.2s ease',
                '&:hover': {
                  borderColor: 'primary.main',
                  transform: 'translateY(-2px)',
                },
              }}
            >
              <TimelineIcon color="primary" fontSize="large" />
              <Box>
                <Typography variant="subtitle1" fontWeight="bold">
                  Compliance Timeline
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  View regulatory path by asset type
                </Typography>
              </Box>
            </Box>
          </Grid>
        </Grid>
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab
            label="Submissions"
            icon={<SubmissionIcon />}
            iconPosition="start"
          />
          <Tab
            label="Compliance Path"
            icon={<TimelineIcon />}
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Tab 0: Submissions */}
      <TabPanel value={tabValue} index={0}>
        {/* Agency Status Cards - Depth 1 (Glass Card with cyan edge) */}
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
            Connected Agencies
          </Typography>
          <Grid container spacing="var(--ob-space-200)">
            {AGENCIES_INFO.map((agency) => (
              <Grid item xs={12} sm={6} md={3} key={agency.code}>
                <Box
                  sx={{
                    p: 'var(--ob-space-200)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--ob-space-200)',
                    borderRadius: 'var(--ob-radius-sm)',
                    border: '1px solid',
                    borderColor: 'divider',
                  }}
                >
                  <AgencyIcon color="primary" fontSize="large" />
                  <Box>
                    <Typography variant="subtitle1" fontWeight="bold">
                      {agency.code}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {agency.name}
                    </Typography>
                  </Box>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Box>

        {/* Submissions Table - Depth 1 (Glass Card with cyan edge) */}
        {loading ? (
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              p: 'var(--ob-space-800)',
            }}
          >
            <CircularProgress />
          </Box>
        ) : (
          <Box className="ob-card-module">
            <Typography
              variant="subtitle2"
              sx={{
                color: 'text.secondary',
                mb: 'var(--ob-space-200)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              Authority Submissions
            </Typography>
            {submissions.length === 0 ? (
              <Box sx={{ p: 'var(--ob-space-400)', textAlign: 'center' }}>
                <Typography color="text.secondary">
                  No authority submissions yet. Change of Use and Heritage
                  drafts appear below.
                </Typography>
              </Box>
            ) : (
              <TableContainer sx={{ width: '100%', overflowX: 'auto' }}>
                <Table sx={tableSx}>
                  <TableHead>
                    <TableRow>
                      <TableCell>Reference No.</TableCell>
                      <TableCell>Title</TableCell>
                      <TableCell>Agency</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Submitted</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {submissions.map((row) => (
                      <TableRow key={row.id} hover>
                        <TableCell sx={{ fontFamily: 'monospace' }}>
                          {row.submission_no || 'PENDING'}
                        </TableCell>
                        <TableCell sx={{ fontWeight: 500 }}>
                          {row.title}
                          {row.description && (
                            <Typography
                              variant="caption"
                              display="block"
                              color="text.secondary"
                            >
                              {row.description}
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell>{row.agency_id}</TableCell>
                        <TableCell>{row.submission_type}</TableCell>
                        <TableCell>
                          <Chip
                            label={row.status.replace('_', ' ')}
                            size="small"
                            color={
                              getStatusColor(row.status) as
                                | 'default'
                                | 'primary'
                                | 'secondary'
                                | 'error'
                                | 'info'
                                | 'success'
                                | 'warning'
                            }
                            icon={getStatusIcon(row.status)}
                            variant="outlined"
                            sx={{ textTransform: 'capitalize' }}
                          />
                        </TableCell>
                        <TableCell>
                          {new Date(
                            row.submitted_at || Date.now(),
                          ).toLocaleDateString()}
                        </TableCell>
                        <TableCell align="right">
                          <Button
                            size="small"
                            onClick={() =>
                              regulatoryApi
                                .getSubmissionStatus(row.id)
                                .then(() => fetchSubmissions(false))
                            }
                          >
                            Track
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>
        )}

        {/* Change of Use Applications Section */}
        <Box className="ob-card-module" sx={{ mt: 'var(--ob-space-400)' }}>
          <Typography
            variant="subtitle2"
            sx={{
              color: 'text.secondary',
              mb: 'var(--ob-space-200)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            Change of Use Applications
          </Typography>
          {changeOfUseApps.length === 0 ? (
            <Box sx={{ p: 'var(--ob-space-250)', textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                No change of use applications yet.
              </Typography>
            </Box>
          ) : (
            <TableContainer sx={{ width: '100%', overflowX: 'auto' }}>
              <Table sx={tableSx}>
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>Current Use</TableCell>
                    <TableCell>Proposed Use</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>DC Amendment</TableCell>
                    <TableCell>Planning Permission</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {changeOfUseApps.map((app) => {
                    const isDraft = app.status.toUpperCase() === 'DRAFT'
                    return (
                      <TableRow key={app.id} hover>
                        <TableCell sx={{ fontFamily: 'monospace' }}>
                          {app.id.slice(0, 8)}...
                        </TableCell>
                        <TableCell sx={{ textTransform: 'capitalize' }}>
                          {app.current_use}
                        </TableCell>
                        <TableCell sx={{ textTransform: 'capitalize' }}>
                          {app.proposed_use}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={app.status.replace('_', ' ')}
                            size="small"
                            color={
                              getStatusColor(app.status.toLowerCase()) as
                                | 'default'
                                | 'primary'
                                | 'secondary'
                                | 'error'
                                | 'info'
                                | 'success'
                                | 'warning'
                            }
                            variant="outlined"
                            sx={{ textTransform: 'capitalize' }}
                          />
                        </TableCell>
                        <TableCell>
                          {app.requires_dc_amendment ? 'Yes' : 'No'}
                        </TableCell>
                        <TableCell>
                          {app.requires_planning_permission ? 'Yes' : 'No'}
                        </TableCell>
                        <TableCell>
                          {new Date(app.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell align="right">
                          <Button
                            size="small"
                            onClick={() => openChangeOfUseForm(app)}
                          >
                            {isDraft ? 'Edit' : 'View'}
                          </Button>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Box>

        {/* Heritage Submissions Section */}
        <Box className="ob-card-module" sx={{ mt: 'var(--ob-space-300)' }}>
          <Typography
            variant="h6"
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--ob-space-100)',
              mb: 'var(--ob-space-200)',
            }}
          >
            <HeritageIcon color="primary" />
            Heritage Submissions (STB)
          </Typography>
          {heritageSubmissions.length === 0 ? (
            <Box
              sx={{
                p: 'var(--ob-space-250)',
                border: '1px dashed',
                borderColor: 'divider',
                borderRadius: 'var(--ob-radius-sm)',
                textAlign: 'center',
              }}
            >
              <Typography variant="body2" color="text.secondary">
                No heritage submissions yet. Start a draft to capture the
                conservation details.
              </Typography>
              <Button
                size="small"
                sx={{ mt: 'var(--ob-space-150)' }}
                onClick={() => openHeritageForm()}
              >
                Start heritage submission
              </Button>
            </Box>
          ) : (
            <TableContainer sx={{ width: '100%', overflowX: 'auto' }}>
              <Table sx={tableSx}>
                <TableHead>
                  <TableRow>
                    <TableCell>Reference</TableCell>
                    <TableCell>Conservation Status</TableCell>
                    <TableCell>Year Built</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {heritageSubmissions.map((sub) => (
                    <TableRow key={sub.id} hover>
                      <TableCell sx={{ fontFamily: 'monospace' }}>
                        {sub.stb_reference || sub.id.slice(0, 8) + '...'}
                      </TableCell>
                      <TableCell sx={{ textTransform: 'capitalize' }}>
                        {sub.conservation_status.replace(/_/g, ' ')}
                      </TableCell>
                      <TableCell>
                        {sub.original_construction_year || '-'}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={sub.status.replace('_', ' ')}
                          size="small"
                          color={
                            getStatusColor(sub.status) as
                              | 'default'
                              | 'primary'
                              | 'secondary'
                              | 'error'
                              | 'info'
                              | 'success'
                              | 'warning'
                          }
                          variant="outlined"
                          sx={{ textTransform: 'capitalize' }}
                        />
                      </TableCell>
                      <TableCell>
                        {new Date(sub.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell align="right">
                        <Button
                          size="small"
                          onClick={() => openHeritageForm(sub)}
                        >
                          {sub.status.toUpperCase() === 'DRAFT'
                            ? 'Edit'
                            : 'View'}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Box>
      </TabPanel>

      {/* Tab 1: Compliance Path - Depth 1 (Glass Card with cyan edge) */}
      <TabPanel value={tabValue} index={1}>
        <Box className="ob-card-module">
          <CompliancePathTimeline
            projectId={projectId}
            projectName={currentProject?.name}
            preferredAssetType={preferredAssetType}
          />
        </Box>
      </TabPanel>

      {/* Dialogs */}
      <SubmissionWizard
        open={wizardOpen}
        onClose={() => setWizardOpen(false)}
        projectId={projectId}
        onSuccess={handleCreateSuccess}
      />

      <ChangeOfUseWizard
        open={changeOfUseOpen}
        onClose={closeChangeOfUseForm}
        projectId={projectId}
        initialApplication={selectedChangeOfUse}
        onSuccess={(application) => {
          closeChangeOfUseForm()
          setChangeOfUseApps((prev) => {
            const existingIndex = prev.findIndex((s) => s.id === application.id)
            if (existingIndex >= 0) {
              const updated = [...prev]
              updated[existingIndex] = application
              persistList(projectId, 'change-of-use', updated)
              return updated
            }
            const next = [application, ...prev]
            persistList(projectId, 'change-of-use', next)
            return next
          })
        }}
      />

      <HeritageSubmissionForm
        open={heritageFormOpen}
        onClose={closeHeritageForm}
        projectId={projectId}
        existingSubmission={selectedHeritageSubmission}
        onSuccess={handleHeritageSuccess}
      />
    </Box>
  )
}
