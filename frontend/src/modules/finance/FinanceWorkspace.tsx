import {
  Suspense,
  type ChangeEvent,
  lazy,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'

import {
  runFinanceFeasibility,
  updateConstructionLoan,
  updateFinanceScenario,
  runScenarioSensitivity,
  deleteFinanceScenario,
  exportFinanceScenarioCsv,
  exportFinanceScenarioWorkbook,
  importFinanceWorkbook,
  previewFinanceWorkbookImport,
  fetchFinanceAuditEvidence,
  type ConstructionLoanInput,
  type FinanceAuditEvidence,
  type FinanceWorkbookImportPreview,
  type SensitivityBandInput,
  type FinanceAnalyticsMetadata,
} from '../../api/finance'
import { resolveDefaultRole } from '../../api/identity'
import { AppLayout } from '../../App'
import { useTranslation } from '../../i18n'
import { useRouterController, useRouterParams } from '../../router'
import { buildSensitivitySummaries } from './components/sensitivitySummary'
import { FinanceScenarioDeleteDialog } from './components/FinanceScenarioDeleteDialog'
import {
  FinanceHeaderControls,
  type FinanceProjectOption,
} from './components/FinanceHeaderControls'
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
  Stack,
  Typography,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
} from '@mui/material'
import {
  Warning,
  PushPin as PushPinIcon,
  PushPinOutlined as PushPinOutlinedIcon,
} from '@mui/icons-material'

// Canonical Components
import { Button } from '../../components/canonical/Button'
import { Card } from '../../components/canonical/Card'
import { useProject } from '../../contexts/useProject'
import { createFinanceProjectFromCapture } from '../../api/siteAcquisition'
import { getCapturePropertyId } from '../../app/pages/capture/utils/captureStorage'
import {
  buildQuickScreenAssessmentSummary,
  buildQuickScreenScenarioDescription,
  clearQuickScreenFinanceDraft,
  readQuickScreenFinanceDraft,
  type QuickScreenFinanceDraft,
} from './quickScreenDraft'

const FinanceAssetBreakdown = lazy(
  () => import('./components/FinanceAssetBreakdown'),
)
const FinanceCapitalStack = lazy(
  () => import('./components/FinanceCapitalStack'),
)
const FinanceDrawdownSchedule = lazy(
  () => import('./components/FinanceDrawdownSchedule'),
)
const FinanceLoanInterest = lazy(
  () => import('./components/FinanceLoanInterest'),
)
const FinanceSensitivityTable = lazy(
  () => import('./components/FinanceSensitivityTable'),
)
const FinanceScenarioCreator = lazy(() =>
  import('./components/FinanceScenarioCreator').then((module) => ({
    default: module.FinanceScenarioCreator,
  })),
)
const FinanceFacilityEditor = lazy(() =>
  import('./components/FinanceFacilityEditor').then((module) => ({
    default: module.FinanceFacilityEditor,
  })),
)
const FinanceJobTimeline = lazy(() =>
  import('./components/FinanceJobTimeline').then((module) => ({
    default: module.FinanceJobTimeline,
  })),
)
const FinanceAnalyticsPanel = lazy(() =>
  import('./components/FinanceAnalyticsPanel').then((module) => ({
    default: module.FinanceAnalyticsPanel,
  })),
)
const FinanceSensitivityControls = lazy(() =>
  import('./components/FinanceSensitivityControls').then((module) => ({
    default: module.FinanceSensitivityControls,
  })),
)
const FinanceSensitivitySummary = lazy(() =>
  import('./components/FinanceSensitivitySummary').then((module) => ({
    default: module.FinanceSensitivitySummary,
  })),
)

const POLL_INTERVAL_MS = 5000
const IN_PROGRESS_STATUSES = new Set([
  'queued',
  'started',
  'in_progress',
  'processing',
])
const ALLOWED_FINANCE_ROLES = new Set(['developer', 'reviewer', 'admin'])

function shortenProjectId(value: string): string {
  if (!value) {
    return ''
  }
  if (value.length <= 12) {
    return value
  }
  return `${value.slice(0, 6)}…${value.slice(-4)}`
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

interface FinanceWorkspaceProps {
  workspace?: 'agent' | 'developer'
}

export function FinanceWorkspace(_props: FinanceWorkspaceProps = {}) {
  const { t } = useTranslation()
  const router = useRouterController()
  const { path, search, navigate } = router
  const { projectId: routeProjectId } = useRouterParams()
  const {
    currentProject,
    projects,
    setCurrentProject,
    projectError,
    isProjectLoading,
  } = useProject()
  const projectOptions = useMemo<FinanceProjectOption[]>(
    () =>
      projects.map((project) => ({
        id: project.id,
        label: project.name,
        projectName: project.name,
      })),
    [projects],
  )
  const [activeTab, setActiveTab] = useState(0)
  const [isHeaderPinned, setIsHeaderPinned] = useState(true)

  const effectiveProjectId = currentProject?.id ?? ''
  const effectiveProjectName = currentProject?.name ?? null
  const { scenarios, loading, error, refresh, addScenario } =
    useFinanceScenarios({
      projectId: effectiveProjectId || undefined,
    })
  const role = resolveDefaultRole()
  const normalizedRole = role ? role.toLowerCase() : null
  const hasAccess = normalizedRole
    ? ALLOWED_FINANCE_ROLES.has(normalizedRole)
    : false
  const projectDisplayName =
    effectiveProjectName ?? shortenProjectId(effectiveProjectId)
  const searchParams = useMemo(() => new URLSearchParams(search), [search])
  const onboardingMode = searchParams.get('onboarding')
  const financeTemplateId = searchParams.get('template')
  const hasProject = Boolean(effectiveProjectId)
  const capturePropertyId = useMemo(
    () => getCapturePropertyId(effectiveProjectId),
    [effectiveProjectId],
  )
  const showProjectGate = !hasProject && !isProjectLoading
  const handleProjectChange = useCallback(
    (projectId: string, projectName?: string | null) => {
      const trimmed = projectId.trim()
      if (!trimmed) {
        return
      }
      const match = projects.find((project) => project.id === trimmed)
      setCurrentProject(
        match ?? { id: trimmed, name: projectName?.trim() || trimmed },
      )
      if (routeProjectId) {
        navigate(
          path.replace(`/projects/${routeProjectId}`, `/projects/${trimmed}`),
        )
      } else {
        navigate(`/projects/${trimmed}/finance`)
      }
    },
    [navigate, path, projects, routeProjectId, setCurrentProject],
  )
  const [savingLoan, setSavingLoan] = useState(false)
  const [_loanError, setLoanError] = useState<string | null>(null)
  const [scenarioMessage, setScenarioMessage] = useState<string | null>(null)
  const [scenarioError, setScenarioError] = useState<string | null>(null)
  const [seedError, setSeedError] = useState<string | null>(null)
  const [seeding, setSeeding] = useState(false)
  const [promotingScenarioId, setPromotingScenarioId] = useState<number | null>(
    null,
  )
  const [runningSensitivity, setRunningSensitivity] = useState(false)
  const [sensitivityError, setSensitivityError] = useState<string | null>(null)
  const [scenarioPendingDelete, setScenarioPendingDelete] = useState<{
    scenarioId: number
    scenarioName: string
  } | null>(null)
  const [deletingScenarioId, setDeletingScenarioId] = useState<number | null>(
    null,
  )
  const [exportingScenario, setExportingScenario] = useState(false)
  const [exportingWorkbook, setExportingWorkbook] = useState(false)
  const [previewingWorkbook, setPreviewingWorkbook] = useState(false)
  const [importingWorkbook, setImportingWorkbook] = useState(false)
  const [workbookPreview, setWorkbookPreview] =
    useState<FinanceWorkbookImportPreview | null>(null)
  const [pendingWorkbookFile, setPendingWorkbookFile] = useState<File | null>(
    null,
  )
  const [quickScreenDraft, setQuickScreenDraft] =
    useState<QuickScreenFinanceDraft | null>(null)
  const [auditEvidence, setAuditEvidence] = useState<FinanceAuditEvidence | null>(
    null,
  )
  const [auditEvidenceError, setAuditEvidenceError] = useState<string | null>(null)
  const workbookInputRef = useRef<HTMLInputElement | null>(null)
  const identityErrorRegex = /restricted/i
  const needsScenarioIdentity =
    typeof error === 'string' && identityErrorRegex.test(error)
  const needsScenarioCreateIdentity =
    typeof scenarioError === 'string' && identityErrorRegex.test(scenarioError)

  const handleSeedFromCapture = useCallback(async () => {
    if (!capturePropertyId || seeding) {
      return
    }
    setSeedError(null)
    setScenarioError(null)
    setScenarioMessage(null)
    setSeeding(true)
    try {
      const seeded = await createFinanceProjectFromCapture(capturePropertyId, {
        projectName: effectiveProjectName ?? undefined,
      })
      setScenarioMessage(`Seeded finance scenario for ${seeded.projectName}.`)
      refresh()
    } catch (err) {
      setSeedError(
        err instanceof Error ? err.message : 'Unable to seed finance scenario.',
      )
    } finally {
      setSeeding(false)
    }
  }, [capturePropertyId, effectiveProjectName, refresh, seeding])

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
  const renderEmptyPanel = useCallback(
    (title: string) => (
      <Card variant="glass" sx={{ p: 'var(--ob-space-300)' }}>
        <Stack spacing={1} alignItems="flex-start">
          <Typography variant="h6">{title}</Typography>
          <Typography variant="body2" color="text.secondary">
            Create or import a finance scenario to populate this view.
          </Typography>
          <Button variant="secondary" size="sm" onClick={() => setActiveTab(0)}>
            Go to scenario builder
          </Button>
        </Stack>
      </Card>
    ),
    [setActiveTab],
  )

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

  const handleExportWorkbook = useCallback(async () => {
    if (!primaryScenario || exportingWorkbook) {
      return
    }
    setExportingWorkbook(true)
    setScenarioError(null)
    try {
      const blob = await exportFinanceScenarioWorkbook(primaryScenario.scenarioId)
      const url = URL.createObjectURL(blob)
      const filename = `finance_scenario_${primaryScenario.scenarioId}.xlsx`
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = filename
      anchor.style.display = 'none'
      document.body.appendChild(anchor)
      anchor.click()
      document.body.removeChild(anchor)
      URL.revokeObjectURL(url)
      setScenarioMessage(
        t('finance.actions.exportWorkbookSuccess', {
          defaultValue: 'Finance workbook downloaded.',
        }),
      )
    } catch (err) {
      console.error('[finance] failed to export workbook', err)
      setScenarioError(
        err instanceof Error
          ? err.message
          : t('finance.errors.exportWorkbook', {
              defaultValue: 'Unable to export the selected workbook.',
            }),
      )
    } finally {
      setExportingWorkbook(false)
    }
  }, [primaryScenario, exportingWorkbook, t])

  const handleImportWorkbookClick = useCallback(() => {
    if (!hasProject || previewingWorkbook || importingWorkbook) {
      return
    }
    workbookInputRef.current?.click()
  }, [hasProject, previewingWorkbook, importingWorkbook])

  const handleWorkbookSelected = useCallback(
    async (event: ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0]
      if (!file || !hasProject) {
        return
      }
      setPreviewingWorkbook(true)
      setScenarioError(null)
      setScenarioMessage(null)
      try {
        const preview = await previewFinanceWorkbookImport(file, {
          projectId: effectiveProjectId,
          projectName: effectiveProjectName ?? projectDisplayName,
        })
        setPendingWorkbookFile(file)
        setWorkbookPreview(preview)
      } catch (err) {
        console.error('[finance] failed to preview workbook import', err)
        setScenarioError(
          err instanceof Error
            ? err.message
            : t('finance.errors.importWorkbook', {
                defaultValue: 'Unable to preview workbook import.',
              }),
        )
        setPendingWorkbookFile(null)
        setWorkbookPreview(null)
      } finally {
        event.target.value = ''
        setPreviewingWorkbook(false)
      }
    },
    [hasProject, effectiveProjectId, effectiveProjectName, projectDisplayName, t],
  )

  const handleDismissWorkbookPreview = useCallback(() => {
    setPendingWorkbookFile(null)
    setWorkbookPreview(null)
  }, [])

  const handleConfirmWorkbookImport = useCallback(async () => {
    if (!pendingWorkbookFile || !hasProject || importingWorkbook) {
      return
    }
    setImportingWorkbook(true)
    setScenarioError(null)
    try {
      const imported = await importFinanceWorkbook(pendingWorkbookFile, {
        projectId: effectiveProjectId,
        projectName: effectiveProjectName ?? projectDisplayName,
      })
      setScenarioMessage(
        t('finance.actions.importWorkbookSuccess', {
          defaultValue: 'Workbook imported into a finance scenario.',
        }),
      )
      addScenario(imported)
      setActiveTab(0)
      setPendingWorkbookFile(null)
      setWorkbookPreview(null)
      await refresh()
    } catch (err) {
      console.error('[finance] failed to import workbook', err)
      setScenarioError(
        err instanceof Error
          ? err.message
          : t('finance.errors.importWorkbook', {
              defaultValue: 'Unable to import workbook.',
            }),
      )
    } finally {
      setImportingWorkbook(false)
    }
  }, [
    pendingWorkbookFile,
    hasProject,
    importingWorkbook,
    effectiveProjectId,
    effectiveProjectName,
    projectDisplayName,
    addScenario,
    refresh,
    t,
  ])

  useEffect(() => {
    setQuickScreenDraft(readQuickScreenFinanceDraft())
  }, [])

  useEffect(() => {
    if (!hasProject) {
      setAuditEvidence(null)
      setAuditEvidenceError(null)
      return undefined
    }
    const controller = new AbortController()
    setAuditEvidenceError(null)
    fetchFinanceAuditEvidence(effectiveProjectId, { signal: controller.signal })
      .then((evidence) => {
        setAuditEvidence(evidence)
      })
      .catch((err) => {
        if (controller.signal.aborted) {
          return
        }
        console.warn('[finance] failed to load audit evidence', err)
        setAuditEvidenceError(
          err instanceof Error ? err.message : 'Unable to load audit evidence.',
        )
      })
    return () => controller.abort()
  }, [effectiveProjectId, hasProject, scenarios.length, primaryScenario?.scenarioId])

  const handleImportQuickScreenDraft = useCallback(async () => {
    if (!quickScreenDraft || !hasProject) {
      return
    }
    setScenarioError(null)
    setScenarioMessage(null)
    try {
      const scenario = {
        ...quickScreenDraft.scenario,
        description: buildQuickScreenScenarioDescription(
          quickScreenDraft.scenario.description,
          quickScreenDraft.assessment,
        ),
      }
      const summary = await runFinanceFeasibility({
        projectId: effectiveProjectId,
        projectName:
          effectiveProjectName ?? quickScreenDraft.projectName ?? projectDisplayName,
        scenario,
      })
      addScenario(summary)
      setScenarioMessage(
        t('finance.actions.importQuickScreenSuccess', {
          defaultValue: 'Quick screen assumptions imported into finance.',
        }),
      )
      clearQuickScreenFinanceDraft()
      setQuickScreenDraft(null)
      setActiveTab(0)
      await refresh()
    } catch (err) {
      console.error('[finance] failed to import quick screen draft', err)
      setScenarioError(
        err instanceof Error
          ? err.message
          : t('finance.errors.importQuickScreen', {
              defaultValue: 'Unable to import quick screen assumptions.',
            }),
      )
    }
  }, [
    quickScreenDraft,
    hasProject,
    effectiveProjectId,
    effectiveProjectName,
    projectDisplayName,
    addScenario,
    refresh,
    t,
  ])

  const quickScreenAssessmentLines = useMemo(
    () => buildQuickScreenAssessmentSummary(quickScreenDraft?.assessment),
    [quickScreenDraft],
  )
  const latestFinanceAuditEvent = useMemo(
    () => auditEvidence?.financeEvents.at(-1) ?? null,
    [auditEvidence],
  )
  const latestWorkbookImport = useMemo(
    () => auditEvidence?.imports.at(-1) ?? null,
    [auditEvidence],
  )
  const latestSubmissionEvent = useMemo(
    () => auditEvidence?.submissionEvents.at(-1) ?? null,
    [auditEvidence],
  )

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
    (scenarioId: number, scenarioName: string) => {
      setScenarioPendingDelete({ scenarioId, scenarioName })
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

  const headerActions = hasAccess ? (
    <Stack
      direction="row"
      spacing="var(--ob-space-100)"
      alignItems="center"
      justifyContent="flex-end"
      sx={{
        flexWrap: 'nowrap',
        minWidth: 0,
        columnGap: 'var(--ob-space-100)',
      }}
    >
      <FinanceHeaderControls
        selectedProjectId={effectiveProjectId}
        selectedProjectName={effectiveProjectName ?? null}
        options={projectOptions}
        onProjectChange={handleProjectChange}
        onRefresh={() => {
          refresh()
        }}
        refreshing={loading}
        onImportWorkbook={handleImportWorkbookClick}
        importingWorkbook={previewingWorkbook || importingWorkbook}
        importDisabled={!hasProject}
        onExportWorkbook={handleExportWorkbook}
        exportingWorkbook={exportingWorkbook}
        onExportCsv={handleExportCsv}
        exportingCsv={exportingScenario}
        exportDisabled={!primaryScenario}
      />

      <Button
        size="sm"
        variant="secondary"
        onClick={() => setIsHeaderPinned((prev) => !prev)}
        aria-label={
          isHeaderPinned
            ? t('finance.header.unpin', {
                defaultValue: 'Unpin header (scroll)',
              })
            : t('finance.header.pin', {
                defaultValue: 'Pin header (sticky)',
              })
        }
        title={
          isHeaderPinned
            ? t('finance.header.unpin', {
                defaultValue: 'Unpin header (scroll)',
              })
            : t('finance.header.pin', {
                defaultValue: 'Pin header (sticky)',
              })
        }
        sx={{
          width: 'var(--ob-size-icon-md)',
          minWidth: 'var(--ob-size-icon-md)',
          px: 0,
        }}
      >
        {isHeaderPinned ? (
          <PushPinIcon fontSize="small" />
        ) : (
          <PushPinOutlinedIcon fontSize="small" />
        )}
      </Button>
    </Stack>
  ) : undefined

  const panelFallback = (
    <Card
      variant="glass"
      sx={{
        p: 'var(--ob-space-200)',
        display: 'flex',
        justifyContent: 'center',
      }}
    >
      <CircularProgress />
    </Card>
  )

  return (
    <AppLayout
      title={t('finance.title')}
      subtitle={t('finance.subtitle')}
      hideHeader
    >
      <Box className="finance-workspace" sx={{ pb: 'var(--ob-space-400)' }}>
        <Box sx={{ px: 'var(--ob-space-150)' }}>
          <Box
            sx={{
              ...(isHeaderPinned
                ? {
                    position: 'sticky',
                    top: 0,
                    zIndex: 'var(--ob-z-sticky)',
                  }
                : {}),
              mb: 'var(--ob-space-150)',
            }}
          >
            {/* Finance Header - Depth 0 (Direct on Grid)
                AI Studio Protocol: Headers sit directly on the background
                NO glass, NO cyan edge for Depth 0 elements */}
            <Box
              component="header"
              key={path}
              className="ob-page-header"
              sx={{
                borderBottom: 1,
                borderColor: 'divider',
                animation:
                  'ob-slide-down-fade var(--ob-motion-header-duration) var(--ob-motion-header-ease) both',
                '@media (prefers-reduced-motion: reduce)': {
                  animation: 'none',
                },
              }}
            >
              <Box
                sx={{
                  px: 'var(--ob-space-300)',
                  py: 'var(--ob-space-200)',
                  display: 'flex',
                  alignItems: 'flex-start',
                  justifyContent: 'space-between',
                  gap: 'var(--ob-space-150)',
                  flexWrap: { xs: 'wrap', md: 'nowrap' },
                }}
              >
                <Box sx={{ minWidth: 0 }}>
                  <Typography variant="h4" sx={{ fontWeight: 700 }}>
                    {t('finance.title')}
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{ color: 'text.secondary', mt: 'var(--ob-space-025)' }}
                  >
                    {t('finance.subtitle')}
                  </Typography>
                </Box>
                {headerActions}
              </Box>

              <Box
                sx={{
                  borderTop: 1,
                  borderColor: 'divider',
                  px: 'var(--ob-space-300)',
                }}
              >
                <Tabs
                  value={activeTab}
                  onChange={(_, v) => setActiveTab(v)}
                  variant="scrollable"
                  scrollButtons="auto"
                  allowScrollButtonsMobile
                  sx={{
                    minHeight: 'var(--ob-space-300)',
                    '& .MuiTabs-indicator': {
                      backgroundColor: 'var(--ob-color-neon-cyan)',
                      boxShadow: 'var(--ob-glow-neon-cyan)',
                      height: '2px',
                    },
                    '& .MuiTab-root': {
                      minHeight: 'var(--ob-space-300)',
                      textTransform: 'uppercase',
                      fontSize: 'var(--ob-font-size-xs)',
                      fontWeight: 'var(--ob-font-weight-semibold)',
                      letterSpacing: 'var(--ob-letter-spacing-wider)',
                      px: 'var(--ob-space-100)',
                      color: 'text.secondary',
                      transition: 'all 0.2s ease',
                      '&.Mui-selected': {
                        color: 'var(--ob-color-neon-cyan)',
                        textShadow: 'var(--ob-glow-neon-text)',
                      },
                      '&:hover': {
                        color: 'var(--ob-color-neon-cyan)',
                      },
                    },
                  }}
                >
                  <Tab label={t('finance.tabs.capitalStack')} />
                  <Tab label={t('finance.tabs.drawdownSchedule')} />
                  <Tab label={t('finance.tabs.assetBreakdown')} />
                  <Tab label={t('finance.tabs.facilityEditor')} />
                  <Tab label={t('finance.tabs.jobTimeline')} />
                  <Tab label={t('finance.tabs.loanInterest')} />
                  <Tab label={t('finance.tabs.analytics')} />
                  <Tab label={t('finance.tabs.sensitivity')} />
                </Tabs>
              </Box>
            </Box>
          </Box>

          {!hasAccess ? (
            <FinanceAccessGate role={normalizedRole} />
          ) : (
            <>
              {showProjectGate && (
                <Card variant="glass" sx={{ p: 'var(--ob-space-200)' }}>
                  <Stack spacing={1}>
                    <Typography variant="h6">
                      Select a project to continue
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Choose a project from the header or open the project list.
                    </Typography>
                    {projectError && (
                      <Typography variant="body2" color="error">
                        {projectError.message}
                      </Typography>
                    )}
                    <Box>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => navigate('/projects')}
                      >
                        Go to projects
                      </Button>
                    </Box>
                  </Stack>
                </Card>
              )}
              {hasProject && (
                <>
                  <input
                    ref={workbookInputRef}
                    type="file"
                    accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    style={{ display: 'none' }}
                    onChange={handleWorkbookSelected}
                  />
                  {error && (
                    <Alert severity="error" sx={{ mb: 'var(--ob-space-150)' }}>
                      <strong>{t('finance.errors.generic')}</strong>
                      <Box component="span" sx={{ display: 'block' }}>
                        {error}
                      </Box>
                      {needsScenarioIdentity && (
                        <FinanceIdentityHelper compact />
                      )}
                    </Alert>
                  )}

                  {loading && (
                    <Card
                      variant="glass"
                      sx={{
                        p: 'var(--ob-space-200)',
                        display: 'flex',
                        justifyContent: 'center',
                      }}
                    >
                      <CircularProgress />
                    </Card>
                  )}

                  {scenarioError && (
                    <Alert severity="error" sx={{ mb: 'var(--ob-space-150)' }}>
                      {scenarioError}
                      {needsScenarioCreateIdentity && (
                        <FinanceIdentityHelper compact />
                      )}
                    </Alert>
                  )}
                  {seedError && (
                    <Alert severity="error" sx={{ mb: 'var(--ob-space-150)' }}>
                      {seedError}
                      {needsScenarioCreateIdentity && (
                        <FinanceIdentityHelper compact />
                      )}
                    </Alert>
                  )}
                  {scenarioMessage && (
                    <Alert
                      severity="success"
                      sx={{ mb: 'var(--ob-space-150)' }}
                    >
                      {scenarioMessage}
                    </Alert>
                  )}
                  {onboardingMode === 'workbook' && (
                    <Alert severity="info" sx={{ mb: 'var(--ob-space-150)' }}>
                      <Stack spacing={1}>
                        <Typography variant="body2">
                          Workbook onboarding is active for this project. Import an
                          existing Excel model to structure it into the Singapore
                          finance workflow without rebuilding assumptions manually.
                        </Typography>
                        <Box>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={handleImportWorkbookClick}
                            disabled={previewingWorkbook || importingWorkbook}
                          >
                            {previewingWorkbook || importingWorkbook
                              ? 'Preparing workbook import...'
                              : 'Choose workbook'}
                          </Button>
                        </Box>
                      </Stack>
                    </Alert>
                  )}
                  {onboardingMode === 'sample' && (
                    <Alert severity="info" sx={{ mb: 'var(--ob-space-150)' }}>
                      <Stack spacing={1}>
                        <Typography variant="body2">
                          This sample project starts with a Singapore underwriting
                          template. Review the template guidance below, then export
                          lender or investor materials once the scenario is ready.
                        </Typography>
                        <Stack direction="row" spacing={1}>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => navigate('/developers/why-not-excel')}
                          >
                            Why not Excel?
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/projects/${effectiveProjectId}/evidence`)}
                          >
                            Review evidence pack
                          </Button>
                        </Stack>
                      </Stack>
                    </Alert>
                  )}
                  {quickScreenDraft && (
                    <Alert severity="info" sx={{ mb: 'var(--ob-space-150)' }}>
                      <Stack spacing={1.25}>
                        <Stack
                          direction={{ xs: 'column', md: 'row' }}
                          spacing={1}
                          justifyContent="space-between"
                          alignItems={{ xs: 'flex-start', md: 'center' }}
                        >
                          <Box>
                            <strong>
                              {t('finance.actions.importQuickScreen', {
                                defaultValue: 'Quick screen draft ready.',
                              })}
                            </strong>
                            <Box component="span" sx={{ display: 'block' }}>
                              {quickScreenDraft.scenario.name}
                            </Box>
                            {quickScreenDraft.assessment?.generatedAt ? (
                              <Box
                                component="span"
                                sx={{
                                  display: 'block',
                                  fontSize: 'var(--ob-font-size-2xs)',
                                  color: 'var(--ob-color-text-tertiary)',
                                  mt: 'var(--ob-space-050)',
                                }}
                              >
                                Screened {new Date(quickScreenDraft.assessment.generatedAt).toLocaleString()}
                              </Box>
                            ) : null}
                          </Box>
                          <Stack direction="row" spacing={1}>
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={handleImportQuickScreenDraft}
                            >
                              {t('finance.actions.importQuickScreen', {
                                defaultValue: 'Import quick screen',
                              })}
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                clearQuickScreenFinanceDraft()
                                setQuickScreenDraft(null)
                              }}
                            >
                              {t('common.actions.cancel')}
                            </Button>
                          </Stack>
                        </Stack>
                        {quickScreenAssessmentLines.length > 0 ? (
                          <Box component="ul" sx={{ m: 0, pl: 3 }}>
                            {quickScreenAssessmentLines.map((line) => (
                              <li key={line}>{line}</li>
                            ))}
                          </Box>
                        ) : null}
                      </Stack>
                    </Alert>
                  )}
                  {workbookPreview && (
                    <Alert
                      severity={workbookPreview.isValid ? 'info' : 'warning'}
                      sx={{ mb: 'var(--ob-space-150)' }}
                    >
                      <Stack spacing={1.25}>
                        <Box>
                          <strong>{workbookPreview.filename}</strong>
                          <Box component="span" sx={{ display: 'block' }}>
                            {workbookPreview.scenarioName ?? 'Workbook preview'} •{' '}
                            {workbookPreview.assetCount} assets •{' '}
                            {workbookPreview.detectedSheets.length} sheets mapped
                          </Box>
                        </Box>
                        {workbookPreview.warnings.length > 0 && (
                          <Box component="ul" sx={{ m: 0, pl: 3 }}>
                            {workbookPreview.warnings.map((warning) => (
                              <li key={warning}>{warning}</li>
                            ))}
                          </Box>
                        )}
                        {workbookPreview.validationErrors.length > 0 && (
                          <Box component="ul" sx={{ m: 0, pl: 3 }}>
                            {workbookPreview.validationErrors.map((issue) => (
                              <li key={`${issue.field}:${issue.message}`}>
                                {issue.field}: {issue.message}
                              </li>
                            ))}
                          </Box>
                        )}
                        <Stack direction="row" spacing={1}>
                          {workbookPreview.isValid ? (
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={handleConfirmWorkbookImport}
                              disabled={importingWorkbook}
                            >
                              {importingWorkbook
                                ? t('finance.actions.importingWorkbook', {
                                    defaultValue: 'Importing workbook…',
                                  })
                                : t('finance.actions.importWorkbook', {
                                    defaultValue: 'Import workbook',
                                  })}
                            </Button>
                          ) : null}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={handleDismissWorkbookPreview}
                          >
                            {t('common.actions.cancel')}
                          </Button>
                        </Stack>
                      </Stack>
                    </Alert>
                  )}
                  {hasProject && (
                    <Card
                      variant="glass"
                      sx={{ mb: 'var(--ob-space-150)', p: 'var(--ob-space-200)' }}
                    >
                      <Stack spacing={1.25}>
                        <Box>
                          <Typography variant="h6">Audit evidence snapshot</Typography>
                          <Typography variant="body2" color="text.secondary">
                            Evidence chain health for finance modeling, workbook imports,
                            and regulatory submission prep.
                          </Typography>
                        </Box>
                        {auditEvidenceError ? (
                          <Alert severity="warning">{auditEvidenceError}</Alert>
                        ) : auditEvidence ? (
                          <>
                            <Stack
                              direction={{ xs: 'column', md: 'row' }}
                              spacing={1}
                              useFlexGap
                              flexWrap="wrap"
                            >
                              <Box
                                sx={{
                                  px: 1.25,
                                  py: 0.75,
                                  borderRadius: 2,
                                  bgcolor: auditEvidence.valid
                                    ? 'rgba(15,118,110,0.10)'
                                    : 'rgba(185,28,28,0.10)',
                                  color: auditEvidence.valid ? '#0f766e' : '#b91c1c',
                                  fontSize: '0.8rem',
                                  fontWeight: 700,
                                }}
                              >
                                {auditEvidence.valid ? 'Chain valid' : 'Chain needs review'}
                              </Box>
                              <Typography variant="body2" color="text.secondary">
                                {auditEvidence.chain.signedEntries}/{auditEvidence.chain.entryCount}{' '}
                                signed entries
                              </Typography>
                              {auditEvidence.recipients.length > 0 ? (
                                <Typography variant="body2" color="text.secondary">
                                  Recipients: {auditEvidence.recipients.join(', ')}
                                </Typography>
                              ) : null}
                            </Stack>
                            <Stack spacing={0.75}>
                              {latestFinanceAuditEvent ? (
                                <Typography variant="body2" color="text.secondary">
                                  Latest finance scenario: {latestFinanceAuditEvent.scenarioName ?? 'Scenario'} via{' '}
                                  <strong>{latestFinanceAuditEvent.origin ?? 'manual'}</strong>
                                  {latestFinanceAuditEvent.recordedAt
                                    ? ` on ${new Date(latestFinanceAuditEvent.recordedAt).toLocaleString()}`
                                    : ''}
                                </Typography>
                              ) : null}
                              {latestWorkbookImport ? (
                                <Typography variant="body2" color="text.secondary">
                                  Latest workbook import: {latestWorkbookImport.scenarioName ?? 'Workbook scenario'}
                                  {latestWorkbookImport.workbookFormat
                                    ? ` (${latestWorkbookImport.workbookFormat})`
                                    : ''}
                                </Typography>
                              ) : null}
                              {latestSubmissionEvent ? (
                                <Typography variant="body2" color="text.secondary">
                                  Latest submission event: {latestSubmissionEvent.agencyName ?? latestSubmissionEvent.agency ?? 'Agency'}{' '}
                                  {latestSubmissionEvent.submissionMode
                                    ? `• ${latestSubmissionEvent.submissionMode.replace('_', ' ')}`
                                    : ''}
                                  {latestSubmissionEvent.packageStatus
                                    ? ` • ${latestSubmissionEvent.packageStatus}`
                                    : ''}
                                </Typography>
                              ) : null}
                            </Stack>
                            <Box>
                              <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => navigate(`/projects/${effectiveProjectId}/evidence`)}
                              >
                                Open evidence pack
                              </Button>
                            </Box>
                          </>
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            No audit evidence recorded for this project yet.
                          </Typography>
                        )}
                      </Stack>
                    </Card>
                  )}

                  <Card
                    variant="glass"
                    sx={{ mb: 'var(--ob-space-150)', p: 'var(--ob-space-200)' }}
                  >
                    <Stack
                      direction={{ xs: 'column', md: 'row' }}
                      spacing={1.5}
                      justifyContent="space-between"
                    >
                      <Box>
                        <Typography variant="h6">Finance mode for Singapore developers</Typography>
                        <Typography variant="body2" color="text.secondary">
                          Build a scenario from a deal screen, import a workbook, or
                          start from an SG template. Then package outputs for lenders,
                          investors, and internal approvals.
                        </Typography>
                      </Box>
                      <Stack direction="row" spacing={1}>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => navigate('/developers/why-not-excel')}
                        >
                          Why not Excel?
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={handleExportWorkbook}
                          disabled={!primaryScenario || exportingWorkbook}
                        >
                          {exportingWorkbook ? 'Preparing workbook...' : 'Lender workbook'}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={handleExportCsv}
                          disabled={!primaryScenario || exportingScenario}
                        >
                          {exportingScenario ? 'Preparing export...' : 'Investor export'}
                        </Button>
                      </Stack>
                    </Stack>
                  </Card>

                  {/* Tab Panels - Depth 1 (Glass Cards with ob-card-module) */}
                  <div role="tabpanel" hidden={activeTab !== 0}>
                    {activeTab === 0 && (
                      <Stack spacing="var(--ob-space-200)">
                        <Box className="ob-card-module">
                          <Suspense fallback={panelFallback}>
                            <FinanceScenarioCreator
                              projectId={effectiveProjectId}
                              projectName={projectDisplayName}
                              initialTemplateId={financeTemplateId}
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
                          </Suspense>
                        </Box>

                        {primaryScenario?.isPrivate ? (
                          <FinancePrivacyNotice
                            projectName={projectDisplayName}
                          />
                        ) : null}

                        {showEmptyState && (
                          <Card
                            variant="glass"
                            sx={{
                              p: 'var(--ob-space-300)',
                              textAlign: 'center',
                            }}
                          >
                            <Stack spacing={2} alignItems="center">
                              <Typography variant="h5">
                                Start a finance model
                              </Typography>
                              <Typography
                                variant="body2"
                                color="text.secondary"
                              >
                                Enter assumptions in the scenario builder above
                                or seed a starting point from your capture.
                              </Typography>
                              <Stack
                                direction={{ xs: 'column', sm: 'row' }}
                                spacing={1}
                                justifyContent="center"
                                alignItems="center"
                              >
                                {capturePropertyId && (
                                  <Button
                                    variant="primary"
                                    size="sm"
                                    onClick={handleSeedFromCapture}
                                    disabled={seeding}
                                  >
                                    {seeding
                                      ? 'Seeding...'
                                      : 'Seed from Capture'}
                                  </Button>
                                )}
                                <Button
                                  variant="secondary"
                                  size="sm"
                                  onClick={() => setActiveTab(0)}
                                >
                                  Build from assumptions
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={handleImportWorkbookClick}
                                >
                                  Import from workbook
                                </Button>
                              </Stack>
                            </Stack>
                          </Card>
                        )}

                        {primaryScenario?.scenarioId === 0 && (
                          <Alert
                            severity="warning"
                            icon={<Warning />}
                            sx={{ mb: 'var(--ob-space-050)' }}
                          >
                            <strong>{t('finance.warnings.offlineMode')}</strong>
                            <Typography variant="body2">
                              {t('finance.warnings.offlineModeDetail') ||
                                'You are viewing offline demonstration data. Changes cannot be saved correctly until the backend service is available.'}
                            </Typography>
                          </Alert>
                        )}

                        {scenarios.length > 0 && (
                          <Box className="ob-card-module">
                            <Suspense fallback={panelFallback}>
                              <FinanceCapitalStack
                                scenarios={scenarios}
                                onMarkPrimary={handleMarkPrimary}
                                updatingScenarioId={promotingScenarioId}
                                onRequestDelete={handleRequestDeleteScenario}
                                deletingScenarioId={deletingScenarioId}
                              />
                            </Suspense>
                          </Box>
                        )}
                      </Stack>
                    )}
                  </div>

                  <div role="tabpanel" hidden={activeTab !== 1}>
                    {activeTab === 1 &&
                      (showEmptyState ? (
                        renderEmptyPanel('Drawdown schedule')
                      ) : (
                        <Box className="ob-card-module">
                          <Suspense fallback={panelFallback}>
                            <FinanceDrawdownSchedule scenarios={scenarios} />
                          </Suspense>
                        </Box>
                      ))}
                  </div>
                  <div role="tabpanel" hidden={activeTab !== 2}>
                    {activeTab === 2 &&
                      (showEmptyState
                        ? renderEmptyPanel('Asset breakdown')
                        : primaryScenario && (
                            <Box className="ob-card-module">
                              <Suspense fallback={panelFallback}>
                                <FinanceAssetBreakdown
                                  summary={
                                    primaryScenario.assetMixSummary ?? null
                                  }
                                  breakdowns={
                                    primaryScenario.assetBreakdowns ?? []
                                  }
                                />
                              </Suspense>
                            </Box>
                          ))}
                  </div>
                  <div role="tabpanel" hidden={activeTab !== 3}>
                    {activeTab === 3 &&
                      (showEmptyState ? (
                        renderEmptyPanel('Facility editor')
                      ) : (
                        <Box className="ob-card-module">
                          <Suspense fallback={panelFallback}>
                            <FinanceFacilityEditor
                              scenario={primaryScenario ?? null}
                              onSave={handleSaveLoan}
                              saving={savingLoan}
                            />
                          </Suspense>
                        </Box>
                      ))}
                  </div>
                  <div role="tabpanel" hidden={activeTab !== 4}>
                    {activeTab === 4 &&
                      (showEmptyState ? (
                        renderEmptyPanel('Job timeline')
                      ) : (
                        <Box className="ob-card-module">
                          <Suspense fallback={panelFallback}>
                            <FinanceJobTimeline
                              jobs={timelineJobs}
                              pendingCount={pendingCount}
                            />
                          </Suspense>
                        </Box>
                      ))}
                  </div>
                  <div role="tabpanel" hidden={activeTab !== 5}>
                    {activeTab === 5 &&
                      (showEmptyState ? (
                        renderEmptyPanel('Loan interest')
                      ) : (
                        <Box className="ob-card-module">
                          <Suspense fallback={panelFallback}>
                            <FinanceLoanInterest
                              schedule={
                                primaryScenario?.constructionLoanInterest ??
                                null
                              }
                            />
                          </Suspense>
                        </Box>
                      ))}
                  </div>
                  <div role="tabpanel" hidden={activeTab !== 6}>
                    {activeTab === 6 &&
                      (showEmptyState
                        ? renderEmptyPanel('Analytics')
                        : analyticsMetadata && (
                            <Stack spacing="var(--ob-space-200)">
                              <Box className="ob-card-module">
                                <Suspense fallback={panelFallback}>
                                  <FinanceAnalyticsPanel
                                    analytics={analyticsMetadata}
                                    currency={
                                      primaryScenario?.currency ?? 'SGD'
                                    }
                                  />
                                </Suspense>
                              </Box>
                              {primaryScenario && (
                                <Box className="ob-card-module">
                                  <FinanceSensitivityControls
                                    scenario={primaryScenario}
                                    pendingJobs={pendingCount}
                                    disabled={runningSensitivity}
                                    error={sensitivityError}
                                    onRun={handleRunSensitivity}
                                  />
                                </Box>
                              )}
                            </Stack>
                          ))}
                  </div>
                  <div role="tabpanel" hidden={activeTab !== 7}>
                    {activeTab === 7 &&
                      (showEmptyState ? (
                        renderEmptyPanel('Sensitivity analysis')
                      ) : (
                        <Stack spacing="var(--ob-space-200)">
                          <Box className="ob-card-module">
                            <Suspense fallback={panelFallback}>
                              <FinanceSensitivitySummary
                                summaries={sensitivitySummaries}
                                currency={primaryScenario?.currency ?? 'SGD'}
                              />
                            </Suspense>
                          </Box>
                          {primaryScenario && (
                            <Box className="ob-card-module">
                              <FinanceSensitivityControls
                                scenario={primaryScenario}
                                pendingJobs={pendingCount}
                                disabled={runningSensitivity}
                                error={sensitivityError}
                                onRun={handleRunSensitivity}
                              />
                            </Box>
                          )}
                          <Box className="ob-card-module">
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
                        </Stack>
                      ))}
                  </div>

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
            </>
          )}
        </Box>
      </Box>
    </AppLayout>
  )
}
