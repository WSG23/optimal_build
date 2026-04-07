import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import type {
  DevelopmentScenario,
  SiteAcquisitionResult,
} from '../../../../api/siteAcquisition'
import { DEFAULT_SCENARIO_ORDER } from '../../../../api/siteAcquisition'
import {
  QUICK_ANALYSIS_HISTORY_LIMIT,
  SCENARIO_METRIC_LABELS,
  SCENARIO_METRIC_PRIORITY,
  SCENARIO_OPTIONS,
} from '../constants'
import type {
  CaptureQuickAnalysisSnapshot,
  CaptureScenarioComparisonDatum,
  QuickAnalysisEntry,
  ScenarioComparisonKey,
  ScenarioComparisonMetric,
} from '../types'
import { formatCategoryName, safeNumber } from '../utils/formatters'

export interface UseCaptureScenarioComparisonOptions {
  capturedProperty: SiteAcquisitionResult | null
  activeScenario: DevelopmentScenario | 'all'
  currencySymbol: string
}

export interface UseCaptureScenarioComparisonResult {
  quickAnalysisScenarios: QuickAnalysisEntry[]
  comparisonScenarios: QuickAnalysisEntry[]
  scenarioComparisonData: CaptureScenarioComparisonDatum[]
  scenarioComparisonVisible: boolean
  activeScenarioSummary: {
    label: string
    headline: string
    detail: string | null
  }
  quickAnalysisHistory: CaptureQuickAnalysisSnapshot[]
  setQuickAnalysisHistory: React.Dispatch<
    React.SetStateAction<CaptureQuickAnalysisSnapshot[]>
  >
  formatMetricLabel: (key: string) => string
  formatScenarioMetricValue: (key: string, value: unknown) => string
  summariseScenarioMetrics: (
    metrics: Record<string, unknown> | null | undefined,
  ) => ScenarioComparisonMetric[]
  formatScenarioLabel: (
    scenario: DevelopmentScenario | 'all' | null | undefined,
  ) => string
  formatNumberMetric: (
    value: number | null | undefined,
    options?: Intl.NumberFormatOptions,
  ) => string
  formatCurrency: (value: number | null | undefined) => string
}

const FINANCE_HEADLINE_PATTERN =
  /\b(noi|revenue|yield|rent|capex|irr|roi|valuation|pricing|price|absorption|market)\b/i

function sanitiseCaptureHeadline(
  headline: string | null | undefined,
  fallbackLabel: string,
): string | null {
  if (!headline) {
    return null
  }
  const trimmed = headline.trim()
  if (!trimmed) {
    return null
  }
  if (FINANCE_HEADLINE_PATTERN.test(trimmed)) {
    return `${fallbackLabel} capture scenario scan available.`
  }
  return trimmed
}

function buildAggregateMetrics(
  capturedProperty: SiteAcquisitionResult | null,
  formatNumberMetric: (
    value: number | null | undefined,
    options?: Intl.NumberFormatOptions,
  ) => string,
): ScenarioComparisonMetric[] {
  if (!capturedProperty?.buildEnvelope) {
    return []
  }

  const envelope = capturedProperty.buildEnvelope
  const metrics: ScenarioComparisonMetric[] = []

  if (envelope.allowablePlotRatio != null) {
    metrics.push({
      key: 'plot_ratio',
      label: 'Plot ratio',
      value: formatNumberMetric(envelope.allowablePlotRatio, {
        maximumFractionDigits: 2,
      }),
    })
  }
  if (envelope.maxBuildableGfaSqm != null) {
    metrics.push({
      key: 'potential_gfa_sqm',
      label: 'Buildable GFA',
      value: `${formatNumberMetric(envelope.maxBuildableGfaSqm, {
        maximumFractionDigits: 0,
      })} sqm`,
    })
  }
  if (envelope.buildingHeightLimitM != null) {
    metrics.push({
      key: 'building_height_limit_m',
      label: 'Height limit',
      value: `${formatNumberMetric(envelope.buildingHeightLimitM, {
        maximumFractionDigits: 0,
      })} m`,
    })
  }

  return metrics
}

export function useCaptureScenarioComparison({
  capturedProperty,
  activeScenario,
  currencySymbol,
}: UseCaptureScenarioComparisonOptions): UseCaptureScenarioComparisonResult {
  const [quickAnalysisHistory, setQuickAnalysisHistory] = useState<
    CaptureQuickAnalysisSnapshot[]
  >([])
  const comparisonSnapshotSignatureRef = useRef<string | null>(null)

  const scenarioLookup = useMemo(
    () => new Map(SCENARIO_OPTIONS.map((option) => [option.value, option])),
    [],
  )

  const formatNumberMetric = useCallback(
    (value: number | null | undefined, options?: Intl.NumberFormatOptions) => {
      if (value === null || value === undefined || Number.isNaN(value)) {
        return '—'
      }
      return new Intl.NumberFormat('en-SG', {
        maximumFractionDigits: 1,
        ...options,
      }).format(value)
    },
    [],
  )

  const formatCurrency = useCallback(
    (value: number | null | undefined) => {
      if (value === null || value === undefined || Number.isNaN(value)) {
        return '—'
      }
      return `${currencySymbol}${new Intl.NumberFormat('en-US', {
        maximumFractionDigits: 0,
      }).format(value)}`
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
      if (key === 'use_groups' && Array.isArray(value)) {
        const groups = value.filter(
          (entry): entry is string => typeof entry === 'string' && !!entry,
        )
        return groups.length > 0 ? groups.join(', ') : '—'
      }
      const numeric = safeNumber(value)
      if (numeric !== null) {
        if (key.includes('_pct')) {
          const percent = numeric <= 1 ? numeric * 100 : numeric
          return `${formatNumberMetric(percent, { maximumFractionDigits: 1 })}%`
        }
        if (key.includes('_sqm')) {
          return `${formatNumberMetric(numeric, { maximumFractionDigits: 0 })} sqm`
        }
        if (key.endsWith('_m')) {
          return `${formatNumberMetric(numeric, { maximumFractionDigits: 1 })} m`
        }
        if (key.includes('_count')) {
          return formatNumberMetric(numeric, { maximumFractionDigits: 0 })
        }
        return formatNumberMetric(numeric, { maximumFractionDigits: 2 })
      }
      const text = String(value)
      return text.charAt(0).toUpperCase() + text.slice(1)
    },
    [formatNumberMetric],
  )

  const summariseScenarioMetrics = useCallback(
    (
      metrics: Record<string, unknown> | null | undefined,
    ): ScenarioComparisonMetric[] => {
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
      if (selected.length < 3 && Array.isArray(metrics['use_groups'])) {
        selected.push('use_groups')
      }

      return selected.map((key) => ({
        key,
        label: formatMetricLabel(key),
        value: formatScenarioMetricValue(key, metrics[key]),
      }))
    },
    [formatMetricLabel, formatScenarioMetricValue],
  )

  const formatScenarioLabel = useCallback(
    (scenario: DevelopmentScenario | 'all' | null | undefined) => {
      if (!scenario || scenario === 'all') {
        return 'All scenarios'
      }
      return (
        scenarioLookup.get(scenario)?.label ??
        formatCategoryName(String(scenario))
      )
    },
    [scenarioLookup],
  )

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

  const scenarioComparisonData = useMemo<
    CaptureScenarioComparisonDatum[]
  >(() => {
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

      if (isAll) {
        const scenarioCount = Math.max(sorted.length - 1, 0)
        return {
          key: scenarioKey,
          label: 'All scenarios',
          icon: '🌐',
          quickHeadline: `Instant capture scan across ${scenarioCount} tracked scenarios.`,
          quickMetrics: buildAggregateMetrics(
            capturedProperty,
            formatNumberMetric,
          ),
        }
      }

      const quickEntry = quickAnalysisScenarios.find(
        (entry) => entry.scenario === scenarioKey,
      )
      return {
        key: scenarioKey,
        label:
          option?.label ??
          formatScenarioLabel(scenarioKey as DevelopmentScenario),
        icon: option?.icon ?? '🏗️',
        quickHeadline: sanitiseCaptureHeadline(
          quickEntry?.headline ?? null,
          option?.label ??
            formatScenarioLabel(scenarioKey as DevelopmentScenario),
        ),
        quickMetrics: summariseScenarioMetrics(quickEntry?.metrics ?? {}),
      }
    })
  }, [
    capturedProperty,
    formatNumberMetric,
    formatScenarioLabel,
    quickAnalysisScenarios,
    scenarioLookup,
    summariseScenarioMetrics,
  ])

  const scenarioComparisonVisible = useMemo(
    () => scenarioComparisonData.some((row) => row.key !== 'all'),
    [scenarioComparisonData],
  )

  useEffect(() => {
    if (!capturedProperty?.quickAnalysis) {
      if (comparisonSnapshotSignatureRef.current !== null) {
        comparisonSnapshotSignatureRef.current = null
        setQuickAnalysisHistory([])
      }
      return
    }
    if (scenarioComparisonData.length === 0) {
      return
    }

    const comparisonSnapshot = scenarioComparisonData.map((row) => ({
      ...row,
      quickMetrics: row.quickMetrics.map((metric) => ({ ...metric })),
    }))

    const signature = [
      capturedProperty.propertyId,
      capturedProperty.quickAnalysis.generatedAt,
      ...comparisonSnapshot.map((row) =>
        [
          row.key,
          row.quickHeadline ?? '',
          row.quickMetrics
            .map((metric) => `${metric.key}:${metric.value}`)
            .join(','),
        ].join('#'),
      ),
    ].join('|')

    if (comparisonSnapshotSignatureRef.current === signature) {
      return
    }
    comparisonSnapshotSignatureRef.current = signature

    const snapshot: CaptureQuickAnalysisSnapshot = {
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
      return [snapshot, ...withoutTimestamp].slice(
        0,
        QUICK_ANALYSIS_HISTORY_LIMIT,
      )
    })
  }, [capturedProperty, scenarioComparisonData])

  const activeScenarioSummary = useMemo(() => {
    const targetKey: ScenarioComparisonKey =
      activeScenario === 'all' ? 'all' : activeScenario
    const row = scenarioComparisonData.find((entry) => entry.key === targetKey)
    if (!row) {
      const scenarioCount = Math.max(scenarioComparisonData.length - 1, 0)
      return {
        label:
          targetKey === 'all'
            ? 'All scenarios'
            : formatScenarioLabel(targetKey),
        headline:
          scenarioCount > 0
            ? `${scenarioCount} tracked scenarios`
            : 'No scenarios selected yet',
        detail: null,
      }
    }

    const detailMetric = row.quickMetrics[0]
    return {
      label: row.label,
      headline: row.quickHeadline ?? 'Instant scenario summary unavailable',
      detail: detailMetric
        ? `${detailMetric.label}: ${detailMetric.value}`
        : null,
    }
  }, [activeScenario, formatScenarioLabel, scenarioComparisonData])

  return {
    quickAnalysisScenarios,
    comparisonScenarios,
    scenarioComparisonData,
    scenarioComparisonVisible,
    activeScenarioSummary,
    quickAnalysisHistory,
    setQuickAnalysisHistory,
    formatMetricLabel,
    formatScenarioMetricValue,
    summariseScenarioMetrics,
    formatScenarioLabel,
    formatNumberMetric,
    formatCurrency,
  }
}
