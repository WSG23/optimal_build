import { Box, Typography, Grid, Chip } from '@mui/material'
import { GlassCard } from '../../../components/canonical/GlassCard'
import { StatusChip } from '../../../components/canonical/StatusChip'
import type { AdvisoryMarketPositioning } from '../../../api/advisory'

interface MarketPositioningPanelProps {
  data: AdvisoryMarketPositioning
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
        <Typography
          variant="h6"
          sx={{
            fontSize: 'var(--ob-font-size-base)',
            fontWeight: 'var(--ob-font-weight-semibold)',
          }}
        >
          Market Positioning
        </Typography>
      </Box>

      <Box sx={{ p: 'var(--ob-space-200)' }}>
        <Grid container spacing="var(--ob-space-200)">
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
                  fontWeight: 'var(--ob-font-weight-bold)',
                  mt: 'var(--ob-space-100)',
                  mb: 'var(--ob-space-100)',
                }}
              >
                {data.market_tier}
              </Typography>
              <StatusChip status="brand">Strategic Fit</StatusChip>
            </Box>
          </Grid>

          {/* Pricing Guidance */}
          <Grid item xs={12} md={8}>
            <Box sx={{ mb: 'var(--ob-space-200)' }}>
              <Typography
                variant="subtitle2"
                sx={{
                  mb: 'var(--ob-space-150)',
                  fontWeight: 'var(--ob-font-weight-semibold)',
                }}
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
                      bgcolor: 'rgba(255,255,255,0.02)',
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
                      sx={{
                        fontWeight: 'var(--ob-font-weight-semibold)',
                        mt: 'var(--ob-space-050)',
                      }}
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
                sx={{
                  mb: 'var(--ob-space-150)',
                  fontWeight: 'var(--ob-font-weight-semibold)',
                }}
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
                      bgcolor: 'rgba(245, 235, 220, 0.03)',
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
                  sx={{
                    mb: 'var(--ob-space-100)',
                    fontWeight: 'var(--ob-font-weight-semibold)',
                  }}
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
