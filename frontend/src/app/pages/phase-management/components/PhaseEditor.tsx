import { useState, useCallback } from 'react'
import {
  Box,
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
  InputAdornment,
} from '@mui/material'
import type {
  DevelopmentPhase,
  PhaseType,
  PhaseStatus,
  HeritageClassification,
  OccupancyStatus,
  CreatePhasePayload,
  UpdatePhasePayload,
} from '../../../../api/development'

interface PhaseEditorProps {
  open: boolean
  phase?: DevelopmentPhase | null
  projectId: string
  onClose: () => void
  onSave: (
    data: CreatePhasePayload | UpdatePhasePayload,
    isNew: boolean,
  ) => Promise<void>
}

const PHASE_TYPES: { value: PhaseType; label: string }[] = [
  { value: 'demolition', label: 'Demolition' },
  { value: 'site_preparation', label: 'Site Preparation' },
  { value: 'foundation', label: 'Foundation' },
  { value: 'structure', label: 'Structure' },
  { value: 'envelope', label: 'Envelope' },
  { value: 'mep_rough_in', label: 'MEP Rough-In' },
  { value: 'interior_fit_out', label: 'Interior Fit-Out' },
  { value: 'external_works', label: 'External Works' },
  { value: 'commissioning', label: 'Commissioning' },
  { value: 'handover', label: 'Handover' },
  { value: 'heritage_restoration', label: 'Heritage Restoration' },
  { value: 'tenant_renovation', label: 'Tenant Renovation' },
  { value: 'facade_upgrade', label: 'Facade Upgrade' },
  { value: 'services_upgrade', label: 'Services Upgrade' },
  { value: 'mixed_use_integration', label: 'Mixed-Use Integration' },
]

const PHASE_STATUSES: { value: PhaseStatus; label: string }[] = [
  { value: 'not_started', label: 'Not Started' },
  { value: 'planning', label: 'Planning' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'on_hold', label: 'On Hold' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
]

const HERITAGE_CLASSIFICATIONS: {
  value: HeritageClassification
  label: string
}[] = [
  { value: 'none', label: 'None' },
  { value: 'national_monument', label: 'National Monument' },
  { value: 'conservation_building', label: 'Conservation Building' },
  { value: 'heritage_site', label: 'Heritage Site' },
  { value: 'traditional_area', label: 'Traditional Area' },
]

const OCCUPANCY_STATUSES: { value: OccupancyStatus; label: string }[] = [
  { value: 'vacant', label: 'Vacant' },
  { value: 'partially_occupied', label: 'Partially Occupied' },
  { value: 'fully_occupied', label: 'Fully Occupied' },
  { value: 'mixed_use_active', label: 'Mixed-Use Active' },
]

interface FormState {
  name: string
  phaseType: PhaseType
  status: PhaseStatus
  sequenceOrder: number
  plannedStartDate: string
  plannedEndDate: string
  actualStartDate: string
  actualEndDate: string
  budgetAmount: string
  actualCostAmount: string
  description: string
  heritageClassification: HeritageClassification
  heritageApprovalRequired: boolean
  heritageApprovalStatus: string
  occupancyStatus: OccupancyStatus
  tenantCoordinationRequired: boolean
}

function getInitialState(phase?: DevelopmentPhase | null): FormState {
  if (phase) {
    return {
      name: phase.name,
      phaseType: phase.phaseType,
      status: phase.status,
      sequenceOrder: phase.sequenceOrder,
      plannedStartDate: phase.plannedStartDate ?? '',
      plannedEndDate: phase.plannedEndDate ?? '',
      actualStartDate: phase.actualStartDate ?? '',
      actualEndDate: phase.actualEndDate ?? '',
      budgetAmount: phase.budgetAmount?.toString() ?? '',
      actualCostAmount: phase.actualCostAmount?.toString() ?? '',
      description: phase.description ?? '',
      heritageClassification: phase.heritageClassification,
      heritageApprovalRequired: phase.heritageApprovalRequired,
      heritageApprovalStatus: phase.heritageApprovalStatus ?? '',
      occupancyStatus: phase.occupancyStatus,
      tenantCoordinationRequired: phase.tenantCoordinationRequired,
    }
  }

  return {
    name: '',
    phaseType: 'site_preparation',
    status: 'not_started',
    sequenceOrder: 1,
    plannedStartDate: '',
    plannedEndDate: '',
    actualStartDate: '',
    actualEndDate: '',
    budgetAmount: '',
    actualCostAmount: '',
    description: '',
    heritageClassification: 'none',
    heritageApprovalRequired: false,
    heritageApprovalStatus: '',
    occupancyStatus: 'vacant',
    tenantCoordinationRequired: false,
  }
}

export function PhaseEditor({
  open,
  phase,
  onClose,
  onSave,
}: PhaseEditorProps) {
  const [form, setForm] = useState<FormState>(() => getInitialState(phase))
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isNew = !phase

  const handleChange = useCallback(
    <K extends keyof FormState>(field: K, value: FormState[K]) => {
      setForm((prev) => ({ ...prev, [field]: value }))
      setError(null)
    },
    [],
  )

  const handleSubmit = useCallback(async () => {
    if (!form.name.trim()) {
      setError('Phase name is required')
      return
    }

    setSaving(true)
    setError(null)

    try {
      if (isNew) {
        const payload: CreatePhasePayload = {
          name: form.name.trim(),
          phaseType: form.phaseType,
          sequenceOrder: form.sequenceOrder,
          plannedStartDate: form.plannedStartDate || null,
          plannedEndDate: form.plannedEndDate || null,
          budgetAmount: form.budgetAmount
            ? parseFloat(form.budgetAmount)
            : null,
          description: form.description || null,
          heritageClassification: form.heritageClassification,
          heritageApprovalRequired: form.heritageApprovalRequired,
          occupancyStatus: form.occupancyStatus,
          tenantCoordinationRequired: form.tenantCoordinationRequired,
        }
        await onSave(payload, true)
      } else {
        const payload: UpdatePhasePayload = {
          name: form.name.trim(),
          status: form.status,
          plannedStartDate: form.plannedStartDate || null,
          plannedEndDate: form.plannedEndDate || null,
          actualStartDate: form.actualStartDate || null,
          actualEndDate: form.actualEndDate || null,
          budgetAmount: form.budgetAmount
            ? parseFloat(form.budgetAmount)
            : null,
          actualCostAmount: form.actualCostAmount
            ? parseFloat(form.actualCostAmount)
            : null,
          description: form.description || null,
          heritageApprovalStatus: form.heritageApprovalStatus || null,
        }
        await onSave(payload, false)
      }
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save phase')
    } finally {
      setSaving(false)
    }
  }, [form, isNew, onSave, onClose])

  // Reset form when phase changes
  const handleOpen = useCallback(() => {
    setForm(getInitialState(phase))
    setError(null)
  }, [phase])

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      TransitionProps={{ onEnter: handleOpen }}
    >
      <DialogTitle>
        {isNew ? 'Add New Phase' : `Edit Phase: ${phase?.name}`}
      </DialogTitle>

      <DialogContent dividers>
        <Stack spacing={3} sx={{ pt: 1 }}>
          {error && (
            <Typography color="error" variant="body2">
              {error}
            </Typography>
          )}

          {/* Basic Info */}
          <Typography
            variant="subtitle2"
            sx={{ fontWeight: 600, color: 'text.secondary' }}
          >
            Basic Information
          </Typography>

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField
              fullWidth
              label="Phase Name"
              value={form.name}
              onChange={(e) => handleChange('name', e.target.value)}
              required
            />

            <FormControl fullWidth>
              <InputLabel>Phase Type</InputLabel>
              <Select
                value={form.phaseType}
                label="Phase Type"
                onChange={(e) =>
                  handleChange('phaseType', e.target.value as PhaseType)
                }
                disabled={!isNew}
              >
                {PHASE_TYPES.map((type) => (
                  <MenuItem key={type.value} value={type.value}>
                    {type.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={form.status}
                label="Status"
                onChange={(e) =>
                  handleChange('status', e.target.value as PhaseStatus)
                }
              >
                {PHASE_STATUSES.map((status) => (
                  <MenuItem key={status.value} value={status.value}>
                    {status.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>

          <TextField
            fullWidth
            label="Sequence Order"
            type="number"
            value={form.sequenceOrder}
            onChange={(e) =>
              handleChange('sequenceOrder', parseInt(e.target.value, 10) || 1)
            }
            inputProps={{ min: 1 }}
            disabled={!isNew}
          />

          <TextField
            fullWidth
            label="Description"
            multiline
            rows={2}
            value={form.description}
            onChange={(e) => handleChange('description', e.target.value)}
          />

          {/* Schedule */}
          <Typography
            variant="subtitle2"
            sx={{ fontWeight: 600, color: 'text.secondary', mt: 2 }}
          >
            Schedule
          </Typography>

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField
              fullWidth
              label="Planned Start Date"
              type="date"
              value={form.plannedStartDate}
              onChange={(e) => handleChange('plannedStartDate', e.target.value)}
              InputLabelProps={{ shrink: true }}
            />

            <TextField
              fullWidth
              label="Planned End Date"
              type="date"
              value={form.plannedEndDate}
              onChange={(e) => handleChange('plannedEndDate', e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Stack>

          {!isNew && (
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField
                fullWidth
                label="Actual Start Date"
                type="date"
                value={form.actualStartDate}
                onChange={(e) =>
                  handleChange('actualStartDate', e.target.value)
                }
                InputLabelProps={{ shrink: true }}
              />

              <TextField
                fullWidth
                label="Actual End Date"
                type="date"
                value={form.actualEndDate}
                onChange={(e) => handleChange('actualEndDate', e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Stack>
          )}

          {/* Budget */}
          <Typography
            variant="subtitle2"
            sx={{ fontWeight: 600, color: 'text.secondary', mt: 2 }}
          >
            Budget
          </Typography>

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField
              fullWidth
              label="Budget Amount"
              type="number"
              value={form.budgetAmount}
              onChange={(e) => handleChange('budgetAmount', e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">$</InputAdornment>
                ),
              }}
            />

            {!isNew && (
              <TextField
                fullWidth
                label="Actual Cost"
                type="number"
                value={form.actualCostAmount}
                onChange={(e) =>
                  handleChange('actualCostAmount', e.target.value)
                }
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">$</InputAdornment>
                  ),
                }}
              />
            )}
          </Stack>

          {/* Heritage */}
          <Typography
            variant="subtitle2"
            sx={{ fontWeight: 600, color: 'text.secondary', mt: 2 }}
          >
            Heritage & Conservation
          </Typography>

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <FormControl fullWidth>
              <InputLabel>Heritage Classification</InputLabel>
              <Select
                value={form.heritageClassification}
                label="Heritage Classification"
                onChange={(e) =>
                  handleChange(
                    'heritageClassification',
                    e.target.value as HeritageClassification,
                  )
                }
                disabled={!isNew}
              >
                {HERITAGE_CLASSIFICATIONS.map((c) => (
                  <MenuItem key={c.value} value={c.value}>
                    {c.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {!isNew && form.heritageApprovalRequired && (
              <TextField
                fullWidth
                label="Heritage Approval Status"
                value={form.heritageApprovalStatus}
                onChange={(e) =>
                  handleChange('heritageApprovalStatus', e.target.value)
                }
              />
            )}
          </Stack>

          {isNew && (
            <FormControlLabel
              control={
                <Checkbox
                  checked={form.heritageApprovalRequired}
                  onChange={(e) =>
                    handleChange('heritageApprovalRequired', e.target.checked)
                  }
                />
              }
              label="Heritage approval required"
            />
          )}

          {/* Occupancy */}
          <Typography
            variant="subtitle2"
            sx={{ fontWeight: 600, color: 'text.secondary', mt: 2 }}
          >
            Occupancy & Tenants
          </Typography>

          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            spacing={2}
            alignItems="center"
          >
            <FormControl fullWidth>
              <InputLabel>Occupancy Status</InputLabel>
              <Select
                value={form.occupancyStatus}
                label="Occupancy Status"
                onChange={(e) =>
                  handleChange(
                    'occupancyStatus',
                    e.target.value as OccupancyStatus,
                  )
                }
                disabled={!isNew}
              >
                {OCCUPANCY_STATUSES.map((s) => (
                  <MenuItem key={s.value} value={s.value}>
                    {s.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {isNew && (
              <Box sx={{ minWidth: 240 }}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={form.tenantCoordinationRequired}
                      onChange={(e) =>
                        handleChange(
                          'tenantCoordinationRequired',
                          e.target.checked,
                        )
                      }
                    />
                  }
                  label="Tenant coordination required"
                />
              </Box>
            )}
          </Stack>
        </Stack>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          Cancel
        </Button>
        <Button variant="contained" onClick={handleSubmit} disabled={saving}>
          {saving ? 'Saving...' : isNew ? 'Create Phase' : 'Save Changes'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
