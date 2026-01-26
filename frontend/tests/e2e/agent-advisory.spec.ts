import { expect, test } from '@playwright/test'

const PROPERTY_ID = 'prop-123'
const SUMMARY_RESPONSE = {
  asset_mix: {
    property_id: PROPERTY_ID,
    total_programmable_gfa_sqm: 87500,
    mix_recommendations: [
      {
        use: 'office',
        allocation_pct: 55,
        target_gfa_sqm: 48125,
        rationale: 'Sustain anchor tenancy demand.',
      },
      {
        use: 'retail',
        allocation_pct: 25,
        target_gfa_sqm: 21875,
        rationale: 'Activate podium frontage.',
      },
    ],
    notes: ['Retain flexibility for podium conversion.'],
  },
  market_positioning: {
    market_tier: 'Prime fringe',
    pricing_guidance: {
      sale_psf: {
        target_min: 2100,
        target_max: 2400,
      },
      rent_psf: {
        target_min: 7.2,
        target_max: 9.1,
      },
    },
    target_segments: [
      { segment: 'Asset-light MNC', weight_pct: 35 },
      { segment: 'Growth tech', weight_pct: 20 },
    ],
    messaging: [
      'Position as next-generation fringe CBD alternative.',
      'Highlight dual frontage and podium amenities.',
    ],
  },
  absorption_forecast: {
    expected_months_to_stabilize: 11,
    monthly_velocity_target: 4,
    confidence: 'medium',
    timeline: [
      {
        milestone: 'Pre-launch marketing',
        month: 1,
        expected_absorption_pct: 10,
      },
      { milestone: 'Sales launch', month: 4, expected_absorption_pct: 35 },
      { milestone: 'Stabilisation', month: 11, expected_absorption_pct: 100 },
    ],
  },
  feedback: [
    {
      id: 'seed-feedback',
      property_id: PROPERTY_ID,
      sentiment: 'neutral',
      notes: 'Awaiting updated pricing guidance.',
      channel: 'email',
      metadata: {},
      created_at: '2025-01-18T08:15:00.000Z',
    },
  ],
}

const FEEDBACK_RESPONSE = {
  id: 'new-feedback',
  property_id: PROPERTY_ID,
  sentiment: 'positive',
  notes: 'Site visit confirmed podium activation opportunities.',
  channel: 'call',
  metadata: {},
  created_at: '2025-02-01T09:30:00.000Z',
}

test.describe('Agent advisory critical flows', () => {
  test.beforeEach(async ({ page }) => {
    await page.route(
      '**/api/v1/agents/commercial-property/properties/*/advisory',
      async (route, request) => {
        if (request.method() !== 'GET') {
          return route.fallback()
        }
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(SUMMARY_RESPONSE),
        })
      },
    )

    await page.route(
      '**/api/v1/agents/commercial-property/properties/*/advisory/feedback',
      async (route, request) => {
        if (request.method() !== 'POST') {
          return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(SUMMARY_RESPONSE.feedback),
          })
        }

        const payload = request.postDataJSON() as Record<string, unknown>
        expect(payload).toMatchObject({
          sentiment: 'positive',
          notes: 'Site visit confirmed podium activation opportunities.',
        })

        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify(FEEDBACK_RESPONSE),
        })
      },
    )
  })

  test('surfaces advisory insights for seeded property', async ({ page }) => {
    await page.goto(`/legacy/agents/advisory?propertyId=${PROPERTY_ID}`)

    await expect(
      page.getByRole('heading', { name: /asset mix strategy/i }),
    ).toBeVisible()
    await expect(page.getByRole('cell', { name: 'office' })).toBeVisible()
    await expect(page.getByRole('cell', { name: '55' })).toBeVisible()
    await expect(
      page.getByText('Retain flexibility for podium conversion.'),
    ).toBeVisible()

    await expect(
      page.getByRole('heading', { name: /market positioning/i }),
    ).toBeVisible()
    await expect(page.getByText('Prime fringe')).toBeVisible()
    await expect(page.getByText('Asset-light MNC')).toBeVisible()
    await expect(
      page.getByText('Position as next-generation fringe CBD alternative.'),
    ).toBeVisible()

    await expect(
      page.getByRole('heading', { name: /absorption forecast/i }),
    ).toBeVisible()
    await expect(page.getByText(/Expected Stabilisation/i)).toBeVisible()
    await expect(page.getByText('Monthly Absorption')).toBeVisible()

    await expect(
      page.getByText('Awaiting updated pricing guidance.', { exact: false }),
    ).toBeVisible()
  })

  test('records new agent feedback and renders it immediately', async ({
    page,
  }) => {
    await page.goto(`/legacy/agents/advisory?propertyId=${PROPERTY_ID}`)

    await page
      .getByLabel('Notes')
      .fill('Site visit confirmed podium activation opportunities.')

    const submitButton = page.getByRole('button', { name: 'Record feedback' })
    await expect(submitButton).toBeEnabled()
    await submitButton.click()

    const recentActivityPanel = page.locator('.advisory-panel', {
      has: page.getByRole('heading', { name: /recent activity/i }),
    })

    await expect(
      recentActivityPanel.getByText(
        'Site visit confirmed podium activation opportunities.',
      ),
    ).toBeVisible()
    await expect(
      recentActivityPanel.getByText('positive', { exact: true }),
    ).toBeVisible()
  })
})
