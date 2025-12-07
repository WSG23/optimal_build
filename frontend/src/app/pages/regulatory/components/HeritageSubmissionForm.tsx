import React, { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Stack,
  Divider,
  List,
  ListItem,
  ListItemText,
  Checkbox,
  Paper,
  Grid,
} from '@mui/material'
import {
  AccountBalance as HeritageIcon,
  Info as InfoIcon,
  History as HistoryIcon,
  Architecture as ArchitectureIcon,
  Build as BuildIcon,
  Send as SendIcon,
} from '@mui/icons-material'
import { regulatoryApi, HeritageSubmission } from '../../../../api/regulatory'

interface HeritageSubmissionFormProps {
  open: boolean
  onClose: () => void
  projectId: string
  onSuccess: (submission: HeritageSubmission) => void
}

const CONSERVATION_STATUSES = [
  {
    value: 'national_monument',
    label: 'National Monument',
    description:
      'Highest level of protection under the Preservation of Monuments Act',
  },
  {
    value: 'conservation_area',
    label: 'Conservation Area',
    description: 'Protected area under URA conservation guidelines',
  },
  {
    value: 'gazetted_building',
    label: 'Gazetted Building',
    description: 'Listed building with specific preservation requirements',
  },
  {
    value: 'identified_heritage',
    label: 'Identified Heritage',
    description: 'Recognized heritage significance, not formally gazetted',
  },
  {
    value: 'potential_heritage',
    label: 'Potential Heritage',
    description: 'Under evaluation for heritage designation',
  },
]

const HERITAGE_ELEMENTS = [
  {
    id: 'facade',
    label: 'Original Facade',
    description: 'External building front',
  },
  {
    id: 'roof',
    label: 'Roof Structure',
    description: 'Original roofing and form',
  },
  {
    id: 'windows',
    label: 'Historic Windows',
    description: 'Original window frames and glass',
  },
  {
    id: 'doors',
    label: 'Historic Doors',
    description: 'Original doorways and hardware',
  },
  {
    id: 'interior',
    label: 'Interior Features',
    description: 'Original internal layouts',
  },
  {
    id: 'flooring',
    label: 'Historic Flooring',
    description: 'Original floor materials',
  },
  {
    id: 'ornaments',
    label: 'Decorative Elements',
    description: 'Moldings, carvings, tiles',
  },
  {
    id: 'structure',
    label: 'Structural System',
    description: 'Load-bearing elements',
  },
]

export const HeritageSubmissionForm: React.FC<HeritageSubmissionFormProps> = ({
  open,
  onClose,
  projectId,
  onSuccess,
}) => {
  const [conservationStatus, setConservationStatus] = useState('')
  const [originalYear, setOriginalYear] = useState<number | ''>('')
  const [selectedElements, setSelectedElements] = useState<string[]>([])
  const [proposedInterventions, setProposedInterventions] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleToggleElement = (elementId: string) => {
    setSelectedElements((prev) =>
      prev.includes(elementId)
        ? prev.filter((e) => e !== elementId)
        : [...prev, elementId],
    )
  }

  const handleSubmit = async () => {
    if (!conservationStatus) {
      setError('Please select a conservation status')
      return
    }

    setSubmitting(true)
    setError(null)

    try {
      const submission = await regulatoryApi.createHeritageSubmission({
        project_id: projectId,
        conservation_status: conservationStatus,
        original_construction_year: originalYear || undefined,
        heritage_elements:
          selectedElements.length > 0
            ? JSON.stringify(selectedElements)
            : undefined,
        proposed_interventions: proposedInterventions || undefined,
      })
      onSuccess(submission)
      handleReset()
    } catch (err) {
      console.error('Failed to create heritage submission', err)
      setError('Failed to submit application. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleReset = () => {
    setConservationStatus('')
    setOriginalYear('')
    setSelectedElements([])
    setProposedInterventions('')
    setError(null)
  }

  const handleClose = () => {
    handleReset()
    onClose()
  }

  const currentYear = new Date().getFullYear()

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{ sx: { bgcolor: '#1A1D1F' } }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <HeritageIcon color="primary" />
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Heritage Submission
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Submit to Singapore Tourism Board (STB) for heritage conservation
              approval
            </Typography>
          </Box>
        </Box>
      </DialogTitle>

      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Stack spacing={3} sx={{ mt: 1 }}>
          {/* Conservation Status */}
          <Box>
            <Typography
              variant="subtitle2"
              gutterBottom
              sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
            >
              <ArchitectureIcon fontSize="small" />
              Conservation Status *
            </Typography>
            <FormControl fullWidth size="small">
              <InputLabel>Select Conservation Status</InputLabel>
              <Select
                value={conservationStatus}
                label="Select Conservation Status"
                onChange={(e) => setConservationStatus(e.target.value)}
              >
                {CONSERVATION_STATUSES.map((status) => (
                  <MenuItem key={status.value} value={status.value}>
                    <Box>
                      <Typography variant="body2">{status.label}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {status.description}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          {/* Original Construction Year */}
          <Box>
            <Typography
              variant="subtitle2"
              gutterBottom
              sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
            >
              <HistoryIcon fontSize="small" />
              Original Construction Year
            </Typography>
            <TextField
              fullWidth
              size="small"
              type="number"
              value={originalYear}
              onChange={(e) =>
                setOriginalYear(e.target.value ? parseInt(e.target.value) : '')
              }
              placeholder="e.g., 1920"
              inputProps={{ min: 1800, max: currentYear }}
              helperText="Enter the year the building was originally constructed"
            />
          </Box>

          <Divider />

          {/* Heritage Elements */}
          <Box>
            <Typography
              variant="subtitle2"
              gutterBottom
              sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
            >
              <ArchitectureIcon fontSize="small" />
              Protected Heritage Elements
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Select the heritage elements that require preservation:
            </Typography>
            <Grid container spacing={1}>
              {HERITAGE_ELEMENTS.map((element) => (
                <Grid item xs={12} sm={6} key={element.id}>
                  <Paper
                    variant="outlined"
                    sx={{
                      p: 1,
                      cursor: 'pointer',
                      borderColor: selectedElements.includes(element.id)
                        ? 'primary.main'
                        : 'divider',
                      bgcolor: selectedElements.includes(element.id)
                        ? 'rgba(0, 201, 255, 0.1)'
                        : 'transparent',
                      transition: 'all 0.2s ease',
                      '&:hover': {
                        borderColor: 'primary.main',
                      },
                    }}
                    onClick={() => handleToggleElement(element.id)}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Checkbox
                        checked={selectedElements.includes(element.id)}
                        size="small"
                        sx={{ p: 0.5 }}
                      />
                      <Box sx={{ ml: 1 }}>
                        <Typography variant="body2" fontWeight={500}>
                          {element.label}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {element.description}
                        </Typography>
                      </Box>
                    </Box>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </Box>

          <Divider />

          {/* Proposed Interventions */}
          <Box>
            <Typography
              variant="subtitle2"
              gutterBottom
              sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
            >
              <BuildIcon fontSize="small" />
              Proposed Interventions
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={4}
              value={proposedInterventions}
              onChange={(e) => setProposedInterventions(e.target.value)}
              placeholder="Describe the proposed modifications, restoration works, or adaptive reuse plans..."
              variant="outlined"
            />
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ mt: 0.5, display: 'block' }}
            >
              Be specific about how you plan to preserve heritage elements while
              achieving development objectives.
            </Typography>
          </Box>

          {/* STB Review Info */}
          <Alert severity="info" icon={<InfoIcon />}>
            <Typography variant="body2" fontWeight={500}>
              STB Review Process:
            </Typography>
            <List dense sx={{ mt: 0.5, mb: 0 }}>
              <ListItem sx={{ py: 0, pl: 0 }}>
                <ListItemText
                  primary="Initial assessment: 2-4 weeks"
                  primaryTypographyProps={{ variant: 'caption' }}
                />
              </ListItem>
              <ListItem sx={{ py: 0, pl: 0 }}>
                <ListItemText
                  primary="Conservation plan review: 4-8 weeks (if required)"
                  primaryTypographyProps={{ variant: 'caption' }}
                />
              </ListItem>
              <ListItem sx={{ py: 0, pl: 0 }}>
                <ListItemText
                  primary="Final approval: 2-4 weeks"
                  primaryTypographyProps={{ variant: 'caption' }}
                />
              </ListItem>
            </List>
          </Alert>
        </Stack>
      </DialogContent>

      <DialogActions sx={{ p: 3 }}>
        <Button onClick={handleClose} disabled={submitting}>
          Cancel
        </Button>
        <Box sx={{ flex: '1 1 auto' }} />
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={submitting || !conservationStatus}
          startIcon={
            submitting ? (
              <CircularProgress size={20} color="inherit" />
            ) : (
              <SendIcon />
            )
          }
          sx={{
            background: 'linear-gradient(135deg, #be185d 0%, #f472b6 100%)',
            color: '#fff',
          }}
        >
          {submitting ? 'Creating...' : 'Create Heritage Submission'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
