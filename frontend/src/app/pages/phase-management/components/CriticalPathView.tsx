import { alpha, Box, Grid, Paper, Stack, Typography } from '@mui/material'
import type { CriticalPathResult } from '../../../../api/development'

interface CriticalPathViewProps {
  data: CriticalPathResult
}

export function CriticalPathView({ data }: CriticalPathViewProps) {
  return (
    <Stack spacing={3}>
      <Paper variant="outlined" sx={{ p: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Critical Path Analysis
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Total Duration: <strong>{data.totalDuration} days</strong>
        </Typography>
        <Typography variant="body2" color="text.secondary">
          The critical path represents the longest sequence of dependent phases
          that determines the minimum project duration. Any delay in critical
          phases will delay the entire project.
        </Typography>
      </Paper>

      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography
              variant="subtitle1"
              sx={{ fontWeight: 600, mb: 2, color: 'error.main' }}
            >
              Critical Phases ({data.criticalPhases.length})
            </Typography>
            <Stack spacing={1}>
              {data.criticalPhases.map((phase) => (
                <Box
                  key={phase.phaseId}
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    p: 1,
                    backgroundColor: (t) => alpha(t.palette.error.main, 0.08),
                    borderRadius: 1,
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
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography
              variant="subtitle1"
              sx={{ fontWeight: 600, mb: 2, color: 'success.main' }}
            >
              Non-Critical Phases ({data.nonCriticalPhases.length})
            </Typography>
            <Stack spacing={1}>
              {data.nonCriticalPhases.map((phase) => (
                <Box
                  key={phase.phaseId}
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    p: 1,
                    backgroundColor: (t) => alpha(t.palette.success.main, 0.08),
                    borderRadius: 1,
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
