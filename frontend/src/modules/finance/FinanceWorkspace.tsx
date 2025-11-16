import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import {
  updateConstructionLoan,
  updateFinanceScenario,
  runScenarioSensitivity,
  deleteFinanceScenario,
  exportFinanceScenarioCsv,
  type ConstructionLoanInput,
  type SensitivityBandInput,
  type FinanceScenarioSummary,
} from '../../api/finance'
import { resolveDefaultRole } from '../../api/identity'
import { AppLayout } from '../../App'
import { useTranslation } from '../../i18n'
import { useRouterController } from '../../router'
import { FinanceAssetBreakdown } from './components/FinanceAssetBreakdown'
import { FinanceCapitalStack } from './components/FinanceCapitalStack'
import { FinanceDrawdownSchedule } from './components/FinanceDrawdownSchedule'
import { FinanceFacilityEditor } from './components/FinanceFacilityEditor'
import { FinanceJobTimeline } from './components/FinanceJobTimeline'
import { FinanceLoanInterest } from './components/FinanceLoanInterest'
import { FinanceScenarioTable } from './components/FinanceScenarioTable'
import { FinanceSensitivityTable } from './components/FinanceSensitivityTable'
import { FinanceSensitivitySummary } from './components/FinanceSensitivitySummary'
import { buildSensitivitySummaries } from './components/sensitivitySummary'
import { FinanceScenarioCreator } from './components/FinanceScenarioCreator'
import { FinanceScenarioDeleteDialog } from './components/FinanceScenarioDeleteDialog'
import { FinanceSensitivityControls } from './components/FinanceSensitivityControls'
import {
  FinanceProjectSelector,
  type FinanceProjectOption,
} from './components/FinanceProjectSelector'
import {
  FinanceAccessGate,
  FinanceIdentityHelper,
  FinancePrivacyNotice,
} from './components/FinancePrivacyNotice'
import { useFinanceScenarios } from './hooks/useFinanceScenarios'

// Align with seeded Phase 2B finance demo data (see backend/scripts/seed_finance_demo.py)
const FINANCE_PROJECT_ID = '401'
const FINANCE_PROJECT_NAME = 'Finance Demo Development'
const POLL_INTERVAL_MS = 5000
const IN_PROGRESS_STATUSES = new Set([
  'queued',
  'started',
  'in_progress',
  'processing',
])
const ASSET_STORAGE_PREFIX = 'developer-asset-mix:'
const LAST_PROJECT_STORAGE_KEY = 'finance:last-project'
const ALLOWED_FINANCE_ROLES = new Set(['developer', 'reviewer', 'admin'])

function readCapturedProjectsFromStorage(): FinanceProjectOption[] {
  if (typeof window === 'undefined' || !window.sessionStorage) {
    return []
  }
  const list: FinanceProjectOption[] = []
  const seen = new Set<string>()
  for (let index = 0; index < window.sessionStorage.length; index += 1) {
    const key = window.sessionStorage.key(index)
    if (!key || !key.startsWith(ASSET_STORAGE_PREFIX)) {
      continue
    }
    const propertyId = key.slice(ASSET_STORAGE_PREFIX.length)
    if (!propertyId || seen.has(propertyId)) {
      continue
    }
    seen.add(propertyId)
    try {
      const raw = window.sessionStorage.getItem(key)
      if (!raw) {
        continue
      }
      const parsed = JSON.parse(raw) as {
        propertyInfo?: { propertyName?: string | null }
        address?: { fullAddress?: string | null }
        metadata?: { propertyName?: string | null; capturedAt?: string | null }
      }
      const label =
        parsed.metadata?.propertyName?.trim() ||
        parsed.propertyInfo?.propertyName?.trim() ||
        parsed.address?.fullAddress?.trim() ||
        propertyId
      list.push({
        id: propertyId,
        label,
        projectName: label,
        capturedAt: parsed.metadata?.capturedAt ?? null,
      })
    } catch (error) {
      console.warn('[finance] unable to parse stored capture metadata', error)
    }
  }
  return list.sort((a, b) => {
    const aTime = a.capturedAt ? Date.parse(a.capturedAt) : 0
    const bTime = b.capturedAt ? Date.parse(b.capturedAt) : 0
    return bTime - aTime
  })
}

function shortenProjectId(value: string): string {
  if (!value) {
    return ''
  }
  if (value.length <= 12) {
    return value
  }
  return `${value.slice(0, 6)}…${value.slice(-4)}`
}

function readLastProjectSelection():
  | { projectId: string; projectName?: string | null }
  | null {
  if (typeof window === 'undefined') {
    return null
  }
  try {
    const raw = window.sessionStorage.getItem(LAST_PROJECT_STORAGE_KEY)
    if (!raw) {
      return null
    }
    const parsed = JSON.parse(raw) as {
      projectId?: string
      projectName?: string | null
    }
    if (!parsed.projectId) {
      return null
    }
    return {
      projectId: parsed.projectId,
      projectName: parsed.projectName ?? null,
    }
  } catch {
    return null
  }
}

function persistLastProjectSelection(
  projectId: string,
  projectName?: string | null,
): void {
  if (typeof window === 'undefined') {
    return
  }
  try {
    window.sessionStorage.setItem(
      LAST_PROJECT_STORAGE_KEY,
      JSON.stringify({ projectId, projectName: projectName ?? null }),
    )
  } catch {
    // Ignore persistence failures
  }
}

function parseProjectParams(search: string) {
  if (!search) {
    return { projectId: null, projectName: null, finProjectId: null }
  }
  try {
    const params = new URLSearchParams(search)
    const projectId = params.get('projectId')
    const projectName = params.get('projectName')
    const finProjectParam = params.get('finProjectId') ?? params.get('fin_project_id')
    const parsedFinProject =
      finProjectParam && !Number.isNaN(Number(finProjectParam))
        ? Number(finProjectParam)
        : null
    return {
      projectId: projectId?.trim() || null,
      projectName: projectName?.trim() || null,
      finProjectId: parsedFinProject,
    }
  } catch {
    return { projectId: null, projectName: null, finProjectId: null }
  }
}

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
  const router = useRouterController()
  const { search, path, navigate } = router
  const projectParams = useMemo(() => parseProjectParams(search), [search])
  const lastProject = useMemo(() => readLastProjectSelection(), [])
  const initialProjectId =
    projectParams.projectId ?? lastProject?.projectId ?? FINANCE_PROJECT_ID
  const initialProjectName =
    projectParams.projectName ?? lastProject?.projectName ?? FINANCE_PROJECT_NAME
  const [selectedProjectId, setSelectedProjectId] = useState(initialProjectId)
  const [selectedProjectName, setSelectedProjectName] = useState<string | null>(
    initialProjectName,
  )
  const [finProjectFilter, setFinProjectFilter] = useState<number | undefined>(
    projectParams.finProjectId ?? undefined,
  )
  const [storageVersion, setStorageVersion] = useState(0)
  const [capturedProjects, setCapturedProjects] = useState<FinanceProjectOption[]>(() =>
    readCapturedProjectsFromStorage(),
  )
  useEffect(() => {
    setCapturedProjects(readCapturedProjectsFromStorage())
  }, [storageVersion])
  useEffect(() => {
    if (projectParams.projectId && projectParams.projectId !== selectedProjectId) {
      setSelectedProjectId(projectParams.projectId)
    }
    if (projectParams.projectName !== selectedProjectName) {
      setSelectedProjectName(projectParams.projectName)
    }
    setFinProjectFilter(projectParams.finProjectId ?? undefined)
  }, [
    projectParams.projectId,
    projectParams.projectName,
    projectParams.finProjectId,
    selectedProjectId,
    selectedProjectName,
  ])
  const effectiveProjectId = selectedProjectId || FINANCE_PROJECT_ID
  const effectiveProjectName =
    selectedProjectName ?? (selectedProjectId ? null : FINANCE_PROJECT_NAME)
  const { scenarios, loading, error, refresh, addScenario } = useFinanceScenarios({
    projectId: effectiveProjectId,
    finProjectId: finProjectFilter,
  })
  const role = resolveDefaultRole()
  const normalizedRole = role ? role.toLowerCase() : null
  const hasAccess = normalizedRole
    ? ALLOWED_FINANCE_ROLES.has(normalizedRole)
    : false
  const projectDisplayName =
    effectiveProjectName ?? shortenProjectId(effectiveProjectId)
  const refreshCapturedProjects = useCallback(() => {
    setStorageVersion((value) => value + 1)
  }, [])
  const handleProjectChange = useCallback(
    (projectId: string, projectName?: string | null) => {
      const trimmed = projectId.trim()
      if (!trimmed) {
        return
      }
      setSelectedProjectId(trimmed)
      setSelectedProjectName(projectName ?? null)
      persistLastProjectSelection(trimmed, projectName ?? null)
      const params = new URLSearchParams(search)
      params.set('projectId', trimmed)
      if (projectName && projectName.trim()) {
        params.set('projectName', projectName.trim())
      } else {
        params.delete('projectName')
      }
      params.delete('finProjectId')
      params.delete('fin_project_id')
      const querySuffix = params.toString()
      navigate(querySuffix ? `${path}?${querySuffix}` : path)
    },
    [navigate, path, search],
  )
  const [savingLoan, setSavingLoan] = useState(false)
  const [loanError, setLoanError] = useState<string | null>(null)
  const [scenarioMessage, setScenarioMessage] = useState<string | null>(null)
  const [scenarioError, setScenarioError] = useState<string | null>(null)
  const [promotingScenarioId, setPromotingScenarioId] = useState<number | null>(null)
  const [runningSensitivity, setRunningSensitivity] = useState(false)
  const [sensitivityError, setSensitivityError] = useState<string | null>(null)
  const [scenarioPendingDelete, setScenarioPendingDelete] =
    useState<FinanceScenarioSummary | null>(null)
  const [deletingScenarioId, setDeletingScenarioId] = useState<number | null>(null)
  const [exportingScenario, setExportingScenario] = useState(false)
  const identityErrorRegex = /restricted/i
  const needsScenarioIdentity =
    typeof error === 'string' && identityErrorRegex.test(error)
  const needsScenarioCreateIdentity =
    typeof scenarioError === 'string' &&
    identityErrorRegex.test(scenarioError)

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
      setSensitivityError(null)
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
    setSensitivityError(null)
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

  const sensitivitySummaries = useMemo(() => {
    if (!primaryScenario) {
      return []
    }
    return buildSensitivitySummaries(primaryScenario.sensitivityResults)
  }, [primaryScenario])

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

  const handleExportCsv = useCallback(async () => {
    if (!primaryScenario || exportingScenario) {
      return
    }
    setExportingScenario(true)
    setScenarioError(null)
    try {
      const blob = await exportFinanceScenarioCsv(primaryScenario.scenarioId)
      const url = URL.createObjectURL(blob)
      const filename = `finance_scenario_${primaryScenario.scenarioId}.csv`
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = filename
      anchor.style.display = 'none'
      document.body.appendChild(anchor)
      anchor.click()
      document.body.removeChild(anchor)
      URL.revokeObjectURL(url)
      setScenarioMessage(t('finance.actions.exportSuccess'))
    } catch (err) {
      console.error('[finance] failed to export finance scenario', err)
      setScenarioError(
        err instanceof Error ? err.message : t('finance.errors.export'),
      )
    } finally {
      setExportingScenario(false)
    }
  }, [primaryScenario, exportingScenario, t])

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

  const handleMarkPrimary = useCallback(
    async (scenarioId: number) => {
      if (!scenarioId || promotingScenarioId === scenarioId) {
        return
      }
      setPromotingScenarioId(scenarioId)
      setScenarioError(null)
      try {
        const updated = await updateFinanceScenario(scenarioId, {
          isPrimary: true,
        })
        setScenarioMessage(
          t('finance.table.messages.primarySuccess', {
            name: updated.scenarioName,
          }),
        )
        await refresh()
      } catch (err) {
        console.error('[finance] failed to mark scenario primary', err)
        setScenarioError(
          err instanceof Error
            ? err.message
            : t('finance.table.messages.primaryError'),
        )
      } finally {
        setPromotingScenarioId(null)
      }
    },
    [promotingScenarioId, refresh, t],
  )

  const handleRequestDeleteScenario = useCallback(
    (scenario: FinanceScenarioSummary) => {
      setScenarioPendingDelete(scenario)
      setScenarioMessage(null)
    },
    [],
  )

  const handleCancelDelete = useCallback(() => {
    setScenarioPendingDelete(null)
  }, [])

  const handleConfirmDelete = useCallback(async () => {
    if (!scenarioPendingDelete) {
      return
    }
    const scenarioId = scenarioPendingDelete.scenarioId
    const scenarioName = scenarioPendingDelete.scenarioName
    setDeletingScenarioId(scenarioId)
    setScenarioError(null)
    try {
      await deleteFinanceScenario(scenarioId)
      setScenarioMessage(
        t('finance.table.messages.deleteSuccess', { name: scenarioName }),
      )
      setScenarioPendingDelete(null)
      await refresh()
    } catch (err) {
      console.error('[finance] failed to delete finance scenario', err)
      setScenarioError(
        err instanceof Error
          ? err.message
          : t('finance.table.messages.deleteError'),
      )
    } finally {
      setDeletingScenarioId(null)
    }
  }, [scenarioPendingDelete, refresh, t])

  const handleRunSensitivity = useCallback(
    async (bands: SensitivityBandInput[]) => {
      if (!primaryScenario || runningSensitivity) {
        return
      }
      setRunningSensitivity(true)
      setSensitivityError(null)
      try {
        await runScenarioSensitivity(primaryScenario.scenarioId, bands)
        setScenarioMessage(
          t('finance.sensitivity.controls.success', {
            defaultValue: 'Sensitivity analysis updated.',
          }),
        )
        await refresh()
      } catch (err) {
        console.error('[finance] failed to rerun sensitivity analysis', err)
        setSensitivityError(
          err instanceof Error
            ? err.message
            : t('finance.sensitivity.controls.errors.generic'),
        )
      } finally {
        setRunningSensitivity(false)
      }
    },
    [primaryScenario, refresh, runningSensitivity, t],
  )

  return (
    <AppLayout
      title={t('finance.title')}
      subtitle={t('finance.subtitle')}
      actions={
        <div className="finance-workspace__actions">
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
          <button
            type="button"
            className="finance-workspace__export"
            onClick={handleExportCsv}
            disabled={!primaryScenario || exportingScenario}
          >
            {exportingScenario
              ? t('finance.actions.exporting')
              : t('finance.actions.exportCsv')}
          </button>
        </div>
      }
    >
      <section className="finance-workspace">
        <FinanceProjectSelector
          selectedProjectId={effectiveProjectId}
          selectedProjectName={effectiveProjectName ?? null}
          options={capturedProjects}
          onProjectChange={handleProjectChange}
          onRefresh={refreshCapturedProjects}
        />
        {!hasAccess ? (
          <FinanceAccessGate role={normalizedRole} />
        ) : (
          <>
            {error && (
              <div className="finance-workspace__error" role="alert">
                <strong>{t('finance.errors.generic')}</strong>
                <span className="finance-workspace__error-detail">{error}</span>
                {needsScenarioIdentity && (
                  <FinanceIdentityHelper compact />
                )}
              </div>
            )}
            {loading && (
              <p className="finance-workspace__status">{t('common.loading')}</p>
            )}
            {scenarioError && (
              <div className="finance-workspace__error" role="alert">
                {scenarioError}
                {needsScenarioCreateIdentity && (
                  <FinanceIdentityHelper compact />
                )}
              </div>
            )}
            {scenarioMessage && (
              <p className="finance-workspace__status" role="status">
                {scenarioMessage}
              </p>
            )}
            <FinanceScenarioCreator
              projectId={effectiveProjectId}
              projectName={projectDisplayName}
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
            {primaryScenario?.isPrivate ? (
              <FinancePrivacyNotice projectName={projectDisplayName} />
            ) : null}
            {showEmptyState && (
              <p className="finance-workspace__empty">
                {t('finance.table.empty')}
              </p>
            )}
            {scenarios.length > 0 && (
              <>
                <div className="finance-workspace__sections">
                  <FinanceScenarioTable
                    scenarios={scenarios}
                    onMarkPrimary={handleMarkPrimary}
                    updatingScenarioId={promotingScenarioId}
                    onDeleteScenario={handleRequestDeleteScenario}
                    deletingScenarioId={deletingScenarioId}
                  />
                  <FinanceCapitalStack scenarios={scenarios} />
                  <FinanceDrawdownSchedule scenarios={scenarios} />
                </div>
                {primaryScenario ? (
                  <>
                    <div className="finance-workspace__sections finance-workspace__sections--details">
                      <FinanceAssetBreakdown
                        summary={primaryScenario.assetMixSummary}
                        breakdowns={primaryScenario.assetBreakdowns}
                        currency={primaryScenario.currency}
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
                    <FinanceSensitivityControls
                      scenario={primaryScenario}
                      pendingJobs={pendingCount}
                      disabled={runningSensitivity || pendingCount > 0}
                      error={sensitivityError}
                      onRun={handleRunSensitivity}
                    />
                    <FinanceSensitivitySummary
                      summaries={sensitivitySummaries}
                      currency={primaryScenario.currency}
                    />
                    <FinanceJobTimeline
                      jobs={timelineJobs}
                      pendingCount={pendingCount}
                    />
                  </>
                ) : null}
              </>
            )}
            <FinanceScenarioDeleteDialog
              open={Boolean(scenarioPendingDelete)}
              scenarioName={scenarioPendingDelete?.scenarioName ?? ''}
              pending={
                Boolean(
                  scenarioPendingDelete &&
                    deletingScenarioId === scenarioPendingDelete.scenarioId,
                )
              }
              onCancel={handleCancelDelete}
              onConfirm={handleConfirmDelete}
            />
          </>
        )}
      </section>
    </AppLayout>
  )
}
export default FinanceWorkspace
