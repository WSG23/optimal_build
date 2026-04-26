import React, { useEffect, useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Stepper,
  Step,
  StepLabel,
  Box,
  Typography,
  Grid,
  Card,
  CardActionArea,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
} from '@mui/material'
import AgencyIcon from '@mui/icons-material/AccountBalance'
import DocIcon from '@mui/icons-material/Description'
import CheckIcon from '@mui/icons-material/CheckCircle'
import {
  regulatoryApi,
  AuthoritySubmission,
  type CorenetCapability,
} from '../../../../api/regulatory'

interface SubmissionWizardProps {
  open: boolean
  onClose: () => void
  projectId: string
  onSuccess: (submission: AuthoritySubmission) => void
}

const AGENCIES = [
  {
    code: 'URA',
    name: 'Urban Redevelopment Authority',
    desc: 'Planning & Zoning',
  },
  {
    code: 'BCA',
    name: 'Building & Construction Authority',
    desc: 'Structural & Accessibility',
  },
  { code: 'SCDF', name: 'Singapore Civil Defence Force', desc: 'Fire Safety' },
  {
    code: 'NEA',
    name: 'National Environment Agency',
    desc: 'Pollution & Waste',
  },
  { code: 'PUB', name: 'Public Utilities Board', desc: 'Water & Drainage' },
  {
    code: 'LTA',
    name: 'Land Transport Authority',
    desc: 'Vehicle Parking & Access',
  },
]

// Maps agency to available submission types with their backend enum values
// Backend SubmissionType enum values: DC, BP, TOP, CSC, WAIVER, CONSULTATION, CHANGE_OF_USE, HERITAGE_APPROVAL, INDUSTRIAL_PERMIT
const SUBMISSION_TYPES: Record<
  string,
  Array<{ label: string; value: string }>
> = {
  URA: [
    { label: 'Development Control (DC)', value: 'DC' },
    { label: 'Change of Use', value: 'CHANGE_OF_USE' },
    { label: 'Consultation', value: 'CONSULTATION' },
  ],
  BCA: [
    { label: 'Building Plan (BP)', value: 'BP' },
    { label: 'Temporary Occupation Permit (TOP)', value: 'TOP' },
    { label: 'Certificate of Statutory Completion (CSC)', value: 'CSC' },
  ],
  SCDF: [
    { label: 'Fire Safety Consultation', value: 'CONSULTATION' },
    { label: 'Waiver Request', value: 'WAIVER' },
  ],
  NEA: [{ label: 'Environmental Consultation', value: 'CONSULTATION' }],
  PUB: [{ label: 'Drainage Consultation', value: 'CONSULTATION' }],
  LTA: [{ label: 'Traffic Consultation', value: 'CONSULTATION' }],
  DEFAULT: [
    { label: 'General Consultation', value: 'CONSULTATION' },
    { label: 'Waiver Request', value: 'WAIVER' },
  ],
}

export const SubmissionWizard: React.FC<SubmissionWizardProps> = ({
  open,
  onClose,
  projectId,
  onSuccess,
}) => {
  const [activeStep, setActiveStep] = useState(0)
  const [selectedAgency, setSelectedAgency] = useState('')
  const [submissionType, setSubmissionType] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [capability, setCapability] = useState<CorenetCapability | null>(null)

  useEffect(() => {
    if (!open) {
      return
    }
    let active = true
    regulatoryApi
      .getCorenetCapability()
      .then((result) => {
        if (active) {
          setCapability(result)
        }
      })
      .catch(() => {
        if (active) {
          setCapability(null)
        }
      })
    return () => {
      active = false
    }
  }, [open])

  const handleNext = () => setActiveStep((prev) => prev + 1)
  const handleBack = () => setActiveStep((prev) => prev - 1)

  const handleSubmit = async () => {
    setSubmitting(true)
    try {
      // Backend accepts project_id as string (UUID or integer string)
      const submission = await regulatoryApi.createSubmission({
        project_id: String(projectId),
        agency: selectedAgency,
        submission_type: submissionType,
        submission_mode:
          capability?.submission_mode_default ?? 'submission_prep',
      })
      onSuccess(submission)
      handleReset()
    } catch (error) {
      console.error('Submission failed', error)
      alert('Failed to submit application. See console for details.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleReset = () => {
    setActiveStep(0)
    setSelectedAgency('')
    setSubmissionType('')
  }

  const getSubmissionTypes = () => {
    return SUBMISSION_TYPES[selectedAgency] || SUBMISSION_TYPES['DEFAULT']
  }

  const getSubmissionTypeLabel = () => {
    const types = getSubmissionTypes()
    const found = types.find((t) => t.value === submissionType)
    return found ? found.label : submissionType
  }

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0: // Select Agency
        return (
          <Grid
            container
            spacing="var(--ob-space-200)"
            sx={{ mt: 'var(--ob-space-100)' }}
          >
            {AGENCIES.map((agency) => (
              <Grid item xs={12} sm={6} key={agency.code}>
                <Card
                  variant="outlined"
                  sx={{
                    borderColor:
                      selectedAgency === agency.code
                        ? 'primary.main'
                        : 'divider',
                    bgcolor:
                      selectedAgency === agency.code
                        ? 'action.selected'
                        : 'background.paper',
                  }}
                >
                  <CardActionArea
                    onClick={() => setSelectedAgency(agency.code)}
                    sx={{ height: '100%' }}
                  >
                    <CardContent>
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          mb: 'var(--ob-space-100)',
                        }}
                      >
                        <AgencyIcon
                          color="primary"
                          sx={{ mr: 'var(--ob-space-100)' }}
                        />
                        <Typography variant="h6">{agency.code}</Typography>
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        {agency.name}
                      </Typography>
                      <Typography
                        variant="caption"
                        display="block"
                        sx={{ mt: 'var(--ob-space-100)' }}
                      >
                        {agency.desc}
                      </Typography>
                    </CardContent>
                  </CardActionArea>
                </Card>
              </Grid>
            ))}
          </Grid>
        )
      case 1: // Submission Details
        return (
          <Box
            sx={{
              mt: 'var(--ob-space-200)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-200)',
            }}
          >
            <Typography variant="body1">
              Select the type of application you are submitting to{' '}
              <strong>{selectedAgency}</strong>.
            </Typography>
            <FormControl fullWidth>
              <InputLabel>Submission Type</InputLabel>
              <Select
                value={submissionType}
                label="Submission Type"
                onChange={(e) => setSubmissionType(e.target.value)}
              >
                {getSubmissionTypes().map((type) => (
                  <MenuItem key={type.value} value={type.value}>
                    {type.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Box
              sx={{
                p: 'var(--ob-space-200)',
                bgcolor: 'background.default',
                borderRadius: 'var(--ob-radius-sm)',
              }}
            >
              <Typography variant="caption" color="text.secondary">
                {capability?.live_submission_available
                  ? 'Live CORENET submission is available for this workspace.'
                  : 'This flow prepares a submission-ready CORENET package. No live government submission will be attempted from this environment.'}
              </Typography>
              {capability?.delivery_blockers?.length ? (
                <Typography
                  variant="caption"
                  color="warning.main"
                  display="block"
                  sx={{ mt: 'var(--ob-space-100)' }}
                >
                  Gate: {capability.delivery_blockers[0]}
                </Typography>
              ) : null}
            </Box>
          </Box>
        )
      case 2: // Review & Submit
        return (
          <Box sx={{ mt: 'var(--ob-space-200)', textAlign: 'center' }}>
            <DocIcon
              sx={{
                fontSize: 60,
                color: 'text.secondary',
                mb: 'var(--ob-space-200)',
              }}
            />
            <Typography variant="h6" gutterBottom>
              Ready to Package
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
              You are about to prepare a{' '}
              <strong>{getSubmissionTypeLabel()}</strong> application to{' '}
              <strong>{selectedAgency}</strong>.
            </Typography>
            <Typography variant="body2" color="warning.main">
              {capability?.live_submission_available
                ? 'Please ensure all required documents are attached before live submission.'
                : 'Please ensure all required documents are attached for the submission-ready package.'}
            </Typography>
            {capability?.package_requirements?.length ? (
              <Typography
                variant="caption"
                display="block"
                sx={{ mt: 'var(--ob-space-150)' }}
              >
                Required: {capability.package_requirements.join(', ')}
              </Typography>
            ) : null}
          </Box>
        )
      default:
        return 'Unknown step'
    }
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{ sx: { bgcolor: 'background.paper' } }}
    >
      <DialogTitle>New Regulatory Submission</DialogTitle>
      <DialogContent>
        <Stepper
          activeStep={activeStep}
          sx={{ pt: 'var(--ob-space-200)', pb: 'var(--ob-space-300)' }}
        >
          <Step>
            <StepLabel>Select Agency</StepLabel>
          </Step>
          <Step>
            <StepLabel>Details</StepLabel>
          </Step>
          <Step>
            <StepLabel>Review</StepLabel>
          </Step>
        </Stepper>
        {renderStepContent(activeStep)}
      </DialogContent>
      <DialogActions sx={{ p: 'var(--ob-space-200)' }}>
        <Button onClick={onClose} disabled={submitting}>
          Cancel
        </Button>
        <Box sx={{ flex: '1 1 auto' }} />
        {activeStep > 0 && (
          <Button onClick={handleBack} disabled={submitting}>
            Back
          </Button>
        )}
        {activeStep === 2 ? (
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={submitting}
            startIcon={
              submitting ? (
                <CircularProgress size={20} color="inherit" />
              ) : (
                <CheckIcon />
              )
            }
            sx={{
              background:
                'linear-gradient(135deg, var(--ob-success-700) 0%, var(--ob-success-400) 100%)',
              color: 'var(--ob-color-text-inverse)',
            }}
          >
            {submitting
              ? 'Submitting...'
              : capability?.live_submission_available
                ? 'Submit'
                : 'Create Package'}
          </Button>
        ) : (
          <Button
            variant="contained"
            onClick={handleNext}
            disabled={activeStep === 0 ? !selectedAgency : !submissionType}
          >
            Next
          </Button>
        )}
      </DialogActions>
    </Dialog>
  )
}
