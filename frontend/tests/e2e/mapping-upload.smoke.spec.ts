import { test, expect } from '@playwright/test';

test.describe('Mapping Upload smoke', () => {
  test('shows the upload control', async ({ page }) => {
    await page.goto('/mapping/upload');
    await expect(page.getByTestId('page-mapping-upload')).toBeVisible();
    await expect(page.getByTestId('control-upload-input')).toBeVisible();
  });
});
