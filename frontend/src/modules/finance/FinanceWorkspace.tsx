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
  type FinanceAnalyticsMetadata,
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
import { FinanceAnalyticsPanel } from './components/FinanceAnalyticsPanel'
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
import '../../styles/finance/polish.css'

// Material UI Imports
import {
  Box,
  Button,
  Stack,
  Typography,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
} from '@mui/material'
import { Refresh, Download, Warning } from '@mui/icons-material'

// Canonical Components
import { AnimatedPageHeader } from '../../components/canonical/AnimatedPageHeader'
import { GlassCard } from '../../components/canonical/GlassCard'

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

function readLastProjectSelection(): {
  projectId: string
  projectName?: string | null
} | null {
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
    const finProjectParam =
      params.get('finProjectId') ?? params.get('fin_project_id')
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
    projectParams.projectName ??
    lastProject?.projectName ??
    FINANCE_PROJECT_NAME
  const [selectedProjectId, setSelectedProjectId] = useState(initialProjectId)
  const [selectedProjectName, setSelectedProjectName] = useState<string | null>(
    initialProjectName,
  )
  const [finProjectFilter, setFinProjectFilter] = useState<number | undefined>(
    projectParams.finProjectId ?? undefined,
  )
  const [storageVersion, setStorageVersion] = useState(0)
  const [capturedProjects, setCapturedProjects] = useState<
    FinanceProjectOption[]
  >(() => readCapturedProjectsFromStorage())
  const [activeTab, setActiveTab] = useState(0)

  useEffect(() => {
    setCapturedProjects(readCapturedProjectsFromStorage())
  }, [storageVersion])
  useEffect(() => {
    if (
      projectParams.projectId &&
      projectParams.projectId !== selectedProjectId
    ) {
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
  const { scenarios, loading, error, refresh, addScenario } =
    useFinanceScenarios({
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
  const [_loanError, setLoanError] = useState<string | null>(null)
  const [scenarioMessage, setScenarioMessage] = useState<string | null>(null)
  const [scenarioError, setScenarioError] = useState<string | null>(null)
  const [promotingScenarioId, setPromotingScenarioId] = useState<number | null>(
    null,
  )
  const [runningSensitivity, setRunningSensitivity] = useState(false)
  const [sensitivityError, setSensitivityError] = useState<string | null>(null)
  const [scenarioPendingDelete, setScenarioPendingDelete] =
    useState<FinanceScenarioSummary | null>(null)
  const [deletingScenarioId, setDeletingScenarioId] = useState<number | null>(
    null,
  )
  const [exportingScenario, setExportingScenario] = useState(false)
  const identityErrorRegex = /restricted/i
  const needsScenarioIdentity =
    typeof error === 'string' && identityErrorRegex.test(error)
  const needsScenarioCreateIdentity =
    typeof scenarioError === 'string' && identityErrorRegex.test(scenarioError)

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
  const analyticsMetadata = useMemo<FinanceAnalyticsMetadata | null>(() => {
    if (!primaryScenario) {
      return null
    }
    const analyticsResult = primaryScenario.results.find(
      (entry) => entry.name === 'analytics_overview',
    )
    if (!analyticsResult || !analyticsResult.metadata) {
      return null
    }
    return analyticsResult.metadata as FinanceAnalyticsMetadata
  }, [primaryScenario])
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
    ? primaryScenario.sensitivityJobs.filter((job) => isJobPending(job.status))
        .length
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
    const content = JSON.stringify(primaryScenario.sensitivityResults, null, 2)
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
      const filename = `finance_scenario_${primaryScenario.scenarioId}.zip`
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
    <AppLayout title={t('finance.title')} subtitle={t('finance.subtitle')}>
      <Box className="finance-workspace" sx={{ pb: 8 }}>
        <Box sx={{ p: 3 }}>
          <AnimatedPageHeader
            title={t('finance.title')}
            subtitle={t('finance.subtitle')}
            breadcrumbs={[
              { label: 'Dashboard', href: '/' },
              { label: 'Finance' },
            ]}
            actions={
              <Stack direction="row" spacing={2}>
                <Button
                  variant="outlined"
                  startIcon={
                    loading ? <CircularProgress size={16} /> : <Refresh />
                  }
                  onClick={refresh}
                  disabled={loading}
                >
                  {t('finance.actions.refresh')}
                </Button>
                <Button
                  variant="contained"
                  startIcon={<Download />}
                  onClick={handleExportCsv}
                  disabled={!primaryScenario || exportingScenario}
                >
                  {exportingScenario
                    ? 'Exporting...'
                    : t('finance.actions.exportCsv')}
                </Button>
              </Stack>
            }
          />

          {/* Project Selector - Wrapped in GlassCard */}
          <Box sx={{ mt: 3, mb: 4 }}>
            <Typography variant="h6" gutterBottom>
              Project Selection
            </Typography>
            <GlassCard sx={{ p: 3 }}>
              <FinanceProjectSelector
                selectedProjectId={effectiveProjectId}
                selectedProjectName={effectiveProjectName ?? null}
                options={capturedProjects}
                onProjectChange={handleProjectChange}
                onRefresh={refreshCapturedProjects}
              />
            </GlassCard>
          </Box>

          {!hasAccess ? (
            <FinanceAccessGate role={normalizedRole} />
          ) : (
            <>
              {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                  <strong>{t('finance.errors.generic')}</strong>
                  <Box component="span" sx={{ display: 'block' }}>
                    {error}
                  </Box>
                  {needsScenarioIdentity && <FinanceIdentityHelper compact />}
                </Alert>
              )}

              {loading && (
                <GlassCard
                  sx={{ p: 4, display: 'flex', justifyContent: 'center' }}
                >
                  <CircularProgress />
                </GlassCard>
              )}

              {scenarioError && (
                <Alert severity="error" sx={{ mb: 3 }}>
                  {scenarioError}
                  {needsScenarioCreateIdentity && (
                    <FinanceIdentityHelper compact />
                  )}
                </Alert>
              )}
              {scenarioMessage && (
                <Alert severity="success" sx={{ mb: 3 }}>
                  {scenarioMessage}
                </Alert>
              )}

              <Box sx={{ mb: 4 }}>
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
              </Box>

              {primaryScenario?.isPrivate ? (
                <FinancePrivacyNotice projectName={projectDisplayName} />
              ) : null}

              {showEmptyState && (
                <GlassCard sx={{ p: 6, textAlign: 'center' }}>
                  <Typography variant="h5" gutterBottom>
                    {t('finance.table.empty')}
                  </Typography>
                </GlassCard>
              )}

              {primaryScenario?.scenarioId === 0 && (
                <Alert severity="warning" sx={{ mb: 4 }} icon={<Warning />}>
                  <strong>{t('finance.warnings.offlineMode')}</strong>
                  <Typography variant="body2">
                    {t('finance.warnings.offlineModeDetail') ||
                      'You are viewing offline demonstration data. Changes cannot be saved correctly until the backend service is available.'}
                  </Typography>
                </Alert>
              )}

              {scenarios.length > 0 && (
                <Stack spacing={4}>
                  {/* Scenario Management */}
                  <GlassCard sx={{ p: 3 }}>
                    <Typography variant="h5" fontWeight={600} gutterBottom>
                      Scenarios
                    </Typography>
                    <FinanceScenarioTable
                      scenarios={scenarios}
                      onMarkPrimary={handleMarkPrimary}
                      updatingScenarioId={promotingScenarioId}
                      onDeleteScenario={handleRequestDeleteScenario}
                      deletingScenarioId={deletingScenarioId}
                    />
                  </GlassCard>

                  {/* Reports Tabs */}
                  <Box>
                    <Tabs
                      value={activeTab}
                      onChange={(_, v) => setActiveTab(v)}
                      sx={{ mb: 2 }}
                    >
                      <Tab label="Capital Stack" />
                      <Tab label="Drawdown Schedule" />
                      <Tab label="Asset Breakdown" />
                      <Tab label="Facility Editor" />
                      <Tab label="Job Timeline" />
                      <Tab label="Loan Interest" />
                      <Tab label="Analytics" />
                      <Tab label="Sensitivity" />
                    </Tabs>

                    <GlassCard sx={{ p: 3, minHeight: 400 }}>
                      <div role="tabpanel" hidden={activeTab !== 0}>
                        {activeTab === 0 && (
                          <FinanceCapitalStack scenarios={scenarios} />
                        )}
                      </div>
                      <div role="tabpanel" hidden={activeTab !== 1}>
                        {activeTab === 1 && (
                          <FinanceDrawdownSchedule scenarios={scenarios} />
                        )}
                      </div>
                      <div role="tabpanel" hidden={activeTab !== 2}>
                        {activeTab === 2 && primaryScenario && (
                          <FinanceAssetBreakdown
                            summary={primaryScenario.assetMixSummary ?? null}
                            breakdowns={primaryScenario.assetBreakdowns ?? []}
                          />
                        )}
                      </div>
                      <div role="tabpanel" hidden={activeTab !== 3}>
                        {activeTab === 3 && (
                          <FinanceFacilityEditor
                            scenario={primaryScenario ?? null}
                            onSave={handleSaveLoan}
                            saving={savingLoan}
                          />
                        )}
                      </div>
                      <div role="tabpanel" hidden={activeTab !== 4}>
                        {activeTab === 4 && (
                          <FinanceJobTimeline
                            jobs={timelineJobs}
                            pendingCount={pendingCount}
                          />
                        )}
                      </div>
                      <div role="tabpanel" hidden={activeTab !== 5}>
                        {activeTab === 5 && (
                          <FinanceLoanInterest
                            schedule={
                              primaryScenario?.constructionLoanInterest ?? null
                            }
                          />
                        )}
                      </div>
                      <div role="tabpanel" hidden={activeTab !== 6}>
                        {activeTab === 6 && analyticsMetadata && (
                          <Box>
                            <FinanceAnalyticsPanel
                              analytics={analyticsMetadata}
                              currency={primaryScenario?.currency ?? 'SGD'}
                            />
                            <Box mt={2}>
                              {primaryScenario && (
                                <FinanceSensitivityControls
                                  scenario={primaryScenario}
                                  pendingJobs={pendingCount}
                                  disabled={runningSensitivity}
                                  error={sensitivityError}
                                  onRun={handleRunSensitivity}
                                />
                              )}
                            </Box>
                          </Box>
                        )}
                      </div>
                      <div role="tabpanel" hidden={activeTab !== 7}>
                        {activeTab === 7 && (
                          <Box>
                            <FinanceSensitivitySummary
                              summaries={sensitivitySummaries}
                              currency={primaryScenario?.currency ?? 'SGD'}
                            />
                            <Box my={2}>
                              {primaryScenario && (
                                <FinanceSensitivityControls
                                  scenario={primaryScenario}
                                  pendingJobs={pendingCount}
                                  disabled={runningSensitivity}
                                  error={sensitivityError}
                                  onRun={handleRunSensitivity}
                                />
                              )}
                            </Box>
                            <FinanceSensitivityTable
                              outcomes={filteredSensitivity}
                              currency={primaryScenario?.currency ?? 'SGD'}
                              parameters={parameters}
                              selectedParameters={selectedParameters}
                              onSelectAll={handleSelectAll}
                              onToggleParameter={handleToggleParameter}
                              onDownloadCsv={handleDownloadCsv}
                              onDownloadJson={handleDownloadJson}
                            />
                          </Box>
                        )}
                      </div>
                    </GlassCard>
                  </Box>
                </Stack>
              )}

              <FinanceScenarioDeleteDialog
                open={scenarioPendingDelete !== null}
                scenarioName={scenarioPendingDelete?.scenarioName ?? ''}
                pending={
                  deletingScenarioId === scenarioPendingDelete?.scenarioId
                }
                onConfirm={handleConfirmDelete}
                onCancel={handleCancelDelete}
              />
            </>
          )}
        </Box>
      </Box>
    </AppLayout>
  )
}
