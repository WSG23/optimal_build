/**
 * SaveProjectDialog - Dialog for saving capture as a new or existing project
 *
 * Extracted from DeveloperResults to reduce file size.
 */

import {
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
  Stack,
  Select,
  MenuItem,
  FormControl,
  Typography,
} from '@mui/material'

import { Button } from '../../../../components/canonical/Button'

export interface SaveProjectDialogProps {
  open: boolean
  saveMode: 'new' | 'existing'
  projectNameInput: string
  existingProjectId: string
  saveError: string | null
  savingProject: boolean
  projects: Array<{ id: string; name: string }>
  suggestedProjectName: string
  onClose: () => void
  onSaveModeChange: (mode: 'new' | 'existing') => void
  onProjectNameChange: (name: string) => void
  onExistingProjectIdChange: (id: string) => void
  onSave: () => void
}

export function SaveProjectDialog({
  open,
  saveMode,
  projectNameInput,
  existingProjectId,
  saveError,
  savingProject,
  projects,
  suggestedProjectName,
  onClose,
  onSaveModeChange,
  onProjectNameChange,
  onExistingProjectIdChange,
  onSave,
}: SaveProjectDialogProps) {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Save Capture as Project</DialogTitle>
      <DialogContent>
        <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
          <Button
            variant={saveMode === 'new' ? 'primary' : 'secondary'}
            onClick={() => {
              onSaveModeChange('new')
              onProjectNameChange(suggestedProjectName)
            }}
          >
            Create New
          </Button>
          <Button
            variant={saveMode === 'existing' ? 'primary' : 'secondary'}
            onClick={() => onSaveModeChange('existing')}
          >
            Use Existing
          </Button>
        </Stack>
        {saveMode === 'new' ? (
          <TextField
            label="Project name"
            value={projectNameInput}
            onChange={(event) => onProjectNameChange(event.target.value)}
            fullWidth
          />
        ) : (
          <FormControl fullWidth>
            <Select
              value={existingProjectId}
              displayEmpty
              onChange={(event) =>
                onExistingProjectIdChange(String(event.target.value))
              }
            >
              <MenuItem value="">
                <em>Select a project</em>
              </MenuItem>
              {projects.map((project) => (
                <MenuItem key={project.id} value={project.id}>
                  {project.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
        {saveError && (
          <Typography color="error" variant="body2" sx={{ mt: 1 }}>
            {saveError}
          </Typography>
        )}
      </DialogContent>
      <DialogActions>
        <Button variant="ghost" onClick={onClose} disabled={savingProject}>
          Cancel
        </Button>
        <Button variant="primary" onClick={onSave} disabled={savingProject}>
          {savingProject ? 'Saving...' : 'Save Project'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
