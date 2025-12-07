import { useEffect, useMemo, useState } from 'react'

import {
  fetchBenchmarks,
  type PerformanceBenchmarkEntry,
} from '../../../api/performance'
import type { DealSummary } from '../../../api/deals'
import type { BenchmarkSet, BenchmarkComparison } from '../types'
import {
  formatCurrency,
  formatCurrencyDelta,
  formatDayDelta,
  formatDays,
  formatPercent,
  formatPercentagePointDelta,
  toPercentValue,
} from '../utils/formatters'

interface UseBenchmarksOptions {
  selectedDeal: DealSummary | null
  latestSnapshot: {
    conversionRate: number | null
    avgCycleDays: number | null
    weightedPipelineValue: number | null
  } | null
  locale: string
  fallbackText: string
  t: (key: string) => string
}

interface UseBenchmarksResult {
  benchmarks: BenchmarkSet
  benchmarksLoading: boolean
  benchmarksError: string | null
  benchmarkComparisons: BenchmarkComparison[]
  benchmarksHasContent: boolean
}

export function useBenchmarks({
  selectedDeal,
  latestSnapshot,
  locale,
  fallbackText,
  t,
}: UseBenchmarksOptions): UseBenchmarksResult {
  const [benchmarks, setBenchmarks] = useState<BenchmarkSet>({
    conversion: null,
    cycle: null,
    pipeline: null,
  })
  const [benchmarksLoading, setBenchmarksLoading] = useState<boolean>(false)
  const [benchmarksError, setBenchmarksError] = useState<string | null>(null)

  const primaryCurrency = selectedDeal?.estimatedValueCurrency ?? 'SGD'

  useEffect(() => {
    if (!selectedDeal) {
      setBenchmarks({
        conversion: null,
        cycle: null,
        pipeline: null,
      })
      setBenchmarksError(null)
      setBenchmarksLoading(false)
      return
    }
    const controller = new AbortController()
    let isActive = true
    setBenchmarksLoading(true)
    setBenchmarksError(null)
    ;(async () => {
      try {
        const [conversion, cycle, pipeline] = await Promise.all([
          fetchBenchmarks('conversion_rate', {
            assetType: selectedDeal.assetType,
            dealType: selectedDeal.dealType,
            signal: controller.signal,
          }),
          fetchBenchmarks('avg_cycle_days', {
            assetType: selectedDeal.assetType,
            dealType: selectedDeal.dealType,
            signal: controller.signal,
          }),
          fetchBenchmarks('pipeline_weighted_value', {
            signal: controller.signal,
          }),
        ])
        if (!isActive) {
          return
        }
        setBenchmarks({
          conversion: conversion[0] ?? null,
          cycle: cycle[0] ?? null,
          pipeline: pipeline[0] ?? null,
        })
      } catch (error) {
        if ((error as { name?: string }).name === 'AbortError') {
          return
        }
        console.error('Failed to load performance benchmarks', error)
        if (!controller.signal.aborted && isActive) {
          setBenchmarksError(t('agentPerformance.analytics.errors.benchmarks'))
        }
        setBenchmarks({
          conversion: null,
          cycle: null,
          pipeline: null,
        })
      } finally {
        if (isActive) {
          setBenchmarksLoading(false)
        }
      }
    })()

    return () => {
      isActive = false
      controller.abort()
    }
  }, [selectedDeal, t])

  const benchmarksHasContent =
    benchmarksLoading ||
    !!benchmarksError ||
    Boolean(benchmarks.conversion || benchmarks.cycle || benchmarks.pipeline)

  const benchmarkComparisons = useMemo<BenchmarkComparison[]>(() => {
    if (!latestSnapshot) {
      return []
    }

    const cohortLabelFor = (entry: PerformanceBenchmarkEntry | null) => {
      if (!entry) {
        return null
      }
      const key = `agentPerformance.analytics.benchmarks.cohort.${entry.cohort}`
      const translated = t(key)
      if (translated === key) {
        return entry.cohort.replace(/_/g, ' ')
      }
      return translated
    }

    const items: BenchmarkComparison[] = []

    const conversionActualPercent = toPercentValue(
      latestSnapshot.conversionRate,
    )
    const conversionBenchmarkPercent = toPercentValue(
      benchmarks.conversion?.valueNumeric ?? null,
    )
    const conversionDelta =
      conversionActualPercent !== null && conversionBenchmarkPercent !== null
        ? conversionActualPercent - conversionBenchmarkPercent
        : null

    if (benchmarks.conversion && conversionActualPercent !== null) {
      const benchmarkValue =
        conversionBenchmarkPercent !== null
          ? formatPercent(conversionBenchmarkPercent / 100, fallbackText)
          : null
      const deltaText = formatPercentagePointDelta(conversionDelta)
      items.push({
        key: 'conversion',
        label: t('agentPerformance.analytics.benchmarks.conversion'),
        actual: formatPercent(latestSnapshot.conversionRate, fallbackText),
        benchmark: benchmarkValue,
        cohort: cohortLabelFor(benchmarks.conversion),
        deltaText,
        deltaPositive: (conversionDelta ?? 0) >= 0,
      })
    }

    const cycleActual = latestSnapshot.avgCycleDays
    const cycleBenchmarkValue = benchmarks.cycle?.valueNumeric ?? null
    const cycleDelta =
      cycleActual !== null && cycleBenchmarkValue !== null
        ? cycleActual - cycleBenchmarkValue
        : null

    if (benchmarks.cycle && cycleActual !== null) {
      const benchmarkValue =
        cycleBenchmarkValue !== null
          ? formatDays(cycleBenchmarkValue, fallbackText)
          : null
      const deltaText = formatDayDelta(cycleDelta)
      items.push({
        key: 'cycle',
        label: t('agentPerformance.analytics.benchmarks.cycle'),
        actual: formatDays(cycleActual, fallbackText),
        benchmark: benchmarkValue,
        cohort: cohortLabelFor(benchmarks.cycle),
        deltaText,
        deltaPositive: (cycleDelta ?? 0) <= 0,
      })
    }

    const pipelineActual = latestSnapshot.weightedPipelineValue
    const pipelineBenchmarkValue = benchmarks.pipeline?.valueNumeric ?? null
    const pipelineDelta =
      pipelineActual !== null && pipelineBenchmarkValue !== null
        ? pipelineActual - pipelineBenchmarkValue
        : null

    if (benchmarks.pipeline && pipelineActual !== null) {
      const benchmarkValue =
        pipelineBenchmarkValue !== null
          ? formatCurrency(
              pipelineBenchmarkValue,
              primaryCurrency,
              locale,
              fallbackText,
            )
          : null
      const deltaText = formatCurrencyDelta(
        pipelineDelta,
        primaryCurrency,
        locale,
      )
      items.push({
        key: 'pipeline',
        label: t('agentPerformance.analytics.benchmarks.pipeline'),
        actual: formatCurrency(
          pipelineActual,
          primaryCurrency,
          locale,
          fallbackText,
        ),
        benchmark: benchmarkValue,
        cohort: cohortLabelFor(benchmarks.pipeline),
        deltaText,
        deltaPositive: (pipelineDelta ?? 0) >= 0,
      })
    }

    return items
  }, [benchmarks, fallbackText, latestSnapshot, locale, primaryCurrency, t])

  return {
    benchmarks,
    benchmarksLoading,
    benchmarksError,
    benchmarkComparisons,
    benchmarksHasContent,
  }
}
