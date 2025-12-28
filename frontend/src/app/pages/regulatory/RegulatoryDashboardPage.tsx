import React, { useState, useEffect, useCallback } from 'react'
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
import { regulatoryApi, AuthoritySubmission } from '../../../api/regulatory'
import { SubmissionWizard } from './components/SubmissionWizard'
import { CompliancePathTimeline } from './components/CompliancePathTimeline'
import { ChangeOfUseWizard } from './components/ChangeOfUseWizard'
import { HeritageSubmissionForm } from './components/HeritageSubmissionForm'
import { useRouterPath } from '../../../router'
import { getTableSx, getPrimaryButtonSx } from '../../../utils/themeStyles'

const AGENCIES_INFO = [
  { code: 'URA', name: 'Urban Redevelopment Authority', status: 'Online' },
  { code: 'BCA', name: 'Building & Construction Authority', status: 'Online' },
  { code: 'SCDF', name: 'Singapore Civil Defence Force', status: 'Online' },
  { code: 'NEA', name: 'National Environment Agency', status: 'Online' },
]

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
  const path = useRouterPath()
  // Extract project ID from URL pattern /projects/:id/regulatory
  // If not found, use '1' as default or handle error
  const pathParts = path.split('/')
  const projectIdx = pathParts.indexOf('projects')
  const projectId = projectIdx !== -1 ? pathParts[projectIdx + 1] : '1'

  const [tabValue, setTabValue] = useState(0)
  const [submissions, setSubmissions] = useState<AuthoritySubmission[]>([])
  const [loading, setLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [wizardOpen, setWizardOpen] = useState(false)
  const [changeOfUseOpen, setChangeOfUseOpen] = useState(false)
  const [heritageFormOpen, setHeritageFormOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Theme-aware styles
  const tableSx = getTableSx(isDarkMode)

  const fetchSubmissions = useCallback(
    async (isRefresh = false) => {
      if (isRefresh) setRefreshing(true)
      else setLoading(true)
      setError(null)

      try {
        if (projectId === '1' && path.includes('/app/regulatory')) {
          // If accessing global dashboard without project context, we might want to handle differently
          // For now, defaulting to project 1
        }
        const data = await regulatoryApi.listSubmissions(projectId)
        setSubmissions(data)

        // Poll recent submissions for updates
        const pendingItems = data.filter((s) =>
          ['submitted', 'in_review'].includes(s.status),
        )
        if (pendingItems.length > 0 && isRefresh) {
          for (const item of pendingItems) {
            await regulatoryApi.getSubmissionStatus(item.id)
          }
          const updatedData = await regulatoryApi.listSubmissions(projectId)
          setSubmissions(updatedData)
        }
      } catch (err) {
        console.error(err)
        // setError('Failed to load submissions')
      } finally {
        if (isRefresh) setRefreshing(false)
        else setLoading(false)
      }
    },
    [projectId, path],
  )

  useEffect(() => {
    fetchSubmissions()
  }, [fetchSubmissions])

  const handleCreateSuccess = (newSubmission: AuthoritySubmission) => {
    setSubmissions([newSubmission, ...submissions])
    setWizardOpen(false)
  }

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'success'
      case 'rejected':
        return 'error'
      case 'rfi':
        return 'warning'
      case 'in_review':
        return 'info'
      default:
        return 'default'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <ApprovedIcon fontSize="small" />
      case 'rejected':
        return <RejectedIcon fontSize="small" />
      case 'rfi':
        return <RfiIcon fontSize="small" />
      case 'in_review':
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
              onClick={() => setChangeOfUseOpen(true)}
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
              onClick={() => setHeritageFormOpen(true)}
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
          <Box className="ob-card-module" sx={{ overflow: 'hidden' }}>
            <Typography
              variant="subtitle2"
              sx={{
                color: 'text.secondary',
                mb: 'var(--ob-space-200)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              Active Submissions
            </Typography>
            {submissions.length === 0 ? (
              <Box sx={{ p: 'var(--ob-space-400)', textAlign: 'center' }}>
                <Typography color="text.secondary">
                  No submissions found for this project.
                </Typography>
              </Box>
            ) : (
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
                        {row.agency_remarks && (
                          <Typography
                            variant="caption"
                            display="block"
                            color="warning.main"
                          >
                            {row.agency_remarks}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>{row.agency}</TableCell>
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
            )}
          </Box>
        )}
      </TabPanel>

      {/* Tab 1: Compliance Path - Depth 1 (Glass Card with cyan edge) */}
      <TabPanel value={tabValue} index={1}>
        <Box className="ob-card-module">
          <CompliancePathTimeline projectId={projectId} />
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
        onClose={() => setChangeOfUseOpen(false)}
        projectId={projectId}
        onSuccess={() => {
          setChangeOfUseOpen(false)
          fetchSubmissions(true)
        }}
      />

      <HeritageSubmissionForm
        open={heritageFormOpen}
        onClose={() => setHeritageFormOpen(false)}
        projectId={projectId}
        onSuccess={() => {
          setHeritageFormOpen(false)
          fetchSubmissions(true)
        }}
      />
    </Box>
  )
}
