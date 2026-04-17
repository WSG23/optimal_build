/**
 * Property Overview - Shared Types and Utility Functions
 */

import { SvgIconProps } from '@mui/material'
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
} from '@mui/icons-material'
import { ComponentType } from 'react'

// ============================================================================
// Types
// ============================================================================

export interface OverviewCard {
  title: string
  subtitle?: string | null
  items: Array<{ label: string; value: string }>
  tags?: string[]
  note?: string | null
  layout?: 'default' | 'status'
}

export interface PropertyOverviewSectionProps {
  cards: OverviewCard[]
}

export type MuiIconComponent = ComponentType<SvgIconProps>

// ============================================================================
// Helper Functions
// ============================================================================

export function getCardIcon(title: string): MuiIconComponent {
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
  return TargetIcon
}

export function getCardColSpan(title: string): 1 | 2 {
  const titleLower = title.toLowerCase()
  if (titleLower.includes('asset mix')) return 2
  return 1
}

export function isProcessingCard(card: OverviewCard): boolean {
  return (
    card.title.toLowerCase().includes('preview') ||
    card.title.toLowerCase().includes('processing') ||
    card.title.toLowerCase().includes('visualization')
  )
}

export function isAssetMixCard(card: OverviewCard): boolean {
  return card.title.toLowerCase().includes('asset mix')
}

export function getCardType(
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
