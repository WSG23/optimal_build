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
  TextField,
  Alert,
  Chip,
  CircularProgress,
  Stack,
} from '@mui/material'
import {
  Business as OfficeIcon,
  Store as RetailIcon,
  Home as ResidentialIcon,
  Factory as IndustrialIcon,
  AccountBalance as HeritageIcon,
  Apartment as MixedUseIcon,
  Hotel as HospitalityIcon,
  ArrowForward as ArrowIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
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
  onSuccess: (application: ChangeOfUseApplication) => void
}

const ASSET_TYPES: Array<{
  value: AssetType
  label: string
  icon: React.ReactNode
  color: string
}> = [
  {
    value: 'office',
    label: 'Office',
    icon: <OfficeIcon />,
    color: 'var(--ob-color-brand-primary)',
  },
  {
    value: 'retail',
    label: 'Retail',
    icon: <RetailIcon />,
    color: 'var(--ob-color-status-success-text)',
  },
  {
    value: 'residential',
    label: 'Residential',
    icon: <ResidentialIcon />,
    color: '#7c3aed', // Purple - no semantic token available
  },
  {
    value: 'industrial',
    label: 'Industrial',
    icon: <IndustrialIcon />,
    color: 'var(--ob-color-status-warning-text)',
  },
  {
    value: 'heritage',
    label: 'Heritage',
    icon: <HeritageIcon />,
    color: '#be185d', // Pink - no semantic token available
  },
  {
    value: 'mixed_use',
    label: 'Mixed-Use',
    icon: <MixedUseIcon />,
    color: '#ea580c', // Orange - no semantic token available
  },
  {
    value: 'hospitality',
    label: 'Hospitality',
    icon: <HospitalityIcon />,
    color: '#0891b2', // Cyan - no semantic token available
  },
]

const STEPS = ['Current Use', 'Proposed Use', 'Justification', 'Review']

export const ChangeOfUseWizard: React.FC<ChangeOfUseWizardProps> = ({
  open,
  onClose,
  projectId,
  onSuccess,
}) => {
  const [activeStep, setActiveStep] = useState(0)
  const [currentUse, setCurrentUse] = useState<AssetType | null>(null)
  const [proposedUse, setProposedUse] = useState<AssetType | null>(null)
  const [justification, setJustification] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleNext = () => setActiveStep((prev) => prev + 1)
  const handleBack = () => setActiveStep((prev) => prev - 1)

  const handleSubmit = async () => {
    if (!currentUse || !proposedUse) return

    setSubmitting(true)
    setError(null)

    try {
      const application = await regulatoryApi.createChangeOfUse({
        project_id: projectId,
        current_use: currentUse,
        proposed_use: proposedUse,
        justification: justification || undefined,
      })
      onSuccess(application)
      handleReset()
    } catch (err) {
      console.error('Failed to create change of use application', err)
      setError('Failed to submit application. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleReset = () => {
    setActiveStep(0)
    setCurrentUse(null)
    setProposedUse(null)
    setJustification('')
    setError(null)
  }

  const handleClose = () => {
    handleReset()
    onClose()
  }

  const getAssetInfo = (type: AssetType | null) => {
    return ASSET_TYPES.find((a) => a.value === type)
  }

  const requiresDCAmendment = currentUse !== proposedUse
  const requiresPlanningPermission =
    proposedUse === 'residential' || proposedUse === 'hospitality'

  const canProceed = () => {
    switch (activeStep) {
      case 0:
        return currentUse !== null
      case 1:
        return proposedUse !== null && proposedUse !== currentUse
      case 2:
        return true // Justification is optional
      default:
        return true
    }
  }

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <Box>
            <Typography variant="body1" sx={{ mb: 2 }}>
              Select the <strong>current</strong> use of the property:
            </Typography>
            <Grid container spacing={2}>
              {ASSET_TYPES.map((type) => (
                <Grid item xs={6} sm={4} key={type.value}>
                  <Card
                    variant="outlined"
                    sx={{
                      borderColor:
                        currentUse === type.value ? type.color : 'divider',
                      borderWidth: currentUse === type.value ? 2 : 1,
                      bgcolor:
                        currentUse === type.value
                          ? `${type.color}10`
                          : 'background.paper',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <CardActionArea
                      onClick={() => setCurrentUse(type.value)}
                      sx={{ height: '100%' }}
                    >
                      <CardContent
                        sx={{ textAlign: 'center', py: 2, minHeight: 100 }}
                      >
                        <Box sx={{ color: type.color, mb: 1 }}>{type.icon}</Box>
                        <Typography variant="body2" fontWeight={500}>
                          {type.label}
                        </Typography>
                      </CardContent>
                    </CardActionArea>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>
        )

      case 1:
        return (
          <Box>
            <Typography variant="body1" sx={{ mb: 2 }}>
              Select the <strong>proposed</strong> use for the property:
            </Typography>
            <Grid container spacing={2}>
              {ASSET_TYPES.filter((t) => t.value !== currentUse).map((type) => (
                <Grid item xs={6} sm={4} key={type.value}>
                  <Card
                    variant="outlined"
                    sx={{
                      borderColor:
                        proposedUse === type.value ? type.color : 'divider',
                      borderWidth: proposedUse === type.value ? 2 : 1,
                      bgcolor:
                        proposedUse === type.value
                          ? `${type.color}10`
                          : 'background.paper',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <CardActionArea
                      onClick={() => setProposedUse(type.value)}
                      sx={{ height: '100%' }}
                    >
                      <CardContent
                        sx={{ textAlign: 'center', py: 2, minHeight: 100 }}
                      >
                        <Box sx={{ color: type.color, mb: 1 }}>{type.icon}</Box>
                        <Typography variant="body2" fontWeight={500}>
                          {type.label}
                        </Typography>
                      </CardContent>
                    </CardActionArea>
                  </Card>
                </Grid>
              ))}
            </Grid>

            {proposedUse && (
              <Alert severity="info" icon={<InfoIcon />} sx={{ mt: 3 }}>
                <Typography variant="body2">
                  Changing from{' '}
                  <strong>{getAssetInfo(currentUse)?.label}</strong> to{' '}
                  <strong>{getAssetInfo(proposedUse)?.label}</strong> will
                  require:
                </Typography>
                <Box component="ul" sx={{ mt: 1, mb: 0, pl: 2 }}>
                  {requiresDCAmendment && (
                    <li>
                      <Typography variant="body2">
                        Development Control (DC) Amendment from URA
                      </Typography>
                    </li>
                  )}
                  {requiresPlanningPermission && (
                    <li>
                      <Typography variant="body2">
                        Planning Permission Application
                      </Typography>
                    </li>
                  )}
                </Box>
              </Alert>
            )}
          </Box>
        )

      case 2:
        return (
          <Box>
            <Typography variant="body1" sx={{ mb: 2 }}>
              Provide justification for the change of use (optional but
              recommended):
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={6}
              value={justification}
              onChange={(e) => setJustification(e.target.value)}
              placeholder="Explain why this change of use is being requested. Include market demand, site suitability, and alignment with planning objectives..."
              variant="outlined"
            />
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ mt: 1, display: 'block' }}
            >
              A strong justification improves approval chances. Consider
              including: market analysis, compatibility with surroundings, and
              benefits to the community.
            </Typography>
          </Box>
        )

      case 3:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Application Summary
            </Typography>

            {/* Visual Change Flow */}
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 2,
                my: 4,
                p: 3,
                bgcolor: 'rgba(255,255,255,0.03)',
                borderRadius: 'var(--ob-radius-sm)',
              }}
            >
              <Box sx={{ textAlign: 'center' }}>
                <Box
                  sx={{
                    color: getAssetInfo(currentUse)?.color,
                    mb: 1,
                    '& .MuiSvgIcon-root': { fontSize: 48 },
                  }}
                >
                  {getAssetInfo(currentUse)?.icon}
                </Box>
                <Typography variant="body2" fontWeight={500}>
                  {getAssetInfo(currentUse)?.label}
                </Typography>
                <Chip label="Current" size="small" sx={{ mt: 0.5 }} />
              </Box>

              <ArrowIcon sx={{ fontSize: 32, color: 'text.secondary' }} />

              <Box sx={{ textAlign: 'center' }}>
                <Box
                  sx={{
                    color: getAssetInfo(proposedUse)?.color,
                    mb: 1,
                    '& .MuiSvgIcon-root': { fontSize: 48 },
                  }}
                >
                  {getAssetInfo(proposedUse)?.icon}
                </Box>
                <Typography variant="body2" fontWeight={500}>
                  {getAssetInfo(proposedUse)?.label}
                </Typography>
                <Chip
                  label="Proposed"
                  size="small"
                  color="primary"
                  sx={{ mt: 0.5 }}
                />
              </Box>
            </Box>

            {/* Requirements */}
            <Stack spacing={2}>
              <Alert
                severity={requiresDCAmendment ? 'warning' : 'success'}
                icon={requiresDCAmendment ? <WarningIcon /> : <CheckIcon />}
              >
                DC Amendment:{' '}
                {requiresDCAmendment ? 'Required' : 'Not Required'}
              </Alert>
              <Alert
                severity={requiresPlanningPermission ? 'warning' : 'success'}
                icon={
                  requiresPlanningPermission ? <WarningIcon /> : <CheckIcon />
                }
              >
                Planning Permission:{' '}
                {requiresPlanningPermission ? 'Required' : 'Not Required'}
              </Alert>
            </Stack>

            {justification && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Justification:
                </Typography>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{
                    p: 2,
                    bgcolor: 'rgba(255,255,255,0.03)',
                    borderRadius: 'var(--ob-radius-xs)',
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {justification}
                </Typography>
              </Box>
            )}

            <Alert severity="info" sx={{ mt: 3 }}>
              <Typography variant="body2">
                This application will be submitted to URA for review. Typical
                processing time is 4-8 weeks depending on complexity.
              </Typography>
            </Alert>
          </Box>
        )

      default:
        return null
    }
  }

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { bgcolor: 'var(--ob-color-bg-surface)', minHeight: 500 },
      }}
    >
      <DialogTitle>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Change of Use Application
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Apply for URA approval to change the permitted use of your property
        </Typography>
      </DialogTitle>

      <DialogContent>
        <Stepper activeStep={activeStep} sx={{ pt: 2, pb: 4 }}>
          {STEPS.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {renderStepContent()}
      </DialogContent>

      <DialogActions sx={{ p: 3 }}>
        <Button onClick={handleClose} disabled={submitting}>
          Cancel
        </Button>
        <Box sx={{ flex: '1 1 auto' }} />
        {activeStep > 0 && (
          <Button onClick={handleBack} disabled={submitting}>
            Back
          </Button>
        )}
        {activeStep === STEPS.length - 1 ? (
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={submitting || !canProceed()}
            startIcon={
              submitting ? (
                <CircularProgress size={20} color="inherit" />
              ) : (
                <CheckIcon />
              )
            }
            sx={{
              background: 'linear-gradient(135deg, #00C853 0%, #B2FF59 100%)',
              color: 'var(--ob-color-text-primary)',
            }}
          >
            {submitting ? 'Submitting...' : 'Submit Application'}
          </Button>
        ) : (
          <Button
            variant="contained"
            onClick={handleNext}
            disabled={!canProceed()}
          >
            Next
          </Button>
        )}
      </DialogActions>
    </Dialog>
  )
}
