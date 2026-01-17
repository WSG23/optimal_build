import { afterEach, assert, beforeEach, describe, it } from 'vitest'

import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from '@testing-library/react'

import React from 'react'

import { TranslationProvider } from '../../i18n'
import { ThemeModeProvider } from '../../theme/ThemeContext'
import AgentIntegrationsPage from '../AgentIntegrationsPage'

/**
 * ⚠️ KNOWN ISSUE: This test may fail with async timing issues in JSDOM.
 *
 * See: docs/all_steps_to_product_completion.md#-known-testing-issues
 * Section: "Frontend: React Testing Library Async Timing"
 *
 * If this test fails but the HTML dump shows content is rendered correctly,
 * the feature is working - it's a test harness issue, not an application bug.
 *
 * When this is fixed, update the Known Testing Issues section per the maintenance checklist.
 */

describe('AgentIntegrationsPage', () => {
  const originalFetch = globalThis.fetch

  beforeEach(() => {
    cleanup()
    window.history.replaceState(null, '', '/agents/integrations')

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
      if (url.includes('/propertyguru/connect')) {
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
      if (url.includes('/edgeprop/connect')) {
        expectJsonBody(init)
        return jsonResponse({
          id: 'account-2',
          user_id: 'user-1',
          provider: 'edgeprop',
          status: 'connected',
          metadata: {},
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        })
      }
      if (url.includes('/zoho_crm/connect')) {
        expectJsonBody(init)
        return jsonResponse({
          id: 'account-3',
          user_id: 'user-1',
          provider: 'zoho_crm',
          status: 'connected',
          metadata: {},
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        })
      }
      if (url.includes('/disconnect')) {
        const provider = url.split('/').slice(-2)[0]
        return jsonResponse({ status: 'disconnected', provider })
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
    globalThis.fetch = originalFetch
  })

  it(
    'links mock account and publishes listing',
    { timeout: 10000 },
    async () => {
      render(
        <ThemeModeProvider>
          <TranslationProvider>
            <AgentIntegrationsPage />
          </TranslationProvider>
        </ThemeModeProvider>,
      )

      await screen.findByRole(
        'heading',
        { name: /Linked accounts/i },
        { timeout: 2000 },
      )

      const propertyGuruSection = screen.getByRole('heading', {
        name: /PropertyGuru/i,
      }).parentElement as HTMLElement

      fireEvent.submit(
        propertyGuruSection.querySelector('form') as HTMLFormElement,
      )
      await screen.findByText(/PropertyGuru .*account linked/i, undefined, {
        timeout: 2000,
      })

      const publishForms = propertyGuruSection.querySelectorAll('form')
      const publishForm = publishForms[publishForms.length - 1]
      assert.ok(publishForm)
      const propertyInput = within(
        publishForm as HTMLElement,
      ).getByPlaceholderText(/e.g. 4271b4aa/i)
      fireEvent.change(propertyInput, { target: { value: 'property-id' } })
      fireEvent.submit(publishForm as HTMLFormElement)
      await screen.findByText(/published .*mock-listing-1/i, undefined, {
        timeout: 5000,
      })
    },
  )
})

function expectJsonBody(init?: RequestInit) {
  if (!init || !init.body) {
    throw new Error('Expected JSON request body')
  }
}
