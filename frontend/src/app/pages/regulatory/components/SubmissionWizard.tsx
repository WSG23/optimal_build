import React, { useState } from 'react'
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
import {
  AccountBalance as AgencyIcon,
  Description as DocIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material'
import { regulatoryApi, AuthoritySubmission } from '../../../../api/regulatory'

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
          <Grid container spacing={2} sx={{ mt: 1 }}>
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
                        sx={{ display: 'flex', alignItems: 'center', mb: 1 }}
                      >
                        <AgencyIcon color="primary" sx={{ mr: 1 }} />
                        <Typography variant="h6">{agency.code}</Typography>
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        {agency.name}
                      </Typography>
                      <Typography
                        variant="caption"
                        display="block"
                        sx={{ mt: 1 }}
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
          <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 3 }}>
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
            <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Note: This simulation connects to a mock MockCorenet service. No
                actual data will be sent to government agencies.
              </Typography>
            </Box>
          </Box>
        )
      case 2: // Review & Submit
        return (
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <DocIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              Ready to Submit
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
              You are about to submit a{' '}
              <strong>{getSubmissionTypeLabel()}</strong> application to{' '}
              <strong>{selectedAgency}</strong>.
            </Typography>
            <Typography variant="body2" color="warning.main">
              Please ensure all required documents (simulated) are attached.
            </Typography>
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
        <Stepper activeStep={activeStep} sx={{ pt: 3, pb: 5 }}>
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
      <DialogActions sx={{ p: 3 }}>
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
            {submitting ? 'Submitting...' : 'Submit'}
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
