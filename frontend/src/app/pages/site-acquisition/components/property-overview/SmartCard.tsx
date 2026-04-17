/**
 * Smart card renderer - selects appropriate layout based on card type
 *
 * CRITICAL: Card-Type-Specific Layouts
 * Each card type has a UNIQUE layout tailored to its content. This is an
 * AI Studio UX requirement to avoid "visual monotony" from uniform label-value
 * pairs. DO NOT replace with a single generic layout.
 *
 * Card-specific layouts:
 * - LocationTenureCard: Address multi-line + 2-col grid
 * - BuildEnvelopeCard: Zone/PlotRatio header row + divider + rows
 * - HeritageCard: Risk level as colored badge
 * - FinancialCard: Reserved for downstream workflows, not Capture
 * - ZoningCard: Bottom divider rows + tags
 *
 * @see frontend/UX_ARCHITECTURE.md - "No More Uniform Label-Value Pairs"
 */

import { memo } from 'react'
import { LocationTenureCard } from './cards/LocationTenureCard'
import { BuildEnvelopeCard } from './cards/BuildEnvelopeCard'
import { HeritageCard } from './cards/HeritageCard'
import { FinancialCard } from './cards/FinancialCard'
import { ZoningCard } from './cards/ZoningCard'
import { StatusCard } from './cards/StatusCard'
import { GenericCard } from './cards/GenericCard'
import { getCardType } from './utils'
import type { OverviewCard } from './utils'

export const SmartCard = memo(function SmartCard({
  card,
}: {
  card: OverviewCard
}) {
  if (card.layout === 'status') {
    return <StatusCard card={card} />
  }

  const cardType = getCardType(card.title)

  // DO NOT simplify to single component - each layout is intentionally unique
  switch (cardType) {
    case 'location':
      return <LocationTenureCard card={card} />
    case 'envelope':
      return <BuildEnvelopeCard card={card} />
    case 'heritage':
      return <HeritageCard card={card} />
    case 'financial':
      return <FinancialCard card={card} />
    case 'zoning':
      return <ZoningCard card={card} />
    default:
      return <GenericCard card={card} />
  }
})
