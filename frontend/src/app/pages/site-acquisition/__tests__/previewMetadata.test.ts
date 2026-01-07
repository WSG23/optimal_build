import { describe, expect, it } from 'vitest'
import { colors } from '@ob/tokens'

import { normaliseLegendEntry, normalisePreviewLayer } from '../previewMetadata'

describe('previewMetadata normalisers', () => {
  it('uses token palette fallbacks when color is missing', () => {
    const layer = normalisePreviewLayer({ id: 'a', name: 'Layer A' })
    expect(layer?.color).toBe(colors.brand[600])

    const entry = normaliseLegendEntry({ asset_type: 'residential' })
    expect(entry?.color).toBe(colors.info[600])
  })
})
