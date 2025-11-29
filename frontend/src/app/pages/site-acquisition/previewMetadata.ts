export type PreviewLayerMetrics = {
  allocationPct: number | null
  gfaSqm: number | null
  niaSqm: number | null
  heightM: number | null
  floors: number | null
}

export type PreviewLayerGeometry = {
  detailLevel: string | null
  baseElevationM: number | null
  previewHeightM: number | null
  topElevationM: number | null
  footprint: number[][] | null
  topFootprint: number[][] | null
  footprintAreaSqm: number | null
  footprintPerimeterM: number | null
  topFootprintAreaSqm: number | null
  topFootprintPerimeterM: number | null
  floorLineHeights: number[]
}

export type PreviewLayerMetadata = {
  id: string
  name: string
  color: string
  metrics: PreviewLayerMetrics
  geometry: PreviewLayerGeometry | null
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
  const metrics: Record<string, unknown> =
    raw.metrics && typeof raw.metrics === 'object'
      ? (raw.metrics as Record<string, unknown>)
      : {}
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
    geometry: normaliseGeometry(raw.geometry),
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

function normaliseGeometry(raw: unknown): PreviewLayerGeometry | null {
  if (!raw || typeof raw !== 'object') {
    return null
  }
  const data = raw as Record<string, unknown>
  const baseElevation = coerceNumber(data, 'base_elevation')
  const previewHeight = coerceNumber(data, 'preview_height') ?? coerceNumber(data, 'height')
  const detail =
    (typeof data.detail_level === 'string' && data.detail_level) ||
    (typeof data.detailLevel === 'string' && data.detailLevel) ||
    null
  const footprint = extractPolygonRing(data.footprint)
  const topFootprint = extractPolygonRing(data.top_footprint ?? data.topFootprint)
  const rawFloorLines = data.floor_lines ?? data.floorLines
  const floorLines = Array.isArray(rawFloorLines)
    ? (rawFloorLines as unknown[])
        .map((value: unknown) => (typeof value === 'number' ? value : null))
        .filter((value): value is number => value !== null)
    : []
  const topElevation =
    baseElevation !== null && previewHeight !== null
      ? baseElevation + previewHeight
      : null
  return {
    detailLevel: detail,
    baseElevationM: baseElevation,
    previewHeightM: previewHeight,
    topElevationM: topElevation,
    footprint,
    topFootprint,
    footprintAreaSqm: computePolygonArea(footprint),
    footprintPerimeterM: computePolygonPerimeter(footprint),
    topFootprintAreaSqm: computePolygonArea(topFootprint),
    topFootprintPerimeterM: computePolygonPerimeter(topFootprint),
    floorLineHeights: floorLines,
  }
}

function extractPolygonRing(
  polygon: unknown,
): number[][] | null {
  if (
    polygon &&
    typeof polygon === 'object' &&
    Array.isArray((polygon as Record<string, unknown>).coordinates)
  ) {
    const coordinates = (polygon as Record<string, unknown>).coordinates
    if (
      Array.isArray(coordinates) &&
      coordinates.length > 0 &&
      Array.isArray(coordinates[0])
    ) {
      const ring = coordinates[0]
      const normalised = ring
        .filter(
          (point) =>
            Array.isArray(point) &&
            point.length >= 2 &&
            Number.isFinite(Number(point[0])) &&
            Number.isFinite(Number(point[1])),
        )
        .map((point) => [Number(point[0]), Number(point[1])])
      return normalised.length >= 3 ? normalised : null
    }
  }
  return null
}

function computePolygonArea(points: number[][] | null): number | null {
  if (!points || points.length < 3) {
    return null
  }
  let total = 0
  for (let i = 0; i < points.length - 1; i += 1) {
    const [x1, y1] = points[i]
    const [x2, y2] = points[i + 1]
    total += x1 * y2 - x2 * y1
  }
  return Math.abs(total) / 2
}

function computePolygonPerimeter(points: number[][] | null): number | null {
  if (!points || points.length < 2) {
    return null
  }
  let total = 0
  for (let i = 0; i < points.length - 1; i += 1) {
    const [x1, y1] = points[i]
    const [x2, y2] = points[i + 1]
    total += Math.hypot(x2 - x1, y2 - y1)
  }
  const [xStart, yStart] = points[0]
  const [xEnd, yEnd] = points[points.length - 1]
  if (xStart !== xEnd || yStart !== yEnd) {
    total += Math.hypot(xStart - xEnd, yStart - yEnd)
  }
  return total
}
