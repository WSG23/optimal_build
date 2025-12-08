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
import { GlassCard } from '../../../components/canonical/GlassCard'
import { AnimatedPageHeader } from '../../../components/canonical/AnimatedPageHeader'
import {
  getSectionHeaderSx,
  getTableSx,
  getPrimaryButtonSx,
  getCardHoverSx,
  getBorderColor,
} from '../../../utils/themeStyles'

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
      sx={{ pt: 3 }}
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
  const sectionHeaderSx = getSectionHeaderSx(isDarkMode)
  const tableSx = getTableSx(isDarkMode)
  const cardHoverSx = getCardHoverSx(isDarkMode)
  const borderColor = getBorderColor(isDarkMode)

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
    <Box
      sx={{
        minHeight: '100vh',
        bgcolor: isDarkMode
          ? 'var(--ob-color-bg-root)'
          : 'var(--ob-color-bg-root)',
        p: 3,
      }}
    >
      <Box sx={{ maxWidth: 1400, margin: '0 auto' }}>
        <AnimatedPageHeader
          title="Regulatory Compliance"
          subtitle="Manage Singapore authority submissions (CORENET 2.0 Integration)"
          breadcrumbs={[
            { label: 'Dashboard', href: '/' },
            { label: 'Regulatory Compliance' },
          ]}
          action={
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={() => fetchSubmissions(true)}
                disabled={refreshing || loading}
              >
                {refreshing ? 'Updating...' : 'Check Status'}
              </Button>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setWizardOpen(true)}
                sx={getPrimaryButtonSx()}
              >
                New Submission
              </Button>
            </Box>
          }
        />

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* Quick Actions */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={4}>
            <GlassCard
              onClick={() => setChangeOfUseOpen(true)}
              hoverEffect
              sx={{ p: 2, cursor: 'pointer' }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
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
            </GlassCard>
          </Grid>
          <Grid item xs={12} sm={4}>
            <GlassCard
              onClick={() => setHeritageFormOpen(true)}
              hoverEffect
              sx={{ p: 2, cursor: 'pointer' }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
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
            </GlassCard>
          </Grid>
          <Grid item xs={12} sm={4}>
            <GlassCard
              onClick={() => setTabValue(1)}
              hoverEffect
              sx={{ p: 2, cursor: 'pointer' }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
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
            </GlassCard>
          </Grid>
        </Grid>

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
          {/* Agency Status Cards */}
          <Typography
            variant="h6"
            gutterBottom
            sx={{ mb: 2, ...sectionHeaderSx }}
          >
            Connected Agencies
          </Typography>
          <Grid container spacing={2} sx={{ mb: 4 }}>
            {AGENCIES_INFO.map((agency) => (
              <Grid item xs={12} sm={6} md={3} key={agency.code}>
                <GlassCard
                  sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2 }}
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
                </GlassCard>
              </Grid>
            ))}
          </Grid>

          {/* Submissions Table */}
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 8 }}>
              <CircularProgress />
            </Box>
          ) : (
            <GlassCard sx={{ overflow: 'hidden' }}>
              <Box sx={{ p: 2, borderBottom: `1px solid ${borderColor}` }}>
                <Typography variant="h6" sx={sectionHeaderSx}>
                  Active Submissions
                </Typography>
              </Box>
              {submissions.length === 0 ? (
                <Box sx={{ p: 4, textAlign: 'center' }}>
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
            </GlassCard>
          )}
        </TabPanel>

        {/* Tab 1: Compliance Path */}
        <TabPanel value={tabValue} index={1}>
          <CompliancePathTimeline projectId={projectId} />
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
    </Box>
  )
}
