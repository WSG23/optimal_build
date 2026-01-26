import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import {
  Box,
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
import { getTableSx } from '../../../utils/themeStyles'
import { useProject } from '../../../contexts/useProject'
import { Button } from '../../../components/canonical/Button'
import { StatusChip } from '../../../components/canonical/StatusChip'
import { GlassCard } from '../../../components/canonical/GlassCard'

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

  const getStatusChipStatus = (
    status: string,
  ):
    | 'success'
    | 'warning'
    | 'error'
    | 'info'
    | 'neutral'
    | 'brand'
    | 'live' => {
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
        return 'brand'
      case 'DRAFT':
        return 'neutral'
      default:
        return 'neutral'
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
      {/* Page Header - Content on background (Content vs Context pattern) */}
      <Box
        component="header"
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: 'var(--ob-space-100)',
          mb: 'var(--ob-space-200)',
          animation:
            'ob-slide-down-fade var(--ob-motion-header-duration) var(--ob-motion-header-ease) both',
        }}
      >
        <Box>
          <Box
            component="h1"
            sx={{
              fontSize: 'var(--ob-font-size-2xl)',
              fontWeight: 700,
              lineHeight: 1.2,
              color: 'var(--ob-color-text-primary)',
              m: '0',
            }}
          >
            Regulatory Dashboard
          </Box>
          <Box
            component="p"
            sx={{
              fontSize: 'var(--ob-font-size-sm)',
              color: 'var(--ob-color-text-secondary)',
              m: '0',
              mt: 'var(--ob-space-025)',
            }}
          >
            Manage authority submissions and compliance tracking
          </Box>
          <Box
            component="span"
            sx={{
              fontSize: 'var(--ob-font-size-xs)',
              color: 'var(--ob-color-text-tertiary)',
              mt: 'var(--ob-space-050)',
              display: 'block',
            }}
          >
            Project: {currentProject?.name ?? projectId}
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 'var(--ob-space-100)' }}>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => fetchSubmissions(true)}
            disabled={refreshing || loading}
          >
            <RefreshIcon sx={{ fontSize: '1rem', mr: 'var(--ob-space-050)' }} />
            {refreshing ? 'Updating...' : 'Check Status'}
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setWizardOpen(true)}
          >
            <AddIcon sx={{ fontSize: '1rem', mr: 'var(--ob-space-050)' }} />
            New Submission
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 'var(--ob-space-200)' }}>
          {error}
        </Alert>
      )}

      {/* Quick Actions - Flat section (no wrapper, cards as siblings) */}
      <Box
        component="section"
        sx={{
          mb: 'var(--ob-space-200)',
        }}
      >
        <Box
          component="h2"
          sx={{
            fontSize: 'var(--ob-font-size-xs)',
            fontWeight: 600,
            color: 'var(--ob-color-text-tertiary)',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
            m: '0',
            mb: 'var(--ob-space-100)',
          }}
        >
          Quick Actions
        </Box>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' },
            gap: 'var(--ob-space-150)',
          }}
        >
          <GlassCard
            variant="default"
            hoverEffect
            onClick={() => openChangeOfUseForm()}
            sx={{
              p: 'var(--ob-space-150)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--ob-space-150)',
            }}
          >
            <SwapIcon
              sx={{ color: 'var(--ob-color-neon-cyan)', fontSize: 32 }}
            />
            <Box>
              <Box
                component="span"
                sx={{
                  fontSize: 'var(--ob-font-size-base)',
                  fontWeight: 600,
                  color: 'var(--ob-color-text-primary)',
                  display: 'block',
                }}
              >
                Change of Use
              </Box>
              <Box
                component="span"
                sx={{
                  fontSize: 'var(--ob-font-size-xs)',
                  color: 'var(--ob-color-text-secondary)',
                }}
              >
                Apply for land use conversion
              </Box>
            </Box>
          </GlassCard>

          <GlassCard
            variant="default"
            hoverEffect
            onClick={() =>
              latestHeritageSubmission
                ? openHeritageForm(latestHeritageSubmission)
                : openHeritageForm()
            }
            sx={{
              p: 'var(--ob-space-150)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--ob-space-150)',
            }}
          >
            <HeritageIcon
              sx={{ color: 'var(--ob-color-neon-cyan)', fontSize: 32 }}
            />
            <Box>
              <Box
                component="span"
                sx={{
                  fontSize: 'var(--ob-font-size-base)',
                  fontWeight: 600,
                  color: 'var(--ob-color-text-primary)',
                  display: 'block',
                }}
              >
                Heritage Submission
              </Box>
              <Box
                component="span"
                sx={{
                  fontSize: 'var(--ob-font-size-xs)',
                  color: 'var(--ob-color-text-secondary)',
                }}
              >
                STB conservation application
              </Box>
              {latestHeritageSubmission ? (
                <Box sx={{ mt: 'var(--ob-space-050)' }}>
                  <Box
                    component="span"
                    sx={{
                      fontSize: 'var(--ob-font-size-2xs)',
                      color: 'var(--ob-color-text-tertiary)',
                      display: 'block',
                    }}
                  >
                    Latest draft{' '}
                    {new Date(
                      latestHeritageSubmission.created_at,
                    ).toLocaleDateString()}
                    {' • '}Click to reopen
                  </Box>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(event) => {
                      event.stopPropagation()
                      openHeritageForm()
                    }}
                  >
                    Start new submission
                  </Button>
                </Box>
              ) : null}
            </Box>
          </GlassCard>

          <GlassCard
            variant="default"
            hoverEffect
            onClick={() => setTabValue(1)}
            sx={{
              p: 'var(--ob-space-150)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--ob-space-150)',
            }}
          >
            <TimelineIcon
              sx={{ color: 'var(--ob-color-neon-cyan)', fontSize: 32 }}
            />
            <Box>
              <Box
                component="span"
                sx={{
                  fontSize: 'var(--ob-font-size-base)',
                  fontWeight: 600,
                  color: 'var(--ob-color-text-primary)',
                  display: 'block',
                }}
              >
                Compliance Timeline
              </Box>
              <Box
                component="span"
                sx={{
                  fontSize: 'var(--ob-font-size-xs)',
                  color: 'var(--ob-color-text-secondary)',
                }}
              >
                View regulatory path by asset type
              </Box>
            </Box>
          </GlassCard>
        </Box>
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 'var(--ob-space-100)', borderColor: 'divider' }}>
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
        {/* Agency Status Cards - Flat section pattern */}
        <Box component="section" sx={{ mb: 'var(--ob-space-200)' }}>
          <Box
            component="h3"
            sx={{
              fontSize: 'var(--ob-font-size-xs)',
              fontWeight: 600,
              color: 'var(--ob-color-text-tertiary)',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              m: '0',
              mb: 'var(--ob-space-100)',
            }}
          >
            Connected Agencies
          </Box>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: {
                xs: '1fr',
                sm: 'repeat(2, 1fr)',
                md: 'repeat(4, 1fr)',
              },
              gap: 'var(--ob-space-100)',
            }}
          >
            {AGENCIES_INFO.map((agency) => (
              <GlassCard
                key={agency.code}
                variant="default"
                sx={{
                  p: 'var(--ob-space-100)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--ob-space-100)',
                }}
              >
                <AgencyIcon
                  sx={{ color: 'var(--ob-color-neon-cyan)', fontSize: 28 }}
                />
                <Box>
                  <Box
                    component="span"
                    sx={{
                      fontSize: 'var(--ob-font-size-sm)',
                      fontWeight: 600,
                      color: 'var(--ob-color-text-primary)',
                      display: 'block',
                    }}
                  >
                    {agency.code}
                  </Box>
                  <Box
                    component="span"
                    sx={{
                      fontSize: 'var(--ob-font-size-2xs)',
                      color: 'var(--ob-color-text-secondary)',
                    }}
                  >
                    {agency.name}
                  </Box>
                </Box>
              </GlassCard>
            ))}
          </Box>
        </Box>

        {/* Submissions Table - Flat section with GlassCard for data */}
        <Box component="section" sx={{ mb: 'var(--ob-space-200)' }}>
          <Box
            component="h3"
            sx={{
              fontSize: 'var(--ob-font-size-xs)',
              fontWeight: 600,
              color: 'var(--ob-color-text-tertiary)',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              m: '0',
              mb: 'var(--ob-space-100)',
            }}
          >
            Authority Submissions
          </Box>
          {loading ? (
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'center',
                p: 'var(--ob-space-400)',
              }}
            >
              <CircularProgress />
            </Box>
          ) : submissions.length === 0 ? (
            <GlassCard
              variant="default"
              sx={{ p: 'var(--ob-space-200)', textAlign: 'center' }}
            >
              <Box
                component="p"
                sx={{
                  color: 'var(--ob-color-text-secondary)',
                  fontSize: 'var(--ob-font-size-sm)',
                  m: '0',
                }}
              >
                No authority submissions yet. Change of Use and Heritage drafts
                appear below.
              </Box>
            </GlassCard>
          ) : (
            <GlassCard variant="default" sx={{ overflow: 'hidden' }}>
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
                        <TableCell
                          sx={{ fontFamily: 'var(--ob-font-family-mono)' }}
                        >
                          {row.submission_no || 'PENDING'}
                        </TableCell>
                        <TableCell sx={{ fontWeight: 500 }}>
                          {row.title}
                          {row.description && (
                            <Box
                              component="span"
                              sx={{
                                display: 'block',
                                fontSize: 'var(--ob-font-size-xs)',
                                color: 'var(--ob-color-text-secondary)',
                              }}
                            >
                              {row.description}
                            </Box>
                          )}
                        </TableCell>
                        <TableCell>{row.agency_id}</TableCell>
                        <TableCell>{row.submission_type}</TableCell>
                        <TableCell>
                          <StatusChip
                            status={getStatusChipStatus(row.status)}
                            size="sm"
                            icon={getStatusIcon(row.status)}
                          >
                            {row.status.replace('_', ' ')}
                          </StatusChip>
                        </TableCell>
                        <TableCell>
                          {new Date(
                            row.submitted_at || Date.now(),
                          ).toLocaleDateString()}
                        </TableCell>
                        <TableCell align="right">
                          <Button
                            variant="ghost"
                            size="sm"
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
            </GlassCard>
          )}
        </Box>

        {/* Change of Use Applications Section - Flat pattern */}
        <Box component="section" sx={{ mb: 'var(--ob-space-200)' }}>
          <Box
            component="h3"
            sx={{
              fontSize: 'var(--ob-font-size-xs)',
              fontWeight: 600,
              color: 'var(--ob-color-text-tertiary)',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              m: '0',
              mb: 'var(--ob-space-100)',
            }}
          >
            Change of Use Applications
          </Box>
          {changeOfUseApps.length === 0 ? (
            <GlassCard
              variant="default"
              sx={{ p: 'var(--ob-space-150)', textAlign: 'center' }}
            >
              <Box
                component="p"
                sx={{
                  fontSize: 'var(--ob-font-size-sm)',
                  color: 'var(--ob-color-text-secondary)',
                  m: '0',
                }}
              >
                No change of use applications yet.
              </Box>
            </GlassCard>
          ) : (
            <GlassCard variant="default" sx={{ overflow: 'hidden' }}>
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
                          <TableCell
                            sx={{ fontFamily: 'var(--ob-font-family-mono)' }}
                          >
                            {app.id.slice(0, 8)}...
                          </TableCell>
                          <TableCell sx={{ textTransform: 'capitalize' }}>
                            {app.current_use}
                          </TableCell>
                          <TableCell sx={{ textTransform: 'capitalize' }}>
                            {app.proposed_use}
                          </TableCell>
                          <TableCell>
                            <StatusChip
                              status={getStatusChipStatus(app.status)}
                              size="sm"
                            >
                              {app.status.replace('_', ' ')}
                            </StatusChip>
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
                              variant="ghost"
                              size="sm"
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
            </GlassCard>
          )}
        </Box>

        {/* Heritage Submissions Section - Flat pattern */}
        <Box component="section">
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--ob-space-075)',
              mb: 'var(--ob-space-100)',
            }}
          >
            <HeritageIcon
              sx={{ color: 'var(--ob-color-neon-cyan)', fontSize: 20 }}
            />
            <Box
              component="h3"
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                fontWeight: 600,
                color: 'var(--ob-color-text-tertiary)',
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
                m: '0',
              }}
            >
              Heritage Submissions (STB)
            </Box>
          </Box>
          {heritageSubmissions.length === 0 ? (
            <GlassCard
              variant="default"
              sx={{
                p: 'var(--ob-space-200)',
                textAlign: 'center',
                border: '1px dashed var(--ob-color-border-subtle)',
              }}
            >
              <Box
                component="p"
                sx={{
                  fontSize: 'var(--ob-font-size-sm)',
                  color: 'var(--ob-color-text-secondary)',
                  m: '0',
                  mb: 'var(--ob-space-100)',
                }}
              >
                No heritage submissions yet. Start a draft to capture the
                conservation details.
              </Box>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => openHeritageForm()}
              >
                Start heritage submission
              </Button>
            </GlassCard>
          ) : (
            <GlassCard variant="default" sx={{ overflow: 'hidden' }}>
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
                        <TableCell
                          sx={{ fontFamily: 'var(--ob-font-family-mono)' }}
                        >
                          {sub.stb_reference || sub.id.slice(0, 8) + '...'}
                        </TableCell>
                        <TableCell sx={{ textTransform: 'capitalize' }}>
                          {sub.conservation_status.replace(/_/g, ' ')}
                        </TableCell>
                        <TableCell>
                          {sub.original_construction_year || '-'}
                        </TableCell>
                        <TableCell>
                          <StatusChip
                            status={getStatusChipStatus(sub.status)}
                            size="sm"
                          >
                            {sub.status.replace('_', ' ')}
                          </StatusChip>
                        </TableCell>
                        <TableCell>
                          {new Date(sub.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell align="right">
                          <Button
                            variant="ghost"
                            size="sm"
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
            </GlassCard>
          )}
        </Box>
      </TabPanel>

      {/* Tab 1: Compliance Path - Content directly on background */}
      <TabPanel value={tabValue} index={1}>
        <CompliancePathTimeline
          projectId={projectId}
          projectName={currentProject?.name}
          preferredAssetType={preferredAssetType}
        />
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
