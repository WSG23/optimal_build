/**
 * Hook for managing condition assessment state
 *
 * Handles:
 * - Loading current condition assessment for property/scenario
 * - Assessment history loading and management
 * - Scenario-specific assessments
 * - Assessment editor state (draft, editing mode, save)
 * - Derived comparison values (latest/previous entries)
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  exportConditionReport,
  fetchConditionAssessment,
  fetchConditionAssessmentHistory,
  fetchScenarioAssessments,
  saveConditionAssessment,
  type ConditionAssessment,
  type ConditionAssessmentUpsertRequest,
  type DevelopmentScenario,
  type SiteAcquisitionResult,
} from '../../../../api/siteAcquisition'
import type { AssessmentDraftSystem, ConditionAssessmentDraft } from '../types'
import { buildAssessmentDraft } from '../utils'
import {
  formatDateTimeLocalInput,
  convertLocalToISO,
  parseAttachmentsText,
} from '../utils'

// ============================================================================
// Constants
// ============================================================================

const HISTORY_FETCH_LIMIT = 10

// ============================================================================
// Types
// ============================================================================

export interface UseConditionAssessmentOptions {
  /** The captured property result (may be null before capture) */
  capturedProperty: SiteAcquisitionResult | null
  /** The currently active development scenario filter */
  activeScenario: DevelopmentScenario | 'all'
}

export interface UseConditionAssessmentResult {
  // Assessment state
  conditionAssessment: ConditionAssessment | null
  isLoadingCondition: boolean

  // Editor state
  isEditingAssessment: boolean
  assessmentEditorMode: 'new' | 'edit'
  assessmentDraft: ConditionAssessmentDraft
  setAssessmentDraft: React.Dispatch<
    React.SetStateAction<ConditionAssessmentDraft>
  >
  isSavingAssessment: boolean
  assessmentSaveMessage: string | null

  // History state
  assessmentHistory: ConditionAssessment[]
  isLoadingAssessmentHistory: boolean
  assessmentHistoryError: string | null
  historyViewMode: 'timeline' | 'compare'
  setHistoryViewMode: React.Dispatch<
    React.SetStateAction<'timeline' | 'compare'>
  >

  // Scenario assessments
  scenarioAssessments: ConditionAssessment[]
  isLoadingScenarioAssessments: boolean
  scenarioAssessmentsError: string | null

  // Report export state
  isExportingReport: boolean
  reportExportMessage: string | null

  // Derived values
  latestAssessmentEntry: ConditionAssessment | null
  previousAssessmentEntry: ConditionAssessment | null

  // Actions
  openAssessmentEditor: (mode: 'new' | 'edit') => void
  closeAssessmentEditor: () => void
  handleAssessmentFieldChange: (
    field: keyof ConditionAssessmentDraft,
    value: string,
  ) => void
  handleAssessmentSystemChange: (
    index: number,
    field: keyof AssessmentDraftSystem,
    value: string,
  ) => void
  handleAssessmentSubmit: (
    event: React.FormEvent<HTMLFormElement>,
  ) => Promise<void>
  resetAssessmentDraft: () => void
  loadAssessmentHistory: (options?: { silent?: boolean }) => Promise<void>
  loadScenarioAssessments: (options?: { silent?: boolean }) => Promise<void>
  handleReportExport: (format: 'json' | 'pdf') => Promise<void>
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useConditionAssessment({
  capturedProperty,
  activeScenario,
}: UseConditionAssessmentOptions): UseConditionAssessmentResult {
  const propertyId = capturedProperty?.propertyId ?? null

  // Assessment state
  const [conditionAssessment, setConditionAssessment] =
    useState<ConditionAssessment | null>(null)
  const [isLoadingCondition, setIsLoadingCondition] = useState(false)

  // Editor state
  const [isEditingAssessment, setIsEditingAssessment] = useState(false)
  const [assessmentEditorMode, setAssessmentEditorMode] = useState<
    'new' | 'edit'
  >('edit')
  const [assessmentDraft, setAssessmentDraft] =
    useState<ConditionAssessmentDraft>(() => buildAssessmentDraft(null, 'all'))
  const [isSavingAssessment, setIsSavingAssessment] = useState(false)
  const [assessmentSaveMessage, setAssessmentSaveMessage] = useState<
    string | null
  >(null)

  // History state
  const [assessmentHistory, setAssessmentHistory] = useState<
    ConditionAssessment[]
  >([])
  const [isLoadingAssessmentHistory, setIsLoadingAssessmentHistory] =
    useState(false)
  const [assessmentHistoryError, setAssessmentHistoryError] = useState<
    string | null
  >(null)
  const [historyViewMode, setHistoryViewMode] = useState<
    'timeline' | 'compare'
  >('timeline')
  const historyRequestIdRef = useRef(0)

  // Scenario assessments state
  const [scenarioAssessments, setScenarioAssessments] = useState<
    ConditionAssessment[]
  >([])
  const [isLoadingScenarioAssessments, setIsLoadingScenarioAssessments] =
    useState(false)
  const [scenarioAssessmentsError, setScenarioAssessmentsError] = useState<
    string | null
  >(null)
  const scenarioAssessmentsRequestIdRef = useRef(0)

  // Report export state
  const [isExportingReport, setIsExportingReport] = useState(false)
  const [reportExportMessage, setReportExportMessage] = useState<string | null>(
    null,
  )

  // ============================================================================
  // Derived Values
  // ============================================================================

  const latestAssessmentEntry = useMemo(
    () => (assessmentHistory.length > 0 ? assessmentHistory[0] : null),
    [assessmentHistory],
  )

  const previousAssessmentEntry = useMemo(
    () => (assessmentHistory.length > 1 ? assessmentHistory[1] : null),
    [assessmentHistory],
  )

  // ============================================================================
  // Data Loading Callbacks
  // ============================================================================

  const loadAssessmentHistory = useCallback(
    async (options?: { silent?: boolean }) => {
      const requestId = historyRequestIdRef.current + 1
      historyRequestIdRef.current = requestId

      if (!propertyId) {
        setAssessmentHistory([])
        setAssessmentHistoryError(null)
        setIsLoadingAssessmentHistory(false)
        return
      }

      if (!options?.silent) {
        setIsLoadingAssessmentHistory(true)
      }
      try {
        const entries = await fetchConditionAssessmentHistory(
          propertyId,
          activeScenario,
          HISTORY_FETCH_LIMIT,
        )
        if (historyRequestIdRef.current === requestId) {
          setAssessmentHistory(entries)
          setAssessmentHistoryError(null)
        }
      } catch (error) {
        console.error('Failed to fetch condition assessment history:', error)
        if (historyRequestIdRef.current === requestId) {
          setAssessmentHistory([])
          setAssessmentHistoryError('Unable to load inspection history.')
        }
      } finally {
        if (!options?.silent && historyRequestIdRef.current === requestId) {
          setIsLoadingAssessmentHistory(false)
        }
      }
    },
    [propertyId, activeScenario],
  )

  const loadScenarioAssessments = useCallback(
    async (options?: { silent?: boolean }) => {
      const requestId = scenarioAssessmentsRequestIdRef.current + 1
      scenarioAssessmentsRequestIdRef.current = requestId

      if (!propertyId) {
        setScenarioAssessments([])
        setScenarioAssessmentsError(null)
        setIsLoadingScenarioAssessments(false)
        return
      }

      if (!options?.silent) {
        setIsLoadingScenarioAssessments(true)
      }
      try {
        const assessments = await fetchScenarioAssessments(propertyId)
        if (scenarioAssessmentsRequestIdRef.current === requestId) {
          setScenarioAssessments(assessments)
          setScenarioAssessmentsError(null)
        }
      } catch (error) {
        console.error('Failed to fetch scenario assessments:', error)
        if (scenarioAssessmentsRequestIdRef.current === requestId) {
          setScenarioAssessments([])
          setScenarioAssessmentsError('Unable to load scenario overrides.')
        }
      } finally {
        if (
          !options?.silent &&
          scenarioAssessmentsRequestIdRef.current === requestId
        ) {
          setIsLoadingScenarioAssessments(false)
        }
      }
    },
    [propertyId],
  )

  // ============================================================================
  // Effects - Load Assessment Data
  // ============================================================================

  // Load condition assessment when property or scenario changes
  useEffect(() => {
    let cancelled = false
    async function loadConditionAssessment() {
      if (!capturedProperty) {
        setConditionAssessment(null)
        return
      }
      setIsLoadingCondition(true)
      try {
        const assessment = await fetchConditionAssessment(
          capturedProperty.propertyId,
          activeScenario,
        )
        if (!cancelled) {
          setConditionAssessment(assessment)
        }
      } catch (error) {
        if (!cancelled) {
          console.error('Failed to fetch condition assessment:', error)
          setConditionAssessment(null)
        }
      } finally {
        if (!cancelled) {
          setIsLoadingCondition(false)
        }
      }
    }

    loadConditionAssessment()
    return () => {
      cancelled = true
    }
  }, [capturedProperty, activeScenario])

  // Load assessment history when property changes
  useEffect(() => {
    void loadAssessmentHistory()
  }, [loadAssessmentHistory])

  // Load scenario assessments when property changes
  useEffect(() => {
    void loadScenarioAssessments()
  }, [loadScenarioAssessments])

  // Reset history view mode when property changes
  useEffect(() => {
    setHistoryViewMode('timeline')
  }, [propertyId])

  // ============================================================================
  // Effects - Sync Draft with Assessment
  // ============================================================================

  // Sync draft with current assessment when not editing
  useEffect(() => {
    if (!capturedProperty) {
      setAssessmentDraft(buildAssessmentDraft(null, 'all'))
      setAssessmentEditorMode('edit')
      setIsEditingAssessment(false)
      return
    }

    if (!isEditingAssessment) {
      const baseDraft = buildAssessmentDraft(
        conditionAssessment,
        activeScenario,
      )
      const nowLocal = formatDateTimeLocalInput(new Date().toISOString())
      setAssessmentDraft({
        ...baseDraft,
        recordedAtLocal: nowLocal,
      })
    }
  }, [
    capturedProperty,
    conditionAssessment,
    activeScenario,
    isEditingAssessment,
    assessmentEditorMode,
  ])

  // ============================================================================
  // Editor Actions
  // ============================================================================

  const openAssessmentEditor = useCallback(
    (mode: 'new' | 'edit') => {
      if (!capturedProperty) {
        return
      }
      const targetScenario = activeScenario === 'all' ? 'all' : activeScenario
      const nowLocal = formatDateTimeLocalInput(new Date().toISOString())

      if (mode === 'new') {
        const baseDraft = buildAssessmentDraft(null, targetScenario)
        setAssessmentDraft({
          ...baseDraft,
          inspectorName: '',
          recordedAtLocal: nowLocal,
          attachmentsText: '',
        })
      } else {
        let sourceAssessment: ConditionAssessment | null = null
        if (activeScenario === 'all' && latestAssessmentEntry) {
          sourceAssessment = latestAssessmentEntry
        } else {
          sourceAssessment = conditionAssessment
        }
        const scenarioForDraft: DevelopmentScenario | 'all' =
          (sourceAssessment?.scenario as
            | DevelopmentScenario
            | null
            | undefined) ?? (activeScenario as DevelopmentScenario | 'all')
        const baseDraft = buildAssessmentDraft(
          sourceAssessment,
          scenarioForDraft,
        )
        setAssessmentDraft({
          ...baseDraft,
          recordedAtLocal: nowLocal,
        })
      }
      setAssessmentEditorMode(mode)
      setAssessmentSaveMessage(null)
      setIsEditingAssessment(true)
    },
    [
      capturedProperty,
      activeScenario,
      latestAssessmentEntry,
      conditionAssessment,
    ],
  )

  const closeAssessmentEditor = useCallback(() => {
    setIsEditingAssessment(false)
    setAssessmentEditorMode('edit')
  }, [])

  const handleAssessmentFieldChange = useCallback(
    (field: keyof ConditionAssessmentDraft, value: string) => {
      setAssessmentDraft((prev) => ({
        ...prev,
        [field]: value,
      }))
    },
    [],
  )

  const handleAssessmentSystemChange = useCallback(
    (index: number, field: keyof AssessmentDraftSystem, value: string) => {
      setAssessmentDraft((prev) => {
        const systems = [...prev.systems]
        systems[index] = {
          ...systems[index],
          [field]: value,
        }
        return { ...prev, systems }
      })
    },
    [],
  )

  const resetAssessmentDraft = useCallback(() => {
    const nowLocal = formatDateTimeLocalInput(new Date().toISOString())

    if (assessmentEditorMode === 'new') {
      const baseDraft = buildAssessmentDraft(null, activeScenario)
      setAssessmentDraft({
        ...baseDraft,
        inspectorName: '',
        recordedAtLocal: nowLocal,
        attachmentsText: '',
      })
    } else {
      let sourceAssessment: ConditionAssessment | null = null
      if (activeScenario === 'all' && latestAssessmentEntry) {
        sourceAssessment = latestAssessmentEntry
      } else {
        sourceAssessment = conditionAssessment
      }
      const baseDraft = buildAssessmentDraft(sourceAssessment, activeScenario)
      setAssessmentDraft({
        ...baseDraft,
        recordedAtLocal: nowLocal,
      })
    }
    setAssessmentSaveMessage(null)
  }, [
    assessmentEditorMode,
    activeScenario,
    latestAssessmentEntry,
    conditionAssessment,
  ])

  const handleAssessmentSubmit = useCallback(
    async (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault()
      if (!capturedProperty) {
        return
      }

      setIsSavingAssessment(true)
      setAssessmentSaveMessage(null)

      try {
        const systemsPayload: ConditionAssessmentUpsertRequest['systems'] =
          assessmentDraft.systems.map((system) => {
            const parsedScore = Number(system.score)
            const scoreValue = Number.isNaN(parsedScore) ? 0 : parsedScore
            return {
              name: system.name,
              rating: system.rating,
              score: scoreValue,
              notes: system.notes,
              recommendedActions: system.recommendedActions
                .split('\n')
                .map((line) => line.trim())
                .filter((line) => line.length > 0),
            }
          })

        const parsedOverallScore = Number(assessmentDraft.overallScore)
        const overallScoreValue = Number.isNaN(parsedOverallScore)
          ? 0
          : parsedOverallScore

        const inspectorNameValue = assessmentDraft.inspectorName.trim()
        const recordedAtIso = convertLocalToISO(assessmentDraft.recordedAtLocal)
        const attachmentsPayload = parseAttachmentsText(
          assessmentDraft.attachmentsText,
        )

        const payload: ConditionAssessmentUpsertRequest = {
          scenario: assessmentDraft.scenario,
          overallRating: assessmentDraft.overallRating,
          overallScore: overallScoreValue,
          riskLevel: assessmentDraft.riskLevel,
          summary: assessmentDraft.summary,
          scenarioContext:
            assessmentDraft.scenarioContext.trim() === ''
              ? undefined
              : assessmentDraft.scenarioContext,
          systems: systemsPayload,
          recommendedActions: assessmentDraft.recommendedActionsText
            .split('\n')
            .map((line) => line.trim())
            .filter((line) => line.length > 0),
          attachments: attachmentsPayload,
        }

        if (inspectorNameValue) {
          payload.inspectorName = inspectorNameValue
        }
        if (recordedAtIso) {
          payload.recordedAt = recordedAtIso
        }

        const saved = await saveConditionAssessment(
          capturedProperty.propertyId,
          payload,
        )

        if (saved) {
          const refreshed = await fetchConditionAssessment(
            capturedProperty.propertyId,
            activeScenario,
          )
          setConditionAssessment(refreshed)
          setAssessmentDraft(buildAssessmentDraft(refreshed, activeScenario))
          await loadAssessmentHistory({ silent: true })
          await loadScenarioAssessments({ silent: true })
          setAssessmentSaveMessage('Inspection saved successfully.')
          closeAssessmentEditor()
        } else {
          setAssessmentSaveMessage(
            'Unable to save inspection data. Please try again.',
          )
        }
      } catch (error) {
        console.error('Failed to save inspection assessment:', error)
        setAssessmentSaveMessage(
          'Unable to save inspection data. Please try again.',
        )
      } finally {
        setIsSavingAssessment(false)
      }
    },
    [
      capturedProperty,
      assessmentDraft,
      activeScenario,
      loadAssessmentHistory,
      loadScenarioAssessments,
      closeAssessmentEditor,
    ],
  )

  // ============================================================================
  // Report Export
  // ============================================================================

  const handleReportExport = useCallback(
    async (format: 'json' | 'pdf') => {
      if (!propertyId) {
        return
      }
      try {
        setIsExportingReport(true)
        setReportExportMessage(null)
        const { blob, filename } = await exportConditionReport(
          propertyId,
          format,
        )
        const downloadUrl = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = downloadUrl
        link.download = filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(downloadUrl)
        setReportExportMessage(
          format === 'pdf'
            ? 'Condition report downloaded (PDF).'
            : 'Condition report downloaded (JSON).',
        )
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : 'Unable to download condition report.'
        console.error('Failed to export condition report:', error)
        setReportExportMessage(message)
      } finally {
        setIsExportingReport(false)
      }
    },
    [propertyId],
  )

  // ============================================================================
  // Return
  // ============================================================================

  return {
    // Assessment state
    conditionAssessment,
    isLoadingCondition,

    // Editor state
    isEditingAssessment,
    assessmentEditorMode,
    assessmentDraft,
    setAssessmentDraft,
    isSavingAssessment,
    assessmentSaveMessage,

    // History state
    assessmentHistory,
    isLoadingAssessmentHistory,
    assessmentHistoryError,
    historyViewMode,
    setHistoryViewMode,

    // Scenario assessments
    scenarioAssessments,
    isLoadingScenarioAssessments,
    scenarioAssessmentsError,

    // Report export state
    isExportingReport,
    reportExportMessage,

    // Derived values
    latestAssessmentEntry,
    previousAssessmentEntry,

    // Actions
    openAssessmentEditor,
    closeAssessmentEditor,
    handleAssessmentFieldChange,
    handleAssessmentSystemChange,
    handleAssessmentSubmit,
    resetAssessmentDraft,
    loadAssessmentHistory,
    loadScenarioAssessments,
    handleReportExport,
  }
}
