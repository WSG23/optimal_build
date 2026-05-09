import { expect, test } from '@playwright/test'
import { installE2EDiagnostics } from './support/diagnostics'

installE2EDiagnostics(test)

test('feasibility simulation renders current advisory workspace', async ({
  page,
}) => {
  await page.addInitScript(() => {
    window.__computeEvents = []
    window.addEventListener('feasibility.compute', (event) => {
      window.__computeEvents.push(event.detail)
    })
  })

  await page.goto('/projects/e2e-project/feasibility')
  await expect(page.getByTestId('feasibility-wizard')).toBeVisible()

  await page.getByTestId('address-input').fill('123 Example Ave')
  await page.getByTestId('site-area-input').fill('1000')
  await page.getByTestId('compute-button').click()

  await page.waitForFunction(
    () =>
      window.__computeEvents?.some(
        (event: { status?: string }) => event.status === 'success',
      ),
    undefined,
    { timeout: 30_000 },
  )

  await expect(
    page.getByRole('heading', { name: '3D Massing Visualization' }),
  ).toBeVisible()
  await expect(page.getByText('Total NIA')).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'AI Optimizer' }),
  ).toBeVisible()
})
