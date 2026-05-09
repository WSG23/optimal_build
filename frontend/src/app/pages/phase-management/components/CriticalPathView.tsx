import { alpha, Box, Grid, Paper, Stack, Typography } from '@mui/material'
import type { CriticalPathResult } from '../../../../api/development'

interface CriticalPathViewProps {
  data: CriticalPathResult
}

export function CriticalPathView({ data }: CriticalPathViewProps) {
  return (
    <Stack spacing="var(--ob-space-200)">
      <Paper variant="outlined" sx={{ p: 'var(--ob-space-200)' }}>
        <Typography variant="h6" sx={{ mb: 'var(--ob-space-200)' }}>
          Critical Path Analysis
        </Typography>
        <Typography variant="body1" sx={{ mb: 'var(--ob-space-200)' }}>
          Total Duration: <strong>{data.totalDuration} days</strong>
        </Typography>
        <Typography variant="body2" color="text.secondary">
          The critical path represents the longest sequence of dependent phases
          that determines the minimum project duration. Any delay in critical
          phases will delay the entire project.
        </Typography>
      </Paper>

      <Grid container spacing="var(--ob-space-200)">
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 'var(--ob-space-200)' }}>
            <Typography
              variant="subtitle1"
              sx={{
                fontWeight: 'var(--ob-font-weight-semibold)',
                mb: 'var(--ob-space-200)',
                color: 'error.main',
              }}
            >
              Critical Phases ({data.criticalPhases.length})
            </Typography>
            <Stack spacing="var(--ob-space-100)">
              {data.criticalPhases.map((phase) => (
                <Box
                  key={phase.phaseId}
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    p: 'var(--ob-space-100)',
                    backgroundColor: (t) => alpha(t.palette.error.main, 0.08),
                    borderRadius: 'var(--ob-radius-sm)',
                  }}
                >
                  <Typography variant="body2">{phase.name}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Float: {phase.float} days
                  </Typography>
                </Box>
              ))}
            </Stack>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 'var(--ob-space-200)' }}>
            <Typography
              variant="subtitle1"
              sx={{
                fontWeight: 'var(--ob-font-weight-semibold)',
                mb: 'var(--ob-space-200)',
                color: 'success.main',
              }}
            >
              Non-Critical Phases ({data.nonCriticalPhases.length})
            </Typography>
            <Stack spacing="var(--ob-space-100)">
              {data.nonCriticalPhases.map((phase) => (
                <Box
                  key={phase.phaseId}
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    p: 'var(--ob-space-100)',
                    backgroundColor: (t) => alpha(t.palette.success.main, 0.08),
                    borderRadius: 'var(--ob-radius-sm)',
                  }}
                >
                  <Typography variant="body2">{phase.name}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Float: {phase.float} days
                  </Typography>
                </Box>
              ))}
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Stack>
  )
}
