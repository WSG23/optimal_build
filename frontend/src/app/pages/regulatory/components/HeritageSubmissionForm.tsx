/**
 * Heritage Submission Form - Detailed STB submission form for conservation projects.
 * Handles heritage building approvals coordination with Singapore Tourism Board.
 */

import React, { useState, useCallback, useEffect } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography,
} from '@mui/material'
import {
  AccountBalance as HeritageIcon,
  Add as AddIcon,
  AttachFile as AttachIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  Delete as DeleteIcon,
  Description as DocumentIcon,
  History as HistoryIcon,
  Info as InfoIcon,
  Save as SaveIcon,
  Send as SendIcon,
  Upload as UploadIcon,
} from '@mui/icons-material'
import {
  regulatoryApi,
  HeritageSubmission,
  HeritageSubmissionCreateRequest,
  HeritageSubmissionUpdateRequest,
} from '../../../../api/regulatory'

interface HeritageSubmissionFormProps {
  open: boolean
  onClose: () => void
  projectId: string
  existingSubmission?: HeritageSubmission
  onSuccess?: (submission: HeritageSubmission) => void
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
      id={`heritage-tabpanel-${index}`}
      aria-labelledby={`heritage-tab-${index}`}
      sx={{ py: 3 }}
    >
      {value === index && children}
    </Box>
  )
}

const CONSERVATION_STATUS_OPTIONS = [
  {
    value: 'national_monument',
    label: 'National Monument',
    description: 'Gazetted under the Preservation of Monuments Act',
  },
  {
    value: 'conservation_building',
    label: 'Conservation Building',
    description: 'URA Conservation Area designation',
  },
  {
    value: 'historic_site',
    label: 'Historic Site',
    description: 'Recognized historic significance',
  },
  {
    value: 'heritage_trail',
    label: 'Heritage Trail Building',
    description: 'Part of designated heritage trail',
  },
  {
    value: 'pre_war',
    label: 'Pre-War Building',
    description: 'Built before 1945',
  },
]

const HERITAGE_ELEMENTS_OPTIONS = [
  { id: 'facade', label: 'Original Facade', category: 'Exterior' },
  { id: 'roof', label: 'Original Roof Form', category: 'Exterior' },
  { id: 'windows', label: 'Original Windows/Doors', category: 'Exterior' },
  { id: 'balcony', label: 'Balconies/Verandahs', category: 'Exterior' },
  { id: 'ornaments', label: 'Decorative Ornaments', category: 'Exterior' },
  { id: 'tiles', label: 'Original Floor Tiles', category: 'Interior' },
  { id: 'staircase', label: 'Original Staircase', category: 'Interior' },
  { id: 'columns', label: 'Columns/Pillars', category: 'Interior' },
  { id: 'ceiling', label: 'Ornate Ceilings', category: 'Interior' },
  { id: 'ironwork', label: 'Wrought Iron Work', category: 'Features' },
  { id: 'signage', label: 'Historic Signage', category: 'Features' },
  { id: 'garden', label: 'Heritage Garden/Landscape', category: 'Features' },
]

const INTERVENTION_TYPES = [
  {
    id: 'restoration',
    label: 'Restoration',
    description: 'Restore to original state',
  },
  {
    id: 'rehabilitation',
    label: 'Rehabilitation',
    description: 'Adapt for new use while preserving character',
  },
  {
    id: 'renovation',
    label: 'Renovation',
    description: 'Update with minimal heritage impact',
  },
  {
    id: 'addition',
    label: 'Addition',
    description: 'New construction complementing heritage structure',
  },
  {
    id: 'demolition',
    label: 'Partial Demolition',
    description: 'Remove non-heritage elements',
  },
]

export const HeritageSubmissionForm: React.FC<HeritageSubmissionFormProps> = ({
  open,
  onClose,
  projectId,
  existingSubmission,
  onSuccess,
}) => {
  const [tabValue, setTabValue] = useState(0)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // Form data
  const [conservationStatus, setConservationStatus] = useState('')
  const [constructionYear, setConstructionYear] = useState<number | ''>('')
  const [selectedElements, setSelectedElements] = useState<string[]>([])
  const [interventions, setInterventions] = useState<
    { type: string; description: string }[]
  >([])
  const [conservationPlanAttached, setConservationPlanAttached] =
    useState(false)

  // Initialize form with existing data
  useEffect(() => {
    if (existingSubmission) {
      setConservationStatus(existingSubmission.conservation_status)
      setConstructionYear(existingSubmission.original_construction_year || '')
      setSelectedElements(
        existingSubmission.heritage_elements?.split(',').filter(Boolean) || [],
      )
      setConservationPlanAttached(existingSubmission.conservation_plan_attached)
      // Parse interventions from string if available
      if (existingSubmission.proposed_interventions) {
        try {
          const parsed = JSON.parse(existingSubmission.proposed_interventions)
          if (Array.isArray(parsed)) {
            setInterventions(parsed)
          }
        } catch {
          setInterventions([
            {
              type: 'restoration',
              description: existingSubmission.proposed_interventions,
            },
          ])
        }
      }
    }
  }, [existingSubmission])

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  const handleElementToggle = (elementId: string) => {
    setSelectedElements((prev) =>
      prev.includes(elementId)
        ? prev.filter((id) => id !== elementId)
        : [...prev, elementId],
    )
  }

  const handleAddIntervention = () => {
    setInterventions((prev) => [...prev, { type: '', description: '' }])
  }

  const handleRemoveIntervention = (index: number) => {
    setInterventions((prev) => prev.filter((_, i) => i !== index))
  }

  const handleInterventionChange = (
    index: number,
    field: 'type' | 'description',
    value: string,
  ) => {
    setInterventions((prev) =>
      prev.map((item, i) => (i === index ? { ...item, [field]: value } : item)),
    )
  }

  const handleSave = useCallback(async () => {
    setSaving(true)
    setError(null)
    setSuccessMessage(null)

    try {
      const payload = {
        conservation_status: conservationStatus,
        original_construction_year: constructionYear || undefined,
        heritage_elements: selectedElements.join(','),
        proposed_interventions: JSON.stringify(interventions),
        conservation_plan_attached: conservationPlanAttached,
      }

      if (existingSubmission) {
        const updated = await regulatoryApi.updateHeritageSubmission(
          existingSubmission.id,
          payload as HeritageSubmissionUpdateRequest,
        )
        setSuccessMessage('Submission saved successfully')
        onSuccess?.(updated)
      } else {
        const created = await regulatoryApi.createHeritageSubmission({
          project_id: projectId,
          ...payload,
        } as HeritageSubmissionCreateRequest)
        setSuccessMessage('Submission created successfully')
        onSuccess?.(created)
      }
    } catch (err) {
      console.error('Failed to save heritage submission:', err)
      setError('Failed to save submission. Please try again.')
    } finally {
      setSaving(false)
    }
  }, [
    conservationStatus,
    constructionYear,
    selectedElements,
    interventions,
    conservationPlanAttached,
    existingSubmission,
    projectId,
    onSuccess,
  ])

  const handleSubmitToSTB = useCallback(async () => {
    if (!existingSubmission) {
      setError('Please save the submission first before submitting to STB')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const submitted = await regulatoryApi.submitToSTB(existingSubmission.id)
      setSuccessMessage(
        `Submitted to STB. Reference: ${submitted.stb_reference}`,
      )
      onSuccess?.(submitted)
    } catch (err) {
      console.error('Failed to submit to STB:', err)
      setError('Failed to submit to STB. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [existingSubmission, onSuccess])

  const canSubmit =
    conservationStatus &&
    selectedElements.length > 0 &&
    interventions.length > 0

  const isSubmitted = existingSubmission?.status !== 'draft'

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: {
          minHeight: '80vh',
          bgcolor: 'background.paper',
        },
      }}
    >
      <DialogTitle
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <HeritageIcon color="primary" />
          <Box>
            <Typography variant="h6">
              Heritage Conservation Submission
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Singapore Tourism Board (STB) Application
            </Typography>
          </Box>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {existingSubmission?.stb_reference && (
            <Chip
              label={existingSubmission.stb_reference}
              color="primary"
              size="small"
              sx={{ fontFamily: 'monospace' }}
            />
          )}
          {existingSubmission && (
            <Chip
              label={existingSubmission.status}
              color={
                existingSubmission.status === 'approved'
                  ? 'success'
                  : existingSubmission.status === 'submitted'
                    ? 'info'
                    : 'default'
              }
              size="small"
              sx={{ textTransform: 'capitalize' }}
            />
          )}
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', px: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab
            label="Building Info"
            icon={<HistoryIcon />}
            iconPosition="start"
          />
          <Tab
            label="Heritage Elements"
            icon={<HeritageIcon />}
            iconPosition="start"
          />
          <Tab
            label="Proposed Works"
            icon={<DocumentIcon />}
            iconPosition="start"
          />
          <Tab label="Documents" icon={<AttachIcon />} iconPosition="start" />
        </Tabs>
      </Box>

      <DialogContent sx={{ px: 3 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        {successMessage && (
          <Alert
            severity="success"
            sx={{ mb: 2 }}
            onClose={() => setSuccessMessage(null)}
          >
            {successMessage}
          </Alert>
        )}

        {/* Tab 0: Building Info */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Conservation Status</InputLabel>
                <Select
                  value={conservationStatus}
                  label="Conservation Status"
                  onChange={(e) => setConservationStatus(e.target.value)}
                  disabled={isSubmitted}
                >
                  {CONSERVATION_STATUS_OPTIONS.map((opt) => (
                    <MenuItem key={opt.value} value={opt.value}>
                      <Box>
                        <Typography variant="body1">{opt.label}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {opt.description}
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Original Construction Year"
                type="number"
                value={constructionYear}
                onChange={(e) =>
                  setConstructionYear(
                    e.target.value ? parseInt(e.target.value) : '',
                  )
                }
                placeholder="e.g., 1920"
                inputProps={{ min: 1800, max: new Date().getFullYear() }}
                disabled={isSubmitted}
              />
            </Grid>

            <Grid item xs={12}>
              <Card
                sx={{
                  bgcolor: 'rgba(25, 118, 210, 0.1)',
                  border: '1px solid rgba(25, 118, 210, 0.3)',
                }}
              >
                <CardContent>
                  <Box
                    sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}
                  >
                    <InfoIcon
                      color="primary"
                      fontSize="small"
                      sx={{ mt: 0.5 }}
                    />
                    <Box>
                      <Typography variant="subtitle2">
                        Heritage Assessment Guidelines
                      </Typography>
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{ mt: 0.5 }}
                      >
                        The STB reviews applications based on:
                      </Typography>
                      <Box component="ul" sx={{ pl: 2, m: 0, mt: 1 }}>
                        <Typography
                          component="li"
                          variant="body2"
                          color="text.secondary"
                        >
                          Architectural and historical significance
                        </Typography>
                        <Typography
                          component="li"
                          variant="body2"
                          color="text.secondary"
                        >
                          Preservation of original heritage elements
                        </Typography>
                        <Typography
                          component="li"
                          variant="body2"
                          color="text.secondary"
                        >
                          Compatibility of proposed interventions
                        </Typography>
                        <Typography
                          component="li"
                          variant="body2"
                          color="text.secondary"
                        >
                          Contribution to Singapore&apos;s built heritage
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Tab 1: Heritage Elements */}
        <TabPanel value={tabValue} index={1}>
          <Typography variant="subtitle1" gutterBottom>
            Select all heritage elements present in the building:
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Identifying heritage elements helps STB understand the
            building&apos;s significance and guide appropriate conservation
            measures.
          </Typography>

          {['Exterior', 'Interior', 'Features'].map((category) => (
            <Box key={category} sx={{ mb: 3 }}>
              <Typography variant="subtitle2" color="primary" sx={{ mb: 1.5 }}>
                {category}
              </Typography>
              <Grid container spacing={1}>
                {HERITAGE_ELEMENTS_OPTIONS.filter(
                  (el) => el.category === category,
                ).map((element) => (
                  <Grid item xs={6} sm={4} md={3} key={element.id}>
                    <Paper
                      onClick={() =>
                        !isSubmitted && handleElementToggle(element.id)
                      }
                      sx={{
                        p: 1.5,
                        cursor: isSubmitted ? 'default' : 'pointer',
                        bgcolor: selectedElements.includes(element.id)
                          ? 'rgba(46, 125, 50, 0.2)'
                          : 'rgba(255, 255, 255, 0.03)',
                        border: selectedElements.includes(element.id)
                          ? '1px solid rgba(46, 125, 50, 0.5)'
                          : '1px solid rgba(255, 255, 255, 0.1)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1,
                        transition: 'all 0.2s',
                        '&:hover': {
                          bgcolor: isSubmitted
                            ? undefined
                            : selectedElements.includes(element.id)
                              ? 'rgba(46, 125, 50, 0.3)'
                              : 'rgba(255, 255, 255, 0.05)',
                        },
                      }}
                    >
                      <Checkbox
                        checked={selectedElements.includes(element.id)}
                        disabled={isSubmitted}
                        size="small"
                        sx={{ p: 0 }}
                      />
                      <Typography variant="body2">{element.label}</Typography>
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            </Box>
          ))}

          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Selected: {selectedElements.length} element(s)
            </Typography>
          </Box>
        </TabPanel>

        {/* Tab 2: Proposed Works */}
        <TabPanel value={tabValue} index={2}>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              mb: 2,
            }}
          >
            <Box>
              <Typography variant="subtitle1">
                Proposed Interventions
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Describe the conservation works planned for this building.
              </Typography>
            </Box>
            {!isSubmitted && (
              <Button
                startIcon={<AddIcon />}
                onClick={handleAddIntervention}
                variant="outlined"
                size="small"
              >
                Add Intervention
              </Button>
            )}
          </Box>

          {interventions.length === 0 ? (
            <Paper
              sx={{
                p: 4,
                textAlign: 'center',
                bgcolor: 'rgba(255, 255, 255, 0.03)',
              }}
            >
              <DocumentIcon
                sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }}
              />
              <Typography color="text.secondary">
                No interventions defined yet. Click &quot;Add Intervention&quot;
                to describe the proposed works.
              </Typography>
            </Paper>
          ) : (
            <Stack spacing={2}>
              {interventions.map((intervention, index) => (
                <Paper
                  key={index}
                  sx={{
                    p: 2,
                    bgcolor: 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      gap: 2,
                      alignItems: 'flex-start',
                    }}
                  >
                    <Chip
                      label={index + 1}
                      size="small"
                      sx={{ minWidth: 32, mt: 1 }}
                    />
                    <Grid container spacing={2} sx={{ flex: 1 }}>
                      <Grid item xs={12} sm={4}>
                        <FormControl fullWidth size="small">
                          <InputLabel>Type</InputLabel>
                          <Select
                            value={intervention.type}
                            label="Type"
                            onChange={(e) =>
                              handleInterventionChange(
                                index,
                                'type',
                                e.target.value,
                              )
                            }
                            disabled={isSubmitted}
                          >
                            {INTERVENTION_TYPES.map((type) => (
                              <MenuItem key={type.id} value={type.id}>
                                <Box>
                                  <Typography variant="body2">
                                    {type.label}
                                  </Typography>
                                  <Typography
                                    variant="caption"
                                    color="text.secondary"
                                  >
                                    {type.description}
                                  </Typography>
                                </Box>
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      </Grid>
                      <Grid item xs={12} sm={8}>
                        <TextField
                          fullWidth
                          size="small"
                          label="Description"
                          multiline
                          rows={2}
                          value={intervention.description}
                          onChange={(e) =>
                            handleInterventionChange(
                              index,
                              'description',
                              e.target.value,
                            )
                          }
                          placeholder="Describe the specific works, materials, and conservation approach..."
                          disabled={isSubmitted}
                        />
                      </Grid>
                    </Grid>
                    {!isSubmitted && (
                      <IconButton
                        onClick={() => handleRemoveIntervention(index)}
                        size="small"
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    )}
                  </Box>
                </Paper>
              ))}
            </Stack>
          )}
        </TabPanel>

        {/* Tab 3: Documents */}
        <TabPanel value={tabValue} index={3}>
          <Typography variant="subtitle1" gutterBottom>
            Required Documents
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Upload supporting documents for your heritage submission.
          </Typography>

          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Paper
                sx={{
                  p: 2,
                  bgcolor: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                }}
              >
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={conservationPlanAttached}
                      onChange={(e) =>
                        setConservationPlanAttached(e.target.checked)
                      }
                      disabled={isSubmitted}
                    />
                  }
                  label={
                    <Box>
                      <Typography variant="body1">
                        Conservation Management Plan
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Detailed plan for preserving heritage significance
                        (Required for National Monuments)
                      </Typography>
                    </Box>
                  }
                />
              </Paper>
            </Grid>

            <Grid item xs={12} sm={6}>
              <Paper
                sx={{
                  p: 3,
                  textAlign: 'center',
                  border: '2px dashed rgba(255, 255, 255, 0.2)',
                  cursor: 'pointer',
                  '&:hover': {
                    bgcolor: 'rgba(255, 255, 255, 0.05)',
                    borderColor: 'primary.main',
                  },
                }}
              >
                <UploadIcon
                  sx={{ fontSize: 40, color: 'text.secondary', mb: 1 }}
                />
                <Typography variant="body2">
                  Upload Historical Photos
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Original photographs, archival images
                </Typography>
              </Paper>
            </Grid>

            <Grid item xs={12} sm={6}>
              <Paper
                sx={{
                  p: 3,
                  textAlign: 'center',
                  border: '2px dashed rgba(255, 255, 255, 0.2)',
                  cursor: 'pointer',
                  '&:hover': {
                    bgcolor: 'rgba(255, 255, 255, 0.05)',
                    borderColor: 'primary.main',
                  },
                }}
              >
                <UploadIcon
                  sx={{ fontSize: 40, color: 'text.secondary', mb: 1 }}
                />
                <Typography variant="body2">
                  Upload Architectural Drawings
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Plans, elevations, sections
                </Typography>
              </Paper>
            </Grid>
          </Grid>

          <Alert severity="info" sx={{ mt: 3 }}>
            <Typography variant="body2">
              Document upload is simulated in this demo. In production, files
              would be uploaded to secure storage and attached to the
              submission.
            </Typography>
          </Alert>
        </TabPanel>
      </DialogContent>

      <DialogActions
        sx={{
          px: 3,
          py: 2,
          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
          gap: 1,
        }}
      >
        <Button onClick={onClose} color="inherit">
          Close
        </Button>
        <Box sx={{ flex: 1 }} />

        {!isSubmitted && (
          <>
            <Button
              onClick={handleSave}
              disabled={saving || !canSubmit}
              startIcon={
                saving ? (
                  <CircularProgress size={20} color="inherit" />
                ) : (
                  <SaveIcon />
                )
              }
              variant="outlined"
            >
              {saving ? 'Saving...' : 'Save Draft'}
            </Button>

            <Button
              onClick={handleSubmitToSTB}
              disabled={loading || !existingSubmission || !canSubmit}
              startIcon={
                loading ? (
                  <CircularProgress size={20} color="inherit" />
                ) : (
                  <SendIcon />
                )
              }
              variant="contained"
              sx={{
                background: 'linear-gradient(135deg, #00C9FF 0%, #92FE9D 100%)',
                color: '#000',
                fontWeight: 'bold',
              }}
            >
              {loading ? 'Submitting...' : 'Submit to STB'}
            </Button>
          </>
        )}

        {isSubmitted && (
          <Chip
            icon={<CheckIcon />}
            label={`Submitted: ${existingSubmission?.stb_reference || ''}`}
            color="success"
          />
        )}
      </DialogActions>
    </Dialog>
  )
}

export default HeritageSubmissionForm
