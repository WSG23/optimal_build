import { useState } from 'react'
import {
  Box,
  Button,
  Chip,
  Divider,
  Grid,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import Assignment from '@mui/icons-material/Assignment'
import Business from '@mui/icons-material/Business'
import Speed from '@mui/icons-material/Speed'
import Timeline from '@mui/icons-material/Timeline'
import Feedback from '@mui/icons-material/Feedback'
import Send from '@mui/icons-material/Send'

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
import { Card } from '../../../components/canonical/Card'
import { EmptyState } from '../../../components/canonical'
import { MetricTile } from '../../../components/canonical/MetricTile'

function toUserFacingAdvisoryError(error: unknown): string {
  if (!(error instanceof Error)) {
    return 'Unable to load advisory data right now.'
  }
  if (/422|404/.test(error.message)) {
    return 'Property not found. Check the property ID and try again.'
  }
  return error.message
}

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
    jurisdiction: string
    asset_type: string
    price_band: string
    units_planned: number | null
    launch_window: string
    inventory_months: string
    recent_absorption: string
  }>({
    jurisdiction: 'SG',
    asset_type: 'residential',
    price_band: '1800-2200_psf',
    units_planned: 200,
    launch_window: '2025-Q2',
    inventory_months: '',
    recent_absorption: '',
  })
  const [velocityResult, setVelocityResult] =
    useState<SalesVelocityResponse | null>(null)
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
      setError(toUserFacingAdvisoryError(err))
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
      const newFeedback = await submitAdvisoryFeedback(
        propertyId.trim(),
        feedbackForm,
      )
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
    <Box sx={{ pb: 'var(--ob-space-400)', maxWidth: 1200, mx: 'auto' }}>
      {/* Search Section */}
      <Card
        variant="default"
        sx={{ p: 'var(--ob-space-150)', mb: 'var(--ob-space-200)' }}
      >
        <Typography variant="h6" gutterBottom>
          Load property analysis
        </Typography>
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          spacing="var(--ob-space-100)"
        >
          <TextField
            fullWidth
            variant="outlined"
            label="Property identifier"
            placeholder="Enter property identifier"
            value={propertyId}
            onChange={(e) => setPropertyId(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleLoad()
            }}
            disabled={loading}
            size="small"
            InputProps={{
              sx: { fontFamily: 'var(--ob-font-family-mono)' },
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
          <Typography
            color="error"
            variant="body2"
            sx={{ mt: 'var(--ob-space-050)' }}
          >
            {error}
          </Typography>
        )}
      </Card>

      {summary && (
        <Stack spacing="var(--ob-space-200)">
          {/* Asset Mix Strategy */}
          <Box>
            <Stack
              direction={{ xs: 'column', sm: 'row' }}
              justifyContent="space-between"
              alignItems={{ xs: 'flex-start', sm: 'center' }}
              spacing="var(--ob-space-100)"
              mb="var(--ob-space-100)"
            >
              <Typography variant="h5" fontWeight={600}>
                Asset Mix Strategy
              </Typography>
              {summary.asset_mix.total_programmable_gfa_sqm && (
                <Chip
                  label={`Total Programmable GFA: ${summary.asset_mix.total_programmable_gfa_sqm.toLocaleString()} m²`}
                  variant="outlined"
                  color="primary"
                />
              )}
            </Stack>

            <Grid container spacing="var(--ob-space-150)">
              {summary.asset_mix.mix_recommendations.map((segment, idx) => (
                <Grid item xs={12} md={4} key={idx}>
                  <Card
                    variant="default"
                    sx={{ height: '100%', p: 'var(--ob-space-150)' }}
                    hover="lift"
                  >
                    <Stack
                      direction="row"
                      justifyContent="space-between"
                      alignItems="center"
                      mb="var(--ob-space-100)"
                    >
                      <Typography variant="h6">{segment.use}</Typography>
                      <Typography variant="h4" color="primary.main">
                        {(segment.allocation_pct * 100).toFixed(0)}%
                      </Typography>
                    </Stack>
                    {segment.target_gfa_sqm && (
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        gutterBottom
                      >
                        Target GFA: {segment.target_gfa_sqm.toLocaleString()} m²
                      </Typography>
                    )}
                    <Typography
                      variant="body1"
                      sx={{ mt: 'var(--ob-space-100)' }}
                    >
                      {segment.rationale}
                    </Typography>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>

          {/* Market Positioning */}
          <Box>
            <Typography variant="h5" fontWeight={600} gutterBottom>
              Market Positioning
            </Typography>
            <Card variant="default" sx={{ p: 'var(--ob-space-150)' }}>
              <Stack
                direction="row"
                spacing="var(--ob-space-100)"
                mb="var(--ob-space-150)"
              >
                <Chip
                  label={`Market Tier: ${summary.market_positioning.market_tier}`}
                  color="secondary"
                  icon={<Business />}
                />
              </Stack>

              <Typography variant="h6" gutterBottom>
                Pricing Guidance
              </Typography>
              <Grid container spacing="var(--ob-space-100)">
                {Object.entries(
                  summary.market_positioning.pricing_guidance,
                ).map(([useType, pricing]) => (
                  <Grid item xs={12} sm={6} md={3} key={useType}>
                    <Box
                      sx={{
                        p: 'var(--ob-space-100)',
                        border: '1px solid',
                        borderColor: 'divider',
                        borderRadius: 'var(--ob-radius-sm)',
                      }}
                    >
                      <Typography
                        variant="subtitle1"
                        fontWeight={600}
                        gutterBottom
                        textTransform="capitalize"
                      >
                        {useType}
                      </Typography>
                      {Object.entries(pricing).map(([key, value]) => (
                        <Stack
                          key={key}
                          direction="row"
                          justifyContent="space-between"
                          mb="var(--ob-space-025)"
                        >
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            textTransform="capitalize"
                          >
                            {key.replace('_', ' ')}
                          </Typography>
                          <Typography variant="caption" fontWeight={600}>
                            ${value.toLocaleString()}
                          </Typography>
                        </Stack>
                      ))}
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </Card>
          </Box>

          {/* Absorption Forecast */}
          <Box>
            <Typography variant="h5" fontWeight={600} gutterBottom>
              Absorption Forecast
            </Typography>
            <Grid
              container
              spacing="var(--ob-space-150)"
              mb="var(--ob-space-150)"
            >
              <Grid item xs={12} sm={4}>
                <MetricTile
                  label="Time to Stabilize"
                  value={String(
                    summary.absorption_forecast.expected_months_to_stabilize,
                  )}
                  variant="compact"
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <MetricTile
                  label="Monthly Velocity"
                  value={String(
                    summary.absorption_forecast.monthly_velocity_target,
                  )}
                  variant="compact"
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <MetricTile
                  label="Confidence"
                  value={summary.absorption_forecast.confidence}
                  variant="compact"
                />
              </Grid>
            </Grid>

            <Card
              variant="default"
              sx={{ p: 'var(--ob-space-150)', overflowX: 'auto' }}
            >
              <Stack
                direction="row"
                spacing="var(--ob-space-200)"
                sx={{ minWidth: '37.5rem' }}
              >
                {summary.absorption_forecast.timeline.map((milestone, idx) => (
                  <Box
                    key={idx}
                    sx={{
                      position: 'relative',
                      minWidth: '7.5rem',
                      textAlign: 'center',
                    }}
                  >
                    <Typography
                      variant="caption"
                      display="block"
                      color="text.secondary"
                      mb="var(--ob-space-050)"
                    >
                      M{milestone.month}
                    </Typography>
                    <Box
                      sx={{
                        width: 'var(--ob-space-075)',
                        height: 'var(--ob-space-075)',
                        borderRadius: 'var(--ob-radius-pill)',
                        bgcolor: 'primary.main',
                        mx: 'auto',
                        mb: 'var(--ob-space-050)',
                      }}
                    />
                    <Typography variant="subtitle2" gutterBottom>
                      {milestone.milestone}
                    </Typography>
                    <Typography variant="caption" color="success.main">
                      {(milestone.expected_absorption_pct * 100).toFixed(0)}%
                      absorbed
                    </Typography>
                  </Box>
                ))}
              </Stack>
            </Card>
          </Box>

          {/* Sales Velocity Model (Calculator) */}
          <Box>
            <Stack
              direction={{ xs: 'column', sm: 'row' }}
              justifyContent="space-between"
              alignItems={{ xs: 'flex-start', sm: 'center' }}
              spacing="var(--ob-space-100)"
              mb="var(--ob-space-100)"
            >
              <Box>
                <Typography variant="h5" fontWeight={600}>
                  Sales Velocity Model
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Forecast launch cadence with inventory and velocity
                  benchmarks.
                </Typography>
              </Box>
              <Button
                variant="contained"
                onClick={handleComputeVelocity}
                disabled={velocityLoading}
                fullWidth
                startIcon={
                  velocityLoading ? <Speed className="fa-spin" /> : <Timeline />
                }
              >
                {velocityLoading ? 'Computing...' : 'Run forecast'}
              </Button>
            </Stack>

            <Card variant="default" sx={{ p: 'var(--ob-space-150)' }}>
              <Grid container spacing="var(--ob-space-150)">
                {/* Inputs */}
                <Grid item xs={12} md={3}>
                  <Stack spacing="var(--ob-space-100)">
                    <TextField
                      select
                      label="Jurisdiction"
                      value={velocityInput.jurisdiction}
                      onChange={(e) =>
                        setVelocityInput({
                          ...velocityInput,
                          jurisdiction: e.target.value,
                        })
                      }
                      fullWidth
                      size="small"
                    >
                      <MenuItem value="SG">Singapore</MenuItem>
                    </TextField>
                    <TextField
                      select
                      label="Asset Type"
                      value={velocityInput.asset_type}
                      onChange={(e) =>
                        setVelocityInput({
                          ...velocityInput,
                          asset_type: e.target.value,
                        })
                      }
                      fullWidth
                      size="small"
                    >
                      <MenuItem value="residential">Residential</MenuItem>
                      <MenuItem value="mixed_use">Mixed-use</MenuItem>
                    </TextField>
                    <TextField
                      label="Price Band"
                      value={velocityInput.price_band}
                      onChange={(e) =>
                        setVelocityInput({
                          ...velocityInput,
                          price_band: e.target.value,
                        })
                      }
                      fullWidth
                      size="small"
                    />
                    <TextField
                      label="Units Planned"
                      type="number"
                      value={velocityInput.units_planned ?? ''}
                      onChange={(e) =>
                        setVelocityInput({
                          ...velocityInput,
                          units_planned: Number(e.target.value),
                        })
                      }
                      fullWidth
                      size="small"
                    />
                  </Stack>
                </Grid>

                {/* Results Area */}
                <Grid item xs={12} md={9}>
                  {velocityError && (
                    <Typography color="error">{velocityError}</Typography>
                  )}
                  {velocityResult ? (
                    <Stack spacing="var(--ob-space-150)">
                      <Grid container spacing="var(--ob-space-100)">
                        <Grid item xs={4}>
                          <MetricTile
                            label="Velocity"
                            value={`${velocityResult.forecast.velocity_units_per_month ?? '—'} units/mo`}
                            variant="compact"
                          />
                        </Grid>
                        <Grid item xs={4}>
                          <MetricTile
                            label="Absorption"
                            value={`${velocityResult.forecast.absorption_months ?? '—'} months`}
                            variant="compact"
                          />
                        </Grid>
                        <Grid item xs={4}>
                          <MetricTile
                            label="Confidence"
                            value={`${(velocityResult.forecast.confidence * 100).toFixed(0)}%`}
                            variant="compact"
                          />
                        </Grid>
                      </Grid>

                      {velocityResult.risks.length > 0 && (
                        <Stack direction="row" spacing="var(--ob-space-050)">
                          {velocityResult.risks.map((risk, idx) => (
                            <Chip
                              key={idx}
                              label={`${risk.label} (${risk.level})`}
                              color={
                                risk.level === 'high' ? 'error' : 'warning'
                              }
                              variant="outlined"
                            />
                          ))}
                        </Stack>
                      )}
                    </Stack>
                  ) : (
                    <Box
                      sx={{
                        height: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        opacity: 0.5,
                      }}
                    >
                      <Typography>Run forecast to see predictions</Typography>
                    </Box>
                  )}
                </Grid>
              </Grid>
            </Card>
          </Box>

          {/* Feedback Loop */}
          <Box>
            <Stack
              direction="row"
              justifyContent="space-between"
              alignItems="center"
              mb="var(--ob-space-100)"
            >
              <Typography variant="h5" fontWeight={600}>
                Market Feedback
              </Typography>
              <Button
                variant="outlined"
                startIcon={<Feedback />}
                onClick={() => setFeedbackOpen(!feedbackOpen)}
              >
                {feedbackOpen ? 'Cancel' : 'Add Feedback'}
              </Button>
            </Stack>

            {feedbackOpen && (
              <Card
                variant="default"
                sx={{
                  p: 'var(--ob-space-150)',
                  mb: 'var(--ob-space-150)',
                  border: '1px solid',
                  borderColor: 'primary.main',
                }}
              >
                <form onSubmit={handleSubmitFeedback}>
                  <Stack spacing="var(--ob-space-100)">
                    <TextField
                      select
                      label="Sentiment"
                      value={feedbackForm.sentiment}
                      onChange={(e) =>
                        setFeedbackForm({
                          ...feedbackForm,
                          sentiment: e.target.value as
                            | 'positive'
                            | 'neutral'
                            | 'negative',
                        })
                      }
                      fullWidth
                    >
                      <MenuItem value="positive">Positive</MenuItem>
                      <MenuItem value="neutral">Neutral</MenuItem>
                      <MenuItem value="negative">Negative</MenuItem>
                    </TextField>
                    <TextField
                      multiline
                      rows={4}
                      label="Notes"
                      value={feedbackForm.notes}
                      onChange={(e) =>
                        setFeedbackForm({
                          ...feedbackForm,
                          notes: e.target.value,
                        })
                      }
                      fullWidth
                      placeholder="Enter feedback..."
                    />
                    <Button
                      type="submit"
                      variant="contained"
                      disabled={submitting || !feedbackForm.notes.trim()}
                      startIcon={<Send />}
                    >
                      Submit Feedback
                    </Button>
                  </Stack>
                </form>
              </Card>
            )}

            <Card variant="default" sx={{ p: 0 }}>
              {summary.feedback.length === 0 ? (
                <Box p="var(--ob-space-200)" textAlign="center">
                  <Typography color="text.secondary">
                    No feedback recorded yet
                  </Typography>
                </Box>
              ) : (
                <Stack divider={<Divider />}>
                  {summary.feedback.map((item) => (
                    <Box key={item.id} p="var(--ob-space-100)">
                      <Stack
                        direction="row"
                        justifyContent="space-between"
                        mb="var(--ob-space-050)"
                      >
                        <Chip
                          label={item.sentiment}
                          size="small"
                          color={
                            item.sentiment === 'positive'
                              ? 'success'
                              : item.sentiment === 'negative'
                                ? 'error'
                                : 'default'
                          }
                        />
                        <Typography variant="caption" color="text.secondary">
                          {new Date(item.created_at).toLocaleString()}
                        </Typography>
                      </Stack>
                      <Typography variant="body2">{item.notes}</Typography>
                    </Box>
                  ))}
                </Stack>
              )}
            </Card>
          </Box>
        </Stack>
      )}

      {/* Empty State */}
      {!summary && !loading && (
        <EmptyState
          title="No advisory data loaded"
          description="Enter a property ID to load advisory data."
          size="md"
          sx={{ mt: 'var(--ob-space-200)' }}
        />
      )}
    </Box>
  )
}
