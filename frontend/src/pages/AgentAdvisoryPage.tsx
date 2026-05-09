import { FormEvent, Suspense, lazy, useEffect, useMemo, useState } from 'react'
import { Box, Container, Stack, Typography, Grid } from '@mui/material'

import { AppLayout } from '../App'
import {
  AdvisoryFeedbackItem,
  AdvisoryFeedbackPayload,
  AdvisorySummary,
  fetchAdvisorySummary,
  submitAdvisoryFeedback,
} from '../api/advisory'
import { useRouterLocation } from '../router'
import { MarketPositioningPanel } from './advisory/components/MarketPositioningPanel'
import { FeedbackForm } from './advisory/components/FeedbackForm'
import { Skeleton } from '../components/canonical/Skeleton'
import '../styles/advisory.css'

const AssetMixPanel = lazy(() =>
  import('./advisory/components/AssetMixPanel').then((module) => ({
    default: module.AssetMixPanel,
  })),
)

const AbsorptionChart = lazy(() =>
  import('./advisory/components/AbsorptionChart').then((module) => ({
    default: module.AbsorptionChart,
  })),
)

function AdvisoryPanelFallback({ height }: { height: number }) {
  return <Skeleton height={height} variant="rounded" />
}

function usePropertyIdFromQuery(): string {
  const { search } = useRouterLocation()
  return useMemo(() => {
    try {
      const params = new URLSearchParams(search)
      return params.get('propertyId') ?? ''
    } catch (error) {
      console.warn('Failed to parse query string', error)
      return ''
    }
  }, [search])
}

export function AgentAdvisoryPage() {
  const propertyId = usePropertyIdFromQuery()
  const [summary, setSummary] = useState<AdvisorySummary | null>(null)
  const [feedback, setFeedback] = useState<AdvisoryFeedbackItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [feedbackNotes, setFeedbackNotes] = useState('')
  const [feedbackSentiment, setFeedbackSentiment] = useState('positive')
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (!propertyId) {
      return
    }
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    fetchAdvisorySummary(propertyId, controller.signal)
      .then((data) => {
        setSummary(data)
        setFeedback(data.feedback)
      })
      .catch((err) => {
        if (err instanceof Error) {
          setError(err.message)
        } else {
          setError('Failed to load advisory insights')
        }
      })
      .finally(() => setLoading(false))

    return () => controller.abort()
  }, [propertyId])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!propertyId || feedbackNotes.trim() === '') {
      return
    }

    const payload: AdvisoryFeedbackPayload = {
      sentiment: feedbackSentiment,
      notes: feedbackNotes.trim(),
    }
    setIsSubmitting(true)
    try {
      const record = await submitAdvisoryFeedback(propertyId, payload)
      setFeedback((existing) => [record, ...existing])
      setFeedbackNotes('')
      setFeedbackSentiment('positive')
    } catch (err) {
      console.error('Failed to record feedback', err)
      setError(err instanceof Error ? err.message : 'Failed to submit feedback')
    } finally {
      setIsSubmitting(false)
    }
  }

  // Loading Skeleton
  if (loading) {
    return (
      <AppLayout
        title="Development Advisory"
        subtitle="Market Intelligence & Strategic Positioning"
      >
        <Container maxWidth="xl" sx={{ py: 'var(--ob-space-300)' }}>
          <Stack spacing="var(--ob-space-200)">
            <Skeleton height={300} variant="rounded" />
            <Grid container spacing="var(--ob-space-200)">
              <Grid item xs={12} md={6}>
                <Skeleton height={200} variant="rounded" />
              </Grid>
              <Grid item xs={12} md={6}>
                <Skeleton height={200} variant="rounded" />
              </Grid>
            </Grid>
          </Stack>
        </Container>
      </AppLayout>
    )
  }

  return (
    <AppLayout
      title="Development Advisory"
      subtitle="Belnd site analysis with market intelligence to recommend positioning, velocity, and next steps."
    >
      <Container maxWidth="xl" sx={{ py: 'var(--ob-space-300)' }}>
        {!propertyId && (
          <Box
            sx={{
              p: 'var(--ob-space-200)',
              border: '1px dashed grey',
              borderRadius: 'var(--ob-radius-sm)',
            }}
          >
            <Typography color="textSecondary">
              Provide a `propertyId` query parameter to load advisory insights.
            </Typography>
          </Box>
        )}

        {error && (
          <Box
            sx={{
              p: 'var(--ob-space-200)',
              mb: 'var(--ob-space-200)',
              bgcolor: 'error.main',
              color: 'white',
              borderRadius: 'var(--ob-radius-sm)',
            }}
          >
            {error}
          </Box>
        )}

        {summary && (
          <Stack spacing="var(--ob-space-300)">
            {/* Top Row: Asset Mix Strategy */}
            <Suspense fallback={<AdvisoryPanelFallback height={300} />}>
              <AssetMixPanel
                totalGfa={summary.asset_mix.total_programmable_gfa_sqm}
                recommendations={summary.asset_mix.mix_recommendations}
                notes={summary.asset_mix.notes}
              />
            </Suspense>

            {/* Middle Row: Market Positioning & Absorption Grid */}
            <Grid container spacing="var(--ob-space-300)">
              <Grid item xs={12} lg={6}>
                <MarketPositioningPanel data={summary.market_positioning} />
              </Grid>
              <Grid item xs={12} lg={6}>
                <Suspense fallback={<AdvisoryPanelFallback height={400} />}>
                  <AbsorptionChart data={summary.absorption_forecast} />
                </Suspense>
              </Grid>
            </Grid>

            {/* Bottom Row: Feedback Loop */}
            <FeedbackForm
              sentiment={feedbackSentiment}
              notes={feedbackNotes}
              isSubmitting={isSubmitting}
              feedbackHistory={feedback}
              onSentimentChange={setFeedbackSentiment}
              onNotesChange={setFeedbackNotes}
              onSubmit={handleSubmit}
            />
          </Stack>
        )}
      </Container>
    </AppLayout>
  )
}

export default AgentAdvisoryPage
