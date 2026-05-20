import { alpha, Box, Divider, Grid, Stack, Typography } from '@mui/material'
import type { HeritageTracker } from '../../../../api/development'
import { GlassCard } from '../../../../components/canonical/GlassCard'

interface HeritageViewProps {
  data: HeritageTracker
}

export function HeritageView({ data }: HeritageViewProps) {
  return (
    <Stack spacing="var(--ob-space-200)">
      <GlassCard sx={{ p: 'var(--ob-space-200)' }}>
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          sx={{ mb: 'var(--ob-space-200)' }}
        >
          <Typography variant="h6">Heritage Preservation Status</Typography>
          <Typography
            variant="body2"
            sx={{
              px: 'var(--ob-space-200)',
              py: 'var(--ob-space-050)',
              backgroundColor: (t) =>
                data.overallApprovalStatus === 'approved'
                  ? alpha(t.palette.success.main, 0.12)
                  : data.overallApprovalStatus === 'pending'
                    ? alpha(t.palette.warning.main, 0.12)
                    : alpha(t.palette.error.main, 0.12),
              borderRadius: 'var(--ob-radius-sm)',
            }}
          >
            {data.overallApprovalStatus}
          </Typography>
        </Stack>
        <Typography variant="body2" color="text.secondary">
          Classification:{' '}
          <strong>{data.heritageClassification.replace(/_/g, ' ')}</strong>
        </Typography>
      </GlassCard>

      <Grid container spacing="var(--ob-space-200)">
        <Grid item xs={12} md={4}>
          <GlassCard sx={{ p: 'var(--ob-space-200)' }}>
            <Typography
              variant="subtitle2"
              sx={{
                fontWeight: 'var(--ob-font-weight-semibold)',
                mb: 'var(--ob-space-200)',
              }}
            >
              Required Approvals
            </Typography>
            <Stack spacing="var(--ob-space-100)">
              {data.requiredApprovals.map((approval, idx) => (
                <Typography key={idx} variant="body2">
                  • {approval}
                </Typography>
              ))}
            </Stack>
          </GlassCard>
        </Grid>
        <Grid item xs={12} md={4}>
          <GlassCard sx={{ p: 'var(--ob-space-200)' }}>
            <Typography
              variant="subtitle2"
              sx={{
                fontWeight: 'var(--ob-font-weight-semibold)',
                mb: 'var(--ob-space-200)',
                color: 'warning.main',
              }}
            >
              Preservation Risks
            </Typography>
            <Stack spacing="var(--ob-space-100)">
              {data.preservationRisks.map((risk, idx) => (
                <Typography key={idx} variant="body2">
                  • {risk}
                </Typography>
              ))}
            </Stack>
          </GlassCard>
        </Grid>
        <Grid item xs={12} md={4}>
          <GlassCard sx={{ p: 'var(--ob-space-200)' }}>
            <Typography
              variant="subtitle2"
              sx={{
                fontWeight: 'var(--ob-font-weight-semibold)',
                mb: 'var(--ob-space-200)',
                color: 'info.main',
              }}
            >
              Recommendations
            </Typography>
            <Stack spacing="var(--ob-space-100)">
              {data.recommendations.map((rec, idx) => (
                <Typography key={idx} variant="body2">
                  • {rec}
                </Typography>
              ))}
            </Stack>
          </GlassCard>
        </Grid>
      </Grid>

      <GlassCard sx={{ p: 'var(--ob-space-200)' }}>
        <Typography
          variant="subtitle1"
          sx={{
            fontWeight: 'var(--ob-font-weight-semibold)',
            mb: 'var(--ob-space-200)',
          }}
        >
          Heritage Phases
        </Typography>
        <Divider sx={{ mb: 'var(--ob-space-200)' }} />
        <Stack spacing="var(--ob-space-200)">
          {data.phases.map((phase) => (
            <Box
              key={phase.phaseId}
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                p: 'var(--ob-space-150)',
                backgroundColor: (t) =>
                  phase.approvalRequired
                    ? alpha(t.palette.warning.main, 0.08)
                    : t.palette.action.hover,
                borderRadius: 'var(--ob-radius-sm)',
                border: '1px solid',
                borderColor: 'divider',
              }}
            >
              <Box>
                <Typography
                  variant="body2"
                  sx={{ fontWeight: 'var(--ob-font-weight-medium)' }}
                >
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
                    px: 'var(--ob-space-150)',
                    py: 'var(--ob-space-050)',
                    backgroundColor: (t) =>
                      phase.approvalStatus === 'approved'
                        ? alpha(t.palette.success.main, 0.12)
                        : alpha(t.palette.warning.main, 0.12),
                    borderRadius: 'var(--ob-radius-sm)',
                  }}
                >
                  {phase.approvalStatus ?? 'Pending'}
                </Typography>
              )}
            </Box>
          ))}
        </Stack>
      </GlassCard>
    </Stack>
  )
}
