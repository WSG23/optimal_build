import { assert, describe, expect, it } from 'vitest'

import type { BuildableRequest } from '../buildable'
import { fetchBuildable } from '../buildable'

describe('buildable API fallback', () => {
  it('falls back to mock data when the primary transport raises a TypeError', async () => {
    let attempts = 0
    const failingTransport = async () => {
      attempts += 1
      throw new TypeError('Load failed')
    }

    const request: BuildableRequest = {
      address: '123 Example Ave',
      typFloorToFloorM: 3.4,
      efficiencyRatio: 0.8,
    }

    const summary = await fetchBuildable(request, {
      transport: failingTransport,
    })

    assert.equal(attempts, 1)
    assert.equal(summary.zoneCode, 'R2')
    assert.equal(summary.metrics.gfaCapM2, 4375)
    assert.ok(summary.advisoryHints.length > 0)
  })

  it('does not swallow AbortError rejections', async () => {
    const abortError = new DOMException('Request aborted', 'AbortError')
    const abortingTransport = async () => {
      throw abortError
    }

    const request: BuildableRequest = {
      address: '999 Unknown Road',
      typFloorToFloorM: 3.4,
      efficiencyRatio: 0.8,
    }

    await expect(
      fetchBuildable(request, {
        transport: abortingTransport,
      }),
    ).rejects.toThrow(/Request aborted/)
  })
})
