export interface PreviewFallbackMassingLayerInput {
  assetType?: string | null
  allocationPct?: number | null
  gfaSqm?: number | null
  estimatedHeightM?: number | null
  color?: string | null
}

export interface PreviewFallbackMassingInput {
  siteAreaSqm?: number | null
  maxBuildableGfaSqm?: number | null
  buildingHeightLimitM?: number | null
  siteCoveragePct?: number | null
  grossPlotRatio?: number | null
  setbacks?: {
    frontM?: number | null
    rearM?: number | null
    sideM?: number | null
  } | null
  massingLayers?: PreviewFallbackMassingLayerInput[] | null
}

export interface PreviewFallbackMassingLayerSpec {
  id: string
  label: string
  widthM: number
  depthM: number
  heightM: number
  yOffsetM: number
  color: string
}

export interface PreviewFallbackMassingSpec {
  footprintWidthM: number
  footprintDepthM: number
  totalHeightM: number
  floorsEstimate: number
  appliedSetbackLimit: boolean
  layers: PreviewFallbackMassingLayerSpec[]
}

const DEFAULT_SITE_COVERAGE = 0.55
const DEFAULT_FLOOR_TO_FLOOR_M = 4
const DEFAULT_HEIGHT_M = 24
const MIN_HEIGHT_M = 6
const MAX_PREVIEW_HEIGHT_M = 260
const FALLBACK_COLORS = ['#3b82f6', '#14b8a6', '#f59e0b', '#a855f7']

export function buildPreviewFallbackMassing(
  input?: PreviewFallbackMassingInput | null,
): PreviewFallbackMassingSpec | null {
  const siteAreaSqm = positiveNumber(input?.siteAreaSqm)
  if (siteAreaSqm == null) {
    return null
  }

  const requestedCoverageRatio = clamp(
    percentToRatio(input?.siteCoveragePct) ?? DEFAULT_SITE_COVERAGE,
    0.1,
    0.95,
  )
  const setbackLimit = deriveSetbackCoverageLimit(siteAreaSqm, input?.setbacks)
  const coverageRatio = Math.min(
    requestedCoverageRatio,
    setbackLimit?.coverageRatio ?? requestedCoverageRatio,
  )
  const footprintAreaSqm = siteAreaSqm * coverageRatio
  const footprintWidthM = Math.sqrt(footprintAreaSqm * 1.35)
  const footprintDepthM = footprintAreaSqm / footprintWidthM
  const totalHeightM = deriveTotalHeightM(input, footprintAreaSqm)
  const floorsEstimate = Math.max(
    1,
    Math.round(totalHeightM / DEFAULT_FLOOR_TO_FLOOR_M),
  )

  const layers = buildLayers(
    input?.massingLayers ?? [],
    footprintWidthM,
    footprintDepthM,
    totalHeightM,
  )

  return {
    footprintWidthM,
    footprintDepthM,
    totalHeightM,
    floorsEstimate,
    appliedSetbackLimit: Boolean(
      setbackLimit && setbackLimit.coverageRatio < requestedCoverageRatio,
    ),
    layers,
  }
}

function deriveSetbackCoverageLimit(
  siteAreaSqm: number,
  setbacks: PreviewFallbackMassingInput['setbacks'],
): { coverageRatio: number } | null {
  const frontM = positiveNumber(setbacks?.frontM) ?? 0
  const rearM = positiveNumber(setbacks?.rearM) ?? 0
  const sideM = positiveNumber(setbacks?.sideM) ?? 0

  if (frontM <= 0 && rearM <= 0 && sideM <= 0) {
    return null
  }

  const siteWidthM = Math.sqrt(siteAreaSqm * 1.35)
  const siteDepthM = siteAreaSqm / siteWidthM
  const buildableWidthM = Math.max(siteWidthM - sideM * 2, siteWidthM * 0.18)
  const buildableDepthM = Math.max(
    siteDepthM - frontM - rearM,
    siteDepthM * 0.18,
  )
  const coverageRatio = clamp(
    (buildableWidthM * buildableDepthM) / siteAreaSqm,
    0.05,
    0.95,
  )

  return { coverageRatio }
}

function deriveTotalHeightM(
  input: PreviewFallbackMassingInput | null | undefined,
  footprintAreaSqm: number,
): number {
  const explicitHeight = positiveNumber(input?.buildingHeightLimitM)
  if (explicitHeight != null) {
    return clamp(explicitHeight, MIN_HEIGHT_M, MAX_PREVIEW_HEIGHT_M)
  }

  const maxBuildableGfaSqm = positiveNumber(input?.maxBuildableGfaSqm)
  if (maxBuildableGfaSqm != null && footprintAreaSqm > 0) {
    const floors = Math.ceil(maxBuildableGfaSqm / footprintAreaSqm)
    return clamp(
      floors * DEFAULT_FLOOR_TO_FLOOR_M,
      MIN_HEIGHT_M,
      MAX_PREVIEW_HEIGHT_M,
    )
  }

  const grossPlotRatio = positiveNumber(input?.grossPlotRatio)
  if (grossPlotRatio != null) {
    const siteAreaSqm = positiveNumber(input?.siteAreaSqm)
    const floors =
      siteAreaSqm != null && footprintAreaSqm > 0
        ? Math.ceil((siteAreaSqm * grossPlotRatio) / footprintAreaSqm)
        : Math.ceil(grossPlotRatio / DEFAULT_SITE_COVERAGE)
    return clamp(
      floors * DEFAULT_FLOOR_TO_FLOOR_M,
      MIN_HEIGHT_M,
      MAX_PREVIEW_HEIGHT_M,
    )
  }

  return DEFAULT_HEIGHT_M
}

function buildLayers(
  inputLayers: PreviewFallbackMassingLayerInput[],
  footprintWidthM: number,
  footprintDepthM: number,
  totalHeightM: number,
): PreviewFallbackMassingLayerSpec[] {
  const usableLayers = inputLayers.filter(
    (layer) =>
      positiveNumber(layer.allocationPct) != null ||
      positiveNumber(layer.gfaSqm) != null ||
      positiveNumber(layer.estimatedHeightM) != null,
  )

  if (!usableLayers.length) {
    return [
      {
        id: 'envelope',
        label: 'Envelope',
        widthM: footprintWidthM,
        depthM: footprintDepthM,
        heightM: totalHeightM,
        yOffsetM: 0,
        color: FALLBACK_COLORS[0],
      },
    ]
  }

  const allocationTotal = usableLayers.reduce(
    (sum, layer) => sum + (positiveNumber(layer.allocationPct) ?? 0),
    0,
  )
  const rawHeights = usableLayers.map((layer) => {
    const explicitHeight = positiveNumber(layer.estimatedHeightM)
    if (explicitHeight != null) {
      return explicitHeight
    }
    const allocationPct = positiveNumber(layer.allocationPct)
    if (allocationPct != null && allocationTotal > 0) {
      return totalHeightM * (allocationPct / allocationTotal)
    }
    return totalHeightM / usableLayers.length
  })
  const rawHeightTotal = rawHeights.reduce((sum, height) => sum + height, 0)
  const scale = rawHeightTotal > 0 ? totalHeightM / rawHeightTotal : 1

  let yOffsetM = 0
  return usableLayers.map((layer, index) => {
    const heightM = Math.max(1.5, rawHeights[index] * scale)
    const upperLayerScale = Math.max(0.62, 1 - index * 0.06)
    const spec = {
      id: normalizeLayerId(layer.assetType, index),
      label: formatLayerLabel(layer.assetType, index),
      widthM: footprintWidthM * upperLayerScale,
      depthM: footprintDepthM * upperLayerScale,
      heightM,
      yOffsetM,
      color: normalizeColor(layer.color, index),
    }
    yOffsetM += heightM
    return spec
  })
}

function positiveNumber(value: number | null | undefined): number | null {
  return typeof value === 'number' && Number.isFinite(value) && value > 0
    ? value
    : null
}

function percentToRatio(value: number | null | undefined): number | null {
  const number = positiveNumber(value)
  if (number == null) {
    return null
  }
  return number > 1 ? number / 100 : number
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}

function normalizeLayerId(assetType: string | null | undefined, index: number) {
  const base = assetType
    ?.trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
  return base ? `${base}_${index + 1}` : `layer_${index + 1}`
}

function formatLayerLabel(assetType: string | null | undefined, index: number) {
  const label = assetType?.trim().replace(/[_-]+/g, ' ')
  return label || `Layer ${index + 1}`
}

function normalizeColor(color: string | null | undefined, index: number) {
  const value = color?.trim()
  if (value && /^#[0-9a-f]{3}([0-9a-f]{3})?$/i.test(value)) {
    return value
  }
  return FALLBACK_COLORS[index % FALLBACK_COLORS.length]
}
