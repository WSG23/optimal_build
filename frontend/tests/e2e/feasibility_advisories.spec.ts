import { expect, test } from '@playwright/test'

test('feasibility advisories render with citations', async ({ page }) => {
  await page.goto('/')
  await page.getByTestId('address-input').fill('123 Example Ave')
  await page.getByTestId('compute-button').click()
  await expect(page.getByTestId('zone-code')).toHaveText(/R|C|B/)
  await expect(page.getByTestId('gfa-cap')).toContainText(/\d/)
  await expect(page.getByTestId('citations')).toContainText(
    /clause|SCDF|URA|BCA|PUB/,
  )
  await page.getByTestId('assumption-floor').fill('3.5')
  await expect(page.getByTestId('floors-max')).toContainText(/\d/)
})
