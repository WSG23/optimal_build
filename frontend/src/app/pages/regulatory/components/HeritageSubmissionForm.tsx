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
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Tab,
  Tabs,
  TextField,
  Typography,
} from '@mui/material'
import HeritageIcon from '@mui/icons-material/AccountBalance'
import AttachIcon from '@mui/icons-material/AttachFile'
import CheckIcon from '@mui/icons-material/Check'
import CloseIcon from '@mui/icons-material/Close'
import DocumentIcon from '@mui/icons-material/Description'
import HistoryIcon from '@mui/icons-material/History'
import InfoIcon from '@mui/icons-material/Info'
import SaveIcon from '@mui/icons-material/Save'
import SendIcon from '@mui/icons-material/Send'
import { HeritageElementsTab } from './heritage/HeritageElementsTab'
import { ProposedWorksTab } from './heritage/ProposedWorksTab'
import { DocumentsTab } from './heritage/DocumentsTab'
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
      sx={{ py: 'var(--ob-space-200)' }}
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
  const [activeSubmission, setActiveSubmission] = useState<
    HeritageSubmission | undefined
  >(existingSubmission)

  // Form data
  const [conservationStatus, setConservationStatus] = useState('')
  const [constructionYear, setConstructionYear] = useState<number | ''>('')
  const [selectedElements, setSelectedElements] = useState<string[]>([])
  const [interventions, setInterventions] = useState<
    { type: string; description: string }[]
  >([])
  const [conservationPlanAttached, setConservationPlanAttached] =
    useState(false)

  // Simulated uploaded files
  const [uploadedPhotos, setUploadedPhotos] = useState<string[]>([])
  const [uploadedDrawings, setUploadedDrawings] = useState<string[]>([])

  // Initialize form with existing data
  useEffect(() => {
    setActiveSubmission(existingSubmission)
  }, [existingSubmission])

  useEffect(() => {
    if (activeSubmission) {
      setConservationStatus(activeSubmission.conservation_status)
      setConstructionYear(activeSubmission.original_construction_year || '')
      setSelectedElements(
        activeSubmission.heritage_elements?.split(',').filter(Boolean) || [],
      )
      setConservationPlanAttached(activeSubmission.conservation_plan_attached)
      if (activeSubmission.proposed_interventions) {
        try {
          const parsed = JSON.parse(activeSubmission.proposed_interventions)
          if (Array.isArray(parsed)) {
            setInterventions(parsed)
          }
        } catch {
          setInterventions([
            {
              type: 'restoration',
              description: activeSubmission.proposed_interventions,
            },
          ])
        }
      } else {
        setInterventions([])
      }
    } else {
      setConservationStatus('')
      setConstructionYear('')
      setSelectedElements([])
      setInterventions([])
      setConservationPlanAttached(false)
      setUploadedPhotos([])
      setUploadedDrawings([])
      setSuccessMessage(null)
      setError(null)
    }
  }, [activeSubmission])

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

  // Simulated file upload handlers
  const handlePhotoUpload = () => {
    if (isSubmitted) return
    // Create a hidden file input and trigger it
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'image/*'
    input.multiple = true
    input.onchange = (e) => {
      const files = (e.target as HTMLInputElement).files
      if (files) {
        const fileNames = Array.from(files).map((f) => f.name)
        setUploadedPhotos((prev) => [...prev, ...fileNames])
        setSuccessMessage(`${files.length} photo(s) added (simulated)`)
      }
    }
    input.click()
  }

  const handleDrawingUpload = () => {
    if (isSubmitted) return
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.pdf,.dwg,.dxf,image/*'
    input.multiple = true
    input.onchange = (e) => {
      const files = (e.target as HTMLInputElement).files
      if (files) {
        const fileNames = Array.from(files).map((f) => f.name)
        setUploadedDrawings((prev) => [...prev, ...fileNames])
        setSuccessMessage(`${files.length} drawing(s) added (simulated)`)
      }
    }
    input.click()
  }

  const handleRemovePhoto = (index: number) => {
    setUploadedPhotos((prev) => prev.filter((_, i) => i !== index))
  }

  const handleRemoveDrawing = (index: number) => {
    setUploadedDrawings((prev) => prev.filter((_, i) => i !== index))
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

      if (activeSubmission) {
        const updated = await regulatoryApi.updateHeritageSubmission(
          activeSubmission.id,
          payload as HeritageSubmissionUpdateRequest,
        )
        setSuccessMessage('Draft updated successfully')
        setActiveSubmission(updated)
        onSuccess?.(updated)
      } else {
        const created = await regulatoryApi.createHeritageSubmission({
          project_id: projectId,
          ...payload,
        } as HeritageSubmissionCreateRequest)
        setSuccessMessage('Draft saved successfully')
        setActiveSubmission(created)
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
    activeSubmission,
    projectId,
    onSuccess,
  ])

  const [confirmSTBOpen, setConfirmSTBOpen] = useState(false)

  const handleSubmitToSTB = useCallback(async () => {
    if (!activeSubmission) {
      setError('Please save the submission first before submitting to STB')
      return
    }

    setConfirmSTBOpen(false)
    setLoading(true)
    setError(null)

    try {
      const submitted = await regulatoryApi.submitToSTB(activeSubmission.id)
      setSuccessMessage(
        `Submitted to STB. Reference: ${submitted.stb_reference}`,
      )
      setActiveSubmission(submitted)
      onSuccess?.(submitted)
    } catch (err) {
      console.error('Failed to submit to STB:', err)
      setError('Failed to submit to STB. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [activeSubmission, onSuccess])

  const hasInterventionDetails =
    interventions.length > 0 &&
    interventions.every(
      (entry) => entry.type.trim() && entry.description.trim(),
    )
  const canSaveDraft = Boolean(conservationStatus)
  const canSubmit =
    Boolean(conservationStatus) &&
    selectedElements.length > 0 &&
    hasInterventionDetails

  // Only mark as submitted if we have an existing submission AND its status is not DRAFT
  // When creating a new submission (no existingSubmission), this should be false
  const isSubmitted = activeSubmission
    ? activeSubmission.status.toUpperCase() !== 'DRAFT'
    : false

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
          borderBottom: '1px solid rgba(245, 235, 220, 0.1)',
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--ob-space-150)',
          }}
        >
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
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--ob-space-100)',
          }}
        >
          {activeSubmission?.stb_reference && (
            <Chip
              label={activeSubmission.stb_reference}
              color="primary"
              size="small"
              sx={{ fontFamily: 'var(--ob-font-family-mono)' }}
            />
          )}
          {activeSubmission && (
            <Chip
              label={activeSubmission.status}
              color={
                activeSubmission.status.toUpperCase() === 'APPROVED'
                  ? 'success'
                  : activeSubmission.status.toUpperCase() === 'SUBMITTED'
                    ? 'info'
                    : activeSubmission.status.toUpperCase() === 'IN_REVIEW'
                      ? 'warning'
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

      <Box
        sx={{
          borderBottom: 1,
          borderColor: 'divider',
          px: 'var(--ob-space-200)',
        }}
      >
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

      <DialogContent sx={{ px: 'var(--ob-space-200)' }}>
        {error && (
          <Alert
            severity="error"
            sx={{ mb: 'var(--ob-space-200)' }}
            onClose={() => setError(null)}
          >
            {error}
          </Alert>
        )}
        {successMessage && (
          <Alert
            severity="success"
            sx={{ mb: 'var(--ob-space-200)' }}
            onClose={() => setSuccessMessage(null)}
          >
            {successMessage}
          </Alert>
        )}

        {/* Tab 0: Building Info */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing="var(--ob-space-200)">
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
                    sx={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: 'var(--ob-space-100)',
                    }}
                  >
                    <InfoIcon
                      color="primary"
                      fontSize="small"
                      sx={{ mt: 'var(--ob-space-050)' }}
                    />
                    <Box>
                      <Typography variant="subtitle2">
                        Heritage Assessment Guidelines
                      </Typography>
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{ mt: 'var(--ob-space-050)' }}
                      >
                        The STB reviews applications based on:
                      </Typography>
                      <Box
                        component="ul"
                        sx={{
                          pl: 'var(--ob-space-200)',
                          m: 0,
                          mt: 'var(--ob-space-100)',
                        }}
                      >
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
          <HeritageElementsTab
            selectedElements={selectedElements}
            onElementToggle={handleElementToggle}
            isSubmitted={isSubmitted}
          />
        </TabPanel>

        {/* Tab 2: Proposed Works */}
        <TabPanel value={tabValue} index={2}>
          <ProposedWorksTab
            interventions={interventions}
            onAddIntervention={handleAddIntervention}
            onRemoveIntervention={handleRemoveIntervention}
            onInterventionChange={handleInterventionChange}
            isSubmitted={isSubmitted}
          />
        </TabPanel>

        {/* Tab 3: Documents */}
        <TabPanel value={tabValue} index={3}>
          <DocumentsTab
            conservationPlanAttached={conservationPlanAttached}
            onConservationPlanChange={setConservationPlanAttached}
            uploadedPhotos={uploadedPhotos}
            uploadedDrawings={uploadedDrawings}
            onPhotoUpload={handlePhotoUpload}
            onDrawingUpload={handleDrawingUpload}
            onRemovePhoto={handleRemovePhoto}
            onRemoveDrawing={handleRemoveDrawing}
            isSubmitted={isSubmitted}
          />
        </TabPanel>
      </DialogContent>

      <DialogActions
        sx={{
          px: 'var(--ob-space-200)',
          py: 'var(--ob-space-200)',
          borderTop: '1px solid rgba(245, 235, 220, 0.1)',
          gap: 'var(--ob-space-100)',
        }}
      >
        <Button onClick={onClose} color="inherit">
          Close
        </Button>
        <Box sx={{ flex: 1 }} />

        {!isSubmitted && (
          <>
            {!activeSubmission && (
              <Typography variant="caption" color="text.secondary">
                Save a draft to enable submission to STB.
              </Typography>
            )}
            {activeSubmission && !canSubmit && (
              <Typography variant="caption" color="text.secondary">
                To submit, select heritage elements and add at least one
                intervention with details.
              </Typography>
            )}
            <Button
              onClick={handleSave}
              disabled={saving || !canSaveDraft}
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
              onClick={() => setConfirmSTBOpen(true)}
              disabled={loading || !activeSubmission || !canSubmit}
              startIcon={<SendIcon />}
              variant="contained"
              color="primary"
            >
              Submit to STB
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

      {/* STB Submission Confirmation */}
      <Dialog open={confirmSTBOpen} onClose={() => setConfirmSTBOpen(false)}>
        <DialogTitle>Submit to STB</DialogTitle>
        <DialogContent>
          <Typography>
            Submit this heritage conservation application to the Singapore
            Tourism Board? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions
          sx={{ p: 'var(--ob-space-200)', gap: 'var(--ob-space-100)' }}
        >
          <Button variant="outlined" onClick={() => setConfirmSTBOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color="primary"
            onClick={handleSubmitToSTB}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={16} /> : <SendIcon />}
          >
            {loading ? 'Submitting...' : 'Confirm Submit'}
          </Button>
        </DialogActions>
      </Dialog>
    </Dialog>
  )
}

export default HeritageSubmissionForm
