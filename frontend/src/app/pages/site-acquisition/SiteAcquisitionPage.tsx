import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  capturePropertyForDevelopment,
  fetchChecklistSummary,
  fetchPropertyChecklist,
  fetchConditionAssessment,
  fetchConditionAssessmentHistory,
  fetchScenarioAssessments,
  saveConditionAssessment,
  updateChecklistItem,
  type ChecklistItem,
  type ChecklistSummary,
  type ConditionAssessment,
  type ConditionAssessmentUpsertRequest,
  type DevelopmentScenario,
  type SiteAcquisitionResult,
} from '../../../api/siteAcquisition'

const SCENARIO_OPTIONS: Array<{
  value: DevelopmentScenario
  label: string
  description: string
  icon: string
}> = [
  {
    value: 'raw_land',
    label: 'New Construction',
    description: 'Raw land development with ground-up construction',
    icon: '🏗️',
  },
  {
    value: 'existing_building',
    label: 'Renovation',
    description: 'Existing building renovation and modernization',
    icon: '🔨',
  },
  {
    value: 'heritage_property',
    label: 'Heritage Integration',
    description: 'Heritage-protected property with conservation requirements',
    icon: '🏛️',
  },
  {
    value: 'underused_asset',
    label: 'Adaptive Reuse',
    description: 'Underutilized asset repositioning and value-add',
    icon: '♻️',
  },
  {
    value: 'mixed_use_redevelopment',
    label: 'Mixed-Use Redevelopment',
    description: 'Complex mixed-use project with residential, commercial, and retail components',
    icon: '🏙️',
  },
]

const CONDITION_RATINGS = ['A', 'B', 'C', 'D', 'E']
const CONDITION_RISK_LEVELS = ['low', 'moderate', 'elevated', 'high', 'critical']
const DEFAULT_CONDITION_SYSTEMS = [
  'Structural frame & envelope',
  'Mechanical & electrical systems',
  'Compliance & envelope maintenance',
]
const HISTORY_FETCH_LIMIT = 10

type AssessmentDraftSystem = {
  name: string
  rating: string
  score: string
  notes: string
  recommendedActions: string
}

type ConditionAssessmentDraft = {
  scenario: DevelopmentScenario | 'all'
  overallRating: string
  overallScore: string
  riskLevel: string
  summary: string
  scenarioContext: string
  systems: AssessmentDraftSystem[]
  recommendedActionsText: string
}

function buildAssessmentDraft(
  assessment: ConditionAssessment | null,
  activeScenario: DevelopmentScenario | 'all',
): ConditionAssessmentDraft {
  const targetScenario =
    assessment?.scenario ?? (activeScenario === 'all' ? 'all' : activeScenario)
  const systemsFromAssessment = assessment?.systems ?? []

  const systems: AssessmentDraftSystem[] = (
    systemsFromAssessment.length > 0
      ? systemsFromAssessment
      : DEFAULT_CONDITION_SYSTEMS.map((name) => ({
          name,
          rating: 'B',
          score: 70,
          notes: '',
          recommendedActions: '',
        }))
  ).map((system) => ({
    name: system.name,
    rating: system.rating,
    score: String(system.score ?? 0),
    notes: system.notes ?? '',
    recommendedActions: Array.isArray(system.recommendedActions)
      ? system.recommendedActions.join('\n')
      : '',
  }))

  return {
    scenario: targetScenario,
    overallRating: assessment?.overallRating ?? 'B',
    overallScore: String(assessment?.overallScore ?? 75),
    riskLevel: assessment?.riskLevel ?? 'moderate',
    summary: assessment?.summary ?? '',
    scenarioContext: assessment?.scenarioContext ?? '',
    systems,
    recommendedActionsText: assessment?.recommendedActions
      ? assessment.recommendedActions.join('\n')
      : '',
  }
}

function formatCategoryName(category: string): string {
  return category
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function computeChecklistSummary(
  items: ChecklistItem[],
  propertyId: string,
): ChecklistSummary {
  const totals = {
    total: items.length,
    completed: 0,
    inProgress: 0,
    pending: 0,
    notApplicable: 0,
  }

  const byCategoryStatus: Record<
    string,
    {
      total: number
      completed: number
      inProgress: number
      pending: number
      notApplicable: number
    }
  > = {}

  items.forEach((item) => {
    switch (item.status) {
      case 'completed':
        totals.completed += 1
        break
      case 'in_progress':
        totals.inProgress += 1
        break
      case 'not_applicable':
        totals.notApplicable += 1
        break
      default:
        totals.pending += 1
        break
    }

    const categoryEntry =
      byCategoryStatus[item.category] ?? {
        total: 0,
        completed: 0,
        inProgress: 0,
        pending: 0,
        notApplicable: 0,
      }

    categoryEntry.total += 1
    if (item.status === 'completed') {
      categoryEntry.completed += 1
    } else if (item.status === 'in_progress') {
      categoryEntry.inProgress += 1
    } else if (item.status === 'not_applicable') {
      categoryEntry.notApplicable += 1
    } else {
      categoryEntry.pending += 1
    }

    byCategoryStatus[item.category] = categoryEntry
  })

  const completionPercentage =
    totals.total > 0 ? Math.round((totals.completed / totals.total) * 100) : 0

  return {
    propertyId,
    total: totals.total,
    completed: totals.completed,
    inProgress: totals.inProgress,
    pending: totals.pending,
    notApplicable: totals.notApplicable,
    completionPercentage,
    byCategoryStatus,
  }
}

export function SiteAcquisitionPage() {
  const [latitude, setLatitude] = useState('1.3000')
  const [longitude, setLongitude] = useState('103.8500')
  const [selectedScenarios, setSelectedScenarios] = useState<DevelopmentScenario[]>([])
  const [isCapturing, setIsCapturing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [capturedProperty, setCapturedProperty] = useState<SiteAcquisitionResult | null>(null)

  // Checklist state
  const [checklistItems, setChecklistItems] = useState<ChecklistItem[]>([])
  const [checklistSummary, setChecklistSummary] = useState<ChecklistSummary | null>(null)
  const [isLoadingChecklist, setIsLoadingChecklist] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [availableChecklistScenarios, setAvailableChecklistScenarios] = useState<
    DevelopmentScenario[]
  >([])
  const [activeScenario, setActiveScenario] = useState<DevelopmentScenario | 'all'>('all')
  const [conditionAssessment, setConditionAssessment] =
    useState<ConditionAssessment | null>(null)
  const [isLoadingCondition, setIsLoadingCondition] = useState(false)
  const [isEditingAssessment, setIsEditingAssessment] = useState(false)
  const [assessmentDraft, setAssessmentDraft] = useState<ConditionAssessmentDraft>(() =>
    buildAssessmentDraft(null, 'all'),
  )
  const [isSavingAssessment, setIsSavingAssessment] = useState(false)
  const [assessmentSaveMessage, setAssessmentSaveMessage] = useState<string | null>(
    null,
  )
  const [assessmentHistory, setAssessmentHistory] = useState<ConditionAssessment[]>([])
  const [isLoadingAssessmentHistory, setIsLoadingAssessmentHistory] = useState(false)
  const [assessmentHistoryError, setAssessmentHistoryError] = useState<string | null>(
    null,
  )
  const [historyViewMode, setHistoryViewMode] = useState<'timeline' | 'compare'>(
    'timeline',
  )
  const historyRequestIdRef = useRef(0)
  const [scenarioAssessments, setScenarioAssessments] = useState<ConditionAssessment[]>(
    [],
  )
  const [isLoadingScenarioAssessments, setIsLoadingScenarioAssessments] =
    useState(false)
  const [scenarioAssessmentsError, setScenarioAssessmentsError] = useState<string | null>(
    null,
  )
  const scenarioAssessmentsRequestIdRef = useRef(0)
  const [scenarioComparisonBase, setScenarioComparisonBase] =
    useState<DevelopmentScenario | null>(null)
  const propertyId = capturedProperty?.propertyId ?? null

  const scenarioLookup = useMemo(
    () => new Map(SCENARIO_OPTIONS.map((option) => [option.value, option])),
    [],
  )

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

  useEffect(() => {
    void loadAssessmentHistory()
  }, [loadAssessmentHistory])

  useEffect(() => {
    void loadScenarioAssessments()
  }, [loadScenarioAssessments])

  useEffect(() => {
    setHistoryViewMode('timeline')
  }, [propertyId])

  // Load checklist when property is captured
  useEffect(() => {
    async function loadChecklist() {
      if (!capturedProperty) {
        setChecklistItems([])
        setChecklistSummary(null)
        setAvailableChecklistScenarios([])
        setActiveScenario('all')
        setSelectedCategory(null)
        setConditionAssessment(null)
        return
      }

      setIsLoadingChecklist(true)
      try {
        const [items, summary] = await Promise.all([
          fetchPropertyChecklist(capturedProperty.propertyId),
          fetchChecklistSummary(capturedProperty.propertyId),
        ])
        const sortedItems = [...items].sort((a, b) => {
          const orderA = a.displayOrder ?? Number.MAX_SAFE_INTEGER
          const orderB = b.displayOrder ?? Number.MAX_SAFE_INTEGER
          if (orderA !== orderB) {
            return orderA - orderB
          }
          return a.itemTitle.localeCompare(b.itemTitle)
        })
        setChecklistItems(sortedItems)
        setChecklistSummary(summary)
        const scenarioSet = new Set<DevelopmentScenario>()
        sortedItems.forEach((item) => {
          if (scenarioLookup.has(item.developmentScenario)) {
            scenarioSet.add(item.developmentScenario)
          }
        })
        const scenarios = Array.from(scenarioSet)
        setAvailableChecklistScenarios(scenarios)
        setActiveScenario((prev) => {
          if (scenarios.length === 0) {
            return 'all'
          }
          if (prev !== 'all' && scenarios.includes(prev)) {
            return prev
          }
          if (scenarios.length === 1) {
            return scenarios[0]
          }
          return 'all'
        })
        setSelectedCategory(null)
      } catch (err) {
        console.error('Failed to load checklist:', err)
      } finally {
        setIsLoadingChecklist(false)
      }
    }

    loadChecklist()
  }, [capturedProperty, scenarioLookup])

  const filteredChecklistItems = useMemo(
    () =>
      activeScenario === 'all'
        ? checklistItems
        : checklistItems.filter(
            (item) => item.developmentScenario === activeScenario,
          ),
    [checklistItems, activeScenario],
  )

  const displaySummary = useMemo(() => {
    if (!capturedProperty) {
      return null
    }
    if (activeScenario === 'all' && checklistSummary) {
      return checklistSummary
    }
    return computeChecklistSummary(filteredChecklistItems, capturedProperty.propertyId)
  }, [activeScenario, capturedProperty, checklistSummary, filteredChecklistItems])

  const activeScenarioDetails = useMemo(
    () => (activeScenario === 'all' ? null : scenarioLookup.get(activeScenario)),
    [activeScenario, scenarioLookup],
  )

  const quickAnalysisScenarios = capturedProperty?.quickAnalysis.scenarios ?? []
  const comparisonScenarios =
    activeScenario === 'all'
      ? quickAnalysisScenarios
      : quickAnalysisScenarios.filter(
          (scenario) => scenario.scenario === activeScenario,
        )
  const scenarioOverrideEntries = useMemo(
    () =>
      scenarioAssessments.filter(
        (
          assessment,
        ): assessment is ConditionAssessment & {
          scenario: DevelopmentScenario
        } => assessment.scenario !== null,
      ),
    [scenarioAssessments],
  )

  useEffect(() => {
    if (scenarioOverrideEntries.length === 0) {
      if (scenarioComparisonBase !== null) {
        setScenarioComparisonBase(null)
      }
      return
    }
    if (
      !scenarioComparisonBase ||
      !scenarioOverrideEntries.some(
        (assessment) => assessment.scenario === scenarioComparisonBase,
      )
    ) {
      setScenarioComparisonBase(scenarioOverrideEntries[0].scenario)
    }
  }, [scenarioOverrideEntries, scenarioComparisonBase])

  const baseScenarioAssessment = useMemo(() => {
    if (scenarioOverrideEntries.length === 0) {
      return null
    }
    if (!scenarioComparisonBase) {
      return scenarioOverrideEntries[0]
    }
    return (
      scenarioOverrideEntries.find(
        (assessment) => assessment.scenario === scenarioComparisonBase,
      ) ?? scenarioOverrideEntries[0]
    )
  }, [scenarioOverrideEntries, scenarioComparisonBase])

  const scenarioComparisonEntries = useMemo(() => {
    if (!baseScenarioAssessment) {
      return []
    }
    return scenarioOverrideEntries.filter(
      (assessment) => assessment.scenario !== baseScenarioAssessment.scenario,
    )
  }, [scenarioOverrideEntries, baseScenarioAssessment])

  const describeRatingChange = useCallback(
    (current: string, reference: string) => {
      const currentIndex = CONDITION_RATINGS.indexOf(current)
      const referenceIndex = CONDITION_RATINGS.indexOf(reference)
      if (currentIndex === -1 || referenceIndex === -1) {
        if (current === reference) {
          return { text: 'Rating unchanged.', tone: 'neutral' as const }
        }
        return {
          text: `Rating changed from ${reference} to ${current}.`,
          tone: 'neutral' as const,
        }
      }
      if (currentIndex === referenceIndex) {
        return { text: 'Rating unchanged.', tone: 'neutral' as const }
      }
      if (currentIndex < referenceIndex) {
        return {
          text: `Rating improved from ${reference} to ${current}.`,
          tone: 'positive' as const,
        }
      }
      return {
        text: `Rating declined from ${reference} to ${current}.`,
        tone: 'negative' as const,
      }
    },
    [],
  )

  const describeRiskChange = useCallback(
    (current: string, reference: string) => {
      const currentIndex = CONDITION_RISK_LEVELS.indexOf(current)
      const referenceIndex = CONDITION_RISK_LEVELS.indexOf(reference)
      if (currentIndex === -1 || referenceIndex === -1) {
        if (current === reference) {
          return { text: 'Risk level unchanged.', tone: 'neutral' as const }
        }
        return {
          text: `Risk level changed from ${reference} to ${current}.`,
          tone: 'neutral' as const,
        }
      }
      if (currentIndex === referenceIndex) {
        return { text: 'Risk level unchanged.', tone: 'neutral' as const }
      }
      if (currentIndex < referenceIndex) {
        return {
          text: `Risk eased from ${reference} to ${current}.`,
          tone: 'positive' as const,
        }
      }
      return {
        text: `Risk intensified from ${reference} to ${current}.`,
        tone: 'negative' as const,
      }
    },
    [],
  )

  const latestAssessmentEntry = useMemo(
    () => (assessmentHistory.length > 0 ? assessmentHistory[0] : null),
    [assessmentHistory],
  )
  const previousAssessmentEntry = useMemo(
    () => (assessmentHistory.length > 1 ? assessmentHistory[1] : null),
    [assessmentHistory],
  )
  const systemComparisons = useMemo(() => {
    if (!latestAssessmentEntry && !previousAssessmentEntry) {
      return []
    }
    const names = new Set<string>()
    ;(latestAssessmentEntry?.systems ?? []).forEach((system) => {
      names.add(system.name)
    })
    ;(previousAssessmentEntry?.systems ?? []).forEach((system) => {
      names.add(system.name)
    })
    return Array.from(names).map((name) => {
      const latestSystem =
        latestAssessmentEntry?.systems.find((system) => system.name === name) ?? null
      const previousSystem =
        previousAssessmentEntry?.systems.find((system) => system.name === name) ?? null
      const scoreDelta =
        latestSystem && previousSystem
          ? latestSystem.score - previousSystem.score
          : undefined
      return {
        name,
        latest: latestSystem,
        previous: previousSystem,
        scoreDelta,
      }
    })
  }, [latestAssessmentEntry, previousAssessmentEntry])
  const recommendedActionDiff = useMemo(() => {
    if (!latestAssessmentEntry || !previousAssessmentEntry) {
      return { newActions: [], clearedActions: [] }
    }
    const latestSet = new Set(latestAssessmentEntry.recommendedActions)
    const previousSet = new Set(previousAssessmentEntry.recommendedActions)
    const newActions = Array.from(latestSet).filter((action) => !previousSet.has(action))
    const clearedActions = Array.from(previousSet).filter(
      (action) => !latestSet.has(action),
    )
    return { newActions, clearedActions }
  }, [latestAssessmentEntry, previousAssessmentEntry])
  const comparisonSummary = useMemo(() => {
    if (!latestAssessmentEntry || !previousAssessmentEntry) {
      return null
    }
    const scoreDelta = latestAssessmentEntry.overallScore - previousAssessmentEntry.overallScore
    const latestRatingIndex = CONDITION_RATINGS.indexOf(latestAssessmentEntry.overallRating)
    const previousRatingIndex = CONDITION_RATINGS.indexOf(previousAssessmentEntry.overallRating)
    let ratingTrend: 'improved' | 'declined' | 'same' | 'changed' = 'same'
    if (latestRatingIndex !== -1 && previousRatingIndex !== -1) {
      if (latestRatingIndex < previousRatingIndex) {
        ratingTrend = 'improved'
      } else if (latestRatingIndex > previousRatingIndex) {
        ratingTrend = 'declined'
      } else {
        ratingTrend = 'same'
      }
    } else if (latestAssessmentEntry.overallRating !== previousAssessmentEntry.overallRating) {
      ratingTrend = 'changed'
    }
    const latestRiskIndex = CONDITION_RISK_LEVELS.indexOf(latestAssessmentEntry.riskLevel)
    const previousRiskIndex = CONDITION_RISK_LEVELS.indexOf(previousAssessmentEntry.riskLevel)
    let riskTrend: 'improved' | 'declined' | 'same' | 'changed' = 'same'
    if (latestRiskIndex !== -1 && previousRiskIndex !== -1) {
      if (latestRiskIndex < previousRiskIndex) {
        riskTrend = 'improved'
      } else if (latestRiskIndex > previousRiskIndex) {
        riskTrend = 'declined'
      } else {
        riskTrend = 'same'
      }
    } else if (latestAssessmentEntry.riskLevel !== previousAssessmentEntry.riskLevel) {
      riskTrend = 'changed'
    }
    return {
      scoreDelta,
      ratingTrend,
      riskTrend,
      ratingChanged: latestAssessmentEntry.overallRating !== previousAssessmentEntry.overallRating,
      riskChanged: latestAssessmentEntry.riskLevel !== previousAssessmentEntry.riskLevel,
    }
  }, [latestAssessmentEntry, previousAssessmentEntry])
  const formatScenarioLabel = useCallback(
    (scenario: ConditionAssessment['scenario']) => {
      if (!scenario) {
        return 'All scenarios'
      }
      const entry = scenarioLookup.get(scenario)
      if (entry) {
        return entry.label
      }
      return formatCategoryName(scenario)
    },
    [scenarioLookup],
  )
  const formatRecordedTimestamp = useCallback((timestamp?: string | null) => {
    if (!timestamp) {
      return 'Draft assessment'
    }
    const parsed = new Date(timestamp)
    if (Number.isNaN(parsed.getTime())) {
      return timestamp
    }
    return parsed.toLocaleString()
  }, [])

  useEffect(() => {
    setSelectedCategory(null)
  }, [activeScenario])

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

  useEffect(() => {
    if (!capturedProperty) {
      setAssessmentDraft(buildAssessmentDraft(null, 'all'))
      setIsEditingAssessment(false)
      return
    }
    setAssessmentDraft(buildAssessmentDraft(conditionAssessment, activeScenario))
  }, [capturedProperty, conditionAssessment, activeScenario])

  function handleAssessmentFieldChange(
    field: keyof ConditionAssessmentDraft,
    value: string,
  ) {
    setAssessmentDraft((prev) => ({
      ...prev,
      [field]: value,
    }))
  }

  function handleAssessmentSystemChange(
    index: number,
    field: keyof AssessmentDraftSystem,
    value: string,
  ) {
    setAssessmentDraft((prev) => {
      const systems = [...prev.systems]
      systems[index] = {
        ...systems[index],
        [field]: value,
      }
      return { ...prev, systems }
    })
  }

  async function handleAssessmentSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()
    if (!capturedProperty) {
      return
    }

    setIsSavingAssessment(true)
    setAssessmentSaveMessage(null)

    try {
      const systemsPayload: ConditionAssessmentUpsertRequest['systems'] = assessmentDraft.systems.map(
        (system) => {
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
        },
      )

      const parsedOverallScore = Number(assessmentDraft.overallScore)
      const overallScoreValue = Number.isNaN(parsedOverallScore)
        ? 0
        : parsedOverallScore

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
        setIsEditingAssessment(false)
      } else {
        setAssessmentSaveMessage('Unable to save inspection data. Please try again.')
      }
    } catch (error) {
      console.error('Failed to save inspection assessment:', error)
      setAssessmentSaveMessage('Unable to save inspection data. Please try again.')
    } finally {
      setIsSavingAssessment(false)
    }
  }

  function resetAssessmentDraft() {
    setAssessmentDraft(buildAssessmentDraft(conditionAssessment, activeScenario))
    setAssessmentSaveMessage(null)
  }

  function toggleScenario(scenario: DevelopmentScenario) {
    setSelectedScenarios((prev) =>
      prev.includes(scenario)
        ? prev.filter((s) => s !== scenario)
        : [...prev, scenario]
    )
  }

  async function handleCapture(e: React.FormEvent) {
    e.preventDefault()
    const lat = parseFloat(latitude)
    const lon = parseFloat(longitude)

    if (isNaN(lat) || isNaN(lon)) {
      setError('Please enter valid coordinates')
      return
    }

    if (selectedScenarios.length === 0) {
      setError('Please select at least one development scenario')
      return
    }

    setIsCapturing(true)
    setError(null)

    try {
      const result = await capturePropertyForDevelopment({
        latitude: lat,
        longitude: lon,
        developmentScenarios: selectedScenarios,
      })

      setCapturedProperty(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to capture property')
    } finally {
      setIsCapturing(false)
    }
  }

  async function handleChecklistUpdate(
    itemId: string,
    newStatus: 'pending' | 'in_progress' | 'completed' | 'not_applicable',
  ) {
    const updated = await updateChecklistItem(itemId, { status: newStatus })
    if (updated) {
      // Update local state
      setChecklistItems((prev) =>
        prev.map((item) => (item.id === itemId ? updated : item)),
      )

      // Reload summary
      if (capturedProperty) {
        const summary = await fetchChecklistSummary(capturedProperty.propertyId)
        setChecklistSummary(summary)
      }
    }
  }

  return (
    <div
      style={{
        padding: '3rem 2rem',
        maxWidth: '1200px',
        margin: '0 auto',
        fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", system-ui, sans-serif',
        color: '#1d1d1f',
      }}
    >
      {/* Header */}
      <header style={{ marginBottom: '3rem' }}>
        <h1
          style={{
            fontSize: '3rem',
            fontWeight: 700,
            letterSpacing: '-0.015em',
            margin: '0 0 0.5rem',
            lineHeight: 1.1,
          }}
        >
          Site Acquisition
        </h1>
        <p
          style={{
            fontSize: '1.25rem',
            color: '#6e6e73',
            margin: 0,
            lineHeight: 1.5,
            letterSpacing: '-0.005em',
          }}
        >
          Comprehensive property capture and development feasibility analysis for developers
        </p>
      </header>

      {/* Property Capture Form */}
      <section
        style={{
          background: 'white',
          border: '1px solid #d2d2d7',
          borderRadius: '18px',
          padding: '2rem',
          marginBottom: '2rem',
        }}
      >
        <h2
          style={{
            fontSize: '1.5rem',
            fontWeight: 600,
            marginBottom: '1.5rem',
            letterSpacing: '-0.01em',
          }}
        >
          Property Coordinates
        </h2>

        <form onSubmit={handleCapture}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: '1rem',
              marginBottom: '2rem',
            }}
          >
            <div>
              <label
                htmlFor="latitude"
                style={{
                  display: 'block',
                  fontSize: '0.9375rem',
                  fontWeight: 500,
                  marginBottom: '0.5rem',
                  color: '#1d1d1f',
                }}
              >
                Latitude
              </label>
              <input
                id="latitude"
                type="text"
                value={latitude}
                onChange={(e) => setLatitude(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.875rem 1rem',
                  fontSize: '1rem',
                  border: '1px solid #d2d2d7',
                  borderRadius: '12px',
                  outline: 'none',
                  fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, monospace',
                  transition: 'all 0.2s ease',
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = '#1d1d1f'
                  e.currentTarget.style.boxShadow = '0 0 0 4px rgba(0, 0, 0, 0.04)'
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = '#d2d2d7'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              />
            </div>

            <div>
              <label
                htmlFor="longitude"
                style={{
                  display: 'block',
                  fontSize: '0.9375rem',
                  fontWeight: 500,
                  marginBottom: '0.5rem',
                  color: '#1d1d1f',
                }}
              >
                Longitude
              </label>
              <input
                id="longitude"
                type="text"
                value={longitude}
                onChange={(e) => setLongitude(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.875rem 1rem',
                  fontSize: '1rem',
                  border: '1px solid #d2d2d7',
                  borderRadius: '12px',
                  outline: 'none',
                  fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, monospace',
                  transition: 'all 0.2s ease',
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = '#1d1d1f'
                  e.currentTarget.style.boxShadow = '0 0 0 4px rgba(0, 0, 0, 0.04)'
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = '#d2d2d7'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              />
            </div>
          </div>

          <h3
            style={{
              fontSize: '1.125rem',
              fontWeight: 600,
              marginBottom: '1rem',
              letterSpacing: '-0.01em',
            }}
          >
            Development Scenarios
          </h3>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '1rem',
              marginBottom: '2rem',
            }}
          >
            {SCENARIO_OPTIONS.map((scenario) => {
              const isSelected = selectedScenarios.includes(scenario.value)
              return (
                <button
                  key={scenario.value}
                  type="button"
                  onClick={() => toggleScenario(scenario.value)}
                  style={{
                    background: isSelected ? '#f5f5f7' : 'white',
                    border: `1px solid ${isSelected ? '#1d1d1f' : '#d2d2d7'}`,
                    borderRadius: '12px',
                    padding: '1.25rem',
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.2s ease',
                    position: 'relative',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-2px)'
                    e.currentTarget.style.boxShadow = '0 8px 16px rgba(0, 0, 0, 0.08)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)'
                    e.currentTarget.style.boxShadow = 'none'
                  }}
                >
                  {isSelected && (
                    <div
                      style={{
                        position: 'absolute',
                        top: '1rem',
                        right: '1rem',
                        width: '20px',
                        height: '20px',
                        borderRadius: '50%',
                        background: '#1d1d1f',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '12px',
                        color: 'white',
                      }}
                    >
                      ✓
                    </div>
                  )}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.75rem',
                      marginBottom: '0.5rem',
                    }}
                  >
                    <span style={{ fontSize: '1.5rem' }}>{scenario.icon}</span>
                    <div
                      style={{
                        fontSize: '1.0625rem',
                        fontWeight: 600,
                        color: '#1d1d1f',
                        letterSpacing: '-0.005em',
                      }}
                    >
                      {scenario.label}
                    </div>
                  </div>
                  <div
                    style={{
                      fontSize: '0.875rem',
                      color: '#6e6e73',
                      lineHeight: 1.4,
                      letterSpacing: '-0.005em',
                    }}
                  >
                    {scenario.description}
                  </div>
                </button>
              )
            })}
          </div>

          <button
            type="submit"
            disabled={isCapturing || selectedScenarios.length === 0}
            style={{
              width: '100%',
              padding: '0.875rem 2rem',
              fontSize: '1.0625rem',
              fontWeight: 500,
              color: 'white',
              background:
                isCapturing || selectedScenarios.length === 0 ? '#d2d2d7' : '#1d1d1f',
              border: 'none',
              borderRadius: '12px',
              cursor:
                isCapturing || selectedScenarios.length === 0 ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s ease',
              letterSpacing: '-0.005em',
            }}
            onMouseEnter={(e) => {
              if (!isCapturing && selectedScenarios.length > 0) {
                e.currentTarget.style.background = '#424245'
              }
            }}
            onMouseLeave={(e) => {
              if (!isCapturing && selectedScenarios.length > 0) {
                e.currentTarget.style.background = '#1d1d1f'
              }
            }}
          >
            {isCapturing ? 'Capturing Property...' : 'Capture Property'}
          </button>

          {error && (
            <div
              style={{
                marginTop: '1rem',
                padding: '1rem',
                background: '#fff5f5',
                border: '1px solid #fed7d7',
                borderRadius: '12px',
                color: '#c53030',
                fontSize: '0.9375rem',
              }}
            >
              {error}
            </div>
          )}

          {capturedProperty && (
            <div
              style={{
                marginTop: '1rem',
                padding: '1rem',
                background: '#f0fdf4',
                border: '1px solid #bbf7d0',
                borderRadius: '12px',
                color: '#15803d',
                fontSize: '0.9375rem',
              }}
            >
              <strong>Property captured successfully</strong>
              <div style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>
                {capturedProperty.address.fullAddress} • {capturedProperty.address.district}
              </div>
            </div>
          )}
        </form>
      </section>

      {/* Due Diligence Checklist */}
      <section
        style={{
          background: 'white',
          border: '1px solid #d2d2d7',
          borderRadius: '18px',
          padding: '2rem',
          marginBottom: '2rem',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            marginBottom: '1.5rem',
          }}
        >
          <div>
            <h2
              style={{
                fontSize: '1.5rem',
                fontWeight: 600,
                marginBottom: '0.5rem',
                letterSpacing: '-0.01em',
              }}
            >
              Due Diligence Checklist
            </h2>
            {displaySummary && (
              <p
                style={{
                  margin: 0,
                  fontSize: '0.9375rem',
                  color: '#6e6e73',
                }}
              >
                {activeScenario === 'all'
                  ? 'Overall progress'
                  : `${activeScenarioDetails?.label ?? 'Scenario'}`}
                : {displaySummary.completed} of {displaySummary.total} items completed (
                {displaySummary.completionPercentage.toFixed(0)}%)
              </p>
            )}
            {activeScenarioDetails?.description && (
              <p
                style={{
                  margin: '0.25rem 0 0',
                  fontSize: '0.875rem',
                  color: '#86868b',
                }}
              >
                {activeScenarioDetails.description}
              </p>
            )}
          </div>
        </div>

        {availableChecklistScenarios.length > 0 && (
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '0.75rem',
              marginBottom: '1.5rem',
            }}
          >
            <button
              type="button"
              onClick={() => setActiveScenario('all')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem 0.85rem',
                borderRadius: '9999px',
                border: `1px solid ${
                  activeScenario === 'all' ? '#1d1d1f' : '#d2d2d7'
                }`,
                background: activeScenario === 'all' ? '#1d1d1f' : '#f5f5f7',
                color: activeScenario === 'all' ? 'white' : '#1d1d1f',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: 500,
                transition: 'all 0.2s ease',
              }}
            >
              All scenarios
            </button>
            {availableChecklistScenarios.map((scenario) => {
              const option = scenarioLookup.get(scenario)
              const isActive = activeScenario === scenario
              return (
                <button
                  key={scenario}
                  type="button"
                  onClick={() => setActiveScenario(scenario)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.5rem 0.85rem',
                    borderRadius: '9999px',
                    border: `1px solid ${isActive ? '#1d1d1f' : '#d2d2d7'}`,
                    background: isActive ? '#1d1d1f' : '#f5f5f7',
                    color: isActive ? 'white' : '#1d1d1f',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                    fontWeight: 500,
                    transition: 'all 0.2s ease',
                  }}
                >
                  {option?.icon ? (
                    <span style={{ fontSize: '1rem' }}>{option.icon}</span>
                  ) : null}
                  <span>{option?.label ?? formatCategoryName(scenario)}</span>
                </button>
              )
            })}
          </div>
        )}

        {isLoadingChecklist ? (
          <div
            style={{
              padding: '3rem 2rem',
              textAlign: 'center',
              color: '#6e6e73',
            }}
          >
            <p>Loading checklist...</p>
          </div>
        ) : !capturedProperty ? (
          <div
            style={{
              padding: '3rem 2rem',
              textAlign: 'center',
              color: '#6e6e73',
              background: '#f5f5f7',
              borderRadius: '12px',
            }}
          >
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📋</div>
            <p style={{ margin: 0, fontSize: '1.0625rem' }}>
              Capture a property to view the comprehensive due diligence checklist
            </p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '0.9375rem' }}>
              Automatically generated based on selected development scenarios
            </p>
          </div>
        ) : checklistItems.length === 0 ? (
          <div
            style={{
              padding: '2rem',
              textAlign: 'center',
              color: '#6e6e73',
              background: '#f5f5f7',
              borderRadius: '12px',
            }}
          >
            <p>No checklist items found for this property.</p>
          </div>
        ) : filteredChecklistItems.length === 0 ? (
          <div
            style={{
              padding: '2rem',
              textAlign: 'center',
              color: '#6e6e73',
              background: '#f5f5f7',
              borderRadius: '12px',
            }}
          >
            <p>
              No checklist items for{' '}
              {activeScenarioDetails?.label ?? 'this scenario'} yet.
            </p>
          </div>
        ) : (
          <>
            {/* Progress bar */}
            {displaySummary && (
              <div
                style={{
                  marginBottom: '1.5rem',
                  background: '#f5f5f7',
                  borderRadius: '12px',
                  height: '8px',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${displaySummary.completionPercentage}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, #0071e3 0%, #005bb5 100%)',
                    transition: 'width 0.3s ease',
                  }}
                />
              </div>
            )}

            {/* Group by category */}
            {Object.entries(
              filteredChecklistItems.reduce((acc, item) => {
                const category = item.category
                if (!acc[category]) {
                  acc[category] = []
                }
                acc[category].push(item)
                return acc
              }, {} as Record<string, ChecklistItem[]>),
            ).map(([category, items]) => (
              <div
                key={category}
                style={{
                  marginBottom: '1.5rem',
                  border: '1px solid #e5e5e7',
                  borderRadius: '12px',
                  overflow: 'hidden',
                }}
              >
                <button
                  type="button"
                  onClick={() =>
                    setSelectedCategory(selectedCategory === category ? null : category)
                  }
                  style={{
                    width: '100%',
                    padding: '1rem 1.25rem',
                    background: '#f5f5f7',
                    border: 'none',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    cursor: 'pointer',
                    fontSize: '1rem',
                    fontWeight: 600,
                    textAlign: 'left',
                  }}
                >
                  <span>{formatCategoryName(category)}</span>
                  <span
                    style={{
                      fontSize: '0.875rem',
                      color: '#6e6e73',
                    }}
                  >
                    {items.filter((item) => item.status === 'completed').length}/{items.length}
                  </span>
                </button>
                {(selectedCategory === category || selectedCategory === null) && (
                  <div style={{ padding: '0' }}>
                    {items.map((item) => (
                      <div
                        key={item.id}
                        style={{
                          padding: '1rem 1.25rem',
                          borderTop: '1px solid #e5e5e7',
                          display: 'flex',
                          gap: '1rem',
                          alignItems: 'flex-start',
                        }}
                      >
                        <select
                          value={item.status}
                          onChange={(e) =>
                            handleChecklistUpdate(
                              item.id,
                              e.target.value as
                                | 'pending'
                                | 'in_progress'
                                | 'completed'
                                | 'not_applicable',
                            )
                          }
                          style={{
                            padding: '0.5rem',
                            border: '1px solid #d2d2d7',
                            borderRadius: '8px',
                            fontSize: '0.875rem',
                            background: 'white',
                            cursor: 'pointer',
                          }}
                        >
                          <option value="pending">Pending</option>
                          <option value="in_progress">In Progress</option>
                          <option value="completed">Completed</option>
                          <option value="not_applicable">Not Applicable</option>
                        </select>
                        <div style={{ flex: 1 }}>
                          <div
                            style={{
                              display: 'flex',
                              gap: '0.75rem',
                              alignItems: 'center',
                              marginBottom: '0.25rem',
                            }}
                          >
                            <h4
                              style={{
                                margin: 0,
                                fontSize: '0.9375rem',
                                fontWeight: 600,
                              }}
                            >
                              {item.itemTitle}
                            </h4>
                            {item.priority === 'critical' && (
                              <span
                                style={{
                                  padding: '0.125rem 0.5rem',
                                  background: '#fee2e2',
                                  color: '#991b1b',
                                  fontSize: '0.75rem',
                                  fontWeight: 600,
                                  borderRadius: '6px',
                                }}
                              >
                                CRITICAL
                              </span>
                            )}
                            {item.priority === 'high' && (
                              <span
                                style={{
                                  padding: '0.125rem 0.5rem',
                                  background: '#fef3c7',
                                  color: '#92400e',
                                  fontSize: '0.75rem',
                                  fontWeight: 600,
                                  borderRadius: '6px',
                                }}
                              >
                                HIGH
                              </span>
                            )}
                          </div>
                          {item.itemDescription && (
                            <p
                              style={{
                                margin: '0.5rem 0 0',
                                fontSize: '0.875rem',
                                color: '#6e6e73',
                                lineHeight: 1.5,
                              }}
                            >
                              {item.itemDescription}
                            </p>
                          )}
                          {item.requiresProfessional && item.professionalType && (
                            <p
                              style={{
                                margin: '0.5rem 0 0',
                                fontSize: '0.8125rem',
                                color: '#0071e3',
                              }}
                            >
                              Requires: {item.professionalType}
                            </p>
                          )}
                          {item.dueDate && (
                            <p
                              style={{
                                margin: '0.25rem 0 0',
                                fontSize: '0.8125rem',
                                color: '#6e6e73',
                              }}
                            >
                              Due: {new Date(item.dueDate).toLocaleDateString()}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </>
        )}
      </section>

      <section
        style={{
          background: 'white',
          border: '1px solid #d2d2d7',
          borderRadius: '18px',
          padding: '2rem',
          marginBottom: '2rem',
        }}
      >
        <h2
          style={{
            fontSize: '1.5rem',
            fontWeight: 600,
            marginBottom: '1rem',
            letterSpacing: '-0.01em',
          }}
        >
          Multi-Scenario Comparison
        </h2>
        {!capturedProperty ? (
          <div
            style={{
              padding: '3rem 2rem',
              textAlign: 'center',
              color: '#6e6e73',
              background: '#f5f5f7',
              borderRadius: '12px',
            }}
          >
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📊</div>
            <p style={{ margin: 0, fontSize: '1.0625rem' }}>
              Capture a property to review scenario economics and development posture
            </p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '0.9375rem' }}>
              Financial and planning metrics for each developer scenario appear here.
            </p>
          </div>
        ) : quickAnalysisScenarios.length === 0 ? (
          <div
            style={{
              padding: '2.5rem',
              textAlign: 'center',
              color: '#6e6e73',
              background: '#f5f5f7',
              borderRadius: '12px',
            }}
          >
            <p style={{ margin: 0 }}>
              Quick analysis metrics unavailable for this capture. Try regenerating the
              scenarios.
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div
              style={{
                display: 'flex',
                gap: '0.75rem',
                flexWrap: 'wrap',
              }}
            >
              {quickAnalysisScenarios.map((scenario) => {
                const label =
                  scenarioLookup.get(scenario.scenario)?.label ??
                  formatCategoryName(scenario.scenario)
                const isActive =
                  activeScenario === 'all' || scenario.scenario === activeScenario
                const scenarioKey = scenario.scenario
                return (
                  <div
                    key={scenario.scenario}
                    style={{
                      border: `2px solid ${isActive ? '#1d1d1f' : '#e5e5e7'}`,
                      borderRadius: '12px',
                      padding: '1.25rem',
                      flex: '1 1 280px',
                      background: isActive ? '#ffffff' : '#f5f5f7',
                      transition: 'border 0.2s ease',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'baseline',
                        marginBottom: '0.75rem',
                      }}
                    >
                      <h3
                        style={{
                          margin: 0,
                          fontSize: '1.0625rem',
                          fontWeight: 600,
                        }}
                      >
                        {label}
                      </h3>
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.6rem',
                        }}
                      >
                        <span
                          style={{
                            fontSize: '0.8125rem',
                            fontWeight: 600,
                            color: '#6e6e73',
                            letterSpacing: '0.08em',
                            textTransform: 'uppercase',
                          }}
                        >
                          {scenario.headline}
                        </span>
                        {activeScenario !== scenarioKey && (
                          <button
                            type="button"
                            onClick={() =>
                              setActiveScenario(
                                scenarioKey as DevelopmentScenario | 'all',
                              )
                            }
                            style={{
                              border: '1px solid #1d1d1f',
                              background: 'white',
                              color: '#1d1d1f',
                              borderRadius: '9999px',
                              padding: '0.25rem 0.75rem',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              cursor: 'pointer',
                            }}
                          >
                            Focus
                          </button>
                        )}
                      </div>
                    </div>
                    <dl
                      style={{
                        margin: 0,
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                        gap: '0.75rem',
                        fontSize: '0.875rem',
                        color: '#3a3a3c',
                      }}
                    >
                      {Object.entries(scenario.metrics).map(([key, value]) => (
                        <div key={key} style={{ display: 'flex', flexDirection: 'column' }}>
                          <dt
                            style={{
                              fontWeight: 600,
                              color: '#6e6e73',
                              marginBottom: '0.15rem',
                              textTransform: 'capitalize',
                            }}
                          >
                            {key.replace(/_/g, ' ')}
                          </dt>
                          <dd style={{ margin: 0 }}>{value ?? '—'}</dd>
                        </div>
                      ))}
                    </dl>
                    {scenario.notes.length > 0 && (
                      <ul
                        style={{
                          margin: '1rem 0 0',
                          paddingLeft: '1.1rem',
                          color: '#3a3a3c',
                          fontSize: '0.85rem',
                          lineHeight: 1.4,
                        }}
                      >
                        {scenario.notes.map((note) => (
                          <li key={note}>{note}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )
              })}
            </div>

            {activeScenario !== 'all' && comparisonScenarios.length > 0 && (
              <div
                style={{
                  padding: '1.25rem',
                  background: '#f0f9ff',
                  borderRadius: '12px',
                  border: '1px solid #bae6fd',
                }}
              >
                <strong>Scenario focus:</strong> Viewing{' '}
                {scenarioLookup.get(activeScenario)?.label ??
                  formatCategoryName(activeScenario)}{' '}
                metrics. Switch back to “All scenarios” to compare options side-by-side.
              </div>
            )}
          </div>
        )}
      </section>

      <section
        style={{
          background: 'white',
          border: '1px solid #d2d2d7',
          borderRadius: '18px',
          padding: '2rem',
        }}
      >
        <h2
          style={{
            fontSize: '1.5rem',
            fontWeight: 600,
            marginBottom: '1rem',
            letterSpacing: '-0.01em',
          }}
        >
          Property Condition Assessment
        </h2>
        {isLoadingCondition ? (
          <div
            style={{
              padding: '2.5rem',
              textAlign: 'center',
              color: '#6e6e73',
              background: '#f5f5f7',
              borderRadius: '12px',
            }}
          >
            <p style={{ margin: 0 }}>Analysing building condition...</p>
          </div>
        ) : !capturedProperty ? (
          <div
            style={{
              padding: '3rem 2rem',
              textAlign: 'center',
              color: '#6e6e73',
              background: '#f5f5f7',
              borderRadius: '12px',
            }}
          >
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🏢</div>
            <p style={{ margin: 0, fontSize: '1.0625rem' }}>
              Capture a property to generate the developer condition assessment
            </p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '0.9375rem' }}>
              Structural, M&amp;E, and compliance insights will appear here with targeted actions.
            </p>
          </div>
        ) : !conditionAssessment ? (
          <div
            style={{
              padding: '2.5rem 2rem',
              textAlign: 'center',
              color: '#6e6e73',
              background: '#fff7ed',
              borderRadius: '12px',
              border: '1px solid #fed7aa',
            }}
          >
            <p style={{ margin: 0 }}>
              Unable to load condition assessment. Please retry after refreshing the capture.
            </p>
          </div>
        ) : (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '1.75rem',
            }}
          >
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '1.5rem',
                alignItems: 'flex-start',
              }}
            >
              <div
                style={{
                  flex: '1 1 260px',
                  background: '#f5f5f7',
                  borderRadius: '12px',
                  padding: '1.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem',
                }}
              >
                <span
                  style={{
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    color: '#6e6e73',
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                  }}
                >
                  Overall Rating
                </span>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'baseline',
                    gap: '0.75rem',
                  }}
                >
                  <span style={{ fontSize: '2.5rem', fontWeight: 700 }}>
                    {conditionAssessment.overallRating}
                  </span>
                  <span style={{ fontSize: '1rem', color: '#6e6e73' }}>
                    {conditionAssessment.overallScore}/100 · {conditionAssessment.riskLevel} risk
                  </span>
                </div>
                <p
                  style={{
                    margin: 0,
                    fontSize: '0.9375rem',
                    color: '#3a3a3c',
                    lineHeight: 1.5,
                  }}
                >
                  {conditionAssessment.summary}
                </p>
                {conditionAssessment.scenarioContext && (
                  <p
                    style={{
                      margin: 0,
                      fontSize: '0.875rem',
                      color: '#0071e3',
                    }}
                  >
                    {conditionAssessment.scenarioContext}
                  </p>
                )}
                {conditionAssessment.recordedAt && (
                  <p
                    style={{
                      margin: 0,
                      fontSize: '0.8125rem',
                      color: '#6e6e73',
                    }}
                  >
                    Inspection recorded{' '}
                    {new Date(conditionAssessment.recordedAt).toLocaleString()}
                  </p>
                )}
              </div>
              <div
                style={{
                  flex: '1 1 280px',
                  background: '#f5f5f7',
                  borderRadius: '12px',
                  padding: '1.5rem',
                }}
              >
                <h3
                  style={{
                    margin: '0 0 0.75rem',
                    fontSize: '1.0625rem',
                    fontWeight: 600,
                  }}
                >
                  Immediate Actions
                </h3>
                <ul
                  style={{
                    margin: 0,
                    paddingLeft: '1.2rem',
                    color: '#3a3a3c',
                    fontSize: '0.9375rem',
                    lineHeight: 1.5,
                  }}
                >
                  {conditionAssessment.recommendedActions.map((action) => (
                    <li key={action}>{action}</li>
                  ))}
                </ul>
              </div>
            </div>

            <div
              style={{
                display: 'grid',
                gap: '1rem',
                gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
              }}
            >
              {conditionAssessment.systems.map((system) => (
                <div
                  key={system.name}
                  style={{
                    border: '1px solid #e5e5e7',
                    borderRadius: '12px',
                    padding: '1.25rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.75rem',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'baseline',
                    }}
                  >
                    <h3
                      style={{
                        margin: 0,
                        fontSize: '1.0625rem',
                        fontWeight: 600,
                      }}
                    >
                      {system.name}
                    </h3>
                    <span
                      style={{
                        fontSize: '0.875rem',
                        fontWeight: 600,
                        color: '#6e6e73',
                      }}
                    >
                      Rating {system.rating} · {system.score}/100
                    </span>
                  </div>
                  <p
                    style={{
                      margin: 0,
                      fontSize: '0.9rem',
                      color: '#3a3a3c',
                      lineHeight: 1.5,
                    }}
                  >
                    {system.notes}
                  </p>
                  <ul
                    style={{
                      margin: 0,
                      paddingLeft: '1.1rem',
                      fontSize: '0.875rem',
                      color: '#3a3a3c',
                      lineHeight: 1.4,
                    }}
                  >
                    {system.recommendedActions.map((action) => (
                      <li key={action}>{action}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>

            <div
              style={{
                border: '1px solid #e5e5e7',
                borderRadius: '12px',
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '0.75rem',
                }}
              >
                <h3
                  style={{
                    margin: 0,
                    fontSize: '1.0625rem',
                    fontWeight: 600,
                  }}
                >
                  Inspection History
                </h3>
                <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    onClick={() => setHistoryViewMode('timeline')}
                    style={{
                      border: '1px solid #1d1d1f',
                      background: historyViewMode === 'timeline' ? '#1d1d1f' : 'white',
                      color: historyViewMode === 'timeline' ? 'white' : '#1d1d1f',
                      borderRadius: '9999px',
                      padding: '0.4rem 0.9rem',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    Timeline
                  </button>
                  <button
                    type="button"
                    onClick={() => setHistoryViewMode('compare')}
                    style={{
                      border: '1px solid #1d1d1f',
                      background: historyViewMode === 'compare' ? '#1d1d1f' : 'white',
                      color: historyViewMode === 'compare' ? 'white' : '#1d1d1f',
                      borderRadius: '9999px',
                      padding: '0.4rem 0.9rem',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    Compare
                  </button>
                </div>
              </div>
              {assessmentHistoryError ? (
                <p
                  style={{
                    margin: 0,
                    fontSize: '0.85rem',
                    color: '#c53030',
                  }}
                >
                  {assessmentHistoryError}
                </p>
              ) : isLoadingAssessmentHistory ? (
                <div
                  style={{
                    padding: '1.5rem',
                    textAlign: 'center',
                    color: '#6e6e73',
                    background: '#f5f5f7',
                    borderRadius: '10px',
                  }}
                >
                  <p style={{ margin: 0, fontSize: '0.9rem' }}>
                    Loading inspection history...
                  </p>
                </div>
              ) : assessmentHistory.length === 0 ? (
                <div
                  style={{
                    padding: '1.5rem',
                    textAlign: 'center',
                    color: '#6e6e73',
                    background: '#f5f5f7',
                    borderRadius: '10px',
                  }}
                >
                  <p style={{ margin: 0, fontSize: '0.9rem' }}>
                    No developer inspections recorded yet.
                  </p>
                  <p style={{ margin: '0.35rem 0 0', fontSize: '0.8rem' }}>
                    Save an inspection above to start the audit trail.
                  </p>
                </div>
              ) : historyViewMode === 'timeline' ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
                  {assessmentHistory.map((entry, index) => {
                    const key = `${entry.recordedAt ?? 'draft'}-${index}`
                    const matchesScenario =
                      activeScenario === 'all' ||
                      !entry.scenario ||
                      entry.scenario === activeScenario
                    const recommendedPreview = entry.recommendedActions.slice(0, 2)
                    const remainingActions =
                      entry.recommendedActions.length - recommendedPreview.length
                    return (
                      <div
                        key={key}
                        style={{
                          border: '1px solid #e5e5e7',
                          borderLeft: `4px solid ${
                            index === 0 ? '#0a84ff' : matchesScenario ? '#34c759' : '#d2d2d7'
                          }`,
                          borderRadius: '10px',
                          padding: '1rem 1.25rem',
                          background: index === 0 ? '#f0f9ff' : '#ffffff',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '0.5rem',
                        }}
                      >
                        <div
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'flex-start',
                            flexWrap: 'wrap',
                            gap: '0.5rem',
                          }}
                        >
                          <div
                            style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}
                          >
                            <span
                              style={{
                                fontSize: '0.75rem',
                                fontWeight: 600,
                                letterSpacing: '0.08em',
                                textTransform: 'uppercase',
                                color: '#6e6e73',
                              }}
                            >
                              {index === 0 ? 'Most recent inspection' : `Inspection ${index + 1}`}
                            </span>
                            <span style={{ fontSize: '0.9375rem', fontWeight: 600 }}>
                              {formatScenarioLabel(entry.scenario)}
                            </span>
                          </div>
                          <span style={{ fontSize: '0.85rem', color: '#6e6e73' }}>
                            {formatRecordedTimestamp(entry.recordedAt)}
                          </span>
                        </div>
                        <div
                          style={{
                            display: 'flex',
                            flexWrap: 'wrap',
                            gap: '0.75rem',
                            alignItems: 'center',
                          }}
                        >
                          <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>
                            Rating {entry.overallRating}
                          </span>
                          <span style={{ fontSize: '0.875rem', color: '#3a3a3c' }}>
                            {entry.overallScore}/100
                          </span>
                          <span
                            style={{
                              fontSize: '0.8rem',
                              color: '#6e6e73',
                              textTransform: 'capitalize',
                            }}
                          >
                            {entry.riskLevel} risk
                          </span>
                        </div>
                        {entry.summary && (
                          <p
                            style={{
                              margin: 0,
                              fontSize: '0.9rem',
                              color: '#3a3a3c',
                              lineHeight: 1.5,
                            }}
                          >
                            {entry.summary}
                          </p>
                        )}
                        {entry.scenarioContext && (
                          <p
                            style={{
                              margin: 0,
                              fontSize: '0.8125rem',
                              color: '#0071e3',
                            }}
                          >
                            {entry.scenarioContext}
                          </p>
                        )}
                        {recommendedPreview.length > 0 && (
                          <ul
                            style={{
                              margin: '0.25rem 0 0',
                              paddingLeft: '1.1rem',
                              fontSize: '0.85rem',
                              color: '#3a3a3c',
                              lineHeight: 1.4,
                            }}
                          >
                            {recommendedPreview.map((action) => (
                              <li key={action}>{action}</li>
                            ))}
                            {remainingActions > 0 && (
                              <li
                                key="more"
                                style={{
                                  listStyle: 'none',
                                  marginLeft: '-1.1rem',
                                  color: '#6e6e73',
                                }}
                              >
                                +{remainingActions} more action
                                {remainingActions > 1 ? 's' : ''}
                              </li>
                            )}
                          </ul>
                        )}
                      </div>
                    )
                  })}
                </div>
              ) : previousAssessmentEntry ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  {comparisonSummary &&
                    latestAssessmentEntry &&
                    previousAssessmentEntry && (
                      <div
                        style={{
                          border: '1px solid #e5e5e7',
                          borderRadius: '10px',
                          padding: '1.1rem 1.25rem',
                          background: '#f5f5f7',
                          display: 'grid',
                          gap: '0.5rem',
                        }}
                      >
                        <div
                          style={{
                            display: 'flex',
                            flexWrap: 'wrap',
                            gap: '0.75rem',
                            alignItems: 'baseline',
                          }}
                        >
                          <span
                            style={{
                              fontSize: '0.8125rem',
                              fontWeight: 600,
                              textTransform: 'uppercase',
                              letterSpacing: '0.08em',
                              color: '#6e6e73',
                            }}
                          >
                            Overall score
                          </span>
                          <span style={{ fontSize: '1.125rem', fontWeight: 600 }}>
                            {latestAssessmentEntry.overallScore}
                          </span>
                          <span
                            style={{
                              fontSize: '0.875rem',
                              fontWeight: 600,
                              color:
                                comparisonSummary.scoreDelta > 0
                                  ? '#15803d'
                                  : comparisonSummary.scoreDelta < 0
                                  ? '#c53030'
                                  : '#6e6e73',
                            }}
                          >
                            {comparisonSummary.scoreDelta > 0 ? '+' : ''}
                            {comparisonSummary.scoreDelta}
                          </span>
                        </div>
                        <p
                          style={{
                            margin: 0,
                            fontSize: '0.875rem',
                            color: '#3a3a3c',
                          }}
                        >
                          {comparisonSummary.scoreDelta === 0
                            ? 'Overall score held steady vs previous inspection.'
                            : comparisonSummary.scoreDelta > 0
                            ? `Improved by ${comparisonSummary.scoreDelta} points from ${previousAssessmentEntry.overallScore}.`
                            : `Declined by ${Math.abs(
                                comparisonSummary.scoreDelta,
                              )} points from ${previousAssessmentEntry.overallScore}.`}
                        </p>
                        <p
                          style={{
                            margin: 0,
                            fontSize: '0.875rem',
                            color: '#3a3a3c',
                          }}
                        >
                          {comparisonSummary.ratingChanged
                            ? `Rating ${
                                comparisonSummary.ratingTrend === 'improved'
                                  ? 'improved'
                                  : comparisonSummary.ratingTrend === 'declined'
                                  ? 'declined'
                                  : 'changed'
                              } from ${previousAssessmentEntry.overallRating} to ${latestAssessmentEntry.overallRating}.`
                            : 'Rating unchanged from previous inspection.'}
                        </p>
                        <p
                          style={{
                            margin: 0,
                            fontSize: '0.875rem',
                            color: '#3a3a3c',
                          }}
                        >
                          {comparisonSummary.riskChanged
                            ? `Risk level ${
                                comparisonSummary.riskTrend === 'improved'
                                  ? 'eased'
                                  : comparisonSummary.riskTrend === 'declined'
                                  ? 'intensified'
                                  : 'changed'
                              } from ${previousAssessmentEntry.riskLevel} to ${latestAssessmentEntry.riskLevel}.`
                            : 'Risk level unchanged.'}
                        </p>
                      </div>
                    )}
                  <div
                    style={{
                      display: 'grid',
                      gap: '1rem',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                    }}
                  >
                    <div
                      style={{
                        border: '1px solid #e5e5e7',
                        borderRadius: '10px',
                        padding: '1.25rem',
                        display: 'grid',
                        gap: '0.6rem',
                        background: '#f0f9ff',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'flex-start',
                          gap: '0.5rem',
                          flexWrap: 'wrap',
                        }}
                      >
                        <span
                          style={{
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            textTransform: 'uppercase',
                            letterSpacing: '0.08em',
                            color: '#0a84ff',
                          }}
                        >
                          Current inspection
                        </span>
                        <span style={{ fontSize: '0.8125rem', color: '#6e6e73' }}>
                          {formatRecordedTimestamp(latestAssessmentEntry?.recordedAt)}
                        </span>
                      </div>
                      <strong style={{ fontSize: '1rem', fontWeight: 600 }}>
                        {formatScenarioLabel(latestAssessmentEntry?.scenario ?? null)}
                      </strong>
                      <span style={{ fontSize: '0.9rem', color: '#3a3a3c' }}>
                        Rating {latestAssessmentEntry?.overallRating} ·{' '}
                        {latestAssessmentEntry?.overallScore}/100 ·{' '}
                        {latestAssessmentEntry?.riskLevel} risk
                      </span>
                      {latestAssessmentEntry?.summary && (
                        <p
                          style={{
                            margin: 0,
                            fontSize: '0.875rem',
                            color: '#3a3a3c',
                            lineHeight: 1.5,
                          }}
                        >
                          {latestAssessmentEntry.summary}
                        </p>
                      )}
                    </div>
                    <div
                      style={{
                        border: '1px solid #e5e5e7',
                        borderRadius: '10px',
                        padding: '1.25rem',
                        display: 'grid',
                        gap: '0.6rem',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'flex-start',
                          gap: '0.5rem',
                          flexWrap: 'wrap',
                        }}
                      >
                        <span
                          style={{
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            textTransform: 'uppercase',
                            letterSpacing: '0.08em',
                            color: '#6e6e73',
                          }}
                        >
                          Previous inspection
                        </span>
                        <span style={{ fontSize: '0.8125rem', color: '#6e6e73' }}>
                          {formatRecordedTimestamp(previousAssessmentEntry?.recordedAt)}
                        </span>
                      </div>
                      <strong style={{ fontSize: '1rem', fontWeight: 600 }}>
                        {formatScenarioLabel(previousAssessmentEntry?.scenario ?? null)}
                      </strong>
                      <span style={{ fontSize: '0.9rem', color: '#3a3a3c' }}>
                        Rating {previousAssessmentEntry?.overallRating} ·{' '}
                        {previousAssessmentEntry?.overallScore}/100 ·{' '}
                        {previousAssessmentEntry?.riskLevel} risk
                      </span>
                      {previousAssessmentEntry?.summary && (
                        <p
                          style={{
                            margin: 0,
                            fontSize: '0.875rem',
                            color: '#3a3a3c',
                            lineHeight: 1.5,
                          }}
                        >
                          {previousAssessmentEntry.summary}
                        </p>
                      )}
                    </div>
                  </div>
                  <div
                    style={{
                      border: '1px solid #e5e5e7',
                      borderRadius: '10px',
                      padding: '1.25rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.75rem',
                    }}
                  >
                    <h4
                      style={{
                        margin: 0,
                        fontSize: '0.95rem',
                        fontWeight: 600,
                      }}
                    >
                      System comparison
                    </h4>
                    <div
                      style={{
                        display: 'grid',
                        rowGap: '0.6rem',
                      }}
                    >
                      <div
                        style={{
                          display: 'grid',
                          gridTemplateColumns:
                            'minmax(160px, 2fr) repeat(3, minmax(110px, 1fr))',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          textTransform: 'uppercase',
                          letterSpacing: '0.08em',
                          color: '#6e6e73',
                        }}
                      >
                        <span>System</span>
                        <span>Current</span>
                        <span>Previous</span>
                        <span>Delta Score</span>
                      </div>
                      {systemComparisons.map((entry) => {
                        const scoreDeltaValue =
                          typeof entry.scoreDelta === 'number' ? entry.scoreDelta : null
                        return (
                          <div
                            key={entry.name}
                            style={{
                              display: 'grid',
                              gridTemplateColumns:
                                'minmax(160px, 2fr) repeat(3, minmax(110px, 1fr))',
                              alignItems: 'center',
                              background: '#f8f9fa',
                              borderRadius: '8px',
                              padding: '0.6rem 0.75rem',
                              fontSize: '0.85rem',
                              color: '#3a3a3c',
                            }}
                          >
                            <span style={{ fontWeight: 600 }}>{entry.name}</span>
                            <span>
                              {entry.latest
                                ? `${entry.latest.rating} · ${entry.latest.score}`
                                : '—'}
                            </span>
                            <span>
                              {entry.previous
                                ? `${entry.previous.rating} · ${entry.previous.score}`
                                : '—'}
                            </span>
                            <span
                              style={{
                                fontWeight: 600,
                                color:
                                  scoreDeltaValue === null
                                    ? '#6e6e73'
                                    : scoreDeltaValue > 0
                                    ? '#15803d'
                                    : scoreDeltaValue < 0
                                    ? '#c53030'
                                    : '#6e6e73',
                              }}
                            >
                              {scoreDeltaValue === null
                                ? '—'
                                : `${scoreDeltaValue > 0 ? '+' : ''}${scoreDeltaValue}`}
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                  <div
                    style={{
                      border: '1px solid #e5e5e7',
                      borderRadius: '10px',
                      padding: '1.25rem',
                      display: 'grid',
                      gap: '0.75rem',
                      background: '#f9f9fb',
                    }}
                  >
                    <h4
                      style={{
                        margin: 0,
                        fontSize: '0.95rem',
                        fontWeight: 600,
                      }}
                    >
                      Recommended actions
                    </h4>
                    <div
                      style={{
                        display: 'grid',
                        gap: '0.75rem',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                      }}
                    >
                      <div>
                        <strong
                          style={{
                            fontSize: '0.85rem',
                            textTransform: 'uppercase',
                            letterSpacing: '0.05em',
                            color: '#15803d',
                          }}
                        >
                          New this cycle
                        </strong>
                        {recommendedActionDiff.newActions.length > 0 ? (
                          <ul
                            style={{
                              margin: '0.4rem 0 0',
                              paddingLeft: '1.1rem',
                              fontSize: '0.85rem',
                              color: '#3a3a3c',
                              lineHeight: 1.4,
                            }}
                          >
                            {recommendedActionDiff.newActions.map((action) => (
                              <li key={action}>{action}</li>
                            ))}
                          </ul>
                        ) : (
                          <p
                            style={{
                              margin: '0.35rem 0 0',
                              fontSize: '0.825rem',
                              color: '#6e6e73',
                            }}
                          >
                            No new actions added.
                          </p>
                        )}
                      </div>
                      <div>
                        <strong
                          style={{
                            fontSize: '0.85rem',
                            textTransform: 'uppercase',
                            letterSpacing: '0.05em',
                            color: '#c53030',
                          }}
                        >
                          Completed / removed
                        </strong>
                        {recommendedActionDiff.clearedActions.length > 0 ? (
                          <ul
                            style={{
                              margin: '0.4rem 0 0',
                              paddingLeft: '1.1rem',
                              fontSize: '0.85rem',
                              color: '#3a3a3c',
                              lineHeight: 1.4,
                            }}
                          >
                            {recommendedActionDiff.clearedActions.map((action) => (
                              <li key={action}>{action}</li>
                            ))}
                          </ul>
                        ) : (
                          <p
                            style={{
                              margin: '0.35rem 0 0',
                              fontSize: '0.825rem',
                              color: '#6e6e73',
                            }}
                          >
                            No actions closed out.
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div
                  style={{
                    padding: '1.5rem',
                    textAlign: 'center',
                    color: '#6e6e73',
                    background: '#f5f5f7',
                    borderRadius: '10px',
                  }}
                >
                  <p style={{ margin: 0, fontSize: '0.9rem' }}>
                    Capture one more inspection to unlock comparison view.
                  </p>
                </div>
              )}
            </div>

            <div
              style={{
                border: '1px solid #e5e5e7',
                borderRadius: '12px',
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '0.75rem',
                }}
              >
                <h3
                  style={{
                    margin: 0,
                    fontSize: '1.0625rem',
                    fontWeight: 600,
                  }}
                >
                  Scenario Overrides
                </h3>
                {scenarioOverrideEntries.length > 1 && baseScenarioAssessment && (
                  <label
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      fontSize: '0.85rem',
                      color: '#3a3a3c',
                    }}
                  >
                    <span style={{ fontWeight: 600 }}>Baseline scenario</span>
                    <select
                      value={baseScenarioAssessment.scenario}
                      onChange={(event) =>
                        setScenarioComparisonBase(event.target.value as DevelopmentScenario)
                      }
                      style={{
                        borderRadius: '8px',
                        border: '1px solid #d2d2d7',
                        padding: '0.4rem 0.6rem',
                        fontSize: '0.85rem',
                      }}
                    >
                      {scenarioOverrideEntries.map((entry) => (
                        <option key={entry.scenario} value={entry.scenario}>
                          {formatScenarioLabel(entry.scenario)}
                        </option>
                      ))}
                    </select>
                  </label>
                )}
              </div>
              {scenarioAssessmentsError ? (
                <p
                  style={{
                    margin: 0,
                    fontSize: '0.85rem',
                    color: '#c53030',
                  }}
                >
                  {scenarioAssessmentsError}
                </p>
              ) : isLoadingScenarioAssessments ? (
                <div
                  style={{
                    padding: '1.5rem',
                    textAlign: 'center',
                    color: '#6e6e73',
                    background: '#f5f5f7',
                    borderRadius: '10px',
                  }}
                >
                  <p style={{ margin: 0, fontSize: '0.9rem' }}>Loading scenario overrides...</p>
                </div>
              ) : scenarioOverrideEntries.length === 0 ? (
                <div
                  style={{
                    padding: '1.5rem',
                    textAlign: 'center',
                    color: '#6e6e73',
                    background: '#f5f5f7',
                    borderRadius: '10px',
                  }}
                >
                  <p style={{ margin: 0, fontSize: '0.9rem' }}>
                    No scenario-specific overrides recorded yet. Save an inspection for a
                    specific scenario to compare outcomes.
                  </p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  {baseScenarioAssessment && (
                    <div
                      style={{
                        border: '1px solid #d2d2d7',
                        borderRadius: '12px',
                        padding: '1.25rem',
                        background: '#f5f5f7',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.6rem',
                      }}
                    >
                      <span
                        style={{
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          letterSpacing: '0.08em',
                          textTransform: 'uppercase',
                          color: '#6e6e73',
                        }}
                      >
                        Baseline scenario
                      </span>
                      <strong style={{ fontSize: '1rem', fontWeight: 600 }}>
                        {formatScenarioLabel(baseScenarioAssessment.scenario)}
                      </strong>
                      <div
                        style={{
                          display: 'flex',
                          flexWrap: 'wrap',
                          gap: '0.75rem',
                          alignItems: 'center',
                          color: '#3a3a3c',
                          fontSize: '0.9rem',
                        }}
                      >
                        <span>Rating {baseScenarioAssessment.overallRating}</span>
                        <span>{baseScenarioAssessment.overallScore}/100 score</span>
                        <span style={{ textTransform: 'capitalize' }}>
                          {baseScenarioAssessment.riskLevel} risk
                        </span>
                      </div>
                      <p
                        style={{
                          margin: 0,
                          fontSize: '0.9rem',
                          color: '#3a3a3c',
                          lineHeight: 1.5,
                        }}
                      >
                        {baseScenarioAssessment.summary}
                      </p>
                      {baseScenarioAssessment.scenarioContext && (
                        <p
                          style={{
                            margin: 0,
                            fontSize: '0.85rem',
                            color: '#0071e3',
                          }}
                        >
                          {baseScenarioAssessment.scenarioContext}
                        </p>
                      )}
                      {baseScenarioAssessment.recommendedActions.length > 0 && (
                        <div style={{ display: 'grid', gap: '0.4rem' }}>
                          <strong style={{ fontSize: '0.85rem' }}>Actions</strong>
                          <ul
                            style={{
                              margin: 0,
                              paddingLeft: '1.1rem',
                              fontSize: '0.85rem',
                              color: '#3a3a3c',
                              lineHeight: 1.4,
                            }}
                          >
                            {baseScenarioAssessment.recommendedActions.map((action) => (
                              <li key={action}>{action}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                  {scenarioComparisonEntries.length === 0 ? (
                    <div
                      style={{
                        padding: '1.25rem',
                        border: '1px solid #d2d2d7',
                        borderRadius: '12px',
                        background: '#ffffff',
                        color: '#6e6e73',
                        fontSize: '0.9rem',
                      }}
                    >
                      Capture another scenario-specific override to compare with the baseline.
                    </div>
                  ) : (
                    <div
                      style={{
                        display: 'grid',
                        gap: '1rem',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                      }}
                    >
                      {scenarioComparisonEntries.map((assessment) => {
                        if (!baseScenarioAssessment) {
                          return null
                        }
                        const scoreDelta = assessment.overallScore - baseScenarioAssessment.overallScore
                        const ratingInfo = describeRatingChange(
                          assessment.overallRating,
                          baseScenarioAssessment.overallRating,
                        )
                        const riskInfo = describeRiskChange(
                          assessment.riskLevel,
                          baseScenarioAssessment.riskLevel,
                        )
                        const toneColorMap: Record<'positive' | 'negative' | 'neutral', string> = {
                          positive: '#15803d',
                          negative: '#c53030',
                          neutral: '#6e6e73',
                        }

                        return (
                          <div
                            key={assessment.scenario}
                            style={{
                              border: '1px solid #e5e5e7',
                              borderRadius: '12px',
                              padding: '1.25rem',
                              display: 'flex',
                              flexDirection: 'column',
                              gap: '0.6rem',
                              background: '#ffffff',
                            }}
                          >
                            <strong style={{ fontSize: '1rem', fontWeight: 600 }}>
                              {formatScenarioLabel(assessment.scenario)}
                            </strong>
                            <div
                              style={{
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '0.4rem',
                                fontSize: '0.9rem',
                                color: '#3a3a3c',
                              }}
                            >
                              <span>
                                Score {assessment.overallScore}/100{' '}
                                <span
                                  style={{
                                    color:
                                      scoreDelta > 0
                                        ? '#15803d'
                                        : scoreDelta < 0
                                        ? '#c53030'
                                        : '#6e6e73',
                                    fontWeight: 600,
                                  }}
                                >
                                  {scoreDelta === 0
                                    ? 'Δ 0'
                                    : `Δ ${scoreDelta > 0 ? '+' : ''}${scoreDelta}`}
                                </span>
                              </span>
                              <span
                                style={{
                                  color: toneColorMap[ratingInfo.tone],
                                  fontWeight: 600,
                                }}
                              >
                                {ratingInfo.text}
                              </span>
                              <span
                                style={{
                                  color: toneColorMap[riskInfo.tone],
                                  fontWeight: 600,
                                }}
                              >
                                {riskInfo.text}
                              </span>
                            </div>
                            <p
                              style={{
                                margin: 0,
                                fontSize: '0.9rem',
                                color: '#3a3a3c',
                                lineHeight: 1.5,
                              }}
                            >
                              {assessment.summary}
                            </p>
                            {assessment.scenarioContext && (
                              <p
                                style={{
                                  margin: 0,
                                  fontSize: '0.85rem',
                                  color: '#0071e3',
                                }}
                              >
                                {assessment.scenarioContext}
                              </p>
                            )}
                            {assessment.recommendedActions.length > 0 && (
                              <div style={{ display: 'grid', gap: '0.4rem' }}>
                                <strong style={{ fontSize: '0.85rem' }}>Actions</strong>
                                <ul
                                  style={{
                                    margin: 0,
                                    paddingLeft: '1.1rem',
                                    fontSize: '0.85rem',
                                    color: '#3a3a3c',
                                    lineHeight: 1.4,
                                  }}
                                >
                                  {assessment.recommendedActions.map((action) => (
                                    <li key={action}>{action}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>

            <div
              style={{
                border: '1px solid #e5e5e7',
                borderRadius: '12px',
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '0.75rem',
                }}
              >
                <h3
                  style={{
                    margin: 0,
                    fontSize: '1.0625rem',
                    fontWeight: 600,
                  }}
                >
                  Record Inspection Assessment
                </h3>
                <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    onClick={() => {
                      setIsEditingAssessment((prev) => !prev)
                      setAssessmentSaveMessage(null)
                    }}
                    style={{
                      border: '1px solid #1d1d1f',
                      background: isEditingAssessment ? '#1d1d1f' : 'white',
                      color: isEditingAssessment ? 'white' : '#1d1d1f',
                      borderRadius: '9999px',
                      padding: '0.4rem 0.95rem',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    {isEditingAssessment ? 'Close editor' : 'Open editor'}
                  </button>
                  <button
                    type="button"
                    onClick={resetAssessmentDraft}
                    disabled={isSavingAssessment}
                    style={{
                      border: '1px solid #d2d2d7',
                      background: 'white',
                      color: '#1d1d1f',
                      borderRadius: '9999px',
                      padding: '0.4rem 0.95rem',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      cursor: isSavingAssessment ? 'not-allowed' : 'pointer',
                    }}
                  >
                    Reset
                  </button>
                </div>
              </div>
              {assessmentSaveMessage && (
                <p
                  style={{
                    margin: 0,
                    fontSize: '0.85rem',
                    color: assessmentSaveMessage.includes('success')
                      ? '#15803d'
                      : '#c53030',
                  }}
                >
                  {assessmentSaveMessage}
                </p>
              )}
              {isEditingAssessment && (
                <form
                  onSubmit={handleAssessmentSubmit}
                  style={{ display: 'grid', gap: '1.25rem' }}
                >
                  <div
                    style={{
                      display: 'grid',
                      gap: '1rem',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                    }}
                  >
                    <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                      <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Scenario</span>
                      <select
                        value={assessmentDraft.scenario}
                        onChange={(e) =>
                          handleAssessmentFieldChange(
                            'scenario',
                            e.target.value as DevelopmentScenario | 'all',
                          )
                        }
                        style={{
                          borderRadius: '8px',
                          border: '1px solid #d2d2d7',
                          padding: '0.55rem 0.75rem',
                          fontSize: '0.9rem',
                        }}
                      >
                        <option value="all">All scenarios</option>
                        {SCENARIO_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                      <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Overall rating</span>
                      <select
                        value={assessmentDraft.overallRating}
                        onChange={(e) => handleAssessmentFieldChange('overallRating', e.target.value)}
                        style={{
                          borderRadius: '8px',
                          border: '1px solid #d2d2d7',
                          padding: '0.55rem 0.75rem',
                          fontSize: '0.9rem',
                        }}
                      >
                        {CONDITION_RATINGS.map((rating) => (
                          <option key={rating} value={rating}>
                            {rating}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                      <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Overall score</span>
                      <input
                        type="number"
                        min={0}
                        max={100}
                        value={assessmentDraft.overallScore}
                        onChange={(e) => handleAssessmentFieldChange('overallScore', e.target.value)}
                        style={{
                          borderRadius: '8px',
                          border: '1px solid #d2d2d7',
                          padding: '0.55rem 0.75rem',
                          fontSize: '0.9rem',
                        }}
                      />
                    </label>
                    <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                      <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Risk level</span>
                      <select
                        value={assessmentDraft.riskLevel}
                        onChange={(e) => handleAssessmentFieldChange('riskLevel', e.target.value)}
                        style={{
                          borderRadius: '8px',
                          border: '1px solid #d2d2d7',
                          padding: '0.55rem 0.75rem',
                          fontSize: '0.9rem',
                        }}
                      >
                        {CONDITION_RISK_LEVELS.map((risk) => (
                          <option key={risk} value={risk}>
                            {risk.charAt(0).toUpperCase() + risk.slice(1)}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>

                  <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Summary</span>
                    <textarea
                      value={assessmentDraft.summary}
                      onChange={(e) => handleAssessmentFieldChange('summary', e.target.value)}
                      rows={3}
                      style={{
                        borderRadius: '8px',
                        border: '1px solid #d2d2d7',
                        padding: '0.75rem',
                        fontSize: '0.9rem',
                      }}
                    />
                  </label>

                  <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Scenario context</span>
                    <textarea
                      value={assessmentDraft.scenarioContext}
                      onChange={(e) =>
                        handleAssessmentFieldChange('scenarioContext', e.target.value)
                      }
                      rows={2}
                      style={{
                        borderRadius: '8px',
                        border: '1px solid #d2d2d7',
                        padding: '0.75rem',
                        fontSize: '0.9rem',
                      }}
                    />
                  </label>

                  <div style={{ display: 'grid', gap: '1rem' }}>
                    {assessmentDraft.systems.map((system, index) => (
                      <div
                        key={`${system.name}-${index}`}
                        style={{
                          border: '1px solid #e5e5e7',
                          borderRadius: '12px',
                          padding: '1rem',
                          display: 'grid',
                          gap: '0.75rem',
                        }}
                      >
                        <div
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            flexWrap: 'wrap',
                            gap: '0.5rem',
                          }}
                        >
                          <strong>{system.name}</strong>
                          <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <select
                              value={system.rating}
                              onChange={(e) =>
                                handleAssessmentSystemChange(index, 'rating', e.target.value)
                              }
                              style={{
                                borderRadius: '8px',
                                border: '1px solid #d2d2d7',
                                padding: '0.45rem 0.65rem',
                                fontSize: '0.85rem',
                              }}
                            >
                              {CONDITION_RATINGS.map((rating) => (
                                <option key={rating} value={rating}>
                                  {rating}
                                </option>
                              ))}
                            </select>
                            <input
                              type="number"
                              min={0}
                              max={100}
                              value={system.score}
                              onChange={(e) =>
                                handleAssessmentSystemChange(index, 'score', e.target.value)
                              }
                              style={{
                                borderRadius: '8px',
                                border: '1px solid #d2d2d7',
                                padding: '0.45rem 0.65rem',
                                width: '80px',
                                fontSize: '0.85rem',
                              }}
                            />
                          </div>
                        </div>
                        <textarea
                          value={system.notes}
                          onChange={(e) =>
                            handleAssessmentSystemChange(index, 'notes', e.target.value)
                          }
                          rows={2}
                          placeholder="Key findings"
                          style={{
                            borderRadius: '8px',
                            border: '1px solid #d2d2d7',
                            padding: '0.65rem',
                            fontSize: '0.85rem',
                          }}
                        />
                        <textarea
                          value={system.recommendedActions}
                          onChange={(e) =>
                            handleAssessmentSystemChange(
                              index,
                              'recommendedActions',
                              e.target.value,
                            )
                          }
                          rows={2}
                          placeholder="Recommended actions (one per line)"
                          style={{
                            borderRadius: '8px',
                            border: '1px solid #d2d2d7',
                            padding: '0.65rem',
                            fontSize: '0.85rem',
                          }}
                        />
                      </div>
                    ))}
                  </div>

                  <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>
                      Global recommended actions
                    </span>
                    <textarea
                      value={assessmentDraft.recommendedActionsText}
                      onChange={(e) =>
                        handleAssessmentFieldChange('recommendedActionsText', e.target.value)
                      }
                      rows={2}
                      placeholder="List actions (one per line)"
                      style={{
                        borderRadius: '8px',
                        border: '1px solid #d2d2d7',
                        padding: '0.75rem',
                        fontSize: '0.9rem',
                      }}
                    />
                  </label>

                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'flex-end',
                      gap: '0.75rem',
                      flexWrap: 'wrap',
                    }}
                  >
                    <button
                      type="button"
                      onClick={() => {
                        setIsEditingAssessment(false)
                        setAssessmentSaveMessage(null)
                      }}
                      disabled={isSavingAssessment}
                      style={{
                        border: '1px solid #d2d2d7',
                        background: 'white',
                        color: '#1d1d1f',
                        borderRadius: '9999px',
                        padding: '0.55rem 1.25rem',
                        fontSize: '0.875rem',
                        fontWeight: 600,
                        cursor: isSavingAssessment ? 'not-allowed' : 'pointer',
                      }}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isSavingAssessment}
                      style={{
                        border: 'none',
                        background: '#1d1d1f',
                        color: 'white',
                        borderRadius: '9999px',
                        padding: '0.55rem 1.5rem',
                        fontSize: '0.875rem',
                        fontWeight: 600,
                        cursor: isSavingAssessment ? 'not-allowed' : 'pointer',
                      }}
                    >
                      {isSavingAssessment ? 'Saving…' : 'Save inspection'}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        )}
      </section>
    </div>
  )
}
