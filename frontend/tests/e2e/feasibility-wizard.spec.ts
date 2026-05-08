import { expect, test } from '@playwright/test'

const SEEDED_ADDRESSES = [
  { address: '123 Example Ave' },
  { address: '456 River Road' },
  { address: '789 Coastal Way' },
]

test.describe('Feasibility wizard', () => {
  for (const { address } of SEEDED_ADDRESSES) {
    test(`runs simulation for ${address}`, async ({ page }) => {
      await page.addInitScript(() => {
        window.__computeEvents = []
        window.addEventListener('feasibility.compute', (event) => {
          window.__computeEvents.push(event.detail)
        })
      })

      await page.goto('/projects/e2e-project/feasibility')
      await expect(page.getByTestId('feasibility-wizard')).toBeVisible()
      await page.getByTestId('address-input').fill(address)
      await page.getByTestId('site-area-input').fill('1200')
      await page.getByTestId('compute-button').click()

      await page.waitForFunction(
        () =>
          window.__computeEvents?.some(
            (event: { status?: string }) => event.status === 'success',
          ),
        undefined,
        { timeout: 30_000 },
      )

      await expect(page.getByText('Total NIA')).toBeVisible()
      await expect(
        page.getByRole('heading', { name: '3D Massing Visualization' }),
      ).toBeVisible()
      await expect(
        page.getByRole('heading', { name: 'AI Optimizer' }),
      ).toBeVisible()
    })
  }

  test('recomputes when assumptions change with debounce', async ({ page }) => {
    const address = SEEDED_ADDRESSES[0].address

    await page.addInitScript(() => {
      window.__computeEvents = []
      window.addEventListener('feasibility.compute', (event) => {
        window.__computeEvents.push(event.detail)
      })
    })

    await page.goto('/projects/e2e-project/feasibility')
    await expect(page.getByTestId('feasibility-wizard')).toBeVisible()
    await page.getByTestId('address-input').fill(address)
    await page.getByTestId('site-area-input').fill('1200')
    await page.getByTestId('compute-button').click()

    await page.waitForFunction(
      () =>
        window.__computeEvents?.some(
          (event: { status?: string }) => event.status === 'success',
        ),
      undefined,
      { timeout: 30_000 },
    )

    const eventsBefore = await page.evaluate(
      () => window.__computeEvents.length,
    )
    await page.fill('#assumption-efficiency', '0.75')
    await page.waitForFunction(
      (previousCount) => window.__computeEvents.length > previousCount,
      eventsBefore,
    )
    const lastEvent = await page.evaluate(
      () => window.__computeEvents[window.__computeEvents.length - 1],
    )
    expect(lastEvent.status).toBe('success')
    expect(lastEvent.durationMs).toBeLessThan(5_000)

    await expect(page.getByText('Total NIA')).toBeVisible()
  })
})
