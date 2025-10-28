import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import {
  updateConstructionLoan,
  type ConstructionLoanInput,
} from '../../api/finance'
import { AppLayout } from '../../App'
import { useTranslation } from '../../i18n'
import { FinanceAssetBreakdown } from './components/FinanceAssetBreakdown'
import { FinanceCapitalStack } from './components/FinanceCapitalStack'
import { FinanceDrawdownSchedule } from './components/FinanceDrawdownSchedule'
import { FinanceFacilityEditor } from './components/FinanceFacilityEditor'
import { FinanceJobTimeline } from './components/FinanceJobTimeline'
import { FinanceLoanInterest } from './components/FinanceLoanInterest'
import { FinanceScenarioTable } from './components/FinanceScenarioTable'
import { FinanceSensitivityTable } from './components/FinanceSensitivityTable'
import { FinanceScenarioCreator } from './components/FinanceScenarioCreator'
import { useFinanceScenarios } from './hooks/useFinanceScenarios'

const FINANCE_PROJECT_ID = '825c99d2-5167-4546-994c-6fab0f832c78'
const FINANCE_PROJECT_NAME = 'Finance Demo Development'
const POLL_INTERVAL_MS = 5000
const IN_PROGRESS_STATUSES = new Set([
  'queued',
  'started',
  'in_progress',
  'processing',
])

function isJobPending(status?: string | null): boolean {
  if (!status) {
    return false
  }
  const key = status.toLowerCase()
  if (IN_PROGRESS_STATUSES.has(key)) {
    return true
  }
  return key !== 'completed' && key !== 'success' && key !== 'failed'
}

function escapeCsvValue(value: string | null | undefined): string {
  if (value == null) {
    return ''
  }
  const needsQuote = /[",\n]/.test(value)
  if (!needsQuote) {
    return value
  }
  return `"${value.replace(/"/g, '""')}"`
}

function downloadFile(content: string, filename: string, mime: string): void {
  if (typeof window === 'undefined') {
    return
  }
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.style.display = 'none'
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  URL.revokeObjectURL(url)
}

const DEFAULT_SENSITIVITY_HEADERS = [
  'parameter',
  'scenario',
  'delta_label',
  'delta_value',
  'npv',
  'irr',
  'escalated_cost',
  'total_interest',
]

export function FinanceWorkspace() {
  const { t } = useTranslation()
  const { scenarios, loading, error, refresh, addScenario } = useFinanceScenarios({
    projectId: FINANCE_PROJECT_ID,
  })
  const [savingLoan, setSavingLoan] = useState(false)
  const [loanError, setLoanError] = useState<string | null>(null)
  const [scenarioMessage, setScenarioMessage] = useState<string | null>(null)
  const [scenarioError, setScenarioError] = useState<string | null>(null)

  useEffect(() => {
    if (!scenarioMessage) {
      return undefined
    }
    const timer = window.setTimeout(() => {
      setScenarioMessage(null)
    }, 5000)
    return () => window.clearTimeout(timer)
  }, [scenarioMessage])

  useEffect(() => {
    if (!scenarioError) {
      return undefined
    }
    const timer = window.setTimeout(() => {
      setScenarioError(null)
    }, 7000)
    return () => window.clearTimeout(timer)
  }, [scenarioError])
  const [selectedParameters, setSelectedParameters] = useState<string[]>([])
  const pollRef = useRef<number | null>(null)
  const primaryScenario = useMemo(() => {
    if (scenarios.length === 0) {
      return null
    }
    const primary = scenarios.find((scenario) => scenario.isPrimary)
    if (primary) {
      return primary
    }
    return [...scenarios].sort((a, b) => b.scenarioId - a.scenarioId)[0]
  }, [scenarios])
  const showEmptyState = !loading && !error && scenarios.length === 0

  useEffect(() => {
    if (!primaryScenario) {
      setSelectedParameters([])
      return
    }
    const params = Array.from(
      new Set(
        primaryScenario.sensitivityResults
          .map((entry) => entry.parameter)
          .filter((value): value is string => Boolean(value)),
      ),
    )
    setSelectedParameters(params)
  }, [primaryScenario?.scenarioId, primaryScenario])

  useEffect(() => {
    if (typeof window === 'undefined') {
      return undefined
    }
    const hasPending = scenarios.some((scenario) =>
      scenario.sensitivityJobs.some((job) => isJobPending(job.status)),
    )
    if (!hasPending) {
      if (pollRef.current !== null) {
        window.clearInterval(pollRef.current)
        pollRef.current = null
      }
      return undefined
    }
    if (pollRef.current === null) {
      pollRef.current = window.setInterval(() => {
        refresh()
      }, POLL_INTERVAL_MS)
    }
    return () => {
      if (pollRef.current !== null) {
        window.clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
  }, [scenarios, refresh])

  const parameters = useMemo(() => {
    if (!primaryScenario) {
      return []
    }
    const set = new Set<string>()
    for (const outcome of primaryScenario.sensitivityResults) {
      if (outcome.parameter) {
        set.add(outcome.parameter)
      }
    }
    return Array.from(set)
  }, [primaryScenario])

  const filteredSensitivity = useMemo(() => {
    if (!primaryScenario) {
      return []
    }
    if (selectedParameters.length === 0) {
      return primaryScenario.sensitivityResults
    }
    const set = new Set(selectedParameters)
    return primaryScenario.sensitivityResults.filter((outcome) =>
      outcome.parameter ? set.has(outcome.parameter) : false,
    )
  }, [primaryScenario, selectedParameters])

  const pendingCount = primaryScenario
    ? primaryScenario.sensitivityJobs.filter((job) =>
        isJobPending(job.status),
      ).length
    : 0

  const timelineJobs = useMemo(
    () =>
      primaryScenario
        ? primaryScenario.sensitivityJobs.map((job) => ({
            scenarioId: job.scenarioId,
            taskId: job.taskId,
            status: job.status,
            backend: job.backend,
            queuedAt: job.queuedAt,
          }))
        : [],
    [primaryScenario],
  )

  const handleToggleParameter = useCallback((parameter: string) => {
    setSelectedParameters((prev) => {
      const exists = prev.includes(parameter)
      if (exists) {
        return prev.filter((item) => item !== parameter)
      }
      return [...prev, parameter]
    })
  }, [])

  const handleSelectAll = useCallback(() => {
    setSelectedParameters(parameters)
  }, [parameters])

  const handleDownloadCsv = useCallback(() => {
    if (!primaryScenario) {
      return
    }
    const rows = [
      DEFAULT_SENSITIVITY_HEADERS.join(','),
      ...filteredSensitivity.map((entry) =>
        [
          entry.parameter ?? '',
          entry.scenario ?? '',
          entry.deltaLabel ?? '',
          entry.deltaValue ?? '',
          entry.npv ?? '',
          entry.irr ?? '',
          entry.escalatedCost ?? '',
          entry.totalInterest ?? '',
        ]
          .map(escapeCsvValue)
          .join(','),
      ),
    ]
    downloadFile(
      rows.join('\n'),
      'finance_sensitivity.csv',
      'text/csv;charset=utf-8',
    )
  }, [filteredSensitivity, primaryScenario])

  const handleDownloadJson = useCallback(() => {
    if (!primaryScenario) {
      return
    }
    const content = JSON.stringify(
      primaryScenario.sensitivityResults,
      null,
      2,
    )
    downloadFile(
      content,
      'finance_sensitivity.json',
      'application/json;charset=utf-8',
    )
  }, [primaryScenario])

  const handleSaveLoan = useCallback(
    async (input: ConstructionLoanInput) => {
      if (!primaryScenario) {
        return
      }
      setSavingLoan(true)
      setLoanError(null)
      try {
        await updateConstructionLoan(primaryScenario.scenarioId, input)
        await refresh()
      } catch (err) {
        console.error('[finance] failed to update construction loan', err)
        setLoanError(
          err instanceof Error
            ? err.message
            : 'Unable to update construction loan.',
        )
      } finally {
        setSavingLoan(false)
      }
    },
    [primaryScenario, refresh],
  )

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
        {scenarioError && (
          <p className="finance-workspace__error" role="alert">
            {scenarioError}
          </p>
        )}
        {scenarioMessage && (
          <p className="finance-workspace__status" role="status">
            {scenarioMessage}
          </p>
        )}
        <FinanceScenarioCreator
          projectId={FINANCE_PROJECT_ID}
          projectName={FINANCE_PROJECT_NAME}
          onCreated={(summary) => {
            setScenarioMessage(
              t('finance.scenarioCreator.success', {
                name: summary.scenarioName,
              }),
            )
            setScenarioError(null)
            addScenario(summary)
          }}
          onError={(message) => {
            setScenarioError(message)
            setScenarioMessage(null)
          }}
          onRefresh={() => {
            refresh()
          }}
        />
        {showEmptyState && (
          <p className="finance-workspace__empty">{t('finance.table.empty')}</p>
        )}
        {scenarios.length > 0 && (
          <>
            <div className="finance-workspace__sections">
              <FinanceScenarioTable scenarios={scenarios} />
              <FinanceCapitalStack scenarios={scenarios} />
              <FinanceDrawdownSchedule scenarios={scenarios} />
            </div>
            {primaryScenario ? (
              <>
                <div className="finance-workspace__sections finance-workspace__sections--details">
                  <FinanceAssetBreakdown
                    summary={primaryScenario.assetMixSummary}
                    breakdowns={primaryScenario.assetBreakdowns}
                  />
                  <FinanceLoanInterest
                    schedule={primaryScenario.constructionLoanInterest}
                  />
                  <div className="finance-workspace__facility-editor">
                    <FinanceFacilityEditor
                      scenario={primaryScenario}
                      saving={savingLoan}
                      onSave={handleSaveLoan}
                    />
                    {loanError ? (
                      <p
                        className="finance-workspace__error finance-workspace__error--inline"
                        role="alert"
                      >
                        {loanError}
                      </p>
                    ) : null}
                  </div>
                </div>
                <FinanceSensitivityTable
                  outcomes={filteredSensitivity}
                  currency={primaryScenario.currency}
                  parameters={parameters}
                  selectedParameters={selectedParameters}
                  onToggleParameter={handleToggleParameter}
                  onSelectAll={handleSelectAll}
                  onDownloadCsv={handleDownloadCsv}
                  onDownloadJson={handleDownloadJson}
                />
                <FinanceJobTimeline
                  jobs={timelineJobs}
                  pendingCount={pendingCount}
                />
              </>
            ) : null}
          </>
        )}
      </section>
    </AppLayout>
  )
}

export default FinanceWorkspace
