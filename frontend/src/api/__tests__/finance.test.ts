import { describe, expect, it } from 'vitest'

import {
  runFinanceFeasibility,
  listFinanceScenarios,
  type FinanceFeasibilityRequest,
} from '../finance'

describe('finance API mapping', () => {
  it('maps capital stack and drawdown schedule fields from the finance API', async () => {
    const originalFetch = globalThis.fetch
    globalThis.fetch = (async () => ({
      ok: true,
      status: 200,
      async json() {
        return {
          scenario_id: 101,
          project_id: 401,
          fin_project_id: 12,
          scenario_name: 'QA Scenario',
          currency: 'SGD',
          escalated_cost: '1200.00',
          cost_index: {
            series_name: 'construction_all_in',
            jurisdiction: 'SG',
            provider: 'Test',
            base_period: '2024-Q1',
            latest_period: '2024-Q4',
            scalar: '1.2000',
            base_index: null,
            latest_index: null,
          },
          results: [],
          dscr_timeline: [],
          capital_stack: {
            currency: 'SGD',
            total: '1200.00',
            equity_total: '400.00',
            debt_total: '800.00',
            other_total: '0.00',
            equity_ratio: '0.3333',
            debt_ratio: '0.6667',
            other_ratio: '0.0000',
            loan_to_cost: '0.6667',
            weighted_average_debt_rate: '0.0650',
            slices: [
              {
                name: 'Sponsor Equity',
                source_type: 'equity',
                category: 'equity',
                amount: '400.00',
                share: '0.3333',
                rate: null,
                tranche_order: 0,
                metadata: {},
              },
              {
                name: 'Senior Loan',
                source_type: 'debt',
                category: 'debt',
                amount: '800.00',
                share: '0.6667',
                rate: '0.0650',
                tranche_order: 1,
                metadata: {},
              },
            ],
          },
          drawdown_schedule: {
            currency: 'SGD',
            entries: [
              {
                period: 'M0',
                equity_draw: '150.00',
                debt_draw: '0.00',
                total_draw: '150.00',
                cumulative_equity: '150.00',
                cumulative_debt: '0.00',
                outstanding_debt: '0.00',
              },
              {
                period: 'M1',
                equity_draw: '250.00',
                debt_draw: '300.00',
                total_draw: '550.00',
                cumulative_equity: '400.00',
                cumulative_debt: '300.00',
                outstanding_debt: '300.00',
              },
            ],
            total_equity: '400.00',
            total_debt: '800.00',
            peak_debt_balance: '800.00',
            final_debt_balance: '800.00',
          },
        }
      },
    })) as typeof globalThis.fetch

    const request: FinanceFeasibilityRequest = {
      projectId: '401',
      scenario: {
        name: 'QA Scenario',
        currency: 'SGD',
        isPrimary: true,
        costEscalation: {
          amount: '1000',
          basePeriod: '2024-Q1',
          seriesName: 'construction_all_in',
          jurisdiction: 'SG',
        },
        cashFlow: {
          discountRate: '0.08',
          cashFlows: ['-1000', '1200'],
        },
      },
    }

    try {
      const summary = await runFinanceFeasibility(request)
      expect(summary.capitalStack?.currency).toBe('SGD')
      expect(summary.capitalStack?.slices.length).toBe(2)
      expect(summary.capitalStack?.slices[0]?.category).toBe('equity')
      expect(summary.drawdownSchedule?.entries.length).toBe(2)
      expect(summary.drawdownSchedule?.entries[1]?.outstandingDebt).toBe(
        '300.00',
      )
    } finally {
      globalThis.fetch = originalFetch
    }
  })

  it('fetches persisted finance scenarios and maps responses', async () => {
    const originalFetch = globalThis.fetch
    globalThis.fetch = (async (input) => {
      const url = typeof input === 'string' ? input : input.toString()
      expect(url.includes('/api/v1/finance/scenarios?project_id=401')).toBe(
        true,
      )
      return {
        ok: true,
        status: 200,
        async json() {
          return [
            {
              scenario_id: 26,
              project_id: 401,
              fin_project_id: 12,
              scenario_name: 'Seeded Scenario',
              currency: 'SGD',
              escalated_cost: '38950000.00',
              cost_index: {
                series_name: 'construction_all_in',
                jurisdiction: 'SG',
                provider: 'Public',
                base_period: '2024-Q1',
                latest_period: '2024-Q4',
                scalar: '1.2000',
                base_index: null,
                latest_index: null,
              },
              results: [],
              dscr_timeline: [],
              capital_stack: null,
              drawdown_schedule: null,
            },
          ]
        },
      }
    }) as typeof globalThis.fetch

    try {
      const summaries = await listFinanceScenarios({ projectId: '401' })
      expect(summaries.length).toBe(1)
      expect(summaries[0]?.scenarioId).toBe(26)
      expect(summaries[0]?.projectId).toBe(401)
    } finally {
      globalThis.fetch = originalFetch
    }
  })

  it('falls back to offline feasibility data when the request hits a network error', async () => {
    const originalFetch = globalThis.fetch
    globalThis.fetch = (async () => {
      throw new TypeError('Load failed')
    }) as typeof globalThis.fetch

    const request: FinanceFeasibilityRequest = {
      projectId: '510',
      scenario: {
        name: 'Offline Mixed-Use Scenario',
        currency: 'USD',
        costEscalation: {
          amount: '24000000.00',
          basePeriod: '2024-Q1',
          seriesName: 'construction_all_in',
          jurisdiction: 'SG',
        },
        cashFlow: {
          discountRate: '0.08',
          cashFlows: [],
        },
      },
    }

    try {
      const summary = await runFinanceFeasibility(request)
      expect(summary.projectId).toBe('510')
      expect(summary.scenarioName).toBe('Offline Mixed-Use Scenario')
      expect(summary.currency).toBe('USD')
      expect(summary.results.length).toBeGreaterThan(0)
      expect(summary.capitalStack).not.toBeNull()
    } finally {
      globalThis.fetch = originalFetch
    }
  })

  it('provides an offline scenario list when listing scenarios fails with a network error', async () => {
    const originalFetch = globalThis.fetch
    globalThis.fetch = (async () => {
      throw new TypeError('Network request failed')
    }) as typeof globalThis.fetch

    try {
      const scenarios = await listFinanceScenarios({ projectId: 777 })
      expect(scenarios.length).toBe(3)
      expect(scenarios.map((scenario) => scenario.scenarioId)).toEqual([
        0, -1, -2,
      ])
      expect(scenarios.every((scenario) => scenario.projectId === 777)).toBe(
        true,
      )
      expect(scenarios.every((scenario) => scenario.capitalStack != null)).toBe(
        true,
      )
    } finally {
      globalThis.fetch = originalFetch
    }
  })
})
