import { test, expect } from '@playwright/test';

/**
 * Smoke tests for optimal_build
 *
 * These tests verify basic functionality and should run quickly.
 * They are the first line of defense for catching major regressions.
 */

test.describe('Smoke Tests', () => {
  test('homepage loads successfully', async ({ page }) => {
    await page.goto('/');

    // Page should load without errors
    await expect(page).toHaveTitle(/Optimal Build|Building Compliance/i);

    // Main content area should be visible
    await expect(page.locator('main, [role="main"], #root')).toBeVisible();
  });

  test('navigation is present', async ({ page }) => {
    await page.goto('/');

    // Navigation should be visible
    const nav = page.getByRole('navigation').first();
    await expect(nav).toBeVisible();
  });

  test('API health check is accessible', async ({ request }) => {
    const response = await request.get(
      process.env.API_URL || 'http://localhost:8000/health'
    );

    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.status).toBe('healthy');
  });

  test('no console errors on homepage', async ({ page }) => {
    const consoleErrors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Filter out known acceptable errors
    const criticalErrors = consoleErrors.filter(
      (error) =>
        !error.includes('favicon') &&
        !error.includes('Failed to load resource: the server responded with a status of 401')
    );

    expect(criticalErrors).toHaveLength(0);
  });

  test('page responds within acceptable time', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    const loadTime = Date.now() - startTime;

    // Page should load within 5 seconds
    expect(loadTime).toBeLessThan(5000);
  });
});

test.describe('Authentication Smoke', () => {
  test('authenticated user can access protected routes', async ({ page }) => {
    // Navigate to a protected route
    await page.goto('/');

    // Should not be redirected to login
    await expect(page).not.toHaveURL(/login|signin/i);
  });
});
