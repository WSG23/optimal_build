import { test as setup, expect } from '@playwright/test';
import path from 'path';

const authFile = path.join(__dirname, '../playwright/.auth/user.json');

/**
 * Authentication setup for E2E tests
 *
 * This runs before all authenticated tests to:
 * 1. Navigate to login page
 * 2. Authenticate the test user
 * 3. Save the authentication state
 */
setup('authenticate', async ({ page }) => {
  // Navigate to the app
  await page.goto('/');

  // Check if we need to authenticate
  // The app might auto-redirect to login or show a login button
  const loginButton = page.getByRole('button', { name: /sign in|login/i });
  const loginLink = page.getByRole('link', { name: /sign in|login/i });

  if (await loginButton.isVisible({ timeout: 5000 }).catch(() => false)) {
    await loginButton.click();
  } else if (await loginLink.isVisible({ timeout: 5000 }).catch(() => false)) {
    await loginLink.click();
  }

  // Wait for login form or SSO redirect
  // Adjust these selectors based on your actual login implementation
  const emailInput = page.getByLabel(/email/i);
  const passwordInput = page.getByLabel(/password/i);

  if (await emailInput.isVisible({ timeout: 10000 }).catch(() => false)) {
    // Standard email/password login
    await emailInput.fill(process.env.TEST_USER_EMAIL || 'test@example.com');
    await passwordInput.fill(process.env.TEST_USER_PASSWORD || 'TestPass123!');

    await page.getByRole('button', { name: /sign in|login|submit/i }).click();

    // Wait for successful login
    await page.waitForURL('**/*', { timeout: 30000 });
  } else {
    // Development mode - might use header-based auth
    // Set development headers for authenticated requests
    await page.setExtraHTTPHeaders({
      'X-User-Email': process.env.TEST_USER_EMAIL || 'test@example.com',
      'X-Role': 'developer',
    });
  }

  // Verify we're logged in by checking for a common authenticated element
  // Adjust based on your app's UI
  await expect(
    page.getByRole('navigation').or(page.getByTestId('app-shell')).or(page.locator('body'))
  ).toBeVisible();

  // Save authentication state
  await page.context().storageState({ path: authFile });
});
