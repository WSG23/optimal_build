import { useState } from 'react'
import {
  Box,
  Button,
  Chip,
  Container,
  Divider,
  Grid,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import {
  Assignment,
  Business,
  Speed,
  Timeline,
  Feedback,
  Send,
} from '@mui/icons-material'

import type {
  AdvisorySummary,
  AdvisoryFeedbackPayload,
  SalesVelocityResponse,
} from '../../../api/advisory'
import {
  fetchAdvisorySummary,
  submitAdvisoryFeedback,
  computeSalesVelocity,
} from '../../../api/advisory'

// Canonical Components
import { AnimatedPageHeader } from '../../../components/canonical/AnimatedPageHeader'
import { GlassCard } from '../../../components/canonical/GlassCard'
import { HeroMetric } from '../../../components/canonical/HeroMetric'

export function AdvisoryPage() {
  const [propertyId, setPropertyId] = useState('')
  const [summary, setSummary] = useState<AdvisorySummary | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [feedbackOpen, setFeedbackOpen] = useState(false)
  const [feedbackForm, setFeedbackForm] = useState<AdvisoryFeedbackPayload>({
    sentiment: 'neutral',
    notes: '',
    channel: '',
  })
  const [submitting, setSubmitting] = useState(false)
  const [velocityInput, setVelocityInput] = useState<{
    jurisdiction: string;
    asset_type: string;
    price_band: string;
    units_planned: number | null;
    launch_window: string;
    inventory_months: string;
    recent_absorption: string;
  }>({
    jurisdiction: 'SG',
    asset_type: 'residential',
    price_band: '1800-2200_psf',
    units_planned: 200,
    launch_window: '2025-Q2',
    inventory_months: '',
    recent_absorption: '',
  })
  const [velocityResult, setVelocityResult] = useState<SalesVelocityResponse | null>(null)
  const [velocityError, setVelocityError] = useState<string | null>(null)
  const [velocityLoading, setVelocityLoading] = useState(false)

  const parseNumber = (value: string): number | null => {
    const trimmed = value.trim()
    if (trimmed === '') return null
    const parsed = Number(trimmed)
    return Number.isFinite(parsed) ? parsed : null
  }

  async function handleLoad() {
    if (!propertyId.trim()) return

    setLoading(true)
    setError(null)
    try {
      const data = await fetchAdvisorySummary(propertyId.trim())
      setSummary(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load advisory data')
      setSummary(null)
    } finally {
      setLoading(false)
    }
  }

  async function handleSubmitFeedback(e: React.FormEvent) {
    e.preventDefault()
    if (!propertyId.trim() || !feedbackForm.notes.trim()) return

    setSubmitting(true)
    try {
      const newFeedback = await submitAdvisoryFeedback(propertyId.trim(), feedbackForm)
      if (summary) {
        setSummary({
          ...summary,
          feedback: [newFeedback, ...summary.feedback],
        })
      }
      setFeedbackForm({ sentiment: 'neutral', notes: '', channel: '' })
      setFeedbackOpen(false)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to submit feedback')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleComputeVelocity() {
    setVelocityLoading(true)
    setVelocityError(null)
    try {
      const payload = {
        jurisdiction: velocityInput.jurisdiction,
        asset_type: velocityInput.asset_type,
        price_band: velocityInput.price_band || null,
        units_planned: velocityInput.units_planned || null,
        launch_window: velocityInput.launch_window || null,
        inventory_months: parseNumber(velocityInput.inventory_months),
        recent_absorption: parseNumber(velocityInput.recent_absorption),
      }
      const result = await computeSalesVelocity(payload)
      setVelocityResult(result)
    } catch (err) {
      setVelocityError(
        err instanceof Error ? err.message : 'Failed to compute sales velocity',
      )
      setVelocityResult(null)
    } finally {
      setVelocityLoading(false)
    }
  }

  return (
    <Box sx={{ pb: 8 }}>
      <Box sx={{ p: 3 }}>
        <AnimatedPageHeader
            title="Advisory Services"
            subtitle="Development strategy insights and market positioning"
            breadcrumbs={[
                { label: 'Dashboard', href: '/' },
                { label: 'Advisory' }
            ]}
        />

        <Container maxWidth="xl" sx={{ mt: 3 }}>
            {/* Search Section */}
            <GlassCard sx={{ p: 3, mb: 4 }}>
                <Typography variant="h6" gutterBottom>Load property analysis</Typography>
                <Stack direction="row" spacing={2}>
                    <TextField
                        fullWidth
                        variant="outlined"
                        placeholder="Enter property identifier"
                        value={propertyId}
                        onChange={(e) => setPropertyId(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter') handleLoad() }}
                        disabled={loading}
                        size="small"
                        InputProps={{
                            sx: { fontFamily: 'monospace' }
                        }}
                    />
                    <Button
                        variant="contained"
                        onClick={handleLoad}
                        disabled={loading || !propertyId.trim()}
                        startIcon={loading ? <Speed className="fa-spin" /> : <Assignment />}
                    >
                        {loading ? 'Loading...' : 'Load'}
                    </Button>
                </Stack>
                {error && (
                    <Typography color="error" variant="body2" sx={{ mt: 1 }}>
                        {error}
                    </Typography>
                )}
            </GlassCard>

            {summary && (
                <Stack spacing={4}>
                    {/* Asset Mix Strategy */}
                    <Box>
                        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
                           <Typography variant="h5" fontWeight={600}>Asset Mix Strategy</Typography>
                            {summary.asset_mix.total_programmable_gfa_sqm && (
                                <Chip
                                    label={`Total Programmable GFA: ${summary.asset_mix.total_programmable_gfa_sqm.toLocaleString()} m²`}
                                    variant="outlined"
                                    color="primary"
                                />
                            )}
                        </Stack>

                        <Grid container spacing={3}>
                            {summary.asset_mix.mix_recommendations.map((segment, idx) => (
                                <Grid item xs={12} md={4} key={idx}>
                                    <GlassCard sx={{ height: '100%', p: 3 }} hoverEffect>
                                        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
                                            <Typography variant="h6">{segment.use}</Typography>
                                            <Typography variant="h4" color="primary.main">
                                                {(segment.allocation_pct * 100).toFixed(0)}%
                                            </Typography>
                                        </Stack>
                                        {segment.target_gfa_sqm && (
                                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                                Target GFA: {segment.target_gfa_sqm.toLocaleString()} m²
                                            </Typography>
                                        )}
                                        <Typography variant="body1" sx={{ mt: 2 }}>
                                            {segment.rationale}
                                        </Typography>
                                    </GlassCard>
                                </Grid>
                            ))}
                        </Grid>
                    </Box>

                    {/* Market Positioning */}
                    <Box>
                        <Typography variant="h5" fontWeight={600} gutterBottom>Market Positioning</Typography>
                        <GlassCard sx={{ p: 3 }}>
                             <Stack direction="row" spacing={2} mb={3}>
                                <Chip
                                    label={`Market Tier: ${summary.market_positioning.market_tier}`}
                                    color="secondary"
                                    icon={<Business />}
                                />
                             </Stack>

                             <Typography variant="h6" gutterBottom>Pricing Guidance</Typography>
                             <Grid container spacing={2}>
                                {Object.entries(summary.market_positioning.pricing_guidance).map(
                                    ([useType, pricing]) => (
                                    <Grid item xs={12} sm={6} md={3} key={useType}>
                                        <Box sx={{
                                            p: 2,
                                            border: '1px solid',
                                            borderColor: 'divider',
                                            borderRadius: 2
                                        }}>
                                            <Typography variant="subtitle1" fontWeight={600} gutterBottom textTransform="capitalize">
                                                {useType}
                                            </Typography>
                                            {Object.entries(pricing).map(([key, value]) => (
                                                <Stack key={key} direction="row" justifyContent="space-between" mb={0.5}>
                                                    <Typography variant="caption" color="text.secondary" textTransform="capitalize">{key.replace('_', ' ')}</Typography>
                                                    <Typography variant="caption" fontWeight={600}>${value.toLocaleString()}</Typography>
                                                </Stack>
                                            ))}
                                        </Box>
                                    </Grid>
                                    )
                                )}
                             </Grid>
                        </GlassCard>
                    </Box>

                    {/* Absorption Forecast */}
                    <Box>
                         <Typography variant="h5" fontWeight={600} gutterBottom>Absorption Forecast</Typography>
                         <Grid container spacing={3} mb={3}>
                            <Grid item xs={12} sm={4}>
                                <HeroMetric
                                    label="Time to Stabilize"
                                    value={String(summary.absorption_forecast.expected_months_to_stabilize)}
                                    variant="glass"
                                    delay={100}
                                />
                            </Grid>
                            <Grid item xs={12} sm={4}>
                                <HeroMetric
                                    label="Monthly Velocity"
                                    value={String(summary.absorption_forecast.monthly_velocity_target)}
                                    variant="glass"
                                    delay={200}
                                />
                            </Grid>
                             <Grid item xs={12} sm={4}>
                                <HeroMetric
                                    label="Confidence"
                                    value={summary.absorption_forecast.confidence}
                                    variant="glass"
                                    delay={300}
                                />
                            </Grid>
                         </Grid>

                         <GlassCard sx={{ p: 3, overflowX: 'auto' }}>
                            <Stack direction="row" spacing={4} sx={{ minWidth: 600 }}>
                                {summary.absorption_forecast.timeline.map((milestone, idx) => (
                                    <Box key={idx} sx={{ position: 'relative', minWidth: 120, textAlign: 'center' }}>
                                        <Typography variant="caption" display="block" color="text.secondary" mb={1}>
                                            M{milestone.month}
                                        </Typography>
                                        <Box sx={{
                                            width: 12,
                                            height: 12,
                                            borderRadius: '50%',
                                            bgcolor: 'primary.main',
                                            mx: 'auto',
                                            mb: 1
                                        }} />
                                        <Typography variant="subtitle2" gutterBottom>{milestone.milestone}</Typography>
                                        <Typography variant="caption" color="success.main">
                                            {(milestone.expected_absorption_pct * 100).toFixed(0)}% absorbed
                                        </Typography>
                                    </Box>
                                ))}
                            </Stack>
                         </GlassCard>
                    </Box>

                    {/* Sales Velocity Model (Calculator) */}
                    <Box>
                        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
                             <Box>
                                <Typography variant="h5" fontWeight={600}>Sales Velocity Model</Typography>
                                <Typography variant="body2" color="text.secondary">Forecast launch cadence with inventory and velocity benchmarks.</Typography>
                             </Box>
                             <Button
                                variant="contained"
                                onClick={handleComputeVelocity}
                                disabled={velocityLoading}
                                startIcon={velocityLoading ? <Speed className="fa-spin" /> : <Timeline />}
                             >
                                {velocityLoading ? 'Computing...' : 'Run forecast'}
                             </Button>
                        </Stack>

                        <GlassCard sx={{ p: 3 }}>
                            <Grid container spacing={3}>
                                {/* Inputs */}
                                <Grid item xs={12} md={3}>
                                    <Stack spacing={2}>
                                        <TextField select label="Jurisdiction" value={velocityInput.jurisdiction} onChange={(e) => setVelocityInput({...velocityInput, jurisdiction: e.target.value})} fullWidth size="small">
                                            <MenuItem value="SG">Singapore</MenuItem>
                                            <MenuItem value="SEA">Seattle</MenuItem>
                                        </TextField>
                                         <TextField select label="Asset Type" value={velocityInput.asset_type} onChange={(e) => setVelocityInput({...velocityInput, asset_type: e.target.value})} fullWidth size="small">
                                            <MenuItem value="residential">Residential</MenuItem>
                                            <MenuItem value="mixed_use">Mixed-use</MenuItem>
                                        </TextField>
                                        <TextField label="Price Band" value={velocityInput.price_band} onChange={(e) => setVelocityInput({...velocityInput, price_band: e.target.value})} fullWidth size="small" />
                                        <TextField label="Units Planned" type="number" value={velocityInput.units_planned ?? ''} onChange={(e) => setVelocityInput({...velocityInput, units_planned: Number(e.target.value)})} fullWidth size="small" />
                                    </Stack>
                                </Grid>

                                {/* Results Area */}
                                <Grid item xs={12} md={9}>
                                    {velocityError && <Typography color="error">{velocityError}</Typography>}
                                    {velocityResult ? (
                                        <Stack spacing={3}>
                                            <Grid container spacing={2}>
                                                <Grid item xs={4}>
                                                    <HeroMetric label="Velocity" value={`${velocityResult.forecast.velocity_units_per_month ?? '—'} units/mo`} variant="glass" />
                                                </Grid>
                                                <Grid item xs={4}>
                                                    <HeroMetric label="Absorption" value={`${velocityResult.forecast.absorption_months ?? '—'} months`} variant="glass" />
                                                </Grid>
                                                 <Grid item xs={4}>
                                                    <HeroMetric label="Confidence" value={`${(velocityResult.forecast.confidence * 100).toFixed(0)}%`} variant="glass" />
                                                </Grid>
                                            </Grid>

                                            {velocityResult.risks.length > 0 && (
                                                <Stack direction="row" spacing={1}>
                                                    {velocityResult.risks.map((risk, idx) => (
                                                        <Chip key={idx} label={`${risk.label} (${risk.level})`} color={risk.level === 'high' ? 'error' : 'warning'} variant="outlined" />
                                                    ))}
                                                </Stack>
                                            )}
                                        </Stack>
                                    ) : (
                                        <Box sx={{
                                            height: '100%',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            opacity: 0.5
                                        }}>
                                            <Typography>Run forecast to see predictions</Typography>
                                        </Box>
                                    )}
                                </Grid>
                            </Grid>
                        </GlassCard>
                    </Box>

                    {/* Feedback Loop */}
                    <Box>
                        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
                             <Typography variant="h5" fontWeight={600}>Market Feedback</Typography>
                             <Button variant="outlined" startIcon={<Feedback />} onClick={() => setFeedbackOpen(!feedbackOpen)}>
                                {feedbackOpen ? 'Cancel' : 'Add Feedback'}
                             </Button>
                        </Stack>

                        {feedbackOpen && (
                             <GlassCard sx={{ p: 3, mb: 3, border: '1px solid', borderColor: 'primary.main' }}>
                                <form onSubmit={handleSubmitFeedback}>
                                    <Stack spacing={2}>
                                        <TextField select label="Sentiment" value={feedbackForm.sentiment} onChange={(e) => setFeedbackForm({...feedbackForm, sentiment: e.target.value as any})} fullWidth>
                                            <MenuItem value="positive">Positive</MenuItem>
                                            <MenuItem value="neutral">Neutral</MenuItem>
                                            <MenuItem value="negative">Negative</MenuItem>
                                        </TextField>
                                        <TextField multiline rows={4} label="Notes" value={feedbackForm.notes} onChange={(e) => setFeedbackForm({...feedbackForm, notes: e.target.value})} fullWidth placeholder="Enter feedback..." />
                                        <Button type="submit" variant="contained" disabled={submitting || !feedbackForm.notes.trim()} startIcon={<Send />}>
                                            Submit Feedback
                                        </Button>
                                    </Stack>
                                </form>
                             </GlassCard>
                        )}

                        <GlassCard sx={{ p: 0 }}>
                            {summary.feedback.length === 0 ? (
                                <Box p={4} textAlign="center">
                                    <Typography color="text.secondary">No feedback recorded yet</Typography>
                                </Box>
                            ) : (
                                <Stack divider={<Divider />}>
                                    {summary.feedback.map((item) => (
                                        <Box key={item.id} p={2}>
                                            <Stack direction="row" justifyContent="space-between" mb={1}>
                                                <Chip label={item.sentiment} size="small" color={item.sentiment === 'positive' ? 'success' : item.sentiment === 'negative' ? 'error' : 'default'} />
                                                <Typography variant="caption" color="text.secondary">{new Date(item.created_at).toLocaleString()}</Typography>
                                            </Stack>
                                            <Typography variant="body2">{item.notes}</Typography>
                                        </Box>
                                    ))}
                                </Stack>
                            )}
                        </GlassCard>
                    </Box>
                </Stack>
            )}

            {/* Empty State */}
            {!summary && !loading && (
                <GlassCard sx={{ p: 8, textAlign: 'center', mt: 4 }}>
                    <Typography variant="h1" sx={{ mb: 2 }}>📊</Typography>
                    <Typography variant="h5" gutterBottom>No advisory data loaded</Typography>
                    <Typography color="text.secondary">Enter a property ID above to view development insights</Typography>
                </GlassCard>
            )}
        </Container>
      </Box>
    </Box>
  )
}
