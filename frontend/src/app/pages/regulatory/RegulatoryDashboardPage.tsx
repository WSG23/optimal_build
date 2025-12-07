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
} from '@mui/material'
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  CheckCircle as ApprovedIcon,
  HourglassEmpty as PendingIcon,
  Error as RejectedIcon,
  QuestionAnswer as RfiIcon,
  Business as AgencyIcon,
} from '@mui/icons-material'
import { regulatoryApi, AuthoritySubmission } from '../../../api/regulatory'
import { SubmissionWizard } from './components/SubmissionWizard'
import { useRouterPath } from '../../../router'

const AGENCIES_INFO = [
  { code: 'URA', name: 'Urban Redevelopment Authority', status: 'Online' },
  { code: 'BCA', name: 'Building & Construction Authority', status: 'Online' },
  { code: 'SCDF', name: 'Singapore Civil Defence Force', status: 'Online' },
  { code: 'NEA', name: 'National Environment Agency', status: 'Online' },
]

export const RegulatoryDashboardPage: React.FC = () => {
  const path = useRouterPath()
  // Extract project ID from URL pattern /projects/:id/regulatory
  // If not found, use '1' as default or handle error
  const pathParts = path.split('/')
  const projectIdx = pathParts.indexOf('projects')
  const projectId = projectIdx !== -1 ? pathParts[projectIdx + 1] : '1'

  const [submissions, setSubmissions] = useState<AuthoritySubmission[]>([])
  const [loading, setLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [wizardOpen, setWizardOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchSubmissions = async (isRefresh = false) => {
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
  }

  useEffect(() => {
    fetchSubmissions()
  }, [projectId])

  const handleCreateSuccess = (newSubmission: AuthoritySubmission) => {
    setSubmissions([newSubmission, ...submissions])
    setWizardOpen(false)
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
    <Box sx={{ p: 4, maxWidth: 1200, margin: '0 auto' }}>
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
            onClick={() => fetchSubmissions(true)}
            disabled={refreshing || loading}
          >
            {refreshing ? 'Updating...' : 'Check Status'}
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setWizardOpen(true)}
            sx={{
              background: 'linear-gradient(135deg, #00C9FF 0%, #92FE9D 100%)',
              boxShadow: '0px 4px 12px rgba(0, 201, 255, 0.3)',
              color: '#000',
              fontWeight: 'bold',
            }}
          >
            New Submission
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={4}>
        {/* Agency Status Cards */}
        <Grid item xs={12}>
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
        </Grid>

        <Grid item xs={12}>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 8 }}>
              <CircularProgress />
            </Box>
          ) : (
            <Card
              sx={{
                border: '1px solid rgba(255,255,255,0.1)',
                bgcolor: 'background.paper',
                borderRadius: 2,
                overflow: 'hidden',
              }}
            >
              <Box
                sx={{ p: 2, borderBottom: '1px solid rgba(255,255,255,0.1)' }}
              >
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
        </Grid>
      </Grid>

      <SubmissionWizard
        open={wizardOpen}
        onClose={() => setWizardOpen(false)}
        projectId={projectId}
        onSuccess={handleCreateSuccess}
      />
    </Box>
  )
}
