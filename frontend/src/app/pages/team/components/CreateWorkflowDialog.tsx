import React, { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Typography,
  IconButton,
  MenuItem,
} from '@mui/material'
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material'
import { workflowApi, ApprovalWorkflow } from '../../../../api/workflow' // Fixed import

interface CreateWorkflowDialogProps {
  open: boolean
  onClose: () => void
  projectId: string
  onSuccess: (workflow: ApprovalWorkflow) => void
}

export const CreateWorkflowDialog: React.FC<CreateWorkflowDialogProps> = ({
  open,
  onClose,
  projectId,
  onSuccess,
}) => {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [type, setType] = useState('design_review')
  const [steps, setSteps] = useState<{ name: string; role: string }[]>([
    { name: 'Review', role: 'consultant' },
  ])
  const [creating, setCreating] = useState(false)

  const handleAddStep = () => {
    setSteps([...steps, { name: '', role: 'consultant' }])
  }

  const handleRemoveStep = (index: number) => {
    setSteps(steps.filter((_, i) => i !== index))
  }

  const handleStepChange = (
    index: number,
    field: 'name' | 'role',
    value: string,
  ) => {
    const newSteps = [...steps]
    newSteps[index] = { ...newSteps[index], [field]: value }
    setSteps(newSteps)
  }

  const handleSubmit = async () => {
    if (!title || steps.some((s) => !s.name)) return

    setCreating(true)
    try {
      const newWorkflow = await workflowApi.createWorkflow(projectId, {
        title,
        description,
        workflow_type: type,
        steps: steps.map((s) => ({
          name: s.name,
          required_role: s.role, // Backend expects required_role enum value
        })),
      })
      onSuccess(newWorkflow)
      // Reset form
      setTitle('')
      setDescription('')
      setSteps([{ name: 'Review', role: 'consultant' }])
    } catch (err) {
      console.error(err)
      alert('Failed to create workflow')
    } finally {
      setCreating(false)
    }
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{ sx: { bgcolor: '#1A1D1F' } }}
    >
      <DialogTitle>Create Approval Workflow</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 1 }}>
          <TextField
            label="Workflow Title"
            fullWidth
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <TextField
            label="Description"
            fullWidth
            multiline
            rows={2}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <TextField
            select
            label="Type"
            fullWidth
            value={type}
            onChange={(e) => setType(e.target.value)}
          >
            <MenuItem value="design_review">Design Review</MenuItem>
            <MenuItem value="feasibility_signoff">
              Feasibility Sign-off
            </MenuItem>
            <MenuItem value="budget_approval">Budget Approval</MenuItem>
          </TextField>

          <Box>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Approval Steps
            </Typography>
            {steps.map((step, index) => (
              <Box
                key={index}
                sx={{
                  display: 'flex',
                  gap: 2,
                  mb: 2,
                  alignItems: 'flex-start',
                }}
              >
                <Typography
                  sx={{ mt: 2, color: 'text.secondary', minWidth: 20 }}
                >
                  {index + 1}.
                </Typography>
                <TextField
                  label="Step Name"
                  value={step.name}
                  onChange={(e) =>
                    handleStepChange(index, 'name', e.target.value)
                  }
                  fullWidth
                  size="small"
                />
                <TextField
                  select
                  label="Approver Role"
                  value={step.role}
                  onChange={(e) =>
                    handleStepChange(index, 'role', e.target.value)
                  }
                  sx={{ minWidth: 150 }}
                  size="small"
                >
                  <MenuItem value="consultant">Consultant</MenuItem>
                  <MenuItem value="architect">Architect</MenuItem>
                  <MenuItem value="engineer">Engineer</MenuItem>
                  <MenuItem value="developer">Developer</MenuItem>
                </TextField>
                <IconButton
                  onClick={() => handleRemoveStep(index)}
                  disabled={steps.length === 1}
                >
                  <DeleteIcon />
                </IconButton>
              </Box>
            ))}
            <Button startIcon={<AddIcon />} onClick={handleAddStep}>
              Add Step
            </Button>
          </Box>
        </Box>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={creating || !title}
          sx={{
            background: 'linear-gradient(135deg, #FF3366 0%, #FF6B3D 100%)',
          }}
        >
          {creating ? 'Creating...' : 'Create Workflow'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
