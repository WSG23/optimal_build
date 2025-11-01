import { test, expect } from '@playwright/test';

test.describe('Data Upload smoke', () => {
  test('shows the upload control', async ({ page }) => {
    await page.goto('/data/upload');
    await expect(page.getByTestId('page-data-upload')).toBeVisible();
    await expect(page.getByTestId('control-upload-input')).toBeVisible();
  });
});
