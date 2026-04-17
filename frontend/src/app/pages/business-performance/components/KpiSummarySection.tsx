import { type ReactNode } from 'react'
import { Box, Grid, Typography } from '@mui/material'
import AccessTime from '@mui/icons-material/AccessTime'
import AttachMoney from '@mui/icons-material/AttachMoney'
import Assessment from '@mui/icons-material/Assessment'
import { MetricTile } from '../../../../components/canonical/MetricTile'

interface OpenPipelineMetric {
  kind: 'loading' | 'pending' | 'value'
  text: string | ReactNode
}

interface KpiSummarySectionProps {
  analyticsLoading: boolean
  lastSnapshot: string
  openPipelineMetric: OpenPipelineMetric
  roiProjectCount: number
}

export function KpiSummarySection({
  analyticsLoading,
  lastSnapshot,
  openPipelineMetric,
  roiProjectCount,
}: KpiSummarySectionProps) {
  return (
    <Box className="ob-card-module ob-section-gap">
      <Typography
        variant="subtitle2"
        sx={{
          color: 'text.secondary',
          mb: 'var(--ob-space-200)',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
        }}
      >
        Key Metrics
      </Typography>
      <Grid
        container
        spacing="var(--ob-space-200)"
        className="bp-page__summary"
        role="region"
        aria-label="Key performance metrics"
      >
        <Grid item xs={12} sm={6} md={3}>
          <MetricTile
            label="Last Snapshot"
            value={analyticsLoading ? '-' : lastSnapshot}
            icon={<AccessTime fontSize="small" />}
            variant="compact"
          />
        </Grid>
        <Grid item xs={12} sm={12} md={6}>
          <MetricTile
            label="Open Pipeline Value"
            value={
              openPipelineMetric.kind === 'pending' ? (
                <Box
                  component="span"
                  sx={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    color: 'var(--ob-color-text-secondary)',
                    fontSize: '0.34em',
                    fontWeight: 'var(--ob-font-weight-semibold)',
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                  }}
                >
                  {openPipelineMetric.text}
                </Box>
              ) : (
                openPipelineMetric.text
              )
            }
            icon={<AttachMoney fontSize="small" />}
            variant="hero"
            trend={openPipelineMetric.kind === 'value' ? '+12%' : undefined}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricTile
            label="ROI Projects Tracked"
            value={analyticsLoading ? '-' : roiProjectCount}
            icon={<Assessment fontSize="small" />}
            variant="compact"
          />
        </Grid>
      </Grid>
    </Box>
  )
}
