import React, { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Grid,
  Card,
  Typography,
  Chip,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tabs,
  Tab,
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
  SwapHoriz as ChangeIcon,
  AccountBalance as HeritageIcon,
} from '@mui/icons-material'
import {
  regulatoryApi,
  AuthoritySubmission,
  ChangeOfUseApplication,
  HeritageSubmission,
} from '../../../api/regulatory'
import { SubmissionWizard } from './components/SubmissionWizard'
import { CompliancePathVisualization } from './components/CompliancePathVisualization'
import { ChangeOfUseWizard } from './components/ChangeOfUseWizard'
import { HeritageSubmissionForm } from './components/HeritageSubmissionForm'
import { useRouterPath } from '../../../router'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`regulatory-tabpanel-${index}`}
      aria-labelledby={`regulatory-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  )
}

const AGENCIES_INFO = [
  { code: 'URA', name: 'Urban Redevelopment Authority', status: 'Online' },
  { code: 'BCA', name: 'Building & Construction Authority', status: 'Online' },
  { code: 'SCDF', name: 'Singapore Civil Defence Force', status: 'Online' },
  { code: 'NEA', name: 'National Environment Agency', status: 'Online' },
]

export const RegulatoryDashboardPage: React.FC = () => {
  const path = useRouterPath()
  const pathParts = path.split('/')
  const projectIdx = pathParts.indexOf('projects')
  const projectId = projectIdx !== -1 ? pathParts[projectIdx + 1] : '1'

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
  const [heritageFormOpen, setHeritageFormOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchSubmissions = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    else setLoading(true)
    setError(null)

    try {
      const data = await regulatoryApi.listSubmissions(projectId)
      setSubmissions(data)

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
    } finally {
      if (isRefresh) setRefreshing(false)
      else setLoading(false)
    }
  }

  const fetchChangeOfUseApps = async () => {
    try {
      const data = await regulatoryApi.listChangeOfUseApplications(projectId)
      setChangeOfUseApps(data)
    } catch (err) {
      console.error(err)
    }
  }

  const fetchHeritageSubmissions = async () => {
    try {
      const data = await regulatoryApi.listHeritageSubmissions(projectId)
      setHeritageSubmissions(data)
    } catch (err) {
      console.error(err)
    }
  }

  useEffect(() => {
    fetchSubmissions()
    fetchChangeOfUseApps()
    fetchHeritageSubmissions()
  }, [projectId])

  const handleCreateSuccess = (newSubmission: AuthoritySubmission) => {
    setSubmissions([newSubmission, ...submissions])
    setWizardOpen(false)
  }

  const handleChangeOfUseSuccess = (app: ChangeOfUseApplication) => {
    setChangeOfUseApps([app, ...changeOfUseApps])
    setChangeOfUseOpen(false)
  }

  const handleHeritageSuccess = (submission: HeritageSubmission) => {
    setHeritageSubmissions([submission, ...heritageSubmissions])
    setHeritageFormOpen(false)
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
    <Box sx={{ p: 4, maxWidth: 1400, margin: '0 auto' }}>
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          mb: 4,
          alignItems: 'center',
        }}
      >
        <Box>
          <Typography
            variant="h4"
            gutterBottom
            sx={{
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: 2,
            }}
          >
            Regulatory Navigation{' '}
            <Chip label="SGP" size="small" color="primary" variant="outlined" />
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage Singapore authority submissions (CORENET 2.0 Integration)
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => {
              fetchSubmissions(true)
              fetchChangeOfUseApps()
              fetchHeritageSubmissions()
            }}
            disabled={refreshing || loading}
          >
            {refreshing ? 'Updating...' : 'Refresh All'}
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Agency Status Cards */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
          Connected Agencies
        </Typography>
        <Grid container spacing={2}>
          {AGENCIES_INFO.map((agency) => (
            <Grid item xs={12} sm={6} md={3} key={agency.code}>
              <Card
                sx={{
                  p: 2,
                  border: '1px solid rgba(255,255,255,0.1)',
                  bgcolor: 'rgba(255,255,255,0.03)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
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
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          aria-label="regulatory navigation tabs"
        >
          <Tab
            icon={<TimelineIcon />}
            iconPosition="start"
            label="Compliance Paths"
          />
          <Tab
            icon={<AgencyIcon />}
            iconPosition="start"
            label={`Submissions (${submissions.length})`}
          />
          <Tab
            icon={<ChangeIcon />}
            iconPosition="start"
            label={`Change of Use (${changeOfUseApps.length})`}
          />
          <Tab
            icon={<HeritageIcon />}
            iconPosition="start"
            label={`Heritage (${heritageSubmissions.length})`}
          />
        </Tabs>
      </Box>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        <CompliancePathVisualization projectId={projectId} />
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setWizardOpen(true)}
            sx={{
              background: 'linear-gradient(135deg, #00C9FF 0%, #92FE9D 100%)',
              boxShadow: '0px 4px 12px rgba(0, 201, 255, 0.3)',
              color: 'var(--ob-color-text-primary)',
              fontWeight: 'bold',
            }}
          >
            New Submission
          </Button>
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 8 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Card
            sx={{
              border: '1px solid rgba(255,255,255,0.1)',
              bgcolor: 'background.paper',
              borderRadius: 'var(--ob-radius-sm)',
              overflow: 'hidden',
            }}
          >
            <Box sx={{ p: 2, borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
              <Typography variant="h6">Active Submissions</Typography>
            </Box>
            {submissions.length === 0 ? (
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <Typography color="text.secondary">
                  No submissions found for this project.
                </Typography>
              </Box>
            ) : (
              <Table>
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
          </Card>
        )}
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button
            variant="contained"
            startIcon={<ChangeIcon />}
            onClick={() => setChangeOfUseOpen(true)}
            sx={{
              background: 'linear-gradient(135deg, #ea580c 0%, #fb923c 100%)',
              boxShadow: '0px 4px 12px rgba(234, 88, 12, 0.3)',
              color: 'var(--ob-color-text-inverse)',
              fontWeight: 'bold',
            }}
          >
            New Change of Use
          </Button>
        </Box>

        <Card
          sx={{
            border: '1px solid rgba(255,255,255,0.1)',
            bgcolor: 'background.paper',
            borderRadius: 'var(--ob-radius-sm)',
            overflow: 'hidden',
          }}
        >
          <Box sx={{ p: 2, borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
            <Typography variant="h6">Change of Use Applications</Typography>
          </Box>
          {changeOfUseApps.length === 0 ? (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <Typography color="text.secondary">
                No change of use applications for this project.
              </Typography>
            </Box>
          ) : (
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>URA Reference</TableCell>
                  <TableCell>Current Use</TableCell>
                  <TableCell>Proposed Use</TableCell>
                  <TableCell>DC Amendment</TableCell>
                  <TableCell>Planning Permission</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Created</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {changeOfUseApps.map((app) => (
                  <TableRow key={app.id} hover>
                    <TableCell sx={{ fontFamily: 'monospace' }}>
                      {app.ura_reference || 'PENDING'}
                    </TableCell>
                    <TableCell sx={{ textTransform: 'capitalize' }}>
                      {app.current_use.replace('_', ' ')}
                    </TableCell>
                    <TableCell sx={{ textTransform: 'capitalize' }}>
                      {app.proposed_use.replace('_', ' ')}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={app.requires_dc_amendment ? 'Required' : 'No'}
                        size="small"
                        color={
                          app.requires_dc_amendment ? 'warning' : 'default'
                        }
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={
                          app.requires_planning_permission ? 'Required' : 'No'
                        }
                        size="small"
                        color={
                          app.requires_planning_permission
                            ? 'warning'
                            : 'default'
                        }
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={app.status.replace('_', ' ')}
                        size="small"
                        color={
                          getStatusColor(app.status) as
                            | 'default'
                            | 'primary'
                            | 'secondary'
                            | 'error'
                            | 'info'
                            | 'success'
                            | 'warning'
                        }
                        icon={getStatusIcon(app.status)}
                        variant="outlined"
                        sx={{ textTransform: 'capitalize' }}
                      />
                    </TableCell>
                    <TableCell>
                      {new Date(app.created_at).toLocaleDateString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Card>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button
            variant="contained"
            startIcon={<HeritageIcon />}
            onClick={() => setHeritageFormOpen(true)}
            sx={{
              background: 'linear-gradient(135deg, #be185d 0%, #f472b6 100%)',
              boxShadow: '0px 4px 12px rgba(190, 24, 93, 0.3)',
              color: 'var(--ob-color-text-inverse)',
              fontWeight: 'bold',
            }}
          >
            New Heritage Submission
          </Button>
        </Box>

        <Card
          sx={{
            border: '1px solid rgba(255,255,255,0.1)',
            bgcolor: 'background.paper',
            borderRadius: 'var(--ob-radius-sm)',
            overflow: 'hidden',
          }}
        >
          <Box sx={{ p: 2, borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
            <Typography variant="h6">Heritage Submissions (STB)</Typography>
          </Box>
          {heritageSubmissions.length === 0 ? (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <Typography color="text.secondary">
                No heritage submissions for this project.
              </Typography>
            </Box>
          ) : (
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>STB Reference</TableCell>
                  <TableCell>Conservation Status</TableCell>
                  <TableCell>Year Built</TableCell>
                  <TableCell>Conservation Plan</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Submitted</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {heritageSubmissions.map((submission) => (
                  <TableRow key={submission.id} hover>
                    <TableCell sx={{ fontFamily: 'monospace' }}>
                      {submission.stb_reference || 'DRAFT'}
                    </TableCell>
                    <TableCell sx={{ textTransform: 'capitalize' }}>
                      {submission.conservation_status.replace(/_/g, ' ')}
                    </TableCell>
                    <TableCell>
                      {submission.original_construction_year || '-'}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={
                          submission.conservation_plan_attached
                            ? 'Attached'
                            : 'Missing'
                        }
                        size="small"
                        color={
                          submission.conservation_plan_attached
                            ? 'success'
                            : 'warning'
                        }
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={submission.status.replace('_', ' ')}
                        size="small"
                        color={
                          getStatusColor(submission.status) as
                            | 'default'
                            | 'primary'
                            | 'secondary'
                            | 'error'
                            | 'info'
                            | 'success'
                            | 'warning'
                        }
                        icon={getStatusIcon(submission.status)}
                        variant="outlined"
                        sx={{ textTransform: 'capitalize' }}
                      />
                    </TableCell>
                    <TableCell>
                      {submission.submitted_at
                        ? new Date(submission.submitted_at).toLocaleDateString()
                        : '-'}
                    </TableCell>
                    <TableCell align="right">
                      {submission.status === 'draft' && (
                        <Button
                          size="small"
                          variant="contained"
                          color="primary"
                          onClick={() =>
                            regulatoryApi
                              .submitHeritageToSTB(submission.id)
                              .then(() => fetchHeritageSubmissions())
                          }
                        >
                          Submit to STB
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Card>
      </TabPanel>

      {/* Wizards and Forms */}
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
        onSuccess={handleChangeOfUseSuccess}
      />

      <HeritageSubmissionForm
        open={heritageFormOpen}
        onClose={() => setHeritageFormOpen(false)}
        projectId={projectId}
        onSuccess={handleHeritageSuccess}
      />
    </Box>
  )
}
