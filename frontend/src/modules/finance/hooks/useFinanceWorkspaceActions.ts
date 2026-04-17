/**
 * Finance Workspace Actions Hook
 *
 * Manages action handlers for export, import, delete, sensitivity,
 * and other workspace operations.
 * Extracted from FinanceWorkspace for component size management.
 */

import { type ChangeEvent, useCallback, useRef, useState } from 'react'
import {
  deleteFinanceScenario,
  exportFinanceScenarioCsv,
  exportFinanceScenarioWorkbook,
  importFinanceWorkbook,
  previewFinanceWorkbookImport,
  type FinanceWorkbookImportPreview,
  type SensitivityBandInput,
  runScenarioSensitivity,
  updateFinanceScenario,
  updateConstructionLoan,
  type ConstructionLoanInput,
} from '../../../api/finance'
import type { FinanceScenarioSummary } from '../hooks/useFinanceScenarios'
import {
  DEFAULT_SENSITIVITY_HEADERS,
  escapeCsvValue,
  downloadFile,
} from '../financeUtils'

interface UseFinanceWorkspaceActionsParams {
  primaryScenario: FinanceScenarioSummary | null
  filteredSensitivity: Array<{
    parameter?: string | null
    scenario?: string | null
    deltaLabel?: string | null
    deltaValue?: string | number | null
    npv?: string | number | null
    irr?: string | number | null
    escalatedCost?: string | number | null
    totalInterest?: string | number | null
  }>
  hasProject: boolean
  effectiveProjectId: string
  effectiveProjectName: string | null
  projectDisplayName: string
  addScenario: (scenario: FinanceScenarioSummary) => void
  refresh: () => void | Promise<void>
  t: (key: string, options?: Record<string, unknown>) => string
}

export function useFinanceWorkspaceActions({
  primaryScenario,
  filteredSensitivity,
  hasProject,
  effectiveProjectId,
  effectiveProjectName,
  projectDisplayName,
  addScenario,
  refresh,
  t,
}: UseFinanceWorkspaceActionsParams) {
  const [savingLoan, setSavingLoan] = useState(false)
  const [_loanError, setLoanError] = useState<string | null>(null)
  const [scenarioMessage, setScenarioMessage] = useState<string | null>(null)
  const [scenarioError, setScenarioError] = useState<string | null>(null)
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
  const workbookInputRef = useRef<HTMLInputElement | null>(null)

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
      setPendingWorkbookFile(null)
      setWorkbookPreview(null)
      await refresh()
      return 0 // signal to set activeTab to 0
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
    return undefined
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

  return {
    // State
    savingLoan,
    scenarioMessage,
    setScenarioMessage,
    scenarioError,
    setScenarioError,
    promotingScenarioId,
    runningSensitivity,
    sensitivityError,
    setSensitivityError,
    scenarioPendingDelete,
    deletingScenarioId,
    exportingScenario,
    exportingWorkbook,
    previewingWorkbook,
    importingWorkbook,
    workbookPreview,
    workbookInputRef,
    // Handlers
    handleSaveLoan,
    handleMarkPrimary,
    handleRequestDeleteScenario,
    handleCancelDelete,
    handleConfirmDelete,
    handleRunSensitivity,
    handleExportCsv,
    handleExportWorkbook,
    handleImportWorkbookClick,
    handleWorkbookSelected,
    handleDismissWorkbookPreview,
    handleConfirmWorkbookImport,
    handleDownloadCsv,
    handleDownloadJson,
  }
}
