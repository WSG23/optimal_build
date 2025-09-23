const test = require('node:test')
const assert = require('node:assert/strict')
const path = require('node:path')

const { loadModule } = require('./helpers/loadModule.cjs')

function restoreFetch(originalFetch) {
  if (originalFetch) {
    global.fetch = originalFetch
  } else {
    delete global.fetch
  }
}

test('fetchBuildable serialises request payload to snake_case', async () => {
  const calls = []
  const originalFetch = global.fetch
  global.fetch = async (input, init) => {
    calls.push({ input, init })
    return new Response(
      JSON.stringify({
        input_kind: 'address',
        zone_code: 'R2',
        overlays: [],
        advisory_hints: [],
        metrics: {
          gfa_cap_m2: 1000,
          floors_max: 5,
          footprint_m2: 200,
          nsa_est_m2: 800,
        },
        zone_source: {
          kind: 'parcel',
        },
        rules: [],
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    )
  }

  const { fetchBuildable } = loadModule(
    path.resolve(__dirname, '../src/api/buildable.ts'),
  )

  await fetchBuildable({
    address: '123 Example Ave',
    typFloorToFloorM: 3.4,
    efficiencyRatio: 0.8,
  })

  restoreFetch(originalFetch)

  assert.strictEqual(calls.length, 1)
  const body = JSON.parse(calls[0].init.body)
  assert.deepEqual(body, {
    address: '123 Example Ave',
    typ_floor_to_floor_m: 3.4,
    efficiency_ratio: 0.8,
  })
})

test('fetchBuildable maps response to camelCase fields', async () => {
  const originalFetch = global.fetch
  global.fetch = async () =>
    new Response(
      JSON.stringify({
        input_kind: 'address',
        zone_code: 'R2',
        overlays: ['heritage'],
        advisory_hints: ['hint'],
        metrics: {
          gfa_cap_m2: 4375,
          floors_max: 8,
          footprint_m2: 563,
          nsa_est_m2: 3588,
        },
        zone_source: {
          kind: 'parcel',
          layer_name: 'MasterPlan',
          parcel_ref: 'MK01-01234',
        },
        rules: [
          {
            id: 10,
            authority: 'URA',
            parameter_key: 'zoning.max_far',
            operator: '<=',
            value: '3.5',
            unit: null,
            provenance: {
              rule_id: 10,
              clause_ref: '4.2.1',
              document_id: 345,
              pages: [7],
              seed_tag: 'zoning',
            },
          },
        ],
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    )

  const { fetchBuildable } = loadModule(
    path.resolve(__dirname, '../src/api/buildable.ts'),
  )

  const result = await fetchBuildable({
    address: '456 River Road',
    typFloorToFloorM: 3.4,
    efficiencyRatio: 0.8,
  })

  restoreFetch(originalFetch)

  assert.strictEqual(result.zoneCode, 'R2')
  assert.deepEqual([...result.overlays], ['heritage'])
  assert.strictEqual(result.metrics.gfaCapM2, 4375)
  assert.strictEqual(result.zoneSource.layerName, 'MasterPlan')
  assert.strictEqual(result.rules[0].authority, 'URA')
  assert.deepEqual(result.rules[0].provenance.pages, [7])
})

test('fetchBuildable can be mocked with createMockBuildableOptions', async () => {
  let calls = 0
  const originalFetch = global.fetch
  global.fetch = async () => {
    calls += 1
    throw new Error('fetch should not run when using mock transport')
  }

  const { fetchBuildable } = loadModule(
    path.resolve(__dirname, '../src/api/buildable.ts'),
  )
  const { createMockBuildableOptions } = loadModule(
    path.resolve(__dirname, '../src/mocks/buildable.ts'),
  )

  const result = await fetchBuildable(
    {
      address: '456 River Road',
      typFloorToFloorM: 3.4,
      efficiencyRatio: 0.8,
    },
    createMockBuildableOptions(),
  )

  restoreFetch(originalFetch)

  assert.strictEqual(calls, 0)
  assert.strictEqual(result.zoneCode, 'C1')
  assert.deepEqual([...result.overlays], ['airport'])
})
