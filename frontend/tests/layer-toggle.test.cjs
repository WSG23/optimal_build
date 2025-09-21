const test = require('node:test')
const assert = require('node:assert/strict')
const path = require('path')

const { loadModule } = require('./helpers/loadModule.cjs')

const { computeNextLayers } = loadModule(
  path.resolve(__dirname, '../src/modules/cad/layerToggle.ts'),
)

test('computeNextLayers removes an active layer', () => {
  const result = computeNextLayers(['source', 'pending'], 'pending')
  assert.strictEqual(result.length, 1)
  assert.ok(result.includes('source'))
})

test('computeNextLayers adds a missing layer', () => {
  const result = computeNextLayers(['source'], 'approved')
  assert.strictEqual(result.length, 2)
  assert.ok(result.includes('source'))
  assert.ok(result.includes('approved'))
})
