import { expect, test } from '@playwright/test'

const SEEDED_ADDRESSES = [
  { address: '123 Example Ave' },
  { address: '456 River Road' },
  { address: '789 Coastal Way' },
]

test.describe('Feasibility wizard', () => {
  for (const { address } of SEEDED_ADDRESSES) {
    test(`renders backend data for ${address}`, async ({ page, request }) => {
      const response = await request.post('http://127.0.0.1:8000/api/v1/screen/buildable', {
        data: {
          address,
          typ_floor_to_floor_m: 3.4,
          efficiency_ratio: 0.8,
        },
      })
      expect(response.ok()).toBeTruthy()
      const body = await response.json()

      await page.goto('/feasibility')
      await page.getByLabel('Site address').fill(address)
      await page.getByRole('button', { name: 'Compute feasibility' }).click()

      const zoneValue = body.zone_code ?? 'Unknown'
      await expect(page.getByTestId('zone-code')).toHaveText(zoneValue)

      const overlayBadges = page.getByTestId('overlay-badges').locator('span')
      const overlayTexts = await overlayBadges.allTextContents()
      const expectedOverlays = body.overlays.length === 0 ? ['None'] : body.overlays
      expect(new Set(overlayTexts)).toEqual(new Set(expectedOverlays))

      const numberFormatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 })
      await expect(page.getByTestId('gfa-cap')).toHaveText(
        numberFormatter.format(body.metrics.gfa_cap_m2),
      )
      await expect(page.getByTestId('floors-max')).toHaveText(
        numberFormatter.format(body.metrics.floors_max),
      )
      await expect(page.getByTestId('footprint')).toHaveText(
        numberFormatter.format(body.metrics.footprint_m2),
      )
      await expect(page.getByTestId('nsa-est')).toHaveText(
        numberFormatter.format(body.metrics.nsa_est_m2),
      )

      const advisoryHints = Array.isArray(body.advisory_hints) ? body.advisory_hints : []
      const advisoryLocator = page.getByTestId('advisory-hints')
      if (advisoryHints.length > 0) {
        await expect(advisoryLocator).toBeVisible()
        const hints = await advisoryLocator.locator('li').allTextContents()
        expect(new Set(hints)).toEqual(new Set(advisoryHints))
      } else {
        await expect(advisoryLocator).toHaveCount(0)
      }

      if (body.rules.length > 0) {
        const firstRule = body.rules[0]
        await expect(page.getByText(firstRule.authority)).toBeVisible()
        if (firstRule.provenance?.clause_ref) {
          await expect(page.getByText(firstRule.provenance.clause_ref)).toBeVisible()
        }
      }
    })
  }

  test('recomputes when assumptions change with debounce', async ({ page, request }) => {
    const address = SEEDED_ADDRESSES[0].address
    const initialResponse = await request.post('http://127.0.0.1:8000/api/v1/screen/buildable', {
      data: {
        address,
        typ_floor_to_floor_m: 3.4,
        efficiency_ratio: 0.8,
      },
    })
    const initialBody = await initialResponse.json()

    const updatedResponse = await request.post('http://127.0.0.1:8000/api/v1/screen/buildable', {
      data: {
        address,
        typ_floor_to_floor_m: 3.4,
        efficiency_ratio: 0.75,
      },
    })
    const updatedBody = await updatedResponse.json()

    await page.addInitScript(() => {
      window.__computeEvents = []
      window.addEventListener('feasibility.compute', (event) => {
        window.__computeEvents.push(event.detail)
      })
    })

    await page.goto('/feasibility')
    await page.getByLabel('Site address').fill(address)
    await page.getByRole('button', { name: 'Compute feasibility' }).click()
    await expect(page.getByTestId('nsa-est')).toHaveText(
      new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(
        initialBody.metrics.nsa_est_m2,
      ),
    )

    const eventsBefore = await page.evaluate(() => window.__computeEvents.length)
    await page.fill('#assumption-efficiency', '0.75')
    await page.waitForFunction(
      (previousCount) => window.__computeEvents.length > previousCount,
      eventsBefore,
    )
    const lastEvent = await page.evaluate(() =>
      window.__computeEvents[window.__computeEvents.length - 1],
    )
    expect(lastEvent.status).toBe('success')
    expect(lastEvent.durationMs).toBeLessThan(500)

    await expect(page.getByTestId('nsa-est')).toHaveText(
      new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(
        updatedBody.metrics.nsa_est_m2,
      ),
    )
  })
})
