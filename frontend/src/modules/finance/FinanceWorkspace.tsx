import { AppLayout } from '../../App'
import { useTranslation } from '../../i18n'
import { FinanceScenarioTable } from './components/FinanceScenarioTable'
import { FinanceCapitalStack } from './components/FinanceCapitalStack'
import { FinanceDrawdownSchedule } from './components/FinanceDrawdownSchedule'
import { useFinanceScenarios } from './hooks/useFinanceScenarios'

const FINANCE_PROJECT_ID = 401
export function FinanceWorkspace() {
  const { t } = useTranslation()
  const { scenarios, loading, error, refresh } = useFinanceScenarios({
    projectId: FINANCE_PROJECT_ID,
  })

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
