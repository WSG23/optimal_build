/**
 * Canonical Component Library - Square Cyber-Minimalism
 * =============================================================================
 * This barrel file exports all canonical UI components with enforced geometry:
 *
 * Radius Scale:
 * - 0px  (none)  : DataBlock, tables
 * - 2px  (xs)    : Button, Tag, StatusChip
 * - 4px  (sm)    : Card, Panel, MetricTile, Input, EmptyState, AlertBlock
 * - 8px  (lg)    : Window (modal) - ONLY
 *
 * All components use:
 * - Fine line borders (1px at low opacity)
 * - Consistent spacing tokens
 * - Dark/light mode support
 * - Preserved animations (shimmer, lift, blur)
 * =============================================================================
 */

// Core containers
export { Card } from './Card'
export type { CardProps } from './Card'

export { Panel } from './Panel'
export type { PanelProps } from './Panel'

export { Window } from './Window'
export type { WindowProps } from './Window'

export { DataBlock } from './DataBlock'
export type { DataBlockProps } from './DataBlock'

// Actions
export { Button } from './Button'
export type { ButtonProps } from './Button'

// Form elements
export { Input } from './Input'
export type { InputProps } from './Input'

// Data display
export { MetricTile } from './MetricTile'
export type { MetricTileProps } from './MetricTile'

export { Tag } from './Tag'
export type { TagProps } from './Tag'

export { StatusChip } from './StatusChip'
export type { StatusChipProps } from './StatusChip'

// Navigation
export { Tabs, TabPanel } from './Tabs'
export type { TabsProps, TabItem, TabPanelProps } from './Tabs'

// Feedback
export { EmptyState } from './EmptyState'
export type { EmptyStateProps } from './EmptyState'

export { AlertBlock } from './AlertBlock'
export type { AlertBlockProps } from './AlertBlock'

// Loading states
export {
  Skeleton,
  SkeletonText,
  SkeletonCard,
  SkeletonMetric,
} from './Skeleton'
export type {
  SkeletonProps,
  SkeletonTextProps,
  SkeletonCardProps,
} from './Skeleton'

// Layout helpers (existing, to be updated)
export { SectionHeader } from './SectionHeader'
export type { SectionHeaderProps } from './SectionHeader'

// =============================================================================
// DEPRECATED - Use new components instead
// These are kept for backward compatibility during migration
// =============================================================================

// GlassCard -> Card
export { GlassCard } from './GlassCard'
export type { GlassCardProps } from './GlassCard'

// GlassButton -> Button
export { GlassButton } from './GlassButton'
export type { GlassButtonProps } from './GlassButton'

// GlassWindow -> Window
export { GlassWindow } from './GlassWindow'
export type { GlassWindowProps } from './GlassWindow'

// MetricCard -> MetricTile
export { MetricCard } from './MetricCard'
export type { MetricCardProps } from './MetricCard'

// HeroMetric -> MetricTile with variant="hero"
export { HeroMetric } from './HeroMetric'
export type { HeroMetricProps } from './HeroMetric'
