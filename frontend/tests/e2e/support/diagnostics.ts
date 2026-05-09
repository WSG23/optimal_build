import { test as base } from '@playwright/test'

const DIAGNOSTICS_KEY = Symbol('e2eDiagnostics')

type DiagnosticPage = Parameters<
  Parameters<typeof base.beforeEach>[0]
>[0]['page'] & {
  [DIAGNOSTICS_KEY]?: string[]
}

export const installE2EDiagnostics = (test: typeof base) => {
  test.beforeEach(async ({ page }) => {
    const diagnosticPage = page as DiagnosticPage
    const messages: string[] = []
    diagnosticPage[DIAGNOSTICS_KEY] = messages

    page.on('console', (message) => {
      messages.push(`[console:${message.type()}] ${message.text()}`)
    })

    page.on('pageerror', (error) => {
      messages.push(`[pageerror] ${error.stack ?? error.message}`)
    })

    page.on('requestfailed', (request) => {
      messages.push(
        `[requestfailed] ${request.method()} ${request.url()} ${
          request.failure()?.errorText ?? 'unknown error'
        }`,
      )
    })

    page.on('response', (response) => {
      if (response.status() >= 400) {
        messages.push(`[response:${response.status()}] ${response.url()}`)
      }
    })
  })

  test.afterEach(async ({ page }, testInfo) => {
    if (testInfo.status === testInfo.expectedStatus) {
      return
    }

    const messages = (page as DiagnosticPage)[DIAGNOSTICS_KEY] ?? []
    if (messages.length > 0) {
      await testInfo.attach('browser-diagnostics.txt', {
        body: messages.join('\n'),
        contentType: 'text/plain',
      })
    }

    const html = await page
      .content()
      .catch(
        (error: Error) => `Unable to capture page content: ${error.message}`,
      )

    await testInfo.attach('page-content.html', {
      body: html,
      contentType: 'text/html',
    })
  })
}
