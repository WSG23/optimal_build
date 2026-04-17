import {
  type ChangeEvent,
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
import { type FinanceProjectOption } from './components/FinanceHeaderControls'
import { FinanceAccessGate } from './components/FinancePrivacyNotice'
import { useFinanceScenarios } from './hooks/useFinanceScenarios'
import '../../styles/finance/polish.css'

import {
  Box,
  Stack,
  Typography,
  CircularProgress,
  useMediaQuery,
  useTheme,
} from '@mui/material'

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

import { FinanceHeader } from './FinanceHeader'
import { FinanceAlerts } from './FinanceAlerts'
import { FinanceAuditCard } from './FinanceAuditCard'
import { FinanceOverviewCard } from './FinanceOverviewCard'
import { FinanceTabPanels } from './FinanceTabPanels'
import {
  POLL_INTERVAL_MS,
  ALLOWED_FINANCE_ROLES,
  DEFAULT_SENSITIVITY_HEADERS,
  shortenProjectId,
  isJobPending,
  escapeCsvValue,
  downloadFile,
} from './financeUtils'

interface FinanceWorkspaceProps {
  workspace?: 'agent' | 'developer'
}

export function FinanceWorkspace(_props: FinanceWorkspaceProps = {}) {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
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
  const showFinanceOverview = activeTab === 0
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
  const [auditEvidence, setAuditEvidence] =
    useState<FinanceAuditEvidence | null>(null)
  const [auditEvidenceError, setAuditEvidenceError] = useState<string | null>(
    null,
  )
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
      const blob = await exportFinanceScenarioWorkbook(
        primaryScenario.scenarioId,
      )
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
    [
      hasProject,
      effectiveProjectId,
      effectiveProjectName,
      projectDisplayName,
      t,
    ],
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
  }, [
    effectiveProjectId,
    hasProject,
    scenarios.length,
    primaryScenario?.scenarioId,
  ])

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
          effectiveProjectName ??
          quickScreenDraft.projectName ??
          projectDisplayName,
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

  return (
    <AppLayout
      title={t('finance.title')}
      subtitle={t('finance.subtitle')}
      hideHeader
    >
      <Box className="finance-workspace" sx={{ pb: 'var(--ob-space-400)' }}>
        <Box sx={{ px: 'var(--ob-space-150)' }}>
          <FinanceHeader
            path={path}
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            isHeaderPinned={isHeaderPinned}
            setIsHeaderPinned={setIsHeaderPinned}
            isMobile={isMobile}
            t={t}
            hasAccess={hasAccess}
            headerControlsProps={{
              selectedProjectId: effectiveProjectId,
              selectedProjectName: effectiveProjectName ?? null,
              options: projectOptions,
              onProjectChange: handleProjectChange,
              onRefresh: () => {
                refresh()
              },
              refreshing: loading,
              onImportWorkbook: handleImportWorkbookClick,
              importingWorkbook: previewingWorkbook || importingWorkbook,
              importDisabled: !hasProject,
              onExportWorkbook: handleExportWorkbook,
              exportingWorkbook,
              onExportCsv: handleExportCsv,
              exportingCsv: exportingScenario,
              exportDisabled: !primaryScenario,
            }}
          />

          {!hasAccess ? (
            <FinanceAccessGate role={normalizedRole} />
          ) : (
            <>
              {showProjectGate && (
                <Card variant="default" sx={{ p: 'var(--ob-space-200)' }}>
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

                  {loading && (
                    <Card
                      variant="default"
                      sx={{
                        p: 'var(--ob-space-200)',
                        display: 'flex',
                        justifyContent: 'center',
                      }}
                    >
                      <CircularProgress />
                    </Card>
                  )}

                  <FinanceAlerts
                    error={error}
                    scenarioError={scenarioError}
                    seedError={seedError}
                    scenarioMessage={scenarioMessage}
                    needsScenarioIdentity={needsScenarioIdentity}
                    needsScenarioCreateIdentity={needsScenarioCreateIdentity}
                    onboardingMode={onboardingMode}
                    effectiveProjectId={effectiveProjectId}
                    previewingWorkbook={previewingWorkbook}
                    importingWorkbook={importingWorkbook}
                    handleImportWorkbookClick={handleImportWorkbookClick}
                    navigate={navigate}
                    t={t}
                    quickScreenDraft={quickScreenDraft}
                    quickScreenAssessmentLines={quickScreenAssessmentLines}
                    handleImportQuickScreenDraft={handleImportQuickScreenDraft}
                    clearQuickScreenDraft={() => {
                      clearQuickScreenFinanceDraft()
                      setQuickScreenDraft(null)
                    }}
                    workbookPreview={workbookPreview}
                    handleConfirmWorkbookImport={handleConfirmWorkbookImport}
                    handleDismissWorkbookPreview={handleDismissWorkbookPreview}
                  />

                  {hasProject && showFinanceOverview && (
                    <FinanceAuditCard
                      effectiveProjectId={effectiveProjectId}
                      auditEvidence={auditEvidence}
                      auditEvidenceError={auditEvidenceError}
                      navigate={navigate}
                    />
                  )}

                  {showFinanceOverview && (
                    <FinanceOverviewCard
                      navigate={navigate}
                      handleExportWorkbook={handleExportWorkbook}
                      handleExportCsv={handleExportCsv}
                      hasPrimaryScenario={!!primaryScenario}
                      exportingWorkbook={exportingWorkbook}
                      exportingScenario={exportingScenario}
                    />
                  )}

                  <FinanceTabPanels
                    activeTab={activeTab}
                    setActiveTab={setActiveTab}
                    scenarios={scenarios}
                    primaryScenario={primaryScenario}
                    analyticsMetadata={analyticsMetadata}
                    showEmptyState={showEmptyState}
                    effectiveProjectId={effectiveProjectId}
                    projectDisplayName={projectDisplayName}
                    financeTemplateId={financeTemplateId}
                    capturePropertyId={capturePropertyId}
                    seeding={seeding}
                    savingLoan={savingLoan}
                    promotingScenarioId={promotingScenarioId}
                    deletingScenarioId={deletingScenarioId}
                    runningSensitivity={runningSensitivity}
                    sensitivityError={sensitivityError}
                    pendingCount={pendingCount}
                    timelineJobs={timelineJobs}
                    parameters={parameters}
                    selectedParameters={selectedParameters}
                    filteredSensitivity={filteredSensitivity}
                    sensitivitySummaries={sensitivitySummaries}
                    t={t}
                    addScenario={addScenario}
                    refresh={refresh}
                    setScenarioMessage={setScenarioMessage}
                    setScenarioError={setScenarioError}
                    handleSeedFromCapture={handleSeedFromCapture}
                    handleImportWorkbookClick={handleImportWorkbookClick}
                    handleSaveLoan={handleSaveLoan}
                    handleMarkPrimary={handleMarkPrimary}
                    handleRequestDeleteScenario={handleRequestDeleteScenario}
                    handleRunSensitivity={handleRunSensitivity}
                    handleSelectAll={handleSelectAll}
                    handleToggleParameter={handleToggleParameter}
                    handleDownloadCsv={handleDownloadCsv}
                    handleDownloadJson={handleDownloadJson}
                  />

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
