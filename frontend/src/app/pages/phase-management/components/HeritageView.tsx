import {
  alpha,
  Box,
  Divider,
  Grid,
  Paper,
  Stack,
  Typography,
} from '@mui/material'
import type { HeritageTracker } from '../../../../api/development'

interface HeritageViewProps {
  data: HeritageTracker
}

export function HeritageView({ data }: HeritageViewProps) {
  return (
    <Stack spacing={3}>
      <Paper variant="outlined" sx={{ p: 3 }}>
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          sx={{ mb: 2 }}
        >
          <Typography variant="h6">Heritage Preservation Status</Typography>
          <Typography
            variant="body2"
            sx={{
              px: 2,
              py: 0.5,
              backgroundColor: (t) =>
                data.overallApprovalStatus === 'approved'
                  ? alpha(t.palette.success.main, 0.12)
                  : data.overallApprovalStatus === 'pending'
                    ? alpha(t.palette.warning.main, 0.12)
                    : alpha(t.palette.error.main, 0.12),
              borderRadius: 1,
            }}
          >
            {data.overallApprovalStatus}
          </Typography>
        </Stack>
        <Typography variant="body2" color="text.secondary">
          Classification:{' '}
          <strong>{data.heritageClassification.replace(/_/g, ' ')}</strong>
        </Typography>
      </Paper>

      <Grid container spacing={2}>
        <Grid item xs={12} md={4}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>
              Required Approvals
            </Typography>
            <Stack spacing={1}>
              {data.requiredApprovals.map((approval, idx) => (
                <Typography key={idx} variant="body2">
                  • {approval}
                </Typography>
              ))}
            </Stack>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography
              variant="subtitle2"
              sx={{ fontWeight: 600, mb: 2, color: 'warning.main' }}
            >
              Preservation Risks
            </Typography>
            <Stack spacing={1}>
              {data.preservationRisks.map((risk, idx) => (
                <Typography key={idx} variant="body2">
                  • {risk}
                </Typography>
              ))}
            </Stack>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography
              variant="subtitle2"
              sx={{ fontWeight: 600, mb: 2, color: 'info.main' }}
            >
              Recommendations
            </Typography>
            <Stack spacing={1}>
              {data.recommendations.map((rec, idx) => (
                <Typography key={idx} variant="body2">
                  • {rec}
                </Typography>
              ))}
            </Stack>
          </Paper>
        </Grid>
      </Grid>

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
          Heritage Phases
        </Typography>
        <Divider sx={{ mb: 2 }} />
        <Stack spacing={2}>
          {data.phases.map((phase) => (
            <Box
              key={phase.phaseId}
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                p: 1.5,
                backgroundColor: (t) =>
                  phase.approvalRequired
                    ? alpha(t.palette.warning.main, 0.08)
                    : t.palette.action.hover,
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'divider',
              }}
            >
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {phase.name}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {phase.heritageClassification.replace(/_/g, ' ')}
                </Typography>
              </Box>
              {phase.approvalRequired && (
                <Typography
                  variant="caption"
                  sx={{
                    px: 1.5,
                    py: 0.5,
                    backgroundColor: (t) =>
                      phase.approvalStatus === 'approved'
                        ? alpha(t.palette.success.main, 0.12)
                        : alpha(t.palette.warning.main, 0.12),
                    borderRadius: 1,
                  }}
                >
                  {phase.approvalStatus ?? 'Pending'}
                </Typography>
              )}
            </Box>
          ))}
        </Stack>
      </Paper>
    </Stack>
  )
}
