import { describe, expect, it } from 'vitest'

import { buildPreviewFallbackMassing } from './previewFallbackMassing'

describe('buildPreviewFallbackMassing', () => {
  it('builds a scalar envelope massing from parcel area and current-code GFA', () => {
    const spec = buildPreviewFallbackMassing({
      siteAreaSqm: 5000,
      maxBuildableGfaSqm: 20000,
      siteCoveragePct: 50,
      grossPlotRatio: 4,
      massingLayers: [],
    })

    expect(spec).toMatchObject({
      totalHeightM: 32,
      floorsEstimate: 8,
    })
    expect(spec?.footprintWidthM).toBeGreaterThan(50)
    expect(spec?.footprintDepthM).toBeGreaterThan(35)
    expect(spec?.layers).toHaveLength(1)
    expect(spec?.layers[0]).toMatchObject({
      id: 'envelope',
      label: 'Envelope',
      heightM: 32,
    })
  })

  it('uses resolved height limits before deriving height from GFA', () => {
    const spec = buildPreviewFallbackMassing({
      siteAreaSqm: 5000,
      maxBuildableGfaSqm: 50000,
      buildingHeightLimitM: 72,
      siteCoveragePct: 60,
    })

    expect(spec?.totalHeightM).toBe(72)
    expect(spec?.floorsEstimate).toBe(18)
  })

  it('limits the fallback footprint when official setbacks are resolved', () => {
    const unconstrained = buildPreviewFallbackMassing({
      siteAreaSqm: 1200,
      siteCoveragePct: 80,
    })
    const constrained = buildPreviewFallbackMassing({
      siteAreaSqm: 1200,
      siteCoveragePct: 80,
      setbacks: {
        frontM: 8,
        rearM: 6,
        sideM: 4,
      },
    })

    expect(constrained?.appliedSetbackLimit).toBe(true)
    expect(constrained?.footprintWidthM).toBeLessThan(
      unconstrained?.footprintWidthM ?? 0,
    )
    expect(constrained?.footprintDepthM).toBeLessThan(
      unconstrained?.footprintDepthM ?? 0,
    )
  })

  it('creates stacked program layers from massing allocations', () => {
    const spec = buildPreviewFallbackMassing({
      siteAreaSqm: 6000,
      buildingHeightLimitM: 80,
      siteCoveragePct: 70,
      massingLayers: [
        {
          assetType: 'industrial',
          allocationPct: 70,
          estimatedHeightM: 50,
          color: '#ef4444',
        },
        {
          assetType: 'office',
          allocationPct: 30,
          estimatedHeightM: 30,
          color: '#0ea5e9',
        },
      ],
    })

    expect(spec?.layers).toHaveLength(2)
    expect(spec?.layers[0]).toMatchObject({
      id: 'industrial_1',
      label: 'industrial',
      color: '#ef4444',
      yOffsetM: 0,
    })
    expect(spec?.layers[1]).toMatchObject({
      id: 'office_2',
      label: 'office',
      color: '#0ea5e9',
      yOffsetM: 50,
    })
    expect(
      spec?.layers.reduce((sum, layer) => sum + layer.heightM, 0),
    ).toBeCloseTo(80)
  })

  it('does not build a massing when parcel area is unresolved', () => {
    expect(
      buildPreviewFallbackMassing({
        siteAreaSqm: null,
        maxBuildableGfaSqm: 10000,
      }),
    ).toBeNull()
  })
})
