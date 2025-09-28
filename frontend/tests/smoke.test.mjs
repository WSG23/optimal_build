import assert from 'node:assert/strict'
import test from 'node:test'

import React from 'react'
import { renderToString } from 'react-dom/server'

import { loadComponent } from './utils.mjs'

test('App renders the expected headline', async () => {
    const { default: App } = await loadComponent('tests/support/appEntry.tsx')
    const html = renderToString(React.createElement(App))
    const expectedHeadingText = 'Optimal Build Studio'
    const headingPattern = new RegExp(
        `<h1[^>]*>\\s*${expectedHeadingText.replace(
            /[-/\\^$*+?.()|[\]{}]/g,
            '\\$&',
        )}\\s*<\\/h1>`,
        'i',
    )
    assert.match(
        html,
        headingPattern,
        `Expected heading to contain "${expectedHeadingText}"`,
    )
})
