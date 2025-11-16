export type PreviewLayerMetrics = {
  allocationPct: number | null
  gfaSqm: number | null
  niaSqm: number | null
  heightM: number | null
  floors: number | null
}

export type PreviewLayerMetadata = {
  id: string
  name: string
  color: string
  metrics: PreviewLayerMetrics
}

export type PreviewLegendEntry = {
  assetType: string
  label: string
  color: string
  description: string | null
}

export function normalisePreviewLayer(
  raw: Record<string, unknown>,
): PreviewLayerMetadata | null {
  const id = typeof raw.id === 'string' && raw.id.trim() ? raw.id : undefined
  const name = typeof raw.name === 'string' && raw.name.trim() ? raw.name : undefined
  if (!id || !name) {
    return null
  }
  const color =
    (typeof raw.color === 'string' && raw.color.trim()) || '#1c7ed6'
  const metrics = raw.metrics && typeof raw.metrics === 'object' ? raw.metrics : {}
  return {
    id,
    name,
    color,
    metrics: {
      allocationPct: coerceNumber(metrics, 'allocation_pct'),
      gfaSqm: coerceNumber(metrics, 'gfa_sqm'),
      niaSqm: coerceNumber(metrics, 'nia_sqm'),
      heightM: coerceNumber(metrics, 'estimated_height_m'),
      floors: coerceNumber(metrics, 'estimated_floors'),
    },
  }
}

export function normaliseLegendEntry(
  raw: Record<string, unknown>,
): PreviewLegendEntry | null {
  const assetType =
    (typeof raw.asset_type === 'string' && raw.asset_type.trim()) ||
    (typeof raw.assetType === 'string' && raw.assetType.trim()) ||
    null
  if (!assetType) {
    return null
  }
  const label =
    (typeof raw.label === 'string' && raw.label.trim()) ||
    assetType.replace(/[_-]/g, ' ')
  const color =
    (typeof raw.color === 'string' && raw.color.trim()) || '#4f46e5'
  const description =
    (typeof raw.description === 'string' && raw.description.trim()) ||
    (typeof raw.legendDescription === 'string' && raw.legendDescription.trim()) ||
    null
  return {
    assetType,
    label,
    color,
    description,
  }
}

function coerceNumber(
  source: Record<string, unknown>,
  key: string,
): number | null {
  const value =
    source[key] ??
    source[key.replace(/_([a-z])/g, (_, char: string) => char.toUpperCase())]
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value
  }
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}
