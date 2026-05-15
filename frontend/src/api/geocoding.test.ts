import { afterEach, describe, expect, it, vi } from 'vitest'

import { forwardGeocodeAddress } from './geocoding'

describe('forwardGeocodeAddress', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('surfaces API problem detail for unavailable Singapore geocoding', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          title: 'Service Unavailable',
          status: 503,
          detail: 'ONEMAP_ACCESS_TOKEN not configured',
        }),
        { status: 503 },
      ),
    )

    await expect(
      forwardGeocodeAddress('1 Nassim Rd', { jurisdictionCode: 'SG' }),
    ).rejects.toThrow('ONEMAP_ACCESS_TOKEN not configured')
  })
})
