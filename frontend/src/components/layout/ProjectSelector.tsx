import { useCallback, useMemo, useState } from 'react'
import type { MouseEvent } from 'react'
import {
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Menu,
  MenuItem,
  Stack,
  TextField,
  Typography,
  alpha,
  useTheme,
} from '@mui/material'
import {
  AddCircleOutline as AddCircleOutlineIcon,
  FolderOpen as FolderOpenIcon,
  SwapHoriz as SwapHorizIcon,
} from '@mui/icons-material'

import { useProject } from '../../contexts/useProject'
import { useRouterController, useRouterParams } from '../../router'

export function ProjectSelector() {
  const theme = useTheme()
  const { navigate, path } = useRouterController()
  const { projectId: routeProjectId } = useRouterParams()
  const {
    currentProject,
    projects,
    isProjectLoading,
    projectError,
    setCurrentProject,
    clearProject,
    refreshProjects,
    createProject,
  } = useProject()

  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [projectName, setProjectName] = useState('')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  const open = Boolean(anchorEl)

  const selectedLabel = currentProject?.name ?? 'Select project'

  const handleOpenMenu = (event: MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
    void refreshProjects()
  }

  const handleCloseMenu = () => setAnchorEl(null)

  const handleClearSelection = useCallback(() => {
    clearProject()

    const segments = path.split('/').filter(Boolean)
    if (segments[0] === 'projects' && segments[1]) {
      const moduleSegment = segments[2] ?? ''
      const moduleFallbacks: Record<string, string> = {
        capture: '/app/capture',
        feasibility: '/app/asset-feasibility',
        finance: '/app/financial-control',
        phases: '/app/phase-management',
        team: '/app/team-coordination',
        regulatory: '/developers/regulatory',
      }
      navigate(moduleFallbacks[moduleSegment] ?? '/projects')
    }

    handleCloseMenu()
  }, [clearProject, navigate, path])

  const handleSelectProject = useCallback(
    (projectId: string) => {
      const match = projects.find((project) => project.id === projectId)
      const nextProject = match ?? {
        id: projectId,
        name: projectId,
      }
      setCurrentProject(nextProject)
      if (routeProjectId) {
        const updatedPath = path.replace(
          `/projects/${routeProjectId}`,
          `/projects/${projectId}`,
        )
        navigate(updatedPath)
      } else if (path.startsWith('/projects')) {
        navigate(`/projects/${projectId}`)
      }
      handleCloseMenu()
    },
    [navigate, path, projects, routeProjectId, setCurrentProject],
  )

  const handleCreateProject = async () => {
    if (!projectName.trim()) {
      setCreateError('Project name is required.')
      return
    }
    setCreating(true)
    setCreateError(null)
    try {
      const created = await createProject({ name: projectName.trim() })
      setProjectName('')
      setCreateOpen(false)
      setCurrentProject(created)
      navigate(`/projects/${created.id}`)
    } catch (error) {
      setCreateError(
        error instanceof Error ? error.message : 'Unable to create project.',
      )
    } finally {
      setCreating(false)
    }
  }

  const orderedProjects = useMemo(() => {
    if (!currentProject) {
      return projects
    }
    const others = projects.filter(
      (project) => project.id !== currentProject.id,
    )
    return [currentProject, ...others]
  }, [currentProject, projects])

  return (
    <>
      <Button
        variant="text"
        onClick={handleOpenMenu}
        startIcon={<FolderOpenIcon />}
        sx={{
          borderRadius: 'var(--ob-radius-pill)',
          px: 'var(--ob-space-150)',
          textTransform: 'none',
          fontWeight: 600,
          color: currentProject ? 'text.primary' : 'text.secondary',
          bgcolor: alpha(theme.palette.background.paper, 0.5),
          border: 1,
          borderColor: alpha(theme.palette.divider, 0.3),
          minWidth: 160,
          '&:hover': {
            bgcolor: alpha(theme.palette.background.paper, 0.7),
          },
        }}
      >
        {selectedLabel}
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleCloseMenu}
        PaperProps={{
          elevation: 10,
          sx: {
            mt: 'var(--ob-space-050)',
            borderRadius: 'var(--ob-radius-sm)',
            border: 1,
            borderColor: alpha(theme.palette.divider, 0.2),
            minWidth: 280,
          },
        }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
      >
        <Box sx={{ px: 'var(--ob-space-150)', py: 'var(--ob-space-100)' }}>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-xs)',
              letterSpacing: 'var(--ob-letter-spacing-wider)',
              textTransform: 'uppercase',
              color: 'text.secondary',
              fontWeight: 700,
            }}
          >
            Project Context
          </Typography>
          {projectError && (
            <Typography
              sx={{
                mt: 'var(--ob-space-050)',
                fontSize: 'var(--ob-font-size-xs)',
                color:
                  projectError.type === 'forbidden'
                    ? 'warning.main'
                    : 'error.main',
              }}
            >
              {projectError.message}
            </Typography>
          )}
        </Box>
        <Divider />
        {isProjectLoading && (
          <Box
            sx={{
              px: 'var(--ob-space-150)',
              py: 'var(--ob-space-150)',
            }}
          >
            <Stack direction="row" spacing={1} alignItems="center">
              <CircularProgress size={16} />
              <Typography variant="body2">Loading projects...</Typography>
            </Stack>
          </Box>
        )}
        {!isProjectLoading &&
          orderedProjects.map((project) => (
            <MenuItem
              key={project.id}
              selected={project.id === currentProject?.id}
              onClick={() => handleSelectProject(project.id)}
            >
              <Stack direction="row" spacing={1} alignItems="center">
                <SwapHorizIcon fontSize="small" />
                <Typography variant="body2">{project.name}</Typography>
              </Stack>
            </MenuItem>
          ))}
        {!isProjectLoading && projects.length === 0 && (
          <Box sx={{ px: 'var(--ob-space-150)', py: 'var(--ob-space-150)' }}>
            <Typography variant="body2" color="text.secondary">
              No projects yet.
            </Typography>
          </Box>
        )}
        <Divider />
        <MenuItem
          onClick={() => {
            setCreateOpen(true)
            handleCloseMenu()
          }}
        >
          <Stack direction="row" spacing={1} alignItems="center">
            <AddCircleOutlineIcon fontSize="small" />
            <Typography variant="body2">Create project</Typography>
          </Stack>
        </MenuItem>
        {currentProject && (
          <MenuItem onClick={handleClearSelection}>
            <Typography variant="body2" color="text.secondary">
              Clear selection
            </Typography>
          </MenuItem>
        )}
      </Menu>

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)}>
        <DialogTitle>Create Project</DialogTitle>
        <DialogContent>
          <TextField
            label="Project name"
            value={projectName}
            onChange={(event) => setProjectName(event.target.value)}
            fullWidth
            margin="dense"
          />
          {createError && (
            <Typography variant="body2" color="error" sx={{ mt: 1 }}>
              {createError}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)} disabled={creating}>
            Cancel
          </Button>
          <Button onClick={handleCreateProject} disabled={creating}>
            {creating ? 'Creating...' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  )
}
