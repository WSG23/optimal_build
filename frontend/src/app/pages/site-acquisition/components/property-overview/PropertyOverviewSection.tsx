/**
 * Property Overview Section Component - Atomic Card Architecture
 *
 * Implements AI Studio UX Friction Solutions:
 * - Problem 1: Atomic Card Architecture with hierarchical typography
 * - Problem 2: Active Status Feedback with progress bars
 * - Problem 4: Contextual Intelligence with charts and AI insights
 *
 * @see frontend/UX_ARCHITECTURE.md - Common UX Friction Points & Solutions
 */

import { Box, Grid, Typography } from '@mui/material'
import { useMemo } from 'react'
import { ProcessingStatusCard, ProcessingStatus } from './ProcessingStatusCard'
import { AssetMixChart, AssetMixItem } from './AssetMixChart'
import { AIInsightPanel } from './AIInsightPanel'
import { GlassCard } from '../../../../../components/canonical/GlassCard'
import '../../../../../styles/site-acquisition.css'

// ============================================================================
// Types
// ============================================================================

export interface OverviewCard {
  title: string
  subtitle?: string | null
  items: Array<{ label: string; value: string }>
  tags?: string[]
  note?: string | null
}

export interface PropertyOverviewSectionProps {
  cards: OverviewCard[]
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Extract primary metric from card items for StatCard display
 */
function extractPrimaryMetric(card: OverviewCard): {
  label: string
  value: string
  subtitle?: string
} | null {
  if (card.items.length === 0) return null

  // For Financial Snapshot, use total revenue
  if (card.title.toLowerCase().includes('financial')) {
    const revenueItem = card.items.find((item) =>
      item.label.toLowerCase().includes('revenue'),
    )
    if (revenueItem) {
      return {
        label: 'EST. REVENUE',
        value: revenueItem.value,
        subtitle: card.subtitle ?? undefined,
      }
    }
  }

  // For Build Envelope, use max buildable GFA
  if (card.title.toLowerCase().includes('envelope')) {
    const gfaItem = card.items.find(
      (item) =>
        item.label.toLowerCase().includes('max buildable') ||
        item.label.toLowerCase().includes('gfa'),
    )
    if (gfaItem) {
      return {
        label: 'MAX BUILDABLE GFA',
        value: gfaItem.value,
        subtitle: card.subtitle ?? undefined,
      }
    }
  }

  // For Site Metrics, use site area
  if (card.title.toLowerCase().includes('site metrics')) {
    const areaItem = card.items.find((item) =>
      item.label.toLowerCase().includes('site area'),
    )
    if (areaItem) {
      return {
        label: 'SITE AREA',
        value: areaItem.value,
        subtitle: card.subtitle ?? undefined,
      }
    }
  }

  // Default: use first item
  return {
    label: card.items[0].label.toUpperCase(),
    value: card.items[0].value,
    subtitle: card.subtitle ?? undefined,
  }
}

/**
 * Determine if card should be rendered as ProcessingStatusCard
 */
function isProcessingCard(card: OverviewCard): boolean {
  return (
    card.title.toLowerCase().includes('preview') ||
    card.title.toLowerCase().includes('processing') ||
    card.title.toLowerCase().includes('visualization')
  )
}

/**
 * Determine if card should be rendered as AssetMixChart
 */
function isAssetMixCard(card: OverviewCard): boolean {
  return card.title.toLowerCase().includes('asset mix')
}

/**
 * Extract processing status from card
 */
function extractProcessingStatus(card: OverviewCard): ProcessingStatus {
  const statusItem = card.items.find((item) =>
    item.label.toLowerCase().includes('status'),
  )
  const statusValue = statusItem?.value?.toLowerCase() ?? ''

  if (statusValue.includes('ready') || statusValue.includes('complete')) {
    return 'ready'
  }
  if (
    statusValue.includes('processing') ||
    statusValue.includes('generating')
  ) {
    return 'processing'
  }
  if (statusValue.includes('failed') || statusValue.includes('error')) {
    return 'failed'
  }
  if (statusValue.includes('expired')) {
    return 'expired'
  }
  return 'pending'
}

/**
 * Extract asset mix data from card items
 */
function extractAssetMixData(card: OverviewCard): AssetMixItem[] {
  return card.items.map((item) => {
    // Parse percentage from value string (e.g., "40% • 2,000 sqm • ...")
    const percentMatch = item.value.match(/^(\d+(?:\.\d+)?)\s*%/)
    const percentage = percentMatch ? parseFloat(percentMatch[1]) : 0

    // Parse GFA if present
    const gfaMatch = item.value.match(
      /(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:k\s*)?sqm/i,
    )
    const gfa = gfaMatch
      ? parseFloat(gfaMatch[1].replace(/,/g, '')) *
        (gfaMatch[0].includes('k') ? 1000 : 1)
      : undefined

    // Parse revenue if present
    const revenueMatch = item.value.match(
      /Rev\s*[≈~]?\s*\$?(\d+(?:\.\d+)?)\s*M/i,
    )
    const revenue = revenueMatch
      ? parseFloat(revenueMatch[1]) * 1_000_000
      : undefined

    // Parse risk level if present
    const riskMatch = item.value.match(/(low|medium|high)\s*risk/i)
    const riskLevel = riskMatch
      ? (riskMatch[1].toLowerCase() as 'low' | 'medium' | 'high')
      : undefined

    return {
      label: item.label,
      value: percentage,
      allocatedGfa: gfa,
      estimatedRevenue: revenue,
      riskLevel,
    }
  })
}

/**
 * Generate AI insight for asset mix based on data
 */
function generateAssetMixInsight(data: AssetMixItem[]): string | undefined {
  if (data.length === 0) return undefined

  // Find dominant asset type
  const sorted = [...data].sort((a, b) => b.value - a.value)
  const dominant = sorted[0]

  if (!dominant || dominant.value === 0) return undefined

  const insights: string[] = []

  // Dominant allocation insight
  insights.push(
    `${dominant.label} represents the largest allocation at ${dominant.value.toFixed(0)}%.`,
  )

  // Risk-based insight if available
  const lowRiskAssets = data.filter((d) => d.riskLevel === 'low')
  const highRiskAssets = data.filter((d) => d.riskLevel === 'high')

  if (lowRiskAssets.length > 0 && highRiskAssets.length === 0) {
    insights.push('Portfolio weighted toward lower-risk asset classes.')
  } else if (highRiskAssets.length > 0) {
    insights.push(
      `Consider de-risking: ${highRiskAssets.map((a) => a.label).join(', ')} flagged as high risk.`,
    )
  }

  return insights.join(' ')
}

// ============================================================================
// Sub-Components
// ============================================================================

/**
 * Renders a card as a detailed info panel (fallback for complex cards)
 */
function DetailCard({ card }: { card: OverviewCard }) {
  return (
    <GlassCard
      sx={{
        p: 'var(--ob-space-150)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-100)',
        height: '100%',
      }}
    >
      {/* Header */}
      <Box>
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-2xs)',
            fontWeight: 600,
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
            color: 'var(--ob-text-secondary)',
          }}
        >
          {card.title}
        </Typography>
        {card.subtitle && (
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-sm)',
              fontWeight: 600,
              color: 'var(--ob-color-text-primary)',
              mt: 'var(--ob-space-025)',
            }}
          >
            {card.subtitle}
          </Typography>
        )}
      </Box>

      {/* Items Grid */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          gap: 'var(--ob-space-100)',
        }}
      >
        {card.items.map((item) => (
          <Box key={item.label}>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-2xs)',
                fontWeight: 600,
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
                color: 'var(--ob-text-tertiary)',
              }}
            >
              {item.label}
            </Typography>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-sm)',
                fontWeight: 600,
                color: 'var(--ob-color-text-primary)',
              }}
            >
              {item.value}
            </Typography>
          </Box>
        ))}
      </Box>

      {/* Tags */}
      {card.tags && card.tags.length > 0 && (
        <Box
          sx={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--ob-space-050)' }}
        >
          {card.tags.map((tag) => (
            <Box
              key={tag}
              sx={{
                px: 'var(--ob-space-075)',
                py: 'var(--ob-space-025)',
                bgcolor: 'rgba(0, 243, 255, 0.1)',
                color: 'var(--ob-color-neon-cyan)',
                borderRadius: 'var(--ob-radius-pill)',
                fontSize: 'var(--ob-font-size-xs)',
                fontWeight: 600,
              }}
            >
              {tag}
            </Box>
          ))}
        </Box>
      )}

      {/* Note as AI Insight */}
      {card.note && (
        <AIInsightPanel label="NOTE" variant="info" compact>
          {card.note}
        </AIInsightPanel>
      )}
    </GlassCard>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export function PropertyOverviewSection({
  cards,
}: PropertyOverviewSectionProps) {
  // Categorize cards for different rendering strategies
  const { statCards, processingCards, assetMixCards, detailCards } =
    useMemo(() => {
      const stat: OverviewCard[] = []
      const processing: OverviewCard[] = []
      const assetMix: OverviewCard[] = []
      const detail: OverviewCard[] = []

      for (const card of cards) {
        if (isAssetMixCard(card)) {
          assetMix.push(card)
        } else if (isProcessingCard(card)) {
          processing.push(card)
        } else {
          // Determine if card has a clear primary metric for StatCard
          const primaryMetric = extractPrimaryMetric(card)
          if (
            primaryMetric &&
            card.items.length <= 6 &&
            (card.title.toLowerCase().includes('financial') ||
              card.title.toLowerCase().includes('envelope') ||
              card.title.toLowerCase().includes('site metrics'))
          ) {
            stat.push(card)
          } else {
            detail.push(card)
          }
        }
      }

      return {
        statCards: stat,
        processingCards: processing,
        assetMixCards: assetMix,
        detailCards: detail,
      }
    }, [cards])

  if (cards.length === 0) {
    return null
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-200)',
      }}
    >
      {/* Key Metrics Cards - Full detail with hierarchical layout */}
      {statCards.length > 0 && (
        <Grid container spacing="var(--ob-space-125)">
          {statCards.map((card) => (
            <Grid item xs={12} sm={6} md={4} key={card.title}>
              <DetailCard card={card} />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Processing Status Cards - Active Feedback */}
      {processingCards.length > 0 && (
        <Grid container spacing="var(--ob-space-125)">
          {processingCards.map((card) => {
            const status = extractProcessingStatus(card)
            const details = card.items.filter(
              (item) =>
                !item.label.toLowerCase().includes('status') &&
                !item.label.toLowerCase().includes('preview url'),
            )

            // Estimate progress based on status
            const progress =
              status === 'ready'
                ? 100
                : status === 'processing'
                  ? 65
                  : status === 'pending'
                    ? 15
                    : 0

            return (
              <Grid item xs={12} md={6} key={card.title}>
                <ProcessingStatusCard
                  title={card.title}
                  status={status}
                  progress={progress}
                  statusMessage={card.note ?? undefined}
                  details={details}
                />
              </Grid>
            )
          })}
        </Grid>
      )}

      {/* Asset Mix Charts - Visualization */}
      {assetMixCards.length > 0 && (
        <Grid container spacing="var(--ob-space-125)">
          {assetMixCards.map((card) => {
            const data = extractAssetMixData(card)
            const insight = generateAssetMixInsight(data)

            return (
              <Grid item xs={12} md={6} key={card.title}>
                <AssetMixChart
                  title={card.title}
                  data={data}
                  aiInsight={insight ?? card.note ?? undefined}
                />
              </Grid>
            )
          })}
        </Grid>
      )}

      {/* Detail Cards - Full Information */}
      {detailCards.length > 0 && (
        <Grid container spacing="var(--ob-space-125)">
          {detailCards.map((card) => (
            <Grid item xs={12} sm={6} md={4} key={card.title}>
              <DetailCard card={card} />
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  )
}
