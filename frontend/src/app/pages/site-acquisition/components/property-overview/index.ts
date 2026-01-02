export { PropertyOverviewSection } from './PropertyOverviewSection'
export type {
  PropertyOverviewSectionProps,
  OverviewCard,
} from './PropertyOverviewSection'

// Master Table - Single Source of Truth for layer data, controls, and legend editing
export { PreviewLayersTable } from './PreviewLayersTable'
export type { PreviewLayersTableProps, LayerAction } from './PreviewLayersTable'

// DEPRECATED: These components are no longer used in SiteAcquisitionPage
// Their functionality has been consolidated into PreviewLayersTable
// Keeping exports for backwards compatibility

/** @deprecated Use PreviewLayersTable with inline accordion instead */
export { LayerBreakdownCards } from './LayerBreakdownCards'
export type { LayerBreakdownCardsProps } from './LayerBreakdownCards'

/** @deprecated Use PreviewLayersTable with legendEntries/onLegendChange props instead */
export { ColorLegendEditor } from './ColorLegendEditor'
export type { ColorLegendEditorProps } from './ColorLegendEditor'

// UX Friction Solution Components
export { StatCard } from './StatCard'
export type { StatCardProps } from './StatCard'

export { ProcessingStatusCard } from './ProcessingStatusCard'
export type {
  ProcessingStatusCardProps,
  ProcessingStatus,
} from './ProcessingStatusCard'

export { AssetMixChart } from './AssetMixChart'
export type { AssetMixChartProps, AssetMixItem } from './AssetMixChart'

export { AIInsightPanel, AIInsightCard } from './AIInsightPanel'
export type {
  AIInsightPanelProps,
  AIInsightCardProps,
  InsightVariant,
} from './AIInsightPanel'
