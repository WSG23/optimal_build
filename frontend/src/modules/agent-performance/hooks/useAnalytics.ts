import { useEffect, useMemo, useState } from 'react'

import {
  fetchLatestSnapshot,
  fetchSnapshotsHistory,
  type PerformanceSnapshot,
} from '../../../api/performance'
import type { TrendDataPoint } from '../types'
import { toPercentValue } from '../utils/formatters'

interface UseAnalyticsOptions {
  selectedAgentId: string | null
  locale: string
  t: (key: string) => string
}

interface UseAnalyticsResult {
  latestSnapshot: PerformanceSnapshot | null
  snapshotHistory: PerformanceSnapshot[]
  analyticsLoading: boolean
  analyticsError: string | null
  trendData: TrendDataPoint[]
}

export function useAnalytics({
  selectedAgentId,
  locale,
  t,
}: UseAnalyticsOptions): UseAnalyticsResult {
  const [latestSnapshot, setLatestSnapshot] = useState<PerformanceSnapshot | null>(
    null,
  )
  const [snapshotHistory, setSnapshotHistory] = useState<PerformanceSnapshot[]>([])
  const [analyticsLoading, setAnalyticsLoading] = useState<boolean>(false)
  const [analyticsError, setAnalyticsError] = useState<string | null>(null)

  useEffect(() => {
    if (!selectedAgentId) {
      setLatestSnapshot(null)
      setSnapshotHistory([])
      setAnalyticsError(null)
      setAnalyticsLoading(false)
      return
    }
    const controller = new AbortController()
    let isActive = true
    setAnalyticsLoading(true)
    setAnalyticsError(null)
    ;(async () => {
      try {
        const [latest, history] = await Promise.all([
          fetchLatestSnapshot(selectedAgentId, controller.signal),
          fetchSnapshotsHistory(selectedAgentId, 30, controller.signal),
        ])
        if (!isActive) {
          return
        }
        setLatestSnapshot(latest)
        setSnapshotHistory(history)
      } catch (error) {
        if ((error as { name?: string }).name === 'AbortError') {
          return
        }
        console.error('Failed to load agent analytics', error)
        if (!controller.signal.aborted && isActive) {
          setAnalyticsError(t('agentPerformance.analytics.errors.analytics'))
        }
        setLatestSnapshot(null)
        setSnapshotHistory([])
      } finally {
        if (isActive) {
          setAnalyticsLoading(false)
        }
      }
    })()
    return () => {
      isActive = false
      controller.abort()
    }
  }, [selectedAgentId, t])

  const trendData = useMemo<TrendDataPoint[]>(() => {
    if (snapshotHistory.length === 0) {
      return []
    }
    const ordered = [...snapshotHistory].sort((a, b) => {
      const left = new Date(a.asOfDate).getTime()
      const right = new Date(b.asOfDate).getTime()
      return left - right
    })
    return ordered.map((snapshot) => {
      let label = snapshot.asOfDate
      try {
        label = new Intl.DateTimeFormat(locale, {
          month: 'short',
          day: 'numeric',
        }).format(new Date(snapshot.asOfDate))
      } catch (error) {
        console.warn('Failed to format chart label', error)
      }
      return {
        label,
        gross: snapshot.grossPipelineValue,
        weighted: snapshot.weightedPipelineValue,
        conversion: toPercentValue(snapshot.conversionRate ?? null),
        cycle: snapshot.avgCycleDays,
      }
    })
  }, [snapshotHistory, locale])

  return {
    latestSnapshot,
    snapshotHistory,
    analyticsLoading,
    analyticsError,
    trendData,
  }
}
