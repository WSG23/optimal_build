import assert from 'node:assert/strict'
import { describe, it } from 'node:test'

import {
  runFinanceFeasibility,
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
      projectId: 401,
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
      assert.equal(summary.capitalStack?.currency, 'SGD')
      assert.equal(summary.capitalStack?.slices.length, 2)
      assert.equal(summary.capitalStack?.slices[0]?.category, 'equity')
      assert.equal(summary.drawdownSchedule?.entries.length, 2)
      assert.equal(summary.drawdownSchedule?.entries[1]?.outstandingDebt, '300.00')
    } finally {
      globalThis.fetch = originalFetch
    }
  })
})
