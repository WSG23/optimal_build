/**
 * Change of Use Wizard - Multi-step workflow for adaptive reuse applications.
 * Guides users through the URA change of use application process.
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
  Divider,
  FormControl,
  FormControlLabel,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  SelectChangeEvent,
  Step,
  StepLabel,
  Stepper,
  TextField,
  Typography,
} from '@mui/material'
import {
  ArrowBack as BackIcon,
  ArrowForward as ForwardIcon,
  Check as CheckIcon,
  SwapHoriz as SwapIcon,
} from '@mui/icons-material'
import {
  regulatoryApi,
  ChangeOfUseApplication,
  AssetType,
} from '../../../../api/regulatory'

interface ChangeOfUseWizardProps {
  open: boolean
  onClose: () => void
  projectId: string
  initialApplication?: ChangeOfUseApplication
  onSuccess?: (application: ChangeOfUseApplication) => void
}

const STEPS = [
  'Current Use',
  'Proposed Use',
  'Requirements Analysis',
  'Justification',
  'Review & Submit',
]

const ASSET_TYPE_OPTIONS: {
  value: AssetType
  label: string
  description: string
}[] = [
  { value: 'office', label: 'Office', description: 'Commercial office space' },
  { value: 'retail', label: 'Retail', description: 'Shopping, F&B, services' },
  {
    value: 'residential',
    label: 'Residential',
    description: 'Housing, apartments',
  },
  {
    value: 'industrial',
    label: 'Industrial',
    description: 'Manufacturing, warehouse',
  },
  {
    value: 'hospitality',
    label: 'Hospitality',
    description: 'Hotels, serviced apartments',
  },
  {
    value: 'mixed_use',
    label: 'Mixed Use',
    description: 'Combination of uses',
  },
  {
    value: 'heritage',
    label: 'Heritage',
    description: 'Conservation building',
  },
]

// Determines if DC amendment is required based on use changes
function requiresDCAmendment(
  currentUse: AssetType,
  proposedUse: AssetType,
): boolean {
  // Simplified logic - in reality this would be more complex
  return currentUse !== proposedUse
}

// Determines if planning permission is needed
function requiresPlanningPermission(proposedUse: AssetType): boolean {
  return ['residential', 'hospitality'].includes(proposedUse)
}

// Get applicable regulatory requirements
function getRequirements(
  currentUse: AssetType,
  proposedUse: AssetType,
): { label: string; required: boolean; agency: string }[] {
  const requirements = [
    {
      label: 'URA Development Application',
      required: requiresDCAmendment(currentUse, proposedUse),
      agency: 'URA',
    },
    {
      label: 'Planning Permission',
      required: requiresPlanningPermission(proposedUse),
      agency: 'URA',
    },
    {
      label: 'Building Plan Approval',
      required: true,
      agency: 'BCA',
    },
    {
      label: 'Fire Safety Certificate',
      required: proposedUse !== 'industrial',
      agency: 'SCDF',
    },
  ]

  if (proposedUse === 'residential' || proposedUse === 'hospitality') {
    requirements.push({
      label: 'Environmental Health License',
      required: true,
      agency: 'NEA',
    })
  }

  if (currentUse === 'heritage' || proposedUse === 'heritage') {
    requirements.push({
      label: 'Heritage Conservation Approval',
      required: true,
      agency: 'URA/NHB',
    })
  }

  return requirements
}

export const ChangeOfUseWizard: React.FC<ChangeOfUseWizardProps> = ({
  open,
  onClose,
  projectId,
  initialApplication,
  onSuccess,
}) => {
  const [activeStep, setActiveStep] = useState(0)
  const [savingDraft, setSavingDraft] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const isReadOnly =
    initialApplication?.status?.toUpperCase() !== 'DRAFT' &&
    Boolean(initialApplication)

  // Form data
  const [currentUse, setCurrentUse] = useState<AssetType | ''>('')
  const [proposedUse, setProposedUse] = useState<AssetType | ''>('')
  const [justification, setJustification] = useState('')
  const [acknowledgements, setAcknowledgements] = useState({
    dcAmendment: false,
    planningPermission: false,
    buildingPlan: false,
    timeline: false,
  })

  const requirements =
    currentUse && proposedUse
      ? getRequirements(currentUse as AssetType, proposedUse as AssetType)
      : []

  const requiresDC =
    currentUse && proposedUse
      ? requiresDCAmendment(currentUse as AssetType, proposedUse as AssetType)
      : false

  const requiresPlanning = proposedUse
    ? requiresPlanningPermission(proposedUse as AssetType)
    : false

  const handleNext = () => {
    setActiveStep((prev) => Math.min(prev + 1, STEPS.length - 1))
  }

  const handleBack = () => {
    setActiveStep((prev) => Math.max(prev - 1, 0))
  }

  const handleCurrentUseChange = (event: SelectChangeEvent) => {
    if (isReadOnly) {
      return
    }
    setCurrentUse(event.target.value as AssetType)
    // Reset proposed use if it would be the same
    if (event.target.value === proposedUse) {
      setProposedUse('')
    }
  }

  const handleProposedUseChange = (event: SelectChangeEvent) => {
    if (isReadOnly) {
      return
    }
    setProposedUse(event.target.value as AssetType)
  }

  const resetForm = useCallback(() => {
    setActiveStep(0)
    setCurrentUse('')
    setProposedUse('')
    setJustification('')
    setAcknowledgements({
      dcAmendment: false,
      planningPermission: false,
      buildingPlan: false,
      timeline: false,
    })
  }, [])

  useEffect(() => {
    if (!open) {
      return
    }
    if (initialApplication) {
      setActiveStep(0)
      setCurrentUse(initialApplication.current_use)
      setProposedUse(initialApplication.proposed_use)
      setJustification(initialApplication.justification ?? '')
      setAcknowledgements({
        dcAmendment: false,
        planningPermission: false,
        buildingPlan: false,
        timeline: false,
      })
      return
    }
    resetForm()
  }, [initialApplication, open, resetForm])

  const handleSaveDraft = useCallback(async () => {
    if (isReadOnly) {
      return
    }
    if (!currentUse || !proposedUse) return

    setSavingDraft(true)
    setError(null)

    try {
      const payload = {
        current_use: currentUse as AssetType,
        proposed_use: proposedUse as AssetType,
        justification: justification || undefined,
      }
      const application = initialApplication
        ? await regulatoryApi.updateChangeOfUse(initialApplication.id, {
            ...payload,
            status: 'DRAFT',
          })
        : await regulatoryApi.createChangeOfUse({
            project_id: projectId,
            ...payload,
          })
      onSuccess?.(application)
      onClose()
      resetForm()
    } catch (err) {
      console.error('Failed to create change of use application:', err)
      setError('Failed to save draft. Please try again.')
    } finally {
      setSavingDraft(false)
    }
  }, [
    currentUse,
    proposedUse,
    justification,
    projectId,
    onSuccess,
    onClose,
    resetForm,
    initialApplication,
    isReadOnly,
  ])

  const handleSubmit = useCallback(async () => {
    if (isReadOnly) {
      return
    }
    if (!currentUse || !proposedUse) return

    setSubmitting(true)
    setError(null)

    try {
      const payload = {
        current_use: currentUse as AssetType,
        proposed_use: proposedUse as AssetType,
        justification: justification || undefined,
        status: 'SUBMITTED',
      }
      const submitted = initialApplication
        ? await regulatoryApi.updateChangeOfUse(initialApplication.id, payload)
        : await regulatoryApi.updateChangeOfUse(
            (
              await regulatoryApi.createChangeOfUse({
                project_id: projectId,
                current_use: currentUse as AssetType,
                proposed_use: proposedUse as AssetType,
                justification: justification || undefined,
              })
            ).id,
            payload,
          )
      onSuccess?.(submitted)
      onClose()
      resetForm()
    } catch (err) {
      console.error('Failed to submit change of use application:', err)
      setError('Failed to submit application. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }, [
    currentUse,
    proposedUse,
    justification,
    projectId,
    onSuccess,
    onClose,
    resetForm,
    initialApplication,
    isReadOnly,
  ])

  const canProceed = () => {
    if (isReadOnly) {
      return true
    }
    switch (activeStep) {
      case 0:
        return !!currentUse
      case 1:
        return !!proposedUse && proposedUse !== currentUse
      case 2:
        return true // Requirements are informational
      case 3:
        return justification.length >= 50 // Minimum justification length
      case 4:
        return (
          acknowledgements.dcAmendment &&
          acknowledgements.buildingPlan &&
          acknowledgements.timeline
        )
      default:
        return false
    }
  }
  const canSaveDraft = Boolean(currentUse && proposedUse)

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              What is the current use of the property?
            </Typography>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mb: 'var(--ob-space-300)' }}
            >
              Select the existing approved land use for this site.
            </Typography>

            <FormControl fullWidth>
              <InputLabel>Current Use</InputLabel>
              <Select
                value={currentUse}
                label="Current Use"
                onChange={handleCurrentUseChange}
                disabled={isReadOnly}
              >
                {ASSET_TYPE_OPTIONS.map((opt) => (
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
          </Box>
        )

      case 1:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              What is the proposed new use?
            </Typography>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mb: 'var(--ob-space-300)' }}
            >
              Select the intended use after conversion. This determines the
              regulatory requirements.
            </Typography>

            <FormControl fullWidth>
              <InputLabel>Proposed Use</InputLabel>
              <Select
                value={proposedUse}
                label="Proposed Use"
                onChange={handleProposedUseChange}
                disabled={isReadOnly}
              >
                {ASSET_TYPE_OPTIONS.filter(
                  (opt) => opt.value !== currentUse,
                ).map((opt) => (
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

            {currentUse && proposedUse && (
              <Card
                sx={{
                  mt: 'var(--ob-space-300)',
                  bgcolor: 'rgba(25, 118, 210, 0.1)',
                  border: '1px solid rgba(25, 118, 210, 0.3)',
                }}
              >
                <CardContent>
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 'var(--ob-space-200)',
                      justifyContent: 'center',
                    }}
                  >
                    <Chip
                      label={
                        ASSET_TYPE_OPTIONS.find((o) => o.value === currentUse)
                          ?.label
                      }
                      color="default"
                      sx={{ fontSize: '1rem', py: 'var(--ob-space-200)' }}
                    />
                    <SwapIcon color="primary" />
                    <Chip
                      label={
                        ASSET_TYPE_OPTIONS.find((o) => o.value === proposedUse)
                          ?.label
                      }
                      color="primary"
                      sx={{ fontSize: '1rem', py: 'var(--ob-space-200)' }}
                    />
                  </Box>
                </CardContent>
              </Card>
            )}
          </Box>
        )

      case 2:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Regulatory Requirements Analysis
            </Typography>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mb: 'var(--ob-space-300)' }}
            >
              Based on your change of use, the following approvals will be
              required:
            </Typography>

            {requiresDC && (
              <Alert severity="warning" sx={{ mb: 'var(--ob-space-200)' }}>
                <Typography variant="subtitle2">
                  DC Amendment Required
                </Typography>
                <Typography variant="body2">
                  Changing from {currentUse} to {proposedUse} requires a
                  Development Control (DC) amendment application to URA.
                </Typography>
              </Alert>
            )}

            {requiresPlanning && (
              <Alert severity="info" sx={{ mb: 'var(--ob-space-200)' }}>
                <Typography variant="subtitle2">
                  Planning Permission Required
                </Typography>
                <Typography variant="body2">
                  {proposedUse === 'residential'
                    ? 'Residential'
                    : 'Hospitality'}{' '}
                  use requires additional planning permission approval.
                </Typography>
              </Alert>
            )}

            <Grid
              container
              spacing="var(--ob-space-200)"
              sx={{ mt: 'var(--ob-space-100)' }}
            >
              {requirements.map((req, index) => (
                <Grid item xs={12} sm={6} key={index}>
                  <Paper
                    sx={{
                      p: 'var(--ob-space-200)',
                      height: '100%',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 'var(--ob-space-150)',
                      bgcolor: req.required
                        ? 'var(--ob-color-surface-overlay-light)'
                        : 'var(--ob-color-overlay-backdrop-light)',
                      opacity: req.required ? 1 : 0.6,
                    }}
                  >
                    {req.required ? (
                      <CheckIcon color="success" />
                    ) : (
                      <Box sx={{ width: 24 }} />
                    )}
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="body2" fontWeight={500}>
                        {req.label}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {req.agency}
                      </Typography>
                    </Box>
                    <Chip
                      label={req.required ? 'Required' : 'N/A'}
                      size="small"
                      color={req.required ? 'success' : 'default'}
                      variant="outlined"
                    />
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </Box>
        )

      case 3:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Justification for Change of Use
            </Typography>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mb: 'var(--ob-space-300)' }}
            >
              Provide a clear justification for why this change of use is
              necessary and beneficial. URA considers market demand, urban
              planning objectives, and community impact.
            </Typography>

            <TextField
              fullWidth
              multiline
              rows={6}
              label="Justification"
              placeholder="Explain the rationale for the proposed change of use, including:
- Market demand and feasibility
- Benefits to the surrounding area
- Alignment with urban planning objectives
- Impact on existing infrastructure"
              value={justification}
              onChange={(e) => {
                if (!isReadOnly) {
                  setJustification(e.target.value)
                }
              }}
              helperText={`${justification.length}/50 characters minimum`}
              error={justification.length > 0 && justification.length < 50}
              disabled={isReadOnly}
            />

            <Box sx={{ mt: 'var(--ob-space-300)' }}>
              <Typography variant="subtitle2" gutterBottom>
                Tips for a Strong Justification:
              </Typography>
              <Box component="ul" sx={{ pl: 'var(--ob-space-200)', m: '0' }}>
                <Typography
                  component="li"
                  variant="body2"
                  color="text.secondary"
                >
                  Reference the URA Master Plan and zoning guidelines
                </Typography>
                <Typography
                  component="li"
                  variant="body2"
                  color="text.secondary"
                >
                  Highlight positive community impact
                </Typography>
                <Typography
                  component="li"
                  variant="body2"
                  color="text.secondary"
                >
                  Address potential concerns proactively
                </Typography>
                <Typography
                  component="li"
                  variant="body2"
                  color="text.secondary"
                >
                  Include market research or feasibility studies if available
                </Typography>
              </Box>
            </Box>
          </Box>
        )

      case 4:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Review & Confirm
            </Typography>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mb: 'var(--ob-space-300)' }}
            >
              Please review your application details and confirm the
              acknowledgements below.
            </Typography>

            <Card
              sx={{
                mb: 'var(--ob-space-300)',
                bgcolor: 'var(--ob-color-table-header)',
              }}
            >
              <CardContent>
                <Grid container spacing="var(--ob-space-200)">
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Current Use
                    </Typography>
                    <Typography variant="body1" fontWeight={500}>
                      {
                        ASSET_TYPE_OPTIONS.find((o) => o.value === currentUse)
                          ?.label
                      }
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Proposed Use
                    </Typography>
                    <Typography variant="body1" fontWeight={500}>
                      {
                        ASSET_TYPE_OPTIONS.find((o) => o.value === proposedUse)
                          ?.label
                      }
                    </Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Divider sx={{ my: 'var(--ob-space-100)' }} />
                    <Typography variant="caption" color="text.secondary">
                      Justification Summary
                    </Typography>
                    <Typography
                      variant="body2"
                      sx={{
                        mt: 'var(--ob-space-50)',
                        maxHeight: 100,
                        overflow: 'auto',
                        whiteSpace: 'pre-wrap',
                      }}
                    >
                      {justification || '(No justification provided)'}
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>

            <Typography variant="subtitle2" gutterBottom>
              Required Acknowledgements:
            </Typography>

            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--ob-space-100)',
              }}
            >
              <FormControlLabel
                control={
                  <Checkbox
                    checked={acknowledgements.dcAmendment}
                    onChange={(e) =>
                      setAcknowledgements({
                        ...acknowledgements,
                        dcAmendment: e.target.checked,
                      })
                    }
                    disabled={isReadOnly}
                  />
                }
                label="I understand that a DC amendment application may be required"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={acknowledgements.buildingPlan}
                    onChange={(e) =>
                      setAcknowledgements({
                        ...acknowledgements,
                        buildingPlan: e.target.checked,
                      })
                    }
                    disabled={isReadOnly}
                  />
                }
                label="I will submit building plan amendments as required"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={acknowledgements.timeline}
                    onChange={(e) =>
                      setAcknowledgements({
                        ...acknowledgements,
                        timeline: e.target.checked,
                      })
                    }
                    disabled={isReadOnly}
                  />
                }
                label="I understand the approval process may take 3-6 months"
              />
            </Box>
          </Box>
        )

      default:
        return null
    }
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          minHeight: '70vh',
          bgcolor: 'background.paper',
        },
      }}
    >
      <DialogTitle
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--ob-space-100)',
          borderBottom: '1px solid var(--ob-color-surface-overlay)',
        }}
      >
        <SwapIcon color="primary" />
        Change of Use Application
      </DialogTitle>

      <DialogContent sx={{ pt: 'var(--ob-space-300)' }}>
        <Stepper
          activeStep={activeStep}
          alternativeLabel
          sx={{ mb: 'var(--ob-space-400)' }}
        >
          {STEPS.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {error && (
          <Alert severity="error" sx={{ mb: 'var(--ob-space-300)' }}>
            {error}
          </Alert>
        )}

        <Box sx={{ minHeight: 300 }}>{renderStepContent()}</Box>
      </DialogContent>

      <DialogActions
        sx={{
          px: 'var(--ob-space-300)',
          py: 'var(--ob-space-200)',
          borderTop: '1px solid var(--ob-color-surface-overlay)',
        }}
      >
        <Button onClick={onClose} color="inherit">
          Cancel
        </Button>
        <Box sx={{ flex: 1 }} />
        <Button
          onClick={handleBack}
          disabled={activeStep === 0 || savingDraft || submitting}
          startIcon={<BackIcon />}
        >
          Back
        </Button>
        {activeStep === STEPS.length - 1 ? (
          isReadOnly ? (
            <Typography variant="caption" color="text.secondary">
              View-only submission
            </Typography>
          ) : (
            <>
              <Button
                variant="outlined"
                onClick={handleSaveDraft}
                disabled={!canSaveDraft || savingDraft || submitting}
                startIcon={
                  savingDraft ? (
                    <CircularProgress size={20} color="inherit" />
                  ) : (
                    <CheckIcon />
                  )
                }
              >
                {savingDraft ? 'Saving...' : 'Save Draft'}
              </Button>
              <Button
                variant="contained"
                onClick={handleSubmit}
                disabled={!canProceed() || submitting || savingDraft}
                startIcon={
                  submitting ? (
                    <CircularProgress size={20} color="inherit" />
                  ) : (
                    <CheckIcon />
                  )
                }
                sx={{
                  background:
                    'linear-gradient(135deg, var(--ob-brand-600) 0%, var(--ob-brand-400) 100%)',
                  color: 'var(--ob-color-text-inverse)',
                  fontWeight: 'var(--ob-font-weight-bold)',
                }}
              >
                {submitting ? 'Submitting...' : 'Submit Application'}
              </Button>
            </>
          )
        ) : (
          <Button
            variant="contained"
            onClick={handleNext}
            disabled={!canProceed() || savingDraft || submitting}
            endIcon={<ForwardIcon />}
          >
            Next
          </Button>
        )}
      </DialogActions>
    </Dialog>
  )
}

export default ChangeOfUseWizard
