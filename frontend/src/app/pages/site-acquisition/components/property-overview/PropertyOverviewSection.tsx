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
 * - Financial Snapshot: Large hero numbers for Rev/CAPEX
 * - Site Metrics: Bottom divider rows + tags
 *
 * @see frontend/UX_ARCHITECTURE.md - Common UX Friction Points & Solutions
 */

import { Box, Divider, Typography, SvgIconProps } from '@mui/material'
import {
  LocationOn as MapPinIcon,
  GpsFixed as TargetIcon,
  AccountBalance as HistoryIcon,
  Schedule as ClockIcon,
  PieChart as PieChartIcon,
  TrendingUp as TrendingUpIcon,
  Visibility as EyeIcon,
  Apartment as BuildingIcon,
  Map as MapIcon,
  Straighten as RulerIcon,
} from '@mui/icons-material'
import { useMemo, ComponentType, ReactNode } from 'react'
import { ProcessingStatusCard, ProcessingStatus } from './ProcessingStatusCard'
import { AssetMixChart, AssetMixItem } from './AssetMixChart'
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

type MuiIconComponent = ComponentType<SvgIconProps>

/**
 * Map card title to appropriate icon
 */
function getCardIcon(title: string): MuiIconComponent {
  const titleLower = title.toLowerCase()
  if (titleLower.includes('location') || titleLower.includes('tenure'))
    return MapPinIcon
  if (titleLower.includes('envelope')) return TargetIcon
  if (titleLower.includes('heritage')) return HistoryIcon
  if (titleLower.includes('preview') || titleLower.includes('processing'))
    return ClockIcon
  if (titleLower.includes('asset mix')) return PieChartIcon
  if (titleLower.includes('financial')) return TrendingUpIcon
  if (titleLower.includes('visualization')) return EyeIcon
  if (titleLower.includes('zoning') || titleLower.includes('planning'))
    return BuildingIcon
  if (titleLower.includes('market') || titleLower.includes('connectivity'))
    return MapIcon
  return TargetIcon // Default
}

/**
 * Get column span for card based on content type
 * Asset Mix cards span 2 columns, others span 1
 */
function getCardColSpan(title: string): 1 | 2 {
  const titleLower = title.toLowerCase()
  if (titleLower.includes('asset mix')) return 2
  return 1
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
// Sub-Components - Card-Type-Specific Layouts (AI Studio Pattern)
// ============================================================================

/**
 * Shared card header with icon
 */
function CardHeader({
  title,
  icon: Icon,
}: {
  title: string
  icon: ComponentType<SvgIconProps>
}) {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--ob-space-075)',
        mb: 'var(--ob-space-100)',
      }}
    >
      <Box
        sx={{
          p: 'var(--ob-space-050)',
          bgcolor: 'color-mix(in srgb, var(--ob-info-500) 10%, transparent)',
          borderRadius: 'var(--ob-radius-sm)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'info.main',
        }}
      >
        <Icon sx={{ fontSize: 'var(--ob-size-icon-sm)' }} />
      </Box>
      <Typography
        sx={{
          fontSize: 'var(--ob-font-size-base)',
          fontWeight: 700,
          color: 'text.primary',
          letterSpacing: '-0.01em',
        }}
      >
        {title}
      </Typography>
    </Box>
  )
}

/**
 * Shared label component (10px uppercase)
 */
function ItemLabel({ children }: { children: ReactNode }) {
  return (
    <Typography
      sx={{
        fontSize: 'var(--ob-font-size-2xs)',
        fontWeight: 600,
        letterSpacing: '0.05em',
        textTransform: 'uppercase',
        color: 'text.secondary',
      }}
    >
      {children}
    </Typography>
  )
}

/**
 * Shared value component
 */
function ItemValue({
  children,
  variant = 'default',
}: {
  children: ReactNode
  variant?: 'default' | 'large' | 'accent'
}) {
  const styles = {
    default: {
      fontSize: 'var(--ob-font-size-sm)',
      fontWeight: 600,
      color: 'text.primary',
    },
    large: {
      fontSize: 'var(--ob-font-size-lg)',
      fontWeight: 700,
      color: 'text.primary',
    },
    accent: {
      fontSize: 'var(--ob-font-size-sm)',
      fontWeight: 700,
      color: 'info.main',
    },
  }

  return <Typography sx={styles[variant]}>{children}</Typography>
}

/**
 * Shared note component (italic footer)
 */
function CardNote({ children }: { children: ReactNode }) {
  return (
    <Box
      sx={{
        mt: 'var(--ob-space-075)',
        p: 'var(--ob-space-050)',
        bgcolor: 'var(--ob-surface-glass-subtle)',
        borderRadius: 'var(--ob-radius-xs)',
      }}
    >
      <Typography
        sx={{
          fontSize: 'var(--ob-font-size-xs)',
          color: 'text.secondary',
          fontStyle: 'italic',
          lineHeight: 1.4,
        }}
      >
        {children}
      </Typography>
    </Box>
  )
}

/**
 * Location & Tenure Card - AI Studio layout
 * - Address as multi-line prominent text
 * - District/Tenure in 2-column grid
 * - Completion Year below
 */
function LocationTenureCard({ card }: { card: OverviewCard }) {
  const address = card.items.find((i) =>
    i.label.toLowerCase().includes('address'),
  )
  const district = card.items.find((i) =>
    i.label.toLowerCase().includes('district'),
  )
  const tenure = card.items.find((i) =>
    i.label.toLowerCase().includes('tenure'),
  )
  const completion = card.items.find(
    (i) =>
      i.label.toLowerCase().includes('completion') ||
      i.label.toLowerCase().includes('year'),
  )

  return (
    <GlassCard
      sx={{
        p: 'var(--ob-space-125)',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
      }}
    >
      <CardHeader title={card.title} icon={MapPinIcon} />

      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-100)',
          flex: 1,
        }}
      >
        {/* Address - prominent multi-line */}
        {address && (
          <Box>
            <ItemLabel>{address.label}</ItemLabel>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-sm)',
                fontWeight: 600,
                color: 'text.primary',
                lineHeight: 1.4,
                mt: 'var(--ob-space-025)',
              }}
            >
              {address.value}
            </Typography>
          </Box>
        )}

        {/* District / Tenure - 2-column grid */}
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: 'var(--ob-space-100)',
          }}
        >
          {district && (
            <Box>
              <ItemLabel>{district.label}</ItemLabel>
              <ItemValue>{district.value}</ItemValue>
            </Box>
          )}
          {tenure && (
            <Box>
              <ItemLabel>{tenure.label}</ItemLabel>
              <ItemValue>{tenure.value}</ItemValue>
            </Box>
          )}
        </Box>

        {/* Completion Year */}
        {completion && (
          <Box>
            <ItemLabel>{completion.label}</ItemLabel>
            <ItemValue>{completion.value}</ItemValue>
          </Box>
        )}
      </Box>
    </GlassCard>
  )
}

/**
 * Build Envelope Card - AI Studio layout
 * - Zone Code + Plot Ratio in header row (Zone Code in accent color)
 * - Divider
 * - Simple flex rows for remaining metrics
 * - Note at bottom
 */
function BuildEnvelopeCard({ card }: { card: OverviewCard }) {
  const zoneCode = card.items.find((i) =>
    i.label.toLowerCase().includes('zone code'),
  )
  const plotRatio = card.items.find(
    (i) =>
      i.label.toLowerCase().includes('plot ratio') ||
      i.label.toLowerCase().includes('allowable'),
  )
  const otherItems = card.items.filter(
    (i) =>
      !i.label.toLowerCase().includes('zone code') &&
      !i.label.toLowerCase().includes('plot ratio') &&
      !i.label.toLowerCase().includes('allowable'),
  )

  return (
    <GlassCard
      sx={{
        p: 'var(--ob-space-125)',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
      }}
    >
      <CardHeader title={card.title} icon={TargetIcon} />

      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-100)',
          flex: 1,
        }}
      >
        {/* Zone Code + Plot Ratio header row */}
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
          }}
        >
          {zoneCode && (
            <Box>
              <ItemLabel>{zoneCode.label}</ItemLabel>
              <ItemValue variant="accent">{zoneCode.value}</ItemValue>
            </Box>
          )}
          {plotRatio && (
            <Box sx={{ textAlign: 'right' }}>
              <ItemLabel>{plotRatio.label}</ItemLabel>
              <ItemValue>{plotRatio.value}</ItemValue>
            </Box>
          )}
        </Box>

        {/* Divider */}
        <Divider sx={{ borderColor: 'var(--ob-color-border-subtle)' }} />

        {/* Other metrics - simple rows */}
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--ob-space-075)',
          }}
        >
          {otherItems.map((item) => (
            <Box
              key={item.label}
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-xs)',
                  color: 'text.secondary',
                }}
              >
                {item.label}
              </Typography>
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-xs)',
                  fontWeight: 600,
                  color: 'text.primary',
                }}
              >
                {item.value}
              </Typography>
            </Box>
          ))}
        </Box>
      </Box>

      {/* Note */}
      {card.note && <CardNote>{card.note}</CardNote>}
    </GlassCard>
  )
}

/**
 * Heritage Context Card - AI Studio layout
 * - Risk Level as colored badge
 * - Description text
 * - Warning callout if needed
 */
function HeritageCard({ card }: { card: OverviewCard }) {
  const riskItem = card.items.find((i) =>
    i.label.toLowerCase().includes('risk'),
  )
  const riskValue = riskItem?.value?.toLowerCase() ?? ''
  const isLowRisk = riskValue.includes('low')
  const isHighRisk =
    riskValue.includes('high') ||
    riskValue.includes('critical') ||
    riskValue.includes('medium')

  const otherItems = card.items.filter(
    (i) => !i.label.toLowerCase().includes('risk'),
  )

  return (
    <GlassCard
      sx={{
        p: 'var(--ob-space-125)',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
      }}
    >
      <CardHeader title={card.title} icon={HistoryIcon} />

      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-100)',
          flex: 1,
        }}
      >
        {/* Risk Level as badge */}
        {riskItem && (
          <Box>
            <ItemLabel>{riskItem.label}</ItemLabel>
            <Box sx={{ mt: 'var(--ob-space-025)' }}>
              <Box
                component="span"
                sx={{
                  display: 'inline-block',
                  px: 'var(--ob-space-075)',
                  py: 'var(--ob-space-025)',
                  borderRadius: 'var(--ob-radius-pill)',
                  fontSize: 'var(--ob-font-size-xs)',
                  fontWeight: 700,
                  bgcolor: isLowRisk
                    ? 'color-mix(in srgb, var(--ob-success-500) 15%, transparent)'
                    : 'color-mix(in srgb, var(--ob-warning-500) 15%, transparent)',
                  color: isLowRisk ? 'success.main' : 'warning.main',
                }}
              >
                {riskItem.value}
              </Box>
            </Box>
          </Box>
        )}

        {/* Other heritage items */}
        {otherItems.map((item) => (
          <Box key={item.label}>
            <ItemLabel>{item.label}</ItemLabel>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-sm)',
                color: 'text.primary',
                mt: 'var(--ob-space-025)',
              }}
            >
              {item.value}
            </Typography>
          </Box>
        ))}

        {/* Warning callout for high risk */}
        {isHighRisk && card.note && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 'var(--ob-space-075)',
              p: 'var(--ob-space-075)',
              bgcolor:
                'color-mix(in srgb, var(--ob-warning-500) 10%, transparent)',
              border: '1px solid',
              borderColor: 'warning.main',
              borderRadius: 'var(--ob-radius-sm)',
            }}
          >
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'warning.dark',
                lineHeight: 1.4,
              }}
            >
              {card.note}
            </Typography>
          </Box>
        )}

        {/* Regular note for low risk */}
        {!isHighRisk && card.note && <CardNote>{card.note}</CardNote>}
      </Box>
    </GlassCard>
  )
}

/**
 * Financial Snapshot Card - AI Studio layout
 * - Large hero numbers for Est. Revenue and Est. CAPEX
 * - Divider
 * - Smaller rows for Capital Stack and Dominant Risk
 */
function FinancialCard({ card }: { card: OverviewCard }) {
  const revenue = card.items.find(
    (i) =>
      i.label.toLowerCase().includes('revenue') ||
      i.label.toLowerCase().includes('est. revenue'),
  )
  const capex = card.items.find(
    (i) =>
      i.label.toLowerCase().includes('capex') ||
      i.label.toLowerCase().includes('est. capex'),
  )
  const otherItems = card.items.filter(
    (i) =>
      !i.label.toLowerCase().includes('revenue') &&
      !i.label.toLowerCase().includes('capex'),
  )

  return (
    <GlassCard
      sx={{
        p: 'var(--ob-space-125)',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
      }}
    >
      <CardHeader title={card.title} icon={TrendingUpIcon} />

      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-100)',
          flex: 1,
        }}
      >
        {/* Hero numbers for Rev/CAPEX */}
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: '1fr',
            gap: 'var(--ob-space-075)',
          }}
        >
          {revenue && (
            <Box>
              <ItemLabel>Est. Revenue</ItemLabel>
              <ItemValue variant="large">{revenue.value}</ItemValue>
            </Box>
          )}
          {capex && (
            <Box>
              <ItemLabel>Est. CAPEX</ItemLabel>
              <ItemValue variant="large">{capex.value}</ItemValue>
            </Box>
          )}
        </Box>

        {/* Divider */}
        {otherItems.length > 0 && (
          <Divider sx={{ borderColor: 'var(--ob-color-border-subtle)' }} />
        )}

        {/* Other items - smaller rows */}
        {otherItems.map((item) => (
          <Box key={item.label}>
            <ItemLabel>{item.label}</ItemLabel>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-050)',
                mt: 'var(--ob-space-025)',
              }}
            >
              {item.label.toLowerCase().includes('risk') && (
                <Box
                  sx={{
                    width: 'var(--ob-space-050)',
                    height: 'var(--ob-space-050)',
                    borderRadius: 'var(--ob-radius-pill)',
                    bgcolor: 'success.main',
                  }}
                />
              )}
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-sm)',
                  fontWeight: 700,
                  color: 'text.primary',
                }}
              >
                {item.value}
              </Typography>
            </Box>
          </Box>
        ))}
      </Box>

      {/* Note */}
      {card.note && <CardNote>{card.note}</CardNote>}
    </GlassCard>
  )
}

/**
 * Zoning Card - AI Studio layout (Site Metrics style)
 * - Bottom divider rows for each metric
 * - Tags at bottom
 */
function ZoningCard({ card }: { card: OverviewCard }) {
  return (
    <GlassCard
      sx={{
        p: 'var(--ob-space-125)',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
      }}
    >
      <CardHeader title={card.title} icon={RulerIcon} />

      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-075)',
          flex: 1,
        }}
      >
        {/* Metrics with bottom dividers */}
        {card.items.map((item, index) => (
          <Box
            key={item.label}
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-end',
              pb: 'var(--ob-space-050)',
              borderBottom:
                index < card.items.length - 1
                  ? '1px solid var(--ob-color-border-subtle)'
                  : 'none',
            }}
          >
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'text.secondary',
              }}
            >
              {item.label}
            </Typography>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-sm)',
                fontWeight: 700,
                color: 'text.primary',
              }}
            >
              {item.value}
            </Typography>
          </Box>
        ))}

        {/* Tags */}
        {card.tags && card.tags.length > 0 && (
          <Box
            sx={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 'var(--ob-space-050)',
              mt: 'var(--ob-space-050)',
            }}
          >
            {card.tags.map((tag) => (
              <Box
                key={tag}
                sx={{
                  px: 'var(--ob-space-050)',
                  py: 'var(--ob-space-025)',
                  bgcolor:
                    'color-mix(in srgb, var(--ob-info-500) 10%, transparent)',
                  color: 'info.main',
                  borderRadius: 'var(--ob-radius-xs)',
                  fontSize: 'var(--ob-font-size-2xs)',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                }}
              >
                {tag}
              </Box>
            ))}
          </Box>
        )}
      </Box>
    </GlassCard>
  )
}

/**
 * Generic/Default Card - for cards without specific layouts
 * Simple uniform layout for less common card types
 */
function GenericCard({ card }: { card: OverviewCard }) {
  const Icon = getCardIcon(card.title)

  return (
    <GlassCard
      sx={{
        p: 'var(--ob-space-125)',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
      }}
    >
      <CardHeader title={card.title} icon={Icon} />

      {/* Subtitle if present */}
      {card.subtitle && (
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-sm)',
            fontWeight: 600,
            color: 'info.main',
            mb: 'var(--ob-space-075)',
          }}
        >
          {card.subtitle}
        </Typography>
      )}

      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-075)',
          flex: 1,
        }}
      >
        {card.items.map((item) => (
          <Box
            key={item.label}
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              gap: 'var(--ob-space-050)',
            }}
          >
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-2xs)',
                fontWeight: 500,
                letterSpacing: '0.05em',
                textTransform: 'uppercase',
                color: 'text.secondary',
                flexShrink: 0,
              }}
            >
              {item.label}
            </Typography>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-sm)',
                fontWeight: 600,
                color: 'text.primary',
                textAlign: 'right',
              }}
            >
              {item.value}
            </Typography>
          </Box>
        ))}

        {/* Tags */}
        {card.tags && card.tags.length > 0 && (
          <Box
            sx={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 'var(--ob-space-050)',
              mt: 'var(--ob-space-050)',
            }}
          >
            {card.tags.map((tag) => (
              <Box
                key={tag}
                sx={{
                  px: 'var(--ob-space-050)',
                  py: 'var(--ob-space-025)',
                  bgcolor:
                    'color-mix(in srgb, var(--ob-info-500) 10%, transparent)',
                  color: 'info.main',
                  borderRadius: 'var(--ob-radius-xs)',
                  fontSize: 'var(--ob-font-size-2xs)',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                }}
              >
                {tag}
              </Box>
            ))}
          </Box>
        )}
      </Box>

      {/* Note */}
      {card.note && <CardNote>{card.note}</CardNote>}
    </GlassCard>
  )
}

/**
 * Card type detector - routes to appropriate component
 */
function getCardType(
  title: string,
): 'location' | 'envelope' | 'heritage' | 'financial' | 'zoning' | 'generic' {
  const titleLower = title.toLowerCase()
  if (titleLower.includes('location') || titleLower.includes('tenure'))
    return 'location'
  if (titleLower.includes('envelope')) return 'envelope'
  if (titleLower.includes('heritage')) return 'heritage'
  if (titleLower.includes('financial')) return 'financial'
  if (titleLower.includes('zoning') || titleLower.includes('planning'))
    return 'zoning'
  return 'generic'
}

/**
 * Smart card renderer - selects appropriate layout based on card type
 *
 * ⚠️ CRITICAL: Card-Type-Specific Layouts
 * ═══════════════════════════════════════════════════════════════════════════
 * Each card type has a UNIQUE layout tailored to its content. This is an
 * AI Studio UX requirement to avoid "visual monotony" from uniform label-value
 * pairs. DO NOT replace with a single generic layout.
 *
 * Card-specific layouts:
 * - LocationTenureCard: Address multi-line + 2-col grid
 * - BuildEnvelopeCard: Zone/PlotRatio header row + divider + rows
 * - HeritageCard: Risk level as colored badge
 * - FinancialCard: Large hero numbers for Rev/CAPEX
 * - ZoningCard: Bottom divider rows + tags
 *
 * @see frontend/UX_ARCHITECTURE.md - "No More Uniform Label-Value Pairs"
 */
function SmartCard({ card }: { card: OverviewCard }) {
  const cardType = getCardType(card.title)

  // ⚠️ DO NOT simplify to single component - each layout is intentionally unique
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
}

// ============================================================================
// Main Component
// ============================================================================

export function PropertyOverviewSection({
  cards,
}: PropertyOverviewSectionProps) {
  // Categorize cards for rendering
  const { processingCards, assetMixCards, standardCards } = useMemo(() => {
    const processing: OverviewCard[] = []
    const assetMix: OverviewCard[] = []
    const standard: OverviewCard[] = []

    for (const card of cards) {
      if (isAssetMixCard(card)) {
        assetMix.push(card)
      } else if (isProcessingCard(card)) {
        processing.push(card)
      } else {
        standard.push(card)
      }
    }

    return {
      processingCards: processing,
      assetMixCards: assetMix,
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
         * ╔══════════════════════════════════════════════════════════════════╗
         * ║  ⚠️  CRITICAL LAYOUT - DO NOT MODIFY WITHOUT APPROVAL  ⚠️        ║
         * ╠══════════════════════════════════════════════════════════════════╣
         * ║  This 4-column grid is a core AI Studio UX requirement.          ║
         * ║  Changing to 2-column or 3-column WILL cause regression.         ║
         * ║                                                                   ║
         * ║  Requirements:                                                    ║
         * ║  - lg breakpoint: 4 columns (repeat(4, 1fr))                     ║
         * ║  - sm breakpoint: 2 columns (repeat(2, 1fr))                     ║
         * ║  - xs breakpoint: 1 column (1fr)                                 ║
         * ║                                                                   ║
         * ║  See: frontend/UX_ARCHITECTURE.md "Property Overview Grid"       ║
         * ║  See: docs/planning/ui-friction-solutions.md                     ║
         * ╚══════════════════════════════════════════════════════════════════╝
         */
        gridTemplateColumns: {
          xs: '1fr',
          sm: 'repeat(2, 1fr)',
          lg: 'repeat(4, 1fr)', // ⚠️ MUST be 4 columns - see comment above
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

      {/* Asset Mix Charts - span 2 columns on desktop */}
      {assetMixCards.map((card) => {
        const data = extractAssetMixData(card)
        const insight = generateAssetMixInsight(data)

        return (
          <Box
            key={card.title}
            sx={{ gridColumn: { xs: 'span 1', sm: 'span 2' } }}
          >
            <AssetMixChart
              title={card.title}
              data={data}
              aiInsight={insight ?? card.note ?? undefined}
            />
          </Box>
        )
      })}
    </Box>
  )
}
