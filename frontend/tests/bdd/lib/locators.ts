import type { Locator, Page } from '@playwright/test'

export const byTestId = (page: Page, id: string): Locator =>
  page.locator(`[data-testid="${id}"]`)
