import assert from 'node:assert/strict'
import { afterEach, beforeEach, describe, it } from 'node:test'

import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { JSDOM } from 'jsdom'
import React from 'react'

import { TranslationProvider } from '../../i18n'
import AgentIntegrationsPage from '../AgentIntegrationsPage'

/**
 * KNOWN ISSUE: This test may fail with async timing issues in JSDOM.
 * See: ../../TESTING_KNOWN_ISSUES.md - "Frontend: React Testing Library Async Timing"
 *
 * If this test fails but the HTML dump shows content is rendered correctly,
 * the feature is working - it's a test harness issue, not an application bug.
 */

describe('AgentIntegrationsPage', () => {
  let dom: JSDOM
  const originalFetch = globalThis.fetch

  beforeEach(() => {
    dom = new JSDOM('<!doctype html><html><body></body></html>', {
      url: 'http://localhost/agents/integrations',
    })
    const globalWithDom = globalThis as typeof globalThis & {
      window: Window & typeof globalThis
      document: Document
      navigator: Navigator
    }
    globalWithDom.window = dom.window
    globalWithDom.document = dom.window.document
    globalWithDom.navigator = dom.window.navigator

    globalThis.fetch = (async (input: RequestInfo, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input.toString()

      const jsonResponse = (body: unknown, status = 200) =>
        new Response(JSON.stringify(body), {
          status,
          headers: { 'content-type': 'application/json' },
        })

      if (url.includes('/accounts')) {
        return jsonResponse([])
      }
      if (url.includes('/connect')) {
        expectJsonBody(init)
        return jsonResponse({
          id: 'account-1',
          user_id: 'user-1',
          provider: 'propertyguru',
          status: 'connected',
          metadata: {},
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        })
      }
      if (url.includes('/disconnect')) {
        return jsonResponse({ status: 'disconnected', provider: 'propertyguru' })
      }
      if (url.includes('/publish')) {
        expectJsonBody(init)
        return jsonResponse({
          listing_id: 'mock-listing-1',
          provider_payload: {},
        })
      }
      throw new Error(`Unhandled fetch call to ${url}`)
    }) as typeof globalThis.fetch
  })

  afterEach(() => {
    cleanup()
    dom.window.close()
    const globalWithDom = globalThis as {
      window?: Window & typeof globalThis
      document?: Document
      navigator?: Navigator
    }
    delete globalWithDom.window
    delete globalWithDom.document
    delete globalWithDom.navigator
    globalThis.fetch = originalFetch
  })

  it('links mock account and publishes listing', async () => {
    render(
      <TranslationProvider>
        <AgentIntegrationsPage />
      </TranslationProvider>,
    )

    await screen.findByRole('heading', { name: /Linked accounts/i }, { timeout: 2000 })

    // Submit the connect form
    fireEvent.submit(screen.getByText(/Link account/i).closest('form') as HTMLFormElement)
    await screen.findByText(/Mock PropertyGuru account linked/i, undefined, {
      timeout: 2000,
    })

    // Submit the publish form
    const publishForm = screen.getByText(/Publish mock listing/i).closest('form')
    assert.ok(publishForm)
    const propertyInput = screen.getByPlaceholderText(/e.g. 4271b4aa/i)
    fireEvent.change(propertyInput, { target: { value: 'property-id' } })
    fireEvent.submit(publishForm as HTMLFormElement)
    await screen.findByText(/Published mock listing/i, undefined, { timeout: 2000 })
  })
})

function expectJsonBody(init?: RequestInit) {
  if (!init || !init.body) {
    throw new Error('Expected JSON request body')
  }
}
