import { expect, test } from '@playwright/test'
import type { APIRequestContext, Page } from '@playwright/test'

const SEEDED_ADDRESSES = [
  { address: '123 Example Ave' },
  { address: '456 River Road' },
  { address: '789 Coastal Way' },
]

async function seedCurrentProject(page: Page, request: APIRequestContext) {
  const identityHeaders = {
    'X-Role': 'reviewer',
    'X-User-Email': 'e2e@example.com',
    'X-User-Id': 'e2e-user',
  }

  const response = await request.get(
    'http://127.0.0.1:8000/api/v1/projects/list',
    { headers: identityHeaders },
  )
  expect(response.ok()).toBeTruthy()
  const projects = await response.json()
  let project =
    Array.isArray(projects) && projects.length > 0 ? projects[0] : null

  if (!project) {
    const createResponse = await request.post(
      'http://127.0.0.1:8000/api/v1/projects/create',
      {
        headers: identityHeaders,
        data: {
          name: `Feasibility Test ${Date.now()}`,
          description: 'Playwright seeded project for feasibility tests.',
        },
      },
    )
    expect(createResponse.ok()).toBeTruthy()
    project = await createResponse.json()
  }

  if (!project?.id || !(project?.name || project?.project_name)) {
    throw new Error('Feasibility test project payload missing id or name.')
  }

  await page.addInitScript(
    (projectValue) => {
      window.__e2eProjectSeeded = true
      window.__e2eFetchIntercepted = false
      const originalFetch = window.fetch.bind(window)
      window.fetch = (input, init) => {
        const url = typeof input === 'string' ? input : input.url
        if (url.includes('/api/v1/projects/list')) {
          window.__e2eFetchIntercepted = true
          return Promise.resolve(
            new Response(JSON.stringify([projectValue.project]), {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            }),
          )
        }
        return originalFetch(input, init)
      }
      window.localStorage.setItem('app:api-role', projectValue.identity.role)
      window.localStorage.setItem(
        'app:api-user-email',
        projectValue.identity.email,
      )
      window.localStorage.setItem(
        'app:api-user-id',
        projectValue.identity.userId,
      )
      window.localStorage.setItem(
        'ob_current_project',
        JSON.stringify(projectValue.project),
      )
      window.localStorage.setItem('ob_skip_project_validation', 'true')
    },
    {
      identity: {
        role: identityHeaders['X-Role'],
        email: identityHeaders['X-User-Email'],
        userId: identityHeaders['X-User-Id'],
      },
      project: {
        id: project.id,
        name: project.name ?? project.project_name,
        status: project.status,
      },
    },
  )
  return project
}

async function gotoFeasibility(page: Page) {
  await page.goto('/feasibility')
  await page.waitForFunction(() => window.__e2eProjectSeeded === true)
  await page.waitForFunction(() => window.__e2eFetchIntercepted === true)
}

test.describe('Feasibility wizard', () => {
  for (const { address } of SEEDED_ADDRESSES) {
    test(`renders backend data for ${address}`, async ({ page, request }) => {
      await seedCurrentProject(page, request)

      await gotoFeasibility(page)
      await page.getByTestId('address-input').fill(address)
      await page.getByTestId('site-area-input').fill('1000')
      await page.getByTestId('compute-button').click()

      const announcement = page.locator('div[aria-live="polite"]')
      await expect(announcement).toContainText(
        /Feasibility updated for zone/i,
      )
    })
  }

  test('recomputes when assumptions change with debounce', async ({
    page,
    request,
  }) => {
    await seedCurrentProject(page, request)
    const address = SEEDED_ADDRESSES[0].address

    await page.addInitScript(() => {
      window.__computeEvents = []
      window.addEventListener('feasibility.compute', (event) => {
        window.__computeEvents.push(event.detail)
      })
    })

    await gotoFeasibility(page)
    await page.getByTestId('address-input').fill(address)
    await page.getByTestId('site-area-input').fill('1000')
    await page.getByTestId('compute-button').click()
    await expect(page.locator('div[aria-live=\"polite\"]')).toContainText(
      /Feasibility updated for zone/i,
    )

    const eventsBefore = await page.evaluate(
      () => window.__computeEvents.length,
    )
    await page.fill('#assumption-efficiency', '0.75')
    await page.waitForFunction(
      (previousCount) => window.__computeEvents.length > previousCount,
      eventsBefore,
    )
    const lastEvent = await page.evaluate(
      () => window.__computeEvents[window.__computeEvents.length - 1],
    )
    expect(lastEvent.status).toBe('success')
    expect(lastEvent.durationMs).toBeLessThan(500)

    await expect(page.locator('div[aria-live=\"polite\"]')).toContainText(
      /Feasibility updated for zone/i,
    )
  })
})
