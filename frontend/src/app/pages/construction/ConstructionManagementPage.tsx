import React, { useState, useEffect, useCallback } from 'react'
import {
  Box,
  Button,
  Card,
  Grid,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  LinearProgress,
  IconButton,
  Tooltip,
} from '@mui/material'
import {
  Add as AddIcon,
  Engineering as ContractorIcon,
  CheckCircle as InspectionIcon,
  Warning as SafetyIcon,
  AccountBalance as DrawdownIcon,
  Check as ApproveIcon,
  Edit as EditIcon,
} from '@mui/icons-material'
import {
  constructionApi,
  Contractor,
  QualityInspection,
  SafetyIncident,
  DrawdownRequest,
  ContractorType,
  InspectionStatus,
  SeverityLevel,
  contractorTypeLabels,
  inspectionStatusLabels,
  severityLabels,
  drawdownStatusLabels,
  inspectionStatusColors,
  severityColors,
  drawdownStatusColors,
} from '../../../api/construction'
import { useRouterPath } from '../../../router'

interface ConstructionManagementPageProps {
  projectId?: string
}

// Tab Panel Component
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
      id={`construction-tabpanel-${index}`}
      aria-labelledby={`construction-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ pt: 'var(--ob-space-200)' }}>{children}</Box>
      )}
    </div>
  )
}

export const ConstructionManagementPage: React.FC<
  ConstructionManagementPageProps
> = ({ projectId: propProjectId }) => {
  const path = useRouterPath()
  const derivedProjectId = path.split('/projects/')[1]?.split('/')[0]
  const projectId = propProjectId || derivedProjectId || 'demo-project-id'

  const [activeTab, setActiveTab] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Data states
  const [contractors, setContractors] = useState<Contractor[]>([])
  const [inspections, setInspections] = useState<QualityInspection[]>([])
  const [incidents, setIncidents] = useState<SafetyIncident[]>([])
  const [drawdowns, setDrawdowns] = useState<DrawdownRequest[]>([])

  // Dialog states
  const [contractorDialogOpen, setContractorDialogOpen] = useState(false)
  const [inspectionDialogOpen, setInspectionDialogOpen] = useState(false)
  const [incidentDialogOpen, setIncidentDialogOpen] = useState(false)
  const [drawdownDialogOpen, setDrawdownDialogOpen] = useState(false)

  // Form states
  const [newContractor, setNewContractor] = useState({
    company_name: '',
    contractor_type: 'general_contractor' as ContractorType,
    contact_person: '',
    email: '',
    phone: '',
  })

  const [newInspection, setNewInspection] = useState({
    inspection_date: new Date().toISOString().split('T')[0],
    inspector_name: '',
    location: '',
    status: 'scheduled' as InspectionStatus,
    notes: '',
  })

  const [newIncident, setNewIncident] = useState({
    incident_date: new Date().toISOString(),
    severity: 'minor' as SeverityLevel,
    title: '',
    description: '',
    location: '',
    reported_by: '',
  })

  const [newDrawdown, setNewDrawdown] = useState({
    request_name: '',
    request_date: new Date().toISOString().split('T')[0],
    amount_requested: 0,
    notes: '',
  })

  // Fetch functions
  const fetchContractors = useCallback(async () => {
    try {
      const data = await constructionApi.listContractors(projectId)
      setContractors(data)
    } catch (err) {
      console.warn('Backend failed, using mock contractors')
      setContractors([
        {
          id: '1',
          project_id: projectId,
          company_name: 'ABC Construction Pte Ltd',
          contractor_type: 'general_contractor',
          contact_person: 'John Tan',
          email: 'john@abc-construction.sg',
          phone: '+65 9123 4567',
          contract_value: 15000000,
          contract_date: '2024-01-15',
          is_active: true,
          metadata: {},
          created_at: new Date().toISOString(),
          updated_at: null,
        },
        {
          id: '2',
          project_id: projectId,
          company_name: 'MEP Systems Pte Ltd',
          contractor_type: 'specialist',
          contact_person: 'Sarah Lee',
          email: 'sarah@mepsystems.sg',
          phone: '+65 9234 5678',
          contract_value: 3500000,
          contract_date: '2024-02-01',
          is_active: true,
          metadata: {},
          created_at: new Date().toISOString(),
          updated_at: null,
        },
      ])
    }
  }, [projectId])

  const fetchInspections = useCallback(async () => {
    try {
      const data = await constructionApi.listInspections(projectId)
      setInspections(data)
    } catch (err) {
      console.warn('Backend failed, using mock inspections')
      setInspections([
        {
          id: '1',
          project_id: projectId,
          development_phase_id: null,
          inspection_date: '2024-12-20',
          inspector_name: 'Michael Chen',
          location: 'Level 5 Structural Slab',
          status: 'passed',
          defects_found: {},
          photos_url: [],
          notes: 'All concrete works satisfactory',
          created_at: new Date().toISOString(),
        },
        {
          id: '2',
          project_id: projectId,
          development_phase_id: null,
          inspection_date: '2024-12-22',
          inspector_name: 'David Wong',
          location: 'Basement Waterproofing',
          status: 'rectification_required',
          defects_found: { items: ['Minor crack at joint B3'] },
          photos_url: [],
          notes: 'Remedial works required before next pour',
          created_at: new Date().toISOString(),
        },
      ])
    }
  }, [projectId])

  const fetchIncidents = useCallback(async () => {
    try {
      const data = await constructionApi.listIncidents(projectId)
      setIncidents(data)
    } catch (err) {
      console.warn('Backend failed, using mock incidents')
      setIncidents([
        {
          id: '1',
          project_id: projectId,
          incident_date: '2024-12-18T10:30:00Z',
          severity: 'near_miss',
          title: 'Unsecured scaffolding',
          description: 'Worker noticed loose scaffolding bracket on level 3',
          location: 'Level 3 East Wing',
          reported_by: 'Ahmad bin Hassan',
          is_resolved: true,
          resolution_notes: 'Scaffolding secured and inspected',
          created_at: new Date().toISOString(),
        },
      ])
    }
  }, [projectId])

  const fetchDrawdowns = useCallback(async () => {
    try {
      const data = await constructionApi.listDrawdowns(projectId)
      setDrawdowns(data)
    } catch (err) {
      console.warn('Backend failed, using mock drawdowns')
      setDrawdowns([
        {
          id: '1',
          project_id: projectId,
          request_name: 'Drawdown #1 - Foundation Works',
          request_date: '2024-11-01',
          amount_requested: 2500000,
          amount_approved: 2500000,
          status: 'paid',
          contractor_id: '1',
          supporting_docs: [],
          notes: 'Foundation complete as per QS certification',
          created_at: new Date().toISOString(),
          updated_at: null,
        },
        {
          id: '2',
          project_id: projectId,
          request_name: 'Drawdown #2 - Structural Frame L1-5',
          request_date: '2024-12-15',
          amount_requested: 3200000,
          amount_approved: null,
          status: 'approved_architect',
          contractor_id: '1',
          supporting_docs: [],
          notes: 'Awaiting lender approval',
          created_at: new Date().toISOString(),
          updated_at: null,
        },
      ])
    }
  }, [projectId])

  // Load all data on mount
  useEffect(() => {
    setLoading(true)
    setError(null)
    Promise.all([
      fetchContractors(),
      fetchInspections(),
      fetchIncidents(),
      fetchDrawdowns(),
    ])
      .catch(() => setError('Failed to load construction data'))
      .finally(() => setLoading(false))
  }, [fetchContractors, fetchInspections, fetchIncidents, fetchDrawdowns])

  // Submit handlers
  const handleAddContractor = async () => {
    try {
      await constructionApi.createContractor({
        project_id: projectId,
        ...newContractor,
      })
      await fetchContractors()
      setContractorDialogOpen(false)
      setNewContractor({
        company_name: '',
        contractor_type: 'general_contractor',
        contact_person: '',
        email: '',
        phone: '',
      })
    } catch (err) {
      console.error('Failed to add contractor:', err)
    }
  }

  const handleAddInspection = async () => {
    try {
      await constructionApi.createInspection({
        project_id: projectId,
        ...newInspection,
      })
      await fetchInspections()
      setInspectionDialogOpen(false)
      setNewInspection({
        inspection_date: new Date().toISOString().split('T')[0],
        inspector_name: '',
        location: '',
        status: 'scheduled',
        notes: '',
      })
    } catch (err) {
      console.error('Failed to add inspection:', err)
    }
  }

  const handleAddIncident = async () => {
    try {
      await constructionApi.createIncident({
        project_id: projectId,
        ...newIncident,
      })
      await fetchIncidents()
      setIncidentDialogOpen(false)
      setNewIncident({
        incident_date: new Date().toISOString(),
        severity: 'minor',
        title: '',
        description: '',
        location: '',
        reported_by: '',
      })
    } catch (err) {
      console.error('Failed to add incident:', err)
    }
  }

  const handleAddDrawdown = async () => {
    try {
      await constructionApi.createDrawdown({
        project_id: projectId,
        ...newDrawdown,
      })
      await fetchDrawdowns()
      setDrawdownDialogOpen(false)
      setNewDrawdown({
        request_name: '',
        request_date: new Date().toISOString().split('T')[0],
        amount_requested: 0,
        notes: '',
      })
    } catch (err) {
      console.error('Failed to add drawdown:', err)
    }
  }

  const handleApproveDrawdown = async (drawdownId: string) => {
    try {
      await constructionApi.approveDrawdown(drawdownId)
      await fetchDrawdowns()
    } catch (err) {
      console.error('Failed to approve drawdown:', err)
    }
  }

  // Calculate stats
  const totalContractValue = contractors.reduce(
    (sum, c) => sum + (c.contract_value || 0),
    0,
  )
  const totalDrawnDown = drawdowns
    .filter((d) => d.status === 'paid')
    .reduce((sum, d) => sum + (d.amount_approved || 0), 0)
  const unresolvedIncidents = incidents.filter((i) => !i.is_resolved).length

  const formatCurrency = (amount: number) =>
    new Intl.NumberFormat('en-SG', {
      style: 'currency',
      currency: 'SGD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)

  if (loading) {
    return (
      <Box sx={{ p: 'var(--ob-space-200)' }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box sx={{ p: 'var(--ob-space-200)' }}>
      {error && (
        <Alert severity="error" sx={{ mb: 'var(--ob-space-200)' }}>
          {error}
        </Alert>
      )}

      {/* Summary Cards */}
      <Grid
        container
        spacing="var(--ob-space-200)"
        sx={{ mb: 'var(--ob-space-200)' }}
      >
        <Grid item xs={12} md={3}>
          <Card
            sx={{
              p: 'var(--ob-space-200)',
              borderRadius: 'var(--ob-radius-sm)',
            }}
          >
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-100)',
              }}
            >
              <ContractorIcon color="primary" />
              <Typography variant="h6">{contractors.length}</Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              Active Contractors
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Total Value: {formatCurrency(totalContractValue)}
            </Typography>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card
            sx={{
              p: 'var(--ob-space-200)',
              borderRadius: 'var(--ob-radius-sm)',
            }}
          >
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-100)',
              }}
            >
              <InspectionIcon color="success" />
              <Typography variant="h6">{inspections.length}</Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              Quality Inspections
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {inspections.filter((i) => i.status === 'passed').length} Passed
            </Typography>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card
            sx={{
              p: 'var(--ob-space-200)',
              borderRadius: 'var(--ob-radius-sm)',
            }}
          >
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-100)',
              }}
            >
              <SafetyIcon
                color={unresolvedIncidents > 0 ? 'warning' : 'success'}
              />
              <Typography variant="h6">{unresolvedIncidents}</Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              Open Safety Issues
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {incidents.length} Total Reported
            </Typography>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card
            sx={{
              p: 'var(--ob-space-200)',
              borderRadius: 'var(--ob-radius-sm)',
            }}
          >
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-100)',
              }}
            >
              <DrawdownIcon color="info" />
              <Typography variant="h6">
                {formatCurrency(totalDrawnDown)}
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              Total Drawn Down
            </Typography>
            {totalContractValue > 0 && (
              <LinearProgress
                variant="determinate"
                value={(totalDrawnDown / totalContractValue) * 100}
                sx={{
                  mt: 'var(--ob-space-050)',
                  borderRadius: 'var(--ob-radius-xs)',
                }}
              />
            )}
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Card sx={{ borderRadius: 'var(--ob-radius-sm)' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={activeTab}
            onChange={(_, v) => setActiveTab(v)}
            aria-label="construction management tabs"
          >
            <Tab
              icon={<ContractorIcon />}
              label="Contractors"
              iconPosition="start"
            />
            <Tab
              icon={<InspectionIcon />}
              label="Inspections"
              iconPosition="start"
            />
            <Tab icon={<SafetyIcon />} label="Safety" iconPosition="start" />
            <Tab
              icon={<DrawdownIcon />}
              label="Drawdowns"
              iconPosition="start"
            />
          </Tabs>
        </Box>

        {/* Contractors Tab */}
        <TabPanel value={activeTab} index={0}>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'flex-end',
              mb: 'var(--ob-space-200)',
              px: 'var(--ob-space-200)',
            }}
          >
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setContractorDialogOpen(true)}
              sx={{ borderRadius: 'var(--ob-radius-xs)' }}
            >
              Add Contractor
            </Button>
          </Box>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Company</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Contact</TableCell>
                <TableCell>Contract Value</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {contractors.map((contractor) => (
                <TableRow key={contractor.id}>
                  <TableCell>
                    <Typography fontWeight={500}>
                      {contractor.company_name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {contractor.email}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {contractorTypeLabels[contractor.contractor_type]}
                  </TableCell>
                  <TableCell>
                    {contractor.contact_person}
                    <br />
                    <Typography variant="caption" color="text.secondary">
                      {contractor.phone}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {contractor.contract_value
                      ? formatCurrency(contractor.contract_value)
                      : '-'}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={contractor.is_active ? 'Active' : 'Inactive'}
                      color={contractor.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                </TableRow>
              ))}
              {contractors.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    No contractors registered
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TabPanel>

        {/* Inspections Tab */}
        <TabPanel value={activeTab} index={1}>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'flex-end',
              mb: 'var(--ob-space-200)',
              px: 'var(--ob-space-200)',
            }}
          >
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setInspectionDialogOpen(true)}
              sx={{ borderRadius: 'var(--ob-radius-xs)' }}
            >
              Log Inspection
            </Button>
          </Box>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>Location</TableCell>
                <TableCell>Inspector</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Notes</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {inspections.map((inspection) => (
                <TableRow key={inspection.id}>
                  <TableCell>{inspection.inspection_date}</TableCell>
                  <TableCell>{inspection.location || '-'}</TableCell>
                  <TableCell>{inspection.inspector_name}</TableCell>
                  <TableCell>
                    <Chip
                      label={inspectionStatusLabels[inspection.status]}
                      color={inspectionStatusColors[inspection.status]}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                      {inspection.notes || '-'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
              {inspections.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    No inspections logged
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TabPanel>

        {/* Safety Tab */}
        <TabPanel value={activeTab} index={2}>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'flex-end',
              mb: 'var(--ob-space-200)',
              px: 'var(--ob-space-200)',
            }}
          >
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setIncidentDialogOpen(true)}
              sx={{ borderRadius: 'var(--ob-radius-xs)' }}
            >
              Report Incident
            </Button>
          </Box>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>Title</TableCell>
                <TableCell>Severity</TableCell>
                <TableCell>Location</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {incidents.map((incident) => (
                <TableRow key={incident.id}>
                  <TableCell>
                    {new Date(incident.incident_date).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <Typography fontWeight={500}>{incident.title}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {incident.description}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={severityLabels[incident.severity]}
                      color={severityColors[incident.severity]}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{incident.location || '-'}</TableCell>
                  <TableCell>
                    <Chip
                      label={incident.is_resolved ? 'Resolved' : 'Open'}
                      color={incident.is_resolved ? 'success' : 'warning'}
                      size="small"
                    />
                  </TableCell>
                </TableRow>
              ))}
              {incidents.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    No safety incidents reported
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TabPanel>

        {/* Drawdowns Tab */}
        <TabPanel value={activeTab} index={3}>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'flex-end',
              mb: 'var(--ob-space-200)',
              px: 'var(--ob-space-200)',
            }}
          >
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setDrawdownDialogOpen(true)}
              sx={{ borderRadius: 'var(--ob-radius-xs)' }}
            >
              New Drawdown Request
            </Button>
          </Box>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Request</TableCell>
                <TableCell>Date</TableCell>
                <TableCell align="right">Requested</TableCell>
                <TableCell align="right">Approved</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {drawdowns.map((drawdown) => (
                <TableRow key={drawdown.id}>
                  <TableCell>
                    <Typography fontWeight={500}>
                      {drawdown.request_name}
                    </Typography>
                  </TableCell>
                  <TableCell>{drawdown.request_date}</TableCell>
                  <TableCell align="right">
                    {formatCurrency(drawdown.amount_requested)}
                  </TableCell>
                  <TableCell align="right">
                    {drawdown.amount_approved
                      ? formatCurrency(drawdown.amount_approved)
                      : '-'}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={drawdownStatusLabels[drawdown.status]}
                      color={drawdownStatusColors[drawdown.status]}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {drawdown.status === 'submitted' && (
                      <Tooltip title="Approve (Architect)">
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => handleApproveDrawdown(drawdown.id)}
                        >
                          <ApproveIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                    <Tooltip title="Edit">
                      <IconButton size="small">
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
              {drawdowns.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    No drawdown requests
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TabPanel>
      </Card>

      {/* Add Contractor Dialog */}
      <Dialog
        open={contractorDialogOpen}
        onClose={() => setContractorDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Add Contractor</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Company Name"
            fullWidth
            value={newContractor.company_name}
            onChange={(e) =>
              setNewContractor({
                ...newContractor,
                company_name: e.target.value,
              })
            }
          />
          <TextField
            select
            margin="dense"
            label="Contractor Type"
            fullWidth
            value={newContractor.contractor_type}
            onChange={(e) =>
              setNewContractor({
                ...newContractor,
                contractor_type: e.target.value as ContractorType,
              })
            }
          >
            {Object.entries(contractorTypeLabels).map(([value, label]) => (
              <MenuItem key={value} value={value}>
                {label}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            margin="dense"
            label="Contact Person"
            fullWidth
            value={newContractor.contact_person}
            onChange={(e) =>
              setNewContractor({
                ...newContractor,
                contact_person: e.target.value,
              })
            }
          />
          <TextField
            margin="dense"
            label="Email"
            type="email"
            fullWidth
            value={newContractor.email}
            onChange={(e) =>
              setNewContractor({ ...newContractor, email: e.target.value })
            }
          />
          <TextField
            margin="dense"
            label="Phone"
            fullWidth
            value={newContractor.phone}
            onChange={(e) =>
              setNewContractor({ ...newContractor, phone: e.target.value })
            }
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setContractorDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleAddContractor} variant="contained">
            Add
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Inspection Dialog */}
      <Dialog
        open={inspectionDialogOpen}
        onClose={() => setInspectionDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Log Quality Inspection</DialogTitle>
        <DialogContent>
          <TextField
            margin="dense"
            label="Inspection Date"
            type="date"
            fullWidth
            InputLabelProps={{ shrink: true }}
            value={newInspection.inspection_date}
            onChange={(e) =>
              setNewInspection({
                ...newInspection,
                inspection_date: e.target.value,
              })
            }
          />
          <TextField
            margin="dense"
            label="Inspector Name"
            fullWidth
            value={newInspection.inspector_name}
            onChange={(e) =>
              setNewInspection({
                ...newInspection,
                inspector_name: e.target.value,
              })
            }
          />
          <TextField
            margin="dense"
            label="Location"
            fullWidth
            placeholder="e.g., Level 5 Structural Slab"
            value={newInspection.location}
            onChange={(e) =>
              setNewInspection({ ...newInspection, location: e.target.value })
            }
          />
          <TextField
            select
            margin="dense"
            label="Status"
            fullWidth
            value={newInspection.status}
            onChange={(e) =>
              setNewInspection({
                ...newInspection,
                status: e.target.value as InspectionStatus,
              })
            }
          >
            {Object.entries(inspectionStatusLabels).map(([value, label]) => (
              <MenuItem key={value} value={value}>
                {label}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            margin="dense"
            label="Notes"
            fullWidth
            multiline
            rows={3}
            value={newInspection.notes}
            onChange={(e) =>
              setNewInspection({ ...newInspection, notes: e.target.value })
            }
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInspectionDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleAddInspection} variant="contained">
            Log Inspection
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Incident Dialog */}
      <Dialog
        open={incidentDialogOpen}
        onClose={() => setIncidentDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Report Safety Incident</DialogTitle>
        <DialogContent>
          <TextField
            margin="dense"
            label="Title"
            fullWidth
            value={newIncident.title}
            onChange={(e) =>
              setNewIncident({ ...newIncident, title: e.target.value })
            }
          />
          <TextField
            select
            margin="dense"
            label="Severity"
            fullWidth
            value={newIncident.severity}
            onChange={(e) =>
              setNewIncident({
                ...newIncident,
                severity: e.target.value as SeverityLevel,
              })
            }
          >
            {Object.entries(severityLabels).map(([value, label]) => (
              <MenuItem key={value} value={value}>
                {label}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            margin="dense"
            label="Location"
            fullWidth
            value={newIncident.location}
            onChange={(e) =>
              setNewIncident({ ...newIncident, location: e.target.value })
            }
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={3}
            value={newIncident.description}
            onChange={(e) =>
              setNewIncident({ ...newIncident, description: e.target.value })
            }
          />
          <TextField
            margin="dense"
            label="Reported By"
            fullWidth
            value={newIncident.reported_by}
            onChange={(e) =>
              setNewIncident({ ...newIncident, reported_by: e.target.value })
            }
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIncidentDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleAddIncident} variant="contained" color="error">
            Report Incident
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Drawdown Dialog */}
      <Dialog
        open={drawdownDialogOpen}
        onClose={() => setDrawdownDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>New Drawdown Request</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Request Name"
            fullWidth
            placeholder="e.g., Drawdown #3 - Superstructure L6-10"
            value={newDrawdown.request_name}
            onChange={(e) =>
              setNewDrawdown({ ...newDrawdown, request_name: e.target.value })
            }
          />
          <TextField
            margin="dense"
            label="Request Date"
            type="date"
            fullWidth
            InputLabelProps={{ shrink: true }}
            value={newDrawdown.request_date}
            onChange={(e) =>
              setNewDrawdown({ ...newDrawdown, request_date: e.target.value })
            }
          />
          <TextField
            margin="dense"
            label="Amount Requested (SGD)"
            type="number"
            fullWidth
            value={newDrawdown.amount_requested}
            onChange={(e) =>
              setNewDrawdown({
                ...newDrawdown,
                amount_requested: parseFloat(e.target.value) || 0,
              })
            }
          />
          <TextField
            margin="dense"
            label="Notes"
            fullWidth
            multiline
            rows={3}
            value={newDrawdown.notes}
            onChange={(e) =>
              setNewDrawdown({ ...newDrawdown, notes: e.target.value })
            }
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDrawdownDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleAddDrawdown} variant="contained">
            Submit Request
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
