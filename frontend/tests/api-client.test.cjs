const test = require('node:test')
const assert = require('node:assert/strict')
const path = require('path')

const { loadModule } = require('./helpers/loadModule.cjs')

const { ApiClient } = loadModule(path.resolve(__dirname, '../src/api/client.ts'))

test('uploadCadDrawing returns overlays and hints from backend', async () => {
  const originalFetch = global.fetch
  global.fetch = async () =>
    new Response(
      JSON.stringify({ overlays: ['fire_access'], advisory_hints: ['Ensure access clearance'] }),
      { status: 200 },
    )

  const client = new ApiClient('http://example.com/')
  const job = await client.uploadCadDrawing({ name: 'site.dxf', size: 1024 }, { zoneCode: 'RA' })

  if (originalFetch) {
    global.fetch = originalFetch
  } else {
    delete global.fetch
  }

  assert.strictEqual(job.status, 'ready')
  assert.deepEqual(job.overlays, ['fire_access'])
  assert.deepEqual(job.hints, ['Ensure access clearance'])
})

test('getDefaultPipelineSuggestions prioritises overlay matches', async () => {
  const client = new ApiClient('http://example.com/')
  client.listRules = async () => [
    {
      id: 1,
      parameterKey: 'fire.width',
      operator: '>=',
      value: '4.5',
      unit: 'm',
      authority: 'SCDF',
      topic: 'Fire safety',
      reviewStatus: 'approved',
      overlays: ['fire_access'],
      advisoryHints: ['Ensure access clearance'],
      normalized: [],
    },
    {
      id: 2,
      parameterKey: 'zoning.plot_ratio',
      operator: '<=',
      value: '3.5',
      unit: null,
      authority: 'URA',
      topic: 'Zoning',
      reviewStatus: 'approved',
      overlays: ['coastal'],
      advisoryHints: [],
      normalized: [],
    },
  ]

  const suggestions = await client.getDefaultPipelineSuggestions({ overlays: ['fire_access'], hints: [] })
  assert.ok(suggestions.length > 0)
  assert.strictEqual(suggestions[0].relatedRuleIds.includes(1), true)
  assert.ok(suggestions[0].focus.toLowerCase().includes('fire'))
})
