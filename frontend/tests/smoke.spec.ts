import { test, expect } from '@playwright/test';

test('app renders headline', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Building Compliance Platform');
});
