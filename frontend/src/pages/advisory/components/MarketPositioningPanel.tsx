import { Box, Typography, Grid, Chip } from '@mui/material'
import { GlassCard } from '../../../components/canonical/GlassCard'
import { StatusChip } from '../../../components/canonical/StatusChip'
import type { MarketPositioning } from '../../api/advisory'

interface MarketPositioningPanelProps {
  data: MarketPositioning
}

export function MarketPositioningPanel({ data }: MarketPositioningPanelProps) {
  return (
    <GlassCard className="advisory-panel">
      <Box
        sx={{
          p: 'var(--ob-space-200)',
          borderBottom: '1px solid var(--ob-color-border-subtle)',
        }}
      >
        <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600 }}>
          Market Positioning
        </Typography>
      </Box>

      <Box sx={{ p: 'var(--ob-space-300)' }}>
        <Grid container spacing="var(--ob-space-300)">
          {/* Header Metric */}
          <Grid item xs={12} md={4}>
            <Box
              sx={{
                p: 'var(--ob-space-200)',
                borderRadius: 'var(--ob-radius-sm)',
                bgcolor: 'var(--ob-background-surface-1)',
                border: '1px solid var(--ob-color-border-subtle)',
                textAlign: 'center',
              }}
            >
              <Typography
                variant="overline"
                sx={{
                  color: 'var(--ob-color-text-secondary)',
                  display: 'block',
                }}
              >
                Target Tier
              </Typography>
              <Typography
                variant="h4"
                sx={{
                  color: 'var(--ob-color-brand-primary)',
                  fontWeight: 700,
                  mt: 'var(--ob-space-100)',
                  mb: 'var(--ob-space-100)',
                }}
              >
                {data.market_tier}
              </Typography>
              <StatusChip status="success">Strategic Fit</StatusChip>
            </Box>
          </Grid>

          {/* Pricing Guidance */}
          <Grid item xs={12} md={8}>
            <Box sx={{ mb: 'var(--ob-space-300)' }}>
              <Typography
                variant="subtitle2"
                sx={{ mb: 'var(--ob-space-150)', fontWeight: 600 }}
              >
                Pricing Guidance (PSF)
              </Typography>
              <Box
                sx={{
                  display: 'flex',
                  gap: 'var(--ob-space-200)',
                  flexWrap: 'wrap',
                }}
              >
                {Object.entries(data.pricing_guidance).map(([key, range]) => (
                  <GlassCard
                    key={key}
                    variant="seamless"
                    sx={{
                      p: 'var(--ob-space-200)',
                      minWidth: 140,
                      bgcolor: 'var(--ob-color-table-row-alt)',
                    }}
                  >
                    <Typography
                      variant="caption"
                      sx={{
                        textTransform: 'uppercase',
                        color: 'var(--ob-color-text-secondary)',
                      }}
                    >
                      {key}
                    </Typography>
                    <Typography
                      variant="body1"
                      sx={{ fontWeight: 600, mt: 'var(--ob-space-50)' }}
                    >
                      {range.target_min.toLocaleString()} –{' '}
                      {range.target_max.toLocaleString()}
                    </Typography>
                  </GlassCard>
                ))}
              </Box>
            </Box>

            {/* Segments */}
            <Box>
              <Typography
                variant="subtitle2"
                sx={{ mb: 'var(--ob-space-150)', fontWeight: 600 }}
              >
                Target Segments
              </Typography>
              <Box
                sx={{
                  display: 'flex',
                  gap: 'var(--ob-space-100)',
                  flexWrap: 'wrap',
                }}
              >
                {data.target_segments.map((seg, i) => (
                  <Chip
                    key={i}
                    label={`${seg.segment} (${seg.weight_pct}%)`}
                    variant="outlined"
                    sx={{
                      borderColor: 'var(--ob-color-border-subtle)',
                      color: 'var(--ob-color-text-primary)',
                      bgcolor: 'var(--ob-color-table-header)',
                    }}
                  />
                ))}
              </Box>
            </Box>
          </Grid>

          {/* Messaging */}
          {data.messaging.length > 0 && (
            <Grid item xs={12}>
              <Box
                sx={{
                  pt: 'var(--ob-space-200)',
                  borderTop: '1px solid var(--ob-color-border-subtle)',
                }}
              >
                <Typography
                  variant="subtitle2"
                  sx={{ mb: 'var(--ob-space-100)', fontWeight: 600 }}
                >
                  Key Messaging
                </Typography>
                <Grid container spacing="var(--ob-space-200)">
                  {data.messaging.map((msg, i) => (
                    <Grid item xs={12} md={6} key={i}>
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'baseline',
                          gap: 'var(--ob-space-150)',
                        }}
                      >
                        <Box
                          sx={{
                            width: 6,
                            height: 6,
                            borderRadius: '50%',
                            bgcolor: 'var(--ob-color-brand-primary)',
                          }}
                        />
                        <Typography
                          variant="body2"
                          sx={{ color: 'var(--ob-color-text-secondary)' }}
                        >
                          {msg}
                        </Typography>
                      </Box>
                    </Grid>
                  ))}
                </Grid>
              </Box>
            </Grid>
          )}
        </Grid>
      </Box>
    </GlassCard>
  )
}
