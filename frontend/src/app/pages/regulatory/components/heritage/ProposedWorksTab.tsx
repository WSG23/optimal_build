import {
  Box,
  Button,
  Chip,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import DeleteIcon from '@mui/icons-material/Delete'
import DocumentIcon from '@mui/icons-material/Description'

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

interface Intervention {
  type: string
  description: string
}

interface ProposedWorksTabProps {
  interventions: Intervention[]
  onAddIntervention: () => void
  onRemoveIntervention: (index: number) => void
  onInterventionChange: (
    index: number,
    field: 'type' | 'description',
    value: string,
  ) => void
  isSubmitted: boolean
}

export function ProposedWorksTab({
  interventions,
  onAddIntervention,
  onRemoveIntervention,
  onInterventionChange,
  isSubmitted,
}: ProposedWorksTabProps) {
  return (
    <>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 'var(--ob-space-200)',
        }}
      >
        <Box>
          <Typography variant="subtitle1">Proposed Interventions</Typography>
          <Typography variant="body2" color="text.secondary">
            Describe the conservation works planned for this building.
          </Typography>
        </Box>
        {!isSubmitted && (
          <Button
            startIcon={<AddIcon />}
            onClick={onAddIntervention}
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
            p: 'var(--ob-space-300)',
            textAlign: 'center',
            bgcolor: 'rgba(245, 235, 220, 0.03)',
          }}
        >
          <DocumentIcon
            sx={{
              fontSize: 48,
              color: 'text.secondary',
              mb: 'var(--ob-space-100)',
            }}
          />
          <Typography color="text.secondary">
            No interventions defined yet. Click &quot;Add Intervention&quot; to
            describe the proposed works.
          </Typography>
        </Paper>
      ) : (
        <Stack spacing="var(--ob-space-200)">
          {interventions.map((intervention, index) => (
            <Paper
              key={index}
              sx={{
                p: 'var(--ob-space-200)',
                bgcolor: 'rgba(245, 235, 220, 0.03)',
                border: '1px solid rgba(245, 235, 220, 0.1)',
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  gap: 'var(--ob-space-200)',
                  alignItems: 'flex-start',
                }}
              >
                <Chip
                  label={index + 1}
                  size="small"
                  sx={{ minWidth: 32, mt: 'var(--ob-space-100)' }}
                />
                <Grid container spacing="var(--ob-space-200)" sx={{ flex: 1 }}>
                  <Grid item xs={12} sm={4}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Type</InputLabel>
                      <Select
                        value={intervention.type}
                        label="Type"
                        onChange={(e) => {
                          onInterventionChange(index, 'type', e.target.value)
                        }}
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
                      onChange={(e) => {
                        onInterventionChange(
                          index,
                          'description',
                          e.target.value,
                        )
                      }}
                      placeholder="Describe the specific works, materials, and conservation approach..."
                      disabled={isSubmitted}
                    />
                  </Grid>
                </Grid>
                {!isSubmitted && (
                  <IconButton
                    onClick={() => {
                      onRemoveIntervention(index)
                    }}
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
    </>
  )
}
