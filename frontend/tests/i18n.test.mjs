import assert from 'node:assert/strict'
import test from 'node:test'

import React from 'react'
import { renderToString } from 'react-dom/server'

import { getGlobalI18n, loadComponent } from './utils.mjs'

const japaneseTagline =
  'シンガポールの開発向けに、コンプライアンスのインサイト、土地インテリジェンス、フィージビリティ分析を自動で探索しましょう。'

await test('internationalisation renders expected content', async (t) => {
  await t.test('App renders Japanese tagline when locale is set to ja', async () => {
    const { default: App } = await loadComponent('tests/support/appEntry.tsx')
    const i18n = getGlobalI18n()
    await i18n.changeLanguage('ja')

    const html = renderToString(React.createElement(App))
    assert.ok(
      html.includes(japaneseTagline),
      'Expected Japanese tagline to be rendered in the App component',
    )

    await i18n.changeLanguage('en')
  })

  await t.test('Feasibility wizard falls back to English for unsupported locales', async () => {
    const { default: FeasibilityWizard } = await loadComponent(
      'tests/support/feasibilityWizardEntry.tsx',
    )
    const i18n = getGlobalI18n()
    await i18n.changeLanguage('fr')

    const html = renderToString(React.createElement(FeasibilityWizard))
    assert.ok(
      html.includes('Feasibility assessment'),
      'Expected wizard heading to use English fallback when locale is unsupported',
    )

    await i18n.changeLanguage('en')
  })
})
