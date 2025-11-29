/**
 * Hook for scenario comparison and derived analysis data
 *
 * Handles:
 * - Scenario comparison data aggregation
 * - System comparisons between assessment entries
 * - Trend insights generation
 * - Quick analysis snapshots
 * - Assessment comparison summaries
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type {
  ConditionAssessment,
  DevelopmentScenario,
  ChecklistSummary,
  SiteAcquisitionResult,
} from '../../../../api/siteAcquisition'
import { DEFAULT_SCENARIO_ORDER } from '../../../../api/siteAcquisition'
import type {
  ConditionInsightView,
  InsightSeverity,
  QuickAnalysisEntry,
  QuickAnalysisSnapshot,
  ScenarioComparisonDatum,
  ScenarioComparisonKey,
  ScenarioComparisonMetric,
  SystemComparisonEntry,
} from '../types'
import {
  CONDITION_RATINGS,
  CONDITION_RISK_LEVELS,
  INSIGHT_SEVERITY_ORDER,
  QUICK_ANALYSIS_HISTORY_LIMIT,
  SCENARIO_METRIC_LABELS,
  SCENARIO_METRIC_PRIORITY,
  SCENARIO_OPTIONS,
} from '../constants'
import {
  buildSystemInsightTitle,
  classifySystemSeverity,
  normaliseInsightSeverity,
  systemSpecialistHint,
} from '../utils/insights'
import { formatCategoryName, formatScoreDelta, safeNumber, slugify } from '../utils/formatters'

// ============================================================================
// Types
// ============================================================================

export interface UseScenarioComparisonOptions {
  /** The captured property result (may be null before capture) */
  capturedProperty: SiteAcquisitionResult | null
  /** The currently active development scenario filter */
  activeScenario: DevelopmentScenario | 'all'
  /** Current condition assessment */
  conditionAssessment: ConditionAssessment | null
  /** Assessment history for trend analysis */
  assessmentHistory: ConditionAssessment[]
  /** Scenario-specific assessments */
  scenarioAssessments: ConditionAssessment[]
  /** Checklist progress by scenario */
  scenarioChecklistProgress: Record<string, { total: number; completed: number }>
  /** Display summary for checklist */
  displaySummary: ChecklistSummary | null
  /** Currency symbol for formatting */
  currencySymbol: string
}

export interface UseScenarioComparisonResult {
  // Scenario data
  quickAnalysisScenarios: QuickAnalysisEntry[]
  comparisonScenarios: QuickAnalysisEntry[]
  scenarioOverrideEntries: (ConditionAssessment & { scenario: DevelopmentScenario })[]
  scenarioAssessmentsMap: Map<DevelopmentScenario, ConditionAssessment>

  // Comparison data
  scenarioComparisonData: ScenarioComparisonDatum[]
  scenarioComparisonTableRows: ScenarioComparisonDatum[]
  scenarioComparisonVisible: boolean
  activeScenarioSummary: {
    label: string
    headline: string
    detail: string | null
  }

  // Scenario assessments comparison
  baseScenarioAssessment: ConditionAssessment | null
  scenarioComparisonBase: DevelopmentScenario | null
  setScenarioComparisonBase: React.Dispatch<React.SetStateAction<DevelopmentScenario | null>>
  scenarioComparisonEntries: ConditionAssessment[]

  // System comparisons
  systemComparisons: SystemComparisonEntry[]
  systemComparisonMap: Map<string, SystemComparisonEntry>
  systemTrendInsights: ConditionInsightView[]

  // Insights
  backendInsightViews: ConditionInsightView[]
  combinedConditionInsights: ConditionInsightView[]
  insightSubtitle: string

  // Assessment trend summary
  recommendedActionDiff: { newActions: string[]; clearedActions: string[] }
  comparisonSummary: {
    scoreDelta: number
    ratingTrend: 'improved' | 'declined' | 'same' | 'changed'
    riskTrend: 'improved' | 'declined' | 'same' | 'changed'
    ratingChanged: boolean
    riskChanged: boolean
  } | null

  // Quick analysis history
  quickAnalysisHistory: QuickAnalysisSnapshot[]
  setQuickAnalysisHistory: React.Dispatch<React.SetStateAction<QuickAnalysisSnapshot[]>>

  // Derived values from assessment history
  latestAssessmentEntry: ConditionAssessment | null
  previousAssessmentEntry: ConditionAssessment | null

  // Formatting helpers
  formatMetricLabel: (key: string) => string
  formatScenarioMetricValue: (key: string, value: unknown) => string
  summariseScenarioMetrics: (
    metrics: Record<string, unknown> | null | undefined,
  ) => ScenarioComparisonMetric[]
  formatScenarioLabel: (scenario: ConditionAssessment['scenario']) => string
  formatNumberMetric: (
    value: number | null | undefined,
    options?: Intl.NumberFormatOptions,
  ) => string
  formatCurrency: (value: number | null | undefined) => string
  convertAssessmentInsights: (
    assessment: ConditionAssessment | null | undefined,
  ) => ConditionInsightView[]
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useScenarioComparison({
  capturedProperty,
  activeScenario,
  conditionAssessment,
  assessmentHistory,
  scenarioAssessments,
  scenarioChecklistProgress,
  displaySummary,
  currencySymbol,
}: UseScenarioComparisonOptions): UseScenarioComparisonResult {
  // State
  const [scenarioComparisonBase, setScenarioComparisonBase] =
    useState<DevelopmentScenario | null>(null)
  const [quickAnalysisHistory, setQuickAnalysisHistory] = useState<QuickAnalysisSnapshot[]>(
    [],
  )
  const comparisonSnapshotSignatureRef = useRef<string | null>(null)

  // Scenario lookup
  const scenarioLookup = useMemo(
    () => new Map(SCENARIO_OPTIONS.map((option) => [option.value, option])),
    [],
  )

  // ============================================================================
  // Formatting Helpers
  // ============================================================================

  const formatNumberMetric = useCallback(
    (value: number | null | undefined, options?: Intl.NumberFormatOptions) => {
      if (value === null || value === undefined || Number.isNaN(value)) {
        return '—'
      }
      const formatter = new Intl.NumberFormat('en-SG', {
        maximumFractionDigits: 1,
        ...options,
      })
      return formatter.format(value)
    },
    [],
  )

  const formatCurrency = useCallback(
    (value: number | null | undefined) => {
      if (value === null || value === undefined || Number.isNaN(value)) {
        return '—'
      }
      const formattedNumber = new Intl.NumberFormat('en-US', {
        maximumFractionDigits: 0,
      }).format(value)
      return `${currencySymbol}${formattedNumber}`
    },
    [currencySymbol],
  )

  const formatMetricLabel = useCallback((key: string) => {
    if (SCENARIO_METRIC_LABELS[key]) {
      return SCENARIO_METRIC_LABELS[key]
    }
    return key
      .split('_')
      .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
      .join(' ')
  }, [])

  const formatScenarioMetricValue = useCallback(
    (key: string, value: unknown) => {
      if (value === null || value === undefined || value === '') {
        return '—'
      }
      const numeric = safeNumber(value)
      if (numeric !== null) {
        if (key.includes('_pct') || key.endsWith('_rate')) {
          return `${formatNumberMetric(numeric * 100, { maximumFractionDigits: 1 })}%`
        }
        if (key.includes('_sqm')) {
          return `${formatNumberMetric(numeric, { maximumFractionDigits: 0 })} sqm`
        }
        if (
          key === 'annual_noi' ||
          key === 'estimated_capex' ||
          key === 'average_psf_price' ||
          key === 'average_monthly_rent'
        ) {
          return formatCurrency(numeric)
        }
        if (key.includes('_count')) {
          return formatNumberMetric(numeric, { maximumFractionDigits: 0 })
        }
        if (key === 'target_lease_term_years') {
          return `${formatNumberMetric(numeric, { maximumFractionDigits: 1 })} yrs`
        }
        return formatNumberMetric(numeric, { maximumFractionDigits: 2 })
      }
      const text = String(value)
      return text.charAt(0).toUpperCase() + text.slice(1)
    },
    [formatCurrency, formatNumberMetric],
  )

  const summariseScenarioMetrics = useCallback(
    (metrics: Record<string, unknown> | null | undefined): ScenarioComparisonMetric[] => {
      if (!metrics) {
        return []
      }
      const selected: string[] = []
      for (const key of SCENARIO_METRIC_PRIORITY) {
        const value = metrics[key]
        if (value !== null && value !== undefined && value !== '') {
          selected.push(key)
        }
        if (selected.length >= 3) {
          break
        }
      }
      if (selected.length < 3) {
        for (const key of Object.keys(metrics)) {
          if (selected.length >= 3) {
            break
          }
          if (
            metrics[key] !== null &&
            metrics[key] !== undefined &&
            metrics[key] !== '' &&
            !selected.includes(key)
          ) {
            selected.push(key)
          }
        }
      }
      return selected.map((key) => ({
        key,
        label: formatMetricLabel(key),
        value: String(metrics[key]),
      }))
    },
    [formatMetricLabel],
  )

  const formatScenarioLabel = useCallback(
    (scenario: ConditionAssessment['scenario']) => {
      if (!scenario || (typeof scenario === 'string' && scenario === 'all')) {
        return 'All scenarios'
      }
      const entry = scenarioLookup.get(scenario as DevelopmentScenario)
      if (entry) {
        return entry.label
      }
      return formatCategoryName(String(scenario))
    },
    [scenarioLookup],
  )

  const convertAssessmentInsights = useCallback(
    (assessment: ConditionAssessment | null | undefined): ConditionInsightView[] => {
      if (!assessment?.insights) {
        return []
      }
      return assessment.insights.map((insight, index) => ({
        id: insight.id || `assessment-insight-${index}`,
        severity: normaliseInsightSeverity(insight.severity),
        title: insight.title,
        detail: insight.detail,
        specialist: insight.specialist ?? null,
      }))
    },
    [],
  )

  // ============================================================================
  // Derived Values from Assessment History
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
  // Quick Analysis Data
  // ============================================================================

  const quickAnalysis = capturedProperty?.quickAnalysis ?? null

  const quickAnalysisScenarios = useMemo(() => {
    const scenarios = quickAnalysis?.scenarios ?? []
    return Array.isArray(scenarios) ? scenarios : []
  }, [quickAnalysis])

  const comparisonScenarios = useMemo(
    () =>
      activeScenario === 'all'
        ? quickAnalysisScenarios
        : quickAnalysisScenarios.filter(
            (scenario) => scenario.scenario === activeScenario,
          ),
    [activeScenario, quickAnalysisScenarios],
  )

  // ============================================================================
  // Scenario Override Entries
  // ============================================================================

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

  const scenarioAssessmentsMap = useMemo(() => {
    const map = new Map<DevelopmentScenario, ConditionAssessment>()
    scenarioAssessments.forEach((assessment) => {
      if (assessment.scenario && assessment.scenario !== 'all') {
        map.set(assessment.scenario, assessment)
      }
    })
    if (
      conditionAssessment &&
      conditionAssessment.scenario &&
      conditionAssessment.scenario !== 'all'
    ) {
      map.set(conditionAssessment.scenario, conditionAssessment)
    }
    return map
  }, [scenarioAssessments, conditionAssessment])

  // ============================================================================
  // System Comparisons
  // ============================================================================

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

  const systemComparisonMap = useMemo(
    () => new Map(systemComparisons.map((entry) => [entry.name, entry])),
    [systemComparisons],
  )

  // ============================================================================
  // System Trend Insights
  // ============================================================================

  const systemTrendInsights = useMemo(() => {
    if (systemComparisons.length === 0) {
      return []
    }
    const insights = systemComparisons
      .map((entry) => {
        if (!entry.latest) {
          return null
        }
        const delta =
          typeof entry.scoreDelta === 'number' && Number.isFinite(entry.scoreDelta)
            ? entry.scoreDelta
            : null
        const severity = classifySystemSeverity(entry.latest.rating, delta)
        if (severity === 'neutral') {
          return null
        }
        const previousRating = entry.previous?.rating ?? null
        const previousScore =
          typeof entry.previous?.score === 'number' ? entry.previous.score : null
        let detail: string
        if (delta !== null && delta !== 0 && previousRating && previousScore !== null) {
          const deltaLabel = formatScoreDelta(delta)
          detail = `${entry.name} ${deltaLabel} vs last inspection (${previousRating} · ${previousScore}/100 → ${entry.latest.rating} · ${entry.latest.score}/100).`
        } else if (delta !== null && delta !== 0) {
          const deltaLabel = formatScoreDelta(delta)
          detail = `${entry.name} ${deltaLabel}; now ${entry.latest.rating} · ${entry.latest.score}/100.`
        } else if (previousRating) {
          detail = `${entry.name} holds at ${entry.latest.rating} · ${entry.latest.score}/100 (was ${previousRating}).`
        } else {
          detail = `${entry.name} recorded as ${entry.latest.rating} · ${entry.latest.score}/100.`
        }
        return {
          id: `trend-${slugify(entry.name)}`,
          severity: severity as InsightSeverity,
          title: buildSystemInsightTitle(entry.name, severity as InsightSeverity, delta),
          detail,
          specialist: systemSpecialistHint(entry.name),
        }
      })
      .filter((value): value is ConditionInsightView => value !== null)

    insights.sort((a, b) => {
      const severityRank =
        INSIGHT_SEVERITY_ORDER[a.severity] - INSIGHT_SEVERITY_ORDER[b.severity]
      if (severityRank !== 0) {
        return severityRank
      }
      return a.title.localeCompare(b.title)
    })

    return insights.slice(0, 3)
  }, [systemComparisons])

  // ============================================================================
  // Backend Insight Views
  // ============================================================================

  const backendInsightViews = useMemo<ConditionInsightView[]>(() => {
    if (!conditionAssessment?.insights) {
      return []
    }
    return conditionAssessment.insights.map((insight, index) => ({
      id: insight.id || `backend-${index}`,
      severity: normaliseInsightSeverity(insight.severity),
      title: insight.title,
      detail: insight.detail,
      specialist: insight.specialist ?? null,
    }))
  }, [conditionAssessment?.insights])

  const combinedConditionInsights = useMemo<ConditionInsightView[]>(() => {
    const merged = new Map<string, ConditionInsightView>()
    backendInsightViews.forEach((insight, index) => {
      const key = insight.id || `backend-${index}`
      merged.set(key, { ...insight, id: key })
    })
    systemTrendInsights.forEach((insight) => {
      merged.set(insight.id, insight)
    })
    return Array.from(merged.values())
  }, [backendInsightViews, systemTrendInsights])

  const backendInsightCount = backendInsightViews.length
  const trendInsightCount = systemTrendInsights.length
  const insightSubtitle =
    backendInsightCount > 0 && trendInsightCount > 0
      ? 'Heuristic insights combined with inspection deltas.'
      : backendInsightCount > 0
        ? 'Heuristic insights generated from property data and specialist playbooks.'
        : 'Inspection deltas compared with previous assessments.'

  // ============================================================================
  // Scenario Comparison Base Management
  // ============================================================================

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
    if (!quickAnalysisScenarios.length) {
      return []
    }
    return scenarioOverrideEntries.filter(
      (assessment) => assessment !== baseScenarioAssessment,
    )
  }, [scenarioOverrideEntries, baseScenarioAssessment, quickAnalysisScenarios.length])

  // ============================================================================
  // Scenario Comparison Data
  // ============================================================================

  const scenarioComparisonData = useMemo<ScenarioComparisonDatum[]>(() => {
    const scenarioOrder = new Map(
      DEFAULT_SCENARIO_ORDER.map((scenario, index) => [scenario, index]),
    )
    const keys = new Set<ScenarioComparisonKey>()
    keys.add('all')
    quickAnalysisScenarios.forEach((scenario) => {
      if (typeof scenario.scenario === 'string') {
        keys.add(scenario.scenario as DevelopmentScenario)
      }
    })
    Object.keys(scenarioChecklistProgress).forEach((scenario) => {
      keys.add(scenario as DevelopmentScenario)
    })
    scenarioAssessments.forEach((assessment) => {
      if (assessment.scenario) {
        keys.add(assessment.scenario)
      }
    })

    const sorted = Array.from(keys).sort((a, b) => {
      if (a === 'all') return -1
      if (b === 'all') return 1
      return (scenarioOrder.get(a) ?? 999) - (scenarioOrder.get(b) ?? 999)
    })

    return sorted.map((scenarioKey) => {
      const isAll = scenarioKey === 'all'
      const option = !isAll
        ? scenarioLookup.get(scenarioKey as DevelopmentScenario)
        : null
      const label = isAll
        ? 'All scenarios'
        : option?.label ?? formatScenarioLabel(scenarioKey as DevelopmentScenario)
      const icon = isAll ? '🌐' : option?.icon ?? '🏗️'

      let quickHeadline: string | null = null
      let quickMetrics: ScenarioComparisonMetric[] = []
      if (isAll) {
        const scenarioCount = Math.max(sorted.length - 1, 0)
        quickHeadline = `Aggregate across ${scenarioCount} tracked scenarios.`
        if (displaySummary) {
          quickMetrics = [
            {
              key: 'checklist',
              label: 'Checklist',
              value: `${displaySummary.completed}/${displaySummary.total}`,
            },
            {
              key: 'completion',
              label: 'Completion',
              value: `${displaySummary.completionPercentage}%`,
            },
          ]
        }
      } else {
        const quickEntry = quickAnalysisScenarios.find(
          (entry) => entry.scenario === scenarioKey,
        )
        quickHeadline = quickEntry?.headline ?? null
        quickMetrics = summariseScenarioMetrics(quickEntry?.metrics ?? {})
      }

      const checklistEntry = isAll
        ? displaySummary
        : scenarioChecklistProgress[scenarioKey as DevelopmentScenario]
      const checklistCompleted =
        typeof checklistEntry?.completed === 'number' ? checklistEntry.completed : null
      const checklistTotal =
        typeof checklistEntry?.total === 'number' ? checklistEntry.total : null
      const checklistPercent =
        checklistCompleted !== null && checklistTotal && checklistTotal > 0
          ? Math.round((checklistCompleted / checklistTotal) * 100)
          : null

      let conditionEntry: ConditionAssessment | null = null
      if (isAll) {
        if (
          conditionAssessment &&
          (!conditionAssessment.scenario || conditionAssessment.scenario === 'all')
        ) {
          conditionEntry = conditionAssessment
        }
      } else {
        const mapped = scenarioAssessmentsMap.get(scenarioKey as DevelopmentScenario)
        if (mapped) {
          conditionEntry = mapped
        } else if (conditionAssessment?.scenario === scenarioKey) {
          conditionEntry = conditionAssessment
        }
      }

      const insights = isAll
        ? combinedConditionInsights
        : convertAssessmentInsights(conditionEntry)
      const sortedInsights = [...insights].sort((a, b) => {
        const rankA = INSIGHT_SEVERITY_ORDER[a.severity]
        const rankB = INSIGHT_SEVERITY_ORDER[b.severity]
        if (rankA !== rankB) {
          return rankA - rankB
        }
        return a.title.localeCompare(b.title)
      })
      const primaryInsight = sortedInsights[0] ?? null

      const conditionRating = conditionEntry?.overallRating ?? null
      const conditionScore =
        typeof conditionEntry?.overallScore === 'number'
          ? conditionEntry.overallScore
          : typeof conditionEntry?.overallScore === 'string'
            ? Number(conditionEntry.overallScore)
            : null
      const riskLevel = conditionEntry?.riskLevel ?? null
      const recommendedAction = isAll
        ? conditionAssessment?.recommendedActions?.[0] ?? null
        : conditionEntry?.recommendedActions?.[0] ?? null
      const inspectorName =
        conditionEntry?.inspectorName ??
        (isAll ? conditionAssessment?.inspectorName ?? null : null)
      const recordedAt =
        conditionEntry?.recordedAt ??
        (isAll ? conditionAssessment?.recordedAt ?? null : null)
      const source: 'manual' | 'heuristic' =
        conditionEntry && conditionEntry.recordedAt ? 'manual' : 'heuristic'

      return {
        key: scenarioKey,
        label,
        icon,
        quickHeadline,
        quickMetrics,
        conditionRating,
        conditionScore,
        riskLevel,
        checklistCompleted,
        checklistTotal,
        checklistPercent,
        insights,
        primaryInsight,
        recommendedAction,
        recordedAt,
        inspectorName,
        source,
      }
    })
  }, [
    quickAnalysisScenarios,
    scenarioChecklistProgress,
    scenarioAssessments,
    scenarioAssessmentsMap,
    conditionAssessment,
    combinedConditionInsights,
    displaySummary,
    scenarioLookup,
    formatScenarioLabel,
    summariseScenarioMetrics,
    convertAssessmentInsights,
  ])

  const scenarioComparisonTableRows = useMemo(
    () => scenarioComparisonData.filter((row) => row.key !== 'all'),
    [scenarioComparisonData],
  )

  const scenarioComparisonVisible = scenarioComparisonTableRows.length > 0

  // ============================================================================
  // Quick Analysis History Snapshot
  // ============================================================================

  useEffect(() => {
    if (!capturedProperty || !capturedProperty.quickAnalysis) {
      if (comparisonSnapshotSignatureRef.current !== null) {
        comparisonSnapshotSignatureRef.current = null
        setQuickAnalysisHistory([])
      }
      return
    }
    if (scenarioComparisonData.length === 0) {
      return
    }

    const comparisonSnapshot = scenarioComparisonData.map((row, index) => ({
      ...row,
      quickMetrics: row.quickMetrics.map((metric) => ({ ...metric })),
      insights: row.insights.map((insight, insightIndex) => ({
        ...insight,
        id: insight.id || `snapshot-${index}-${insightIndex}`,
      })),
      primaryInsight: row.primaryInsight ? { ...row.primaryInsight } : null,
    }))

    const signatureParts = [
      capturedProperty.propertyId,
      capturedProperty.quickAnalysis.generatedAt,
      ...comparisonSnapshot.map((row) =>
        [
          row.key,
          row.conditionRating ?? '',
          row.conditionScore ?? '',
          row.riskLevel ?? '',
          row.quickMetrics.map((metric) => `${metric.label}:${metric.value ?? ''}`).join(
            ',',
          ),
          row.primaryInsight?.id ?? '',
          row.recommendedAction ?? '',
        ].join('#'),
      ),
    ]
    const signature = signatureParts.join('|')
    if (comparisonSnapshotSignatureRef.current === signature) {
      return
    }
    comparisonSnapshotSignatureRef.current = signature

    const snapshot: QuickAnalysisSnapshot = {
      propertyId: capturedProperty.propertyId,
      generatedAt: capturedProperty.quickAnalysis.generatedAt,
      scenarios: capturedProperty.quickAnalysis.scenarios,
      comparison: comparisonSnapshot,
    }

    setQuickAnalysisHistory((previous) => {
      const sameProperty = previous.filter(
        (entry) => entry.propertyId === snapshot.propertyId,
      )
      const withoutTimestamp = sameProperty.filter(
        (entry) => entry.generatedAt !== snapshot.generatedAt,
      )
      return [snapshot, ...withoutTimestamp].slice(0, QUICK_ANALYSIS_HISTORY_LIMIT)
    })
  }, [capturedProperty, scenarioComparisonData])

  // ============================================================================
  // Active Scenario Summary
  // ============================================================================

  const scenarioFocusOptions = useMemo(() => {
    const collected = new Set<DevelopmentScenario>()
    quickAnalysisScenarios.forEach((scenario) =>
      collected.add(scenario.scenario as DevelopmentScenario),
    )
    return ['all', ...Array.from(collected)] as Array<'all' | DevelopmentScenario>
  }, [quickAnalysisScenarios])

  const activeScenarioSummary = useMemo(() => {
    const targetKey: ScenarioComparisonKey =
      activeScenario === 'all' ? 'all' : (activeScenario as DevelopmentScenario)
    const row = scenarioComparisonData.find((entry) => entry.key === targetKey)
    if (!row) {
      const scenarioCount = Math.max(scenarioFocusOptions.length - 1, 0)
      return {
        label: targetKey === 'all' ? 'All scenarios' : formatScenarioLabel(targetKey),
        headline:
          scenarioCount > 0
            ? `${scenarioCount} tracked scenarios`
            : 'No scenarios selected yet',
        detail: null as string | null,
      }
    }

    const headline =
      row.quickHeadline ??
      (row.conditionRating
        ? `Condition ${row.conditionRating}${
            row.conditionScore !== null ? ` · ${row.conditionScore}/100` : ''
          }`
        : 'Scenario summary unavailable')
    const detailMetric = row.quickMetrics[0]
    const detail = detailMetric ? `${detailMetric.label}: ${detailMetric.value}` : null

    return {
      label: row.label,
      headline,
      detail,
    }
  }, [activeScenario, scenarioComparisonData, scenarioFocusOptions.length, formatScenarioLabel])

  // ============================================================================
  // Assessment Comparison Summary
  // ============================================================================

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
    const scoreDelta =
      latestAssessmentEntry.overallScore - previousAssessmentEntry.overallScore
    const latestRatingIndex = (CONDITION_RATINGS as readonly string[]).indexOf(
      latestAssessmentEntry.overallRating,
    )
    const previousRatingIndex = (CONDITION_RATINGS as readonly string[]).indexOf(
      previousAssessmentEntry.overallRating,
    )
    let ratingTrend: 'improved' | 'declined' | 'same' | 'changed' = 'same'
    if (latestRatingIndex !== -1 && previousRatingIndex !== -1) {
      if (latestRatingIndex < previousRatingIndex) {
        ratingTrend = 'improved'
      } else if (latestRatingIndex > previousRatingIndex) {
        ratingTrend = 'declined'
      } else {
        ratingTrend = 'same'
      }
    } else if (
      latestAssessmentEntry.overallRating !== previousAssessmentEntry.overallRating
    ) {
      ratingTrend = 'changed'
    }
    const latestRiskIndex = (CONDITION_RISK_LEVELS as readonly string[]).indexOf(
      latestAssessmentEntry.riskLevel,
    )
    const previousRiskIndex = (CONDITION_RISK_LEVELS as readonly string[]).indexOf(
      previousAssessmentEntry.riskLevel,
    )
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
      ratingChanged:
        latestAssessmentEntry.overallRating !== previousAssessmentEntry.overallRating,
      riskChanged: latestAssessmentEntry.riskLevel !== previousAssessmentEntry.riskLevel,
    }
  }, [latestAssessmentEntry, previousAssessmentEntry])

  // ============================================================================
  // Return
  // ============================================================================

  return {
    // Scenario data
    quickAnalysisScenarios,
    comparisonScenarios,
    scenarioOverrideEntries,
    scenarioAssessmentsMap,

    // Comparison data
    scenarioComparisonData,
    scenarioComparisonTableRows,
    scenarioComparisonVisible,
    activeScenarioSummary,

    // Scenario assessments comparison
    baseScenarioAssessment,
    scenarioComparisonBase,
    setScenarioComparisonBase,
    scenarioComparisonEntries,

    // System comparisons
    systemComparisons,
    systemComparisonMap,
    systemTrendInsights,

    // Insights
    backendInsightViews,
    combinedConditionInsights,
    insightSubtitle,

    // Assessment trend summary
    recommendedActionDiff,
    comparisonSummary,

    // Quick analysis history
    quickAnalysisHistory,
    setQuickAnalysisHistory,

    // Derived values from assessment history
    latestAssessmentEntry,
    previousAssessmentEntry,

    // Formatting helpers
    formatMetricLabel,
    formatScenarioMetricValue,
    summariseScenarioMetrics,
    formatScenarioLabel,
    formatNumberMetric,
    formatCurrency,
    convertAssessmentInsights,
  }
}
