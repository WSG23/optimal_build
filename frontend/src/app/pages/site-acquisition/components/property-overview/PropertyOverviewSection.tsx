/**
 * Property Overview Section Component - AI Studio Compact Grid Layout
 *
 * Implements AI Studio UX Friction Solutions:
 * - Problem 1: Atomic Card Architecture with hierarchical typography
 * - Problem 2: Active Status Feedback with progress bars
 * - Problem 4: Contextual Intelligence with charts and AI insights
 *
 * Key Layout Features:
 * - 4-column responsive grid (single viewport, minimal scrolling)
 * - Card-type-specific layouts (not uniform label-value pairs)
 * - Dense information display with 10px labels
 *
 * AI Studio Card Patterns:
 * - Location & Tenure: Address multi-line + 2-col grid for District/Tenure
 * - Build Envelope: Zone/PlotRatio header row + divider + simple rows
 * - Heritage Context: Risk level as colored badge
 * - Analysis Status: Explicit capture completeness and scope
 * - Site Metrics: Bottom divider rows + tags
 *
 * @see frontend/UX_ARCHITECTURE.md - Common UX Friction Points & Solutions
 */

import { Box } from '@mui/material'
import { useMemo } from 'react'
import { ProcessingStatusCard } from './ProcessingStatusCard'
import type { ProcessingStatus } from './ProcessingStatusCard'
import { SmartCard } from './SmartCard'
import { getCardColSpan, isProcessingCard, isAssetMixCard } from './utils'
import type { OverviewCard, PropertyOverviewSectionProps } from './utils'
import '../../../../../styles/site-acquisition.css'

// Re-export types so existing imports from this file continue to work
export type { OverviewCard, PropertyOverviewSectionProps }

// ============================================================================
// Helper Functions (local to main component)
// ============================================================================

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

// Note: Capture no longer renders asset-mix charts. Any asset-mix cards are
// filtered out here so downstream workflows such as Feasibility can own them.

// ============================================================================
// Main Component
// ============================================================================

export function PropertyOverviewSection({
  cards,
}: PropertyOverviewSectionProps) {
  // Categorize cards for rendering. Asset-mix cards are filtered out so
  // Capture stays focused on overview and preview status.
  const { processingCards, standardCards } = useMemo(() => {
    const processing: OverviewCard[] = []
    const standard: OverviewCard[] = []

    for (const card of cards) {
      if (isAssetMixCard(card)) {
        // Skip - owned by downstream workflows such as Feasibility
        continue
      } else if (isProcessingCard(card)) {
        processing.push(card)
      } else {
        standard.push(card)
      }
    }

    return {
      processingCards: processing,
      standardCards: standard,
    }
  }, [cards])

  if (cards.length === 0) {
    return null
  }

  return (
    <Box
      sx={{
        display: 'grid',
        /**
         * CRITICAL LAYOUT - DO NOT MODIFY WITHOUT APPROVAL
         *
         * This 4-column grid is a core AI Studio UX requirement.
         * Changing to 2-column or 3-column WILL cause regression.
         *
         * Requirements:
         * - lg breakpoint: 4 columns (repeat(4, 1fr))
         * - sm breakpoint: 2 columns (repeat(2, 1fr))
         * - xs breakpoint: 1 column (1fr)
         *
         * See: frontend/UX_ARCHITECTURE.md "Property Overview Grid"
         * See: docs/planning/ui-friction-solutions.md
         */
        gridTemplateColumns: {
          xs: '1fr',
          sm: 'repeat(2, 1fr)',
          lg: 'repeat(4, 1fr)', // MUST be 4 columns - see comment above
        },
        gap: 'var(--ob-space-150)',
        // Align items to start so cards don't stretch
        alignItems: 'start',
      }}
    >
      {/* Render all cards with smart type-specific layouts */}
      {standardCards.map((card) => (
        <Box
          key={card.title}
          sx={{
            gridColumn: {
              xs: 'span 1',
              lg: `span ${getCardColSpan(card.title)}`,
            },
          }}
        >
          <SmartCard card={card} />
        </Box>
      ))}

      {/* Processing Status Cards */}
      {processingCards.map((card) => {
        const status = extractProcessingStatus(card)
        const details = card.items.filter(
          (item) =>
            !item.label.toLowerCase().includes('status') &&
            !item.label.toLowerCase().includes('preview url'),
        )

        const progress =
          status === 'ready'
            ? 100
            : status === 'processing'
              ? 65
              : status === 'pending'
                ? 15
                : 0

        return (
          <Box key={card.title} sx={{ gridColumn: { xs: 'span 1' } }}>
            <ProcessingStatusCard
              title={card.title}
              status={status}
              progress={progress}
              statusMessage={card.note ?? undefined}
              details={details}
            />
          </Box>
        )
      })}
    </Box>
  )
}
