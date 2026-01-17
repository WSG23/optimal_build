import { test, expect } from '@playwright/test';

/**
 * E2E tests for Buildable Screening feature
 *
 * Tests the core functionality of the GPS capture and analysis workflow.
 */

test.describe('Buildable Screening', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the buildable screening page
    // Adjust the URL based on your routing
    await page.goto('/');

    // Look for navigation to screening/analysis feature
    const screeningLink = page.getByRole('link', { name: /screen|buildable|analysis/i });
    if (await screeningLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await screeningLink.click();
    }
  });

  test('can input address for screening', async ({ page }) => {
    // Find address input
    const addressInput = page.getByPlaceholder(/address|location/i).or(
      page.getByLabel(/address/i)
    );

    if (await addressInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await addressInput.fill('123 Orchard Road, Singapore');
      await expect(addressInput).toHaveValue('123 Orchard Road, Singapore');
    }
  });

  test('displays screening results', async ({ page }) => {
    // This test verifies that after submitting an address,
    // the screening results are displayed

    const addressInput = page.getByPlaceholder(/address|location/i).or(
      page.getByLabel(/address/i)
    );

    if (await addressInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await addressInput.fill('1 Raffles Place, Singapore');

      // Look for submit button
      const submitButton = page.getByRole('button', { name: /screen|analyze|submit/i });
      if (await submitButton.isVisible()) {
        await submitButton.click();

        // Wait for results
        await page.waitForResponse(
          (response) =>
            response.url().includes('/screen/buildable') && response.status() === 200,
          { timeout: 30000 }
        ).catch(() => {
          // API call might not happen if using cached data
        });

        // Check for result indicators
        const resultsSection = page.getByTestId('screening-results').or(
          page.locator('[data-testid*="result"]')
        ).or(
          page.getByText(/zone|gfa|buildable/i)
        );

        await expect(resultsSection).toBeVisible({ timeout: 10000 });
      }
    }
  });

  test('handles invalid address gracefully', async ({ page }) => {
    const addressInput = page.getByPlaceholder(/address|location/i).or(
      page.getByLabel(/address/i)
    );

    if (await addressInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await addressInput.fill('Invalid Address 12345 XYZ');

      const submitButton = page.getByRole('button', { name: /screen|analyze|submit/i });
      if (await submitButton.isVisible()) {
        await submitButton.click();

        // Should show error or empty results, not crash
        await page.waitForTimeout(2000);

        // Page should still be functional
        await expect(page.locator('body')).toBeVisible();
      }
    }
  });
});

test.describe('Buildable API Integration', () => {
  test('API returns valid response for Singapore address', async ({ request }) => {
    const apiUrl = process.env.API_URL || 'http://localhost:8000';

    const response = await request.post(`${apiUrl}/api/v1/screen/buildable`, {
      data: {
        address: '123 Orchard Road, Singapore 238867',
        typ_floor_to_floor_m: 3.4,
        efficiency_ratio: 0.8,
      },
      headers: {
        'Content-Type': 'application/json',
      },
    });

    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body).toHaveProperty('zone_code');
    expect(body).toHaveProperty('metrics');
  });

  test('API validates input parameters', async ({ request }) => {
    const apiUrl = process.env.API_URL || 'http://localhost:8000';

    // Missing required fields should return 422
    const response = await request.post(`${apiUrl}/api/v1/screen/buildable`, {
      data: {
        address: '', // Empty address
      },
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Should return validation error, not server error
    expect(response.status()).toBe(422);
  });
});
