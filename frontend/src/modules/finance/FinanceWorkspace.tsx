import { AppLayout } from '../../App'
import { useTranslation } from '../../i18n'
import {
  type FinanceFeasibilityRequest,
  type FinanceScenarioInput,
} from '../../api/finance'
import { FinanceScenarioTable } from './components/FinanceScenarioTable'
import { FinanceCapitalStack } from './components/FinanceCapitalStack'
import { FinanceDrawdownSchedule } from './components/FinanceDrawdownSchedule'
import { useFinanceFeasibility } from './hooks/useFinanceFeasibility'

const FINANCE_PROJECT_ID = 401
const FINANCE_PROJECT_NAME = 'Finance Demo Development'

const FINANCE_SCENARIOS: readonly FinanceScenarioInput[] = [
  {
    name: 'Scenario A – Base Case',
    description: 'Baseline absorption with phased sales releases.',
    currency: 'SGD',
    isPrimary: true,
    costEscalation: {
      amount: '38950000',
      basePeriod: '2024-Q1',
      seriesName: 'construction_all_in',
      jurisdiction: 'SG',
      provider: 'Public',
    },
    cashFlow: {
      discountRate: '0.08',
      cashFlows: [
        '-2500000',
        '-4100000',
        '-4650000',
        '-200000',
        '4250000',
        '10200000',
      ],
    },
    dscr: {
      netOperatingIncomes: [
        '0',
        '0',
        '3800000',
        '5600000',
        '7200000',
        '7800000',
      ],
      debtServices: ['0', '0', '3200000', '3300000', '3400000', '3400000'],
      periodLabels: ['M1', 'M2', 'M3', 'M4', 'M5', 'M6'],
    },
  },
  {
    name: 'Scenario B – Upside Release',
    description: 'Faster sales velocity with premium unit mix.',
    currency: 'SGD',
    isPrimary: false,
    costEscalation: {
      amount: '41100000',
      basePeriod: '2024-Q1',
      seriesName: 'construction_all_in',
      jurisdiction: 'SG',
      provider: 'Public',
    },
    cashFlow: {
      discountRate: '0.075',
      cashFlows: [
        '-2750000',
        '-4250000',
        '-4900000',
        '50000',
        '5700000',
        '11350000',
      ],
    },
    dscr: {
      netOperatingIncomes: [
        '0',
        '0',
        '4200000',
        '6500000',
        '8200000',
        '9200000',
      ],
      debtServices: ['0', '0', '3100000', '3200000', '3200000', '3200000'],
      periodLabels: ['M1', 'M2', 'M3', 'M4', 'M5', 'M6'],
    },
  },
  {
    name: 'Scenario C – Downside Stress',
    description: 'Conservative absorption with extended sales cycle.',
    currency: 'SGD',
    isPrimary: false,
    costEscalation: {
      amount: '36800000',
      basePeriod: '2024-Q1',
      seriesName: 'construction_all_in',
      jurisdiction: 'SG',
      provider: 'Public',
    },
    cashFlow: {
      discountRate: '0.085',
      cashFlows: [
        '-2250000',
        '-3750000',
        '-4100000',
        '-850000',
        '1900000',
        '6500000',
      ],
    },
    dscr: {
      netOperatingIncomes: [
        '0',
        '0',
        '3200000',
        '4500000',
        '5200000',
        '5800000',
      ],
      debtServices: ['0', '0', '3100000', '3200000', '3250000', '3250000'],
      periodLabels: ['M1', 'M2', 'M3', 'M4', 'M5', 'M6'],
    },
  },
]

const FINANCE_REQUESTS: readonly FinanceFeasibilityRequest[] =
  FINANCE_SCENARIOS.map((scenario) => ({
    projectId: FINANCE_PROJECT_ID,
    projectName: FINANCE_PROJECT_NAME,
    scenario,
  }))

export function FinanceWorkspace() {
  const { t } = useTranslation()
  const { scenarios, loading, error, refresh } =
    useFinanceFeasibility(FINANCE_REQUESTS)

  const showEmptyState = !loading && !error && scenarios.length === 0

  return (
    <AppLayout
      title={t('finance.title')}
      subtitle={t('finance.subtitle')}
      actions={
        <button
          type="button"
          className="finance-workspace__refresh"
          onClick={refresh}
          disabled={loading}
        >
          {loading
            ? t('finance.actions.refreshing')
            : t('finance.actions.refresh')}
        </button>
      }
    >
      <section className="finance-workspace">
        {error && (
          <div className="finance-workspace__error" role="alert">
            <strong>{t('finance.errors.generic')}</strong>
            <span className="finance-workspace__error-detail">{error}</span>
          </div>
        )}
        {loading && (
          <p className="finance-workspace__status">{t('common.loading')}</p>
        )}
        {showEmptyState && (
          <p className="finance-workspace__empty">{t('finance.table.empty')}</p>
        )}
        {scenarios.length > 0 && (
          <div className="finance-workspace__sections">
            <FinanceScenarioTable scenarios={scenarios} />
            <FinanceCapitalStack scenarios={scenarios} />
            <FinanceDrawdownSchedule scenarios={scenarios} />
          </div>
        )}
      </section>
    </AppLayout>
  )
}

export default FinanceWorkspace
