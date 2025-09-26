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

test('runFinanceFeasibility serialises payloads and maps responses', async () => {
  const calls = []
  const originalFetch = global.fetch

  global.fetch = async (input, init) => {
    calls.push({ input, init })
    return new Response(
      JSON.stringify({
        scenario_id: 9,
        project_id: 401,
        fin_project_id: 1234,
        scenario_name: 'Scenario A',
        currency: 'SGD',
        escalated_cost: '41000000',
        cost_index: {
          series_name: 'construction_all_in',
          jurisdiction: 'SG',
          base_period: '2024-Q1',
          latest_period: '2024-Q2',
          scalar: '1.03',
          base_index: {
            period: '2024-Q1',
            value: '100',
            unit: 'index',
            source: 'Public',
          },
          latest_index: {
            period: '2024-Q2',
            value: '103',
            unit: 'index',
            provider: 'Public',
          },
        },
        results: [
          { name: 'npv', value: '1200000', unit: 'currency', metadata: { source: 'demo' } },
          { name: 'irr', value: '0.12', unit: 'ratio', metadata: null },
        ],
        dscr_timeline: [
          { period: 'M1', noi: '0', debt_service: '0', dscr: null, currency: 'SGD' },
          { period: 'M2', noi: '3500000', debt_service: '3100000', dscr: '1.13', currency: 'SGD' },
        ],
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    )
  }

  const { runFinanceFeasibility } = loadModule(
    path.resolve(__dirname, '../src/api/finance.ts'),
  )

  try {
    const summary = await runFinanceFeasibility({
      projectId: 401,
      projectName: 'Finance Demo Development',
      finProjectId: 1234,
      scenario: {
        name: 'Scenario A',
        description: 'Baseline case',
        currency: 'SGD',
        isPrimary: true,
        costEscalation: {
          amount: '41000000',
          basePeriod: '2024-Q1',
          seriesName: 'construction_all_in',
          jurisdiction: 'SG',
          provider: 'Public',
        },
        cashFlow: {
          discountRate: '0.075',
          cashFlows: ['-2500000', '4200000'],
        },
        dscr: {
          netOperatingIncomes: ['0', '3500000'],
          debtServices: ['0', '3100000'],
          periodLabels: ['M1', 'M2'],
        },
      },
    })

    assert.strictEqual(calls.length, 1)
    assert.strictEqual(calls[0].input, '/api/v1/finance/feasibility')

    assert.deepEqual(calls[0].init.headers, {
      'Content-Type': 'application/json',
      'X-Role': 'admin',
    })

    const body = JSON.parse(calls[0].init.body)
    assert.deepEqual(body, {
      project_id: 401,
      project_name: 'Finance Demo Development',
      fin_project_id: 1234,
      scenario: {
        name: 'Scenario A',
        description: 'Baseline case',
        currency: 'SGD',
        is_primary: true,
        cost_escalation: {
          amount: '41000000',
          base_period: '2024-Q1',
          series_name: 'construction_all_in',
          jurisdiction: 'SG',
          provider: 'Public',
        },
        cash_flow: {
          discount_rate: '0.075',
          cash_flows: ['-2500000', '4200000'],
        },
        dscr: {
          net_operating_incomes: ['0', '3500000'],
          debt_services: ['0', '3100000'],
          period_labels: ['M1', 'M2'],
        },
      },
    })

    assert.strictEqual(summary.scenarioId, 9)
    assert.strictEqual(summary.projectId, 401)
    assert.strictEqual(summary.finProjectId, 1234)
    assert.strictEqual(summary.scenarioName, 'Scenario A')
    assert.strictEqual(summary.currency, 'SGD')
    assert.strictEqual(summary.escalatedCost, '41000000')
    assert.strictEqual(summary.costIndex.seriesName, 'construction_all_in')
    assert.strictEqual(summary.costIndex.latestPeriod, '2024-Q2')
    assert.strictEqual(summary.results.length, 2)
    assert.strictEqual(summary.results[0].name, 'npv')
    assert.deepEqual(summary.results[0].metadata, { source: 'demo' })
    assert.strictEqual(summary.dscrTimeline.length, 2)
    assert.strictEqual(summary.dscrTimeline[1].dscr, '1.13')
  } finally {
    restoreFetch(originalFetch)
  }
})

test('runFinanceFeasibility throws helpful error when response is not ok', async () => {
  const originalFetch = global.fetch

  global.fetch = async () =>
    new Response('boom', {
      status: 500,
      headers: { 'Content-Type': 'text/plain' },
    })

  const { runFinanceFeasibility } = loadModule(
    path.resolve(__dirname, '../src/api/finance.ts'),
  )

  try {
    await assert.rejects(
      () =>
        runFinanceFeasibility({
          projectId: 1,
          scenario: {
            name: 'Bad Scenario',
            currency: 'SGD',
            costEscalation: {
              amount: '0',
              basePeriod: '2024-Q1',
              seriesName: 'index',
              jurisdiction: 'SG',
            },
            cashFlow: { discountRate: '0.05', cashFlows: ['0'] },
          },
        }),
      /Finance feasibility request failed with status 500/i,
    )
  } finally {
    restoreFetch(originalFetch)
  }
})
