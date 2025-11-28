import { useEffect, useState } from 'react'

import { fetchDealTimeline, type DealTimelineEvent } from '../../../api/deals'
import { isAbortError } from '../utils/formatters'

interface UseTimelineOptions {
  selectedDealId: string | null
  t: (key: string) => string
}

interface UseTimelineResult {
  timeline: DealTimelineEvent[]
  timelineLoading: boolean
  timelineError: string | null
}

export function useTimeline({
  selectedDealId,
  t,
}: UseTimelineOptions): UseTimelineResult {
  const [timeline, setTimeline] = useState<DealTimelineEvent[]>([])
  const [timelineLoading, setTimelineLoading] = useState<boolean>(false)
  const [timelineError, setTimelineError] = useState<string | null>(null)

  useEffect(() => {
    if (!selectedDealId) {
      setTimeline([])
      return
    }
    const abort = new AbortController()
    setTimelineLoading(true)
    setTimelineError(null)
    fetchDealTimeline(selectedDealId, abort.signal)
      .then((events) => {
        setTimeline(events)
      })
      .catch((error: unknown) => {
        if (isAbortError(error, abort)) {
          return
        }
        console.error('Failed to load timeline', error)
        setTimelineError(t('agentPerformance.errors.loadTimeline'))
      })
      .finally(() => {
        setTimelineLoading(false)
      })
    return () => {
      abort.abort()
    }
  }, [selectedDealId, t])

  return {
    timeline,
    timelineLoading,
    timelineError,
  }
}
